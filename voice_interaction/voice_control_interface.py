"""
语音交互控制接口 - Voice Control Interface
==========================================

提供统一的语音交互控制接口，集成：
- 语音识别 (ASR)
- 语音合成 (TTS)
- 声纹识别和情感分析
- 语音命令处理
- 对话管理

Author: MiniMax Agent
Date: 2025-11-06
"""

import asyncio
import logging
import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Union, Callable, AsyncGenerator
from pathlib import Path
from datetime import datetime, timedelta
import time
import uuid

# 音频处理
import numpy as np
import sounddevice as sd
import soundfile as sf
from pydub import AudioSegment

# 异步支持
import aiofiles
import aiohttp

# 框架集成
from .asr_framework import ASRFramework, ASRConfig, ASRResult
from .tts_framework import TTSFramework, TTSConfig, TTSResult
from .voice_biometrics_emotion import (
    VoiceBiometricsEmotion, 
    BiometricsConfig, 
    VoiceprintResult, 
    EmotionResult
)
from agno_bmad_integration.framework import IntegrationFramework
from agno.memory.working import WorkingMemory


@dataclass
class VoiceCommand:
    """语音命令类"""
    command_id: str
    text: str
    intent: str
    confidence: float
    parameters: Dict[str, Any]
    timestamp: datetime
    speaker_id: Optional[str] = None
    emotion: Optional[str] = None
    context: Optional[Dict] = None
    status: str = "pending"  # pending, processing, completed, failed
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'command_id': self.command_id,
            'text': self.text,
            'intent': self.intent,
            'confidence': self.confidence,
            'parameters': self.parameters,
            'timestamp': self.timestamp.isoformat(),
            'speaker_id': self.speaker_id,
            'emotion': self.emotion,
            'context': self.context,
            'status': self.status
        }


@dataclass
class VoiceSession:
    """语音会话类"""
    session_id: str
    speaker_id: Optional[str]
    start_time: datetime
    end_time: Optional[datetime] = None
    commands: List[VoiceCommand] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    is_active: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_command(self, command: VoiceCommand):
        """添加命令到会话"""
        self.commands.append(command)
    
    def get_command_history(self) -> List[VoiceCommand]:
        """获取命令历史"""
        return self.commands.copy()
    
    def update_context(self, key: str, value: Any):
        """更新会话上下文"""
        self.context[key] = value
    
    def get_context(self, key: str, default: Any = None) -> Any:
        """获取会话上下文"""
        return self.context.get(key, default)
    
    def end_session(self):
        """结束会话"""
        self.end_time = datetime.now()
        self.is_active = False
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'session_id': self.session_id,
            'speaker_id': self.speaker_id,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'commands': [cmd.to_dict() for cmd in self.commands],
            'context': self.context,
            'is_active': self.is_active,
            'metadata': self.metadata
        }


@dataclass
class VoiceControlConfig:
    """语音控制配置类"""
    # 音频配置
    sample_rate: int = 16000
    channels: int = 1
    dtype: str = 'float32'
    blocksize: int = 1024
    
    # ASR配置
    asr_config: ASRConfig = field(default_factory=ASRConfig)
    
    # TTS配置
    tts_config: TTSConfig = field(default_factory=TTSConfig)
    
    # 生物识别配置
    biometrics_config: BiometricsConfig = field(default_factory=BiometricsConfig)
    
    # 交互配置
    max_session_duration: int = 3600  # 1小时
    max_commands_per_session: int = 100
    command_timeout: int = 30
    response_timeout: int = 10
    
    # 设备配置
    input_device: Optional[int] = None
    output_device: Optional[int] = None
    enable_audio_feedback: bool = True
    
    # 命令配置
    enable_voiceprint_auth: bool = True
    enable_emotion_analysis: bool = True
    enable_context_awareness: bool = True
    
    # 性能配置
    max_concurrent_sessions: int = 5
    enable_real_time_processing: bool = True
    
    # 集成配置
    integration_enabled: bool = True
    memory_sync_enabled: bool = True


class CommandProcessor(ABC):
    """命令处理器抽象基类"""
    
    @abstractmethod
    async def process_command(self, command: VoiceCommand, 
                            session: VoiceSession) -> Dict[str, Any]:
        """处理语音命令"""
        pass
    
    @abstractmethod
    def can_handle(self, intent: str) -> bool:
        """检查是否能处理指定意图"""
        pass


class SystemCommandProcessor(CommandProcessor):
    """系统命令处理器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def can_handle(self, intent: str) -> bool:
        """检查是否能处理指定意图"""
        system_intents = [
            'system_control', 'volume_control', 'navigation', 
            'help_request', 'status_query', 'exit'
        ]
        return intent in system_intents
    
    async def process_command(self, command: VoiceCommand, 
                            session: VoiceSession) -> Dict[str, Any]:
        """处理系统命令"""
        try:
            intent = command.intent
            params = command.parameters
            
            if intent == 'system_control':
                action = params.get('action', '')
                if action == 'shutdown':
                    return {'status': 'success', 'message': '系统即将关闭'}
                elif action == 'restart':
                    return {'status': 'success', 'message': '系统即将重启'}
                else:
                    return {'status': 'error', 'message': '未知的系统控制动作'}
            
            elif intent == 'volume_control':
                volume_level = params.get('level', 50)
                return {
                    'status': 'success', 
                    'message': f'音量已设置为{volume_level}%'
                }
            
            elif intent == 'help_request':
                return {
                    'status': 'success',
                    'message': '可用的命令包括：系统控制、音量调节、导航帮助等'
                }
            
            elif intent == 'status_query':
                return {
                    'status': 'success',
                    'message': '系统运行正常',
                    'data': {
                        'session_duration': str(datetime.now() - session.start_time),
                        'commands_count': len(session.commands)
                    }
                }
            
            else:
                return {'status': 'error', 'message': '无法处理的系统命令'}
                
        except Exception as e:
            self.logger.error(f"系统命令处理失败: {e}")
            return {'status': 'error', 'message': f'命令处理失败: {str(e)}'}


class ApplicationCommandProcessor(CommandProcessor):
    """应用命令处理器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.app_handlers = {}
    
    def register_handler(self, app_name: str, handler: Callable):
        """注册应用处理器"""
        self.app_handlers[app_name] = handler
    
    def can_handle(self, intent: str) -> bool:
        """检查是否能处理指定意图"""
        return intent.startswith('app_') or intent in [
            'open_application', 'close_application', 'app_control'
        ]
    
    async def process_command(self, command: VoiceCommand, 
                            session: VoiceSession) -> Dict[str, Any]:
        """处理应用命令"""
        try:
            intent = command.intent
            params = command.parameters
            
            if intent == 'open_application':
                app_name = params.get('application', '')
                if app_name in self.app_handlers:
                    handler = self.app_handlers[app_name]
                    result = await handler('open', params)
                    return {'status': 'success', 'message': f'已打开{app_name}', 'data': result}
                else:
                    return {'status': 'error', 'message': f'未找到应用{app_name}'}
            
            elif intent == 'close_application':
                app_name = params.get('application', '')
                if app_name in self.app_handlers:
                    handler = self.app_handlers[app_name]
                    result = await handler('close', params)
                    return {'status': 'success', 'message': f'已关闭{app_name}', 'data': result}
                else:
                    return {'status': 'error', 'message': f'未找到应用{app_name}'}
            
            else:
                return {'status': 'error', 'message': '无法处理的应用命令'}
                
        except Exception as e:
            self.logger.error(f"应用命令处理失败: {e}")
            return {'status': 'error', 'message': f'命令处理失败: {str(e)}'}


class IntentClassifier:
    """意图分类器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.intent_patterns = {
            'system_control': ['关机', '重启', '关闭', '退出'],
            'volume_control': ['音量', '声音', '调大', '调小'],
            'navigation': ['打开', '启动', '进入', '导航'],
            'help_request': ['帮助', '怎么用', '使用方法'],
            'status_query': ['状态', '情况', '怎么样'],
            'open_application': ['打开', '启动'],
            'close_application': ['关闭', '退出']
        }
    
    def classify_intent(self, text: str) -> tuple[str, float]:
        """分类意图"""
        text_lower = text.lower()
        
        best_intent = 'unknown'
        best_score = 0.0
        
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if pattern in text_lower:
                    score = len(pattern) / len(text)
                    if score > best_score:
                        best_score = score
                        best_intent = intent
        
        return best_intent, best_score
    
    def extract_parameters(self, text: str, intent: str) -> Dict[str, Any]:
        """提取参数"""
        parameters = {}
        
        if intent == 'volume_control':
            # 提取音量级别
            import re
            volume_match = re.search(r'(\d+)%', text)
            if volume_match:
                parameters['level'] = int(volume_match.group(1))
        
        elif intent in ['open_application', 'close_application']:
            # 提取应用名称
            import re
            app_match = re.search(r'(打开|启动|关闭|退出)\s*(\w+)', text)
            if app_match:
                parameters['application'] = app_match.group(2)
        
        elif intent == 'system_control':
            # 提取系统动作
            if '关机' in text or '关闭' in text:
                parameters['action'] = 'shutdown'
            elif '重启' in text:
                parameters['action'] = 'restart'
        
        return parameters


class VoiceControlInterface:
    """语音控制接口主类"""
    
    def __init__(self, config: VoiceControlConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # 初始化组件
        self.asr_framework = ASRFramework(config.asr_config)
        self.tts_framework = TTSFramework(config.tts_config)
        self.biometrics_emotion = VoiceBiometricsEmotion(config.biometrics_config)
        
        # 意图分类器
        self.intent_classifier = IntentClassifier()
        
        # 命令处理器
        self.command_processors = [
            SystemCommandProcessor(),
            ApplicationCommandProcessor()
        ]
        
        # 会话管理
        self.sessions: Dict[str, VoiceSession] = {}
        self.active_sessions: Dict[str, VoiceSession] = {}
        
        # 集成框架
        self.integration_framework = None
        if config.integration_enabled:
            self.integration_framework = IntegrationFramework()
        
        # 工作记忆
        self.working_memory = None
        if config.memory_sync_enabled:
            self.working_memory = WorkingMemory()
        
        # 音频流
        self.audio_stream = None
        self.is_recording = False
        
        self.logger.info("语音控制接口初始化完成")
    
    async def start_session(self, speaker_id: Optional[str] = None) -> str:
        """开始语音会话"""
        session_id = str(uuid.uuid4())
        session = VoiceSession(
            session_id=session_id,
            speaker_id=speaker_id,
            start_time=datetime.now()
        )
        
        self.sessions[session_id] = session
        self.active_sessions[session_id] = session
        
        # 同步到记忆系统
        if self.working_memory:
            await self._sync_session_to_memory(session)
        
        self.logger.info(f"开始语音会话: {session_id}")
        return session_id
    
    async def end_session(self, session_id: str) -> bool:
        """结束语音会话"""
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            session.end_session()
            
            del self.active_sessions[session_id]
            
            # 同步到记忆系统
            if self.working_memory:
                await self._sync_session_end_to_memory(session)
            
            self.logger.info(f"结束语音会话: {session_id}")
            return True
        
        return False
    
    async def process_voice_input(self, session_id: str, audio_data: np.ndarray) -> Dict[str, Any]:
        """处理语音输入"""
        if session_id not in self.active_sessions:
            raise ValueError(f"会话不存在: {session_id}")
        
        session = self.active_sessions[session_id]
        results = {}
        
        try:
            # 声纹识别和情感分析
            if (self.config.enable_voiceprint_auth or self.config.enable_emotion_analysis):
                voice_analysis = await self.biometrics_emotion.analyze_voice(
                    audio_data,
                    enable_voiceprint=self.config.enable_voiceprint_auth,
                    enable_emotion=self.config.enable_emotion_analysis
                )
                results['analysis'] = voice_analysis
            
            # 语音识别
            asr_result = await self.asr_framework.transcribe_audio(audio_data)
            results['asr'] = asr_result.to_dict()
            
            # 如果没有识别到文本，返回空结果
            if not asr_result.text.strip():
                return results
            
            # 意图分类
            intent, confidence = self.intent_classifier.classify_intent(asr_result.text)
            parameters = self.intent_classifier.extract_parameters(asr_result.text, intent)
            
            # 创建语音命令
            command = VoiceCommand(
                command_id=str(uuid.uuid4()),
                text=asr_result.text,
                intent=intent,
                confidence=confidence,
                parameters=parameters,
                timestamp=datetime.now(),
                speaker_id=session.speaker_id,
                emotion=voice_analysis.get('emotion', {}).get('primary_emotion') if 'analysis' in results else None,
                context=session.context.copy()
            )
            
            # 处理命令
            command.status = "processing"
            session.add_command(command)
            
            # 获取可用的处理器
            processor = None
            for cmd_processor in self.command_processors:
                if cmd_processor.can_handle(intent):
                    processor = cmd_processor
                    break
            
            if processor:
                try:
                    response = await processor.process_command(command, session)
                    command.status = "completed" if response.get('status') == 'success' else "failed"
                    results['command'] = command.to_dict()
                    results['response'] = response
                    
                    # 生成语音回复
                    if response.get('message'):
                        tts_result = await self.tts_framework.synthesize_speech(response['message'])
                        results['tts'] = tts_result.to_dict()
                        
                        # 播放音频
                        if self.config.enable_audio_feedback:
                            await self._play_audio(tts_result.audio_data)
                    
                except Exception as e:
                    self.logger.error(f"命令处理失败: {e}")
                    command.status = "failed"
                    results['command'] = command.to_dict()
                    results['response'] = {'status': 'error', 'message': f'处理失败: {str(e)}'}
            else:
                command.status = "failed"
                results['command'] = command.to_dict()
                results['response'] = {'status': 'error', 'message': f'无法处理意图: {intent}'}
            
            # 同步到记忆系统
            if self.working_memory:
                await self._sync_command_to_memory(command, results)
            
            # 集成到框架
            if self.integration_framework:
                await self._integrate_voice_interaction(results)
            
            return results
            
        except Exception as e:
            self.logger.error(f"语音输入处理失败: {e}")
            results['error'] = str(e)
            return results
    
    async def process_voice_file(self, session_id: str, file_path: Union[str, Path]) -> Dict[str, Any]:
        """处理语音文件"""
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"音频文件不存在: {file_path}")
        
        # 加载音频文件
        audio_data, sample_rate = sf.read(file_path)
        
        # 重采样到配置采样率
        if sample_rate != self.config.sample_rate:
            import librosa
            audio_data = librosa.resample(
                audio_data, 
                orig_sr=sample_rate, 
                target_sr=self.config.sample_rate
            )
        
        return await self.process_voice_input(session_id, audio_data)
    
    async def start_voice_recording(self, session_id: str) -> AsyncGenerator[np.ndarray, None]:
        """开始语音录制"""
        if session_id not in self.active_sessions:
            raise ValueError(f"会话不存在: {session_id}")
        
        self.is_recording = True
        
        try:
            with sd.InputStream(
                samplerate=self.config.sample_rate,
                channels=self.config.channels,
                dtype=self.config.dtype,
                blocksize=self.config.blocksize,
                device=self.config.input_device
            ) as stream:
                while self.is_recording:
                    audio_chunk, overflowed = stream.read(self.config.blocksize)
                    if not overflowed:
                        yield audio_chunk.flatten()
                    await asyncio.sleep(0.01)  # 避免CPU占用过高
                    
        except Exception as e:
            self.logger.error(f"语音录制失败: {e}")
            raise
    
    async def stop_voice_recording(self):
        """停止语音录制"""
        self.is_recording = False
    
    async def _play_audio(self, audio_data: Union[bytes, np.ndarray]):
        """播放音频"""
        try:
            if isinstance(audio_data, bytes):
                # 从字节数据播放
                audio_segment = AudioSegment.from_file(io.BytesIO(audio_data))
                audio_array = np.array(audio_segment.get_array_of_samples(), dtype=np.float32)
                audio_array = audio_array / 32768.0  # 归一化
            else:
                audio_array = audio_data
            
            # 播放音频
            sd.play(audio_array, self.config.sample_rate, device=self.config.output_device)
            sd.wait()  # 等待播放完成
            
        except Exception as e:
            self.logger.error(f"音频播放失败: {e}")
    
    async def register_speaker(self, speaker_id: str, audio_data: np.ndarray) -> bool:
        """注册说话人"""
        try:
            success = await self.biometrics_emotion.enroll_speaker(speaker_id, audio_data)
            
            if success and self.working_memory:
                memory_data = {
                    'type': 'speaker_registration',
                    'speaker_id': speaker_id,
                    'timestamp': datetime.now().isoformat()
                }
                await self.working_memory.add(memory_data)
            
            return success
            
        except Exception as e:
            self.logger.error(f"说话人注册失败: {e}")
            return False
    
    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取会话信息"""
        if session_id in self.sessions:
            return self.sessions[session_id].to_dict()
        return None
    
    def get_active_sessions(self) -> List[str]:
        """获取活跃会话列表"""
        return list(self.active_sessions.keys())
    
    def get_session_stats(self) -> Dict[str, Any]:
        """获取会话统计信息"""
        total_sessions = len(self.sessions)
        active_sessions = len(self.active_sessions)
        
        stats = {
            'total_sessions': total_sessions,
            'active_sessions': active_sessions,
            'session_details': []
        }
        
        for session_id, session in self.sessions.items():
            stats['session_details'].append({
                'session_id': session_id,
                'speaker_id': session.speaker_id,
                'start_time': session.start_time.isoformat(),
                'is_active': session.is_active,
                'commands_count': len(session.commands)
            })
        
        return stats
    
    async def _sync_session_to_memory(self, session: VoiceSession):
        """同步会话到记忆系统"""
        try:
            memory_data = {
                'type': 'voice_session_start',
                'session_id': session.session_id,
                'speaker_id': session.speaker_id,
                'timestamp': session.start_time.isoformat()
            }
            
            await self.working_memory.add(memory_data)
            
        except Exception as e:
            self.logger.error(f"会话记忆同步失败: {e}")
    
    async def _sync_session_end_to_memory(self, session: VoiceSession):
        """同步会话结束到记忆系统"""
        try:
            memory_data = {
                'type': 'voice_session_end',
                'session_id': session.session_id,
                'end_time': session.end_time.isoformat(),
                'commands_count': len(session.commands),
                'duration': str(session.end_time - session.start_time)
            }
            
            await self.working_memory.add(memory_data)
            
        except Exception as e:
            self.logger.error(f"会话结束记忆同步失败: {e}")
    
    async def _sync_command_to_memory(self, command: VoiceCommand, results: Dict[str, Any]):
        """同步命令到记忆系统"""
        try:
            memory_data = {
                'type': 'voice_command',
                'command_id': command.command_id,
                'text': command.text,
                'intent': command.intent,
                'confidence': command.confidence,
                'status': command.status,
                'timestamp': command.timestamp.isoformat()
            }
            
            await self.working_memory.add(memory_data)
            
        except Exception as e:
            self.logger.error(f"命令记忆同步失败: {e}")
    
    async def _integrate_voice_interaction(self, results: Dict[str, Any]):
        """集成语音交互到框架"""
        try:
            if self.integration_framework:
                await self.integration_framework.broadcast_event(
                    'voice_interaction_completed',
                    results
                )
                
        except Exception as e:
            self.logger.error(f"语音交互框架集成失败: {e}")
    
    def register_application_handler(self, app_name: str, handler: Callable):
        """注册应用处理器"""
        for processor in self.command_processors:
            if isinstance(processor, ApplicationCommandProcessor):
                processor.register_handler(app_name, handler)
                break
    
    def get_interface_stats(self) -> Dict[str, Any]:
        """获取接口统计信息"""
        return {
            'asr_stats': self.asr_framework.get_transcription_stats(),
            'tts_stats': self.tts_framework.get_synthesis_stats(),
            'biometrics_stats': self.biometrics_emotion.get_analysis_stats(),
            'session_stats': self.get_session_stats(),
            'available_engines': {
                'asr': self.asr_framework.get_available_engines(),
                'tts': self.tts_framework.get_available_engines()
            }
        }