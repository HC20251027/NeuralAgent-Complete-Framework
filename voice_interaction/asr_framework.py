"""
语音识别(ASR)框架 - Automatic Speech Recognition Framework
==========================================================

支持多种ASR引擎：
- OpenAI Whisper
- SpeechRecognition (Google, Azure, AWS)
- Faster Whisper (优化版本)
- 本地VAD (Voice Activity Detection)

Author: MiniMax Agent
Date: 2025-11-06
"""

import asyncio
import logging
import numpy as np
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, List, Dict, Any, Union, Callable
from pathlib import Path
import json
import time
from datetime import datetime

# 音频处理库
import librosa
import soundfile as sf
from pydub import AudioSegment
import speech_recognition as sr

# 异步支持
import aiofiles
import aiohttp

# 配置管理
from agno_bmad_integration.framework import IntegrationFramework
from agno.memory.working import WorkingMemory


@dataclass
class ASRConfig:
    """ASR配置类"""
    # 基本配置
    engine: str = "whisper"  # whisper, speech_recognition, faster_whisper
    language: str = "zh-CN"
    sample_rate: int = 16000
    chunk_duration: float = 30.0  # 分块处理时长(秒)
    
    # Whisper配置
    whisper_model: str = "base"  # tiny, base, small, medium, large
    whisper_device: str = "cpu"  # cpu, cuda
    
    # SpeechRecognition配置
    sr_engine: str = "google"  # google, sphinx, google_cloud, azure, aws
    sr_api_key: Optional[str] = None
    
    # VAD配置
    enable_vad: bool = True
    vad_threshold: float = 0.5
    min_speech_duration: float = 1.0
    max_speech_duration: float = 30.0
    
    # 预处理配置
    enable_noise_reduction: bool = True
    enable_normalization: bool = True
    enable_voice_activity_detection: bool = True
    
    # 性能配置
    max_concurrent_requests: int = 5
    timeout: int = 30
    retry_attempts: int = 3
    
    # 集成配置
    integration_enabled: bool = True
    memory_sync_enabled: bool = True


@dataclass
class ASRResult:
    """ASR结果类"""
    text: str
    confidence: float
    language: str
    duration: float
    timestamp: datetime
    engine_used: str
    processing_time: float
    segments: Optional[List[Dict]] = None
    metadata: Optional[Dict] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'text': self.text,
            'confidence': self.confidence,
            'language': self.language,
            'duration': self.duration,
            'timestamp': self.timestamp.isoformat(),
            'engine_used': self.engine_used,
            'processing_time': self.processing_time,
            'segments': self.segments,
            'metadata': self.metadata
        }


class ASREngine(ABC):
    """ASR引擎抽象基类"""
    
    @abstractmethod
    async def transcribe(self, audio_data: Union[bytes, np.ndarray], 
                        config: ASRConfig) -> ASRResult:
        """转录音频数据"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """检查引擎是否可用"""
        pass


class WhisperEngine(ASREngine):
    """Whisper ASR引擎"""
    
    def __init__(self):
        self.model = None
        self.logger = logging.getLogger(__name__)
    
    def is_available(self) -> bool:
        """检查Whisper是否可用"""
        try:
            import whisper
            return True
        except ImportError:
            return False
    
    async def transcribe(self, audio_data: Union[bytes, np.ndarray], 
                        config: ASRConfig) -> ASRResult:
        """使用Whisper转录音频"""
        start_time = time.time()
        
        try:
            import whisper
            
            # 加载模型
            if self.model is None:
                self.model = whisper.load_model(config.whisper_model, 
                                              device=config.whisper_device)
            
            # 处理音频数据
            if isinstance(audio_data, bytes):
                # 保存临时文件
                temp_path = Path("/tmp/temp_audio.wav")
                with open(temp_path, 'wb') as f:
                    f.write(audio_data)
                audio_data = str(temp_path)
            
            # 转录
            result = self.model.transcribe(
                audio_data,
                language=config.language,
                task="transcribe",
                verbose=False
            )
            
            processing_time = time.time() - start_time
            
            return ASRResult(
                text=result["text"].strip(),
                confidence=1.0,  # Whisper不提供置信度
                language=result.get("language", config.language),
                duration=result.get("duration", 0.0),
                timestamp=datetime.now(),
                engine_used="whisper",
                processing_time=processing_time,
                segments=result.get("segments", []),
                metadata={
                    "model": config.whisper_model,
                    "device": config.whisper_device
                }
            )
            
        except Exception as e:
            self.logger.error(f"Whisper转录失败: {e}")
            raise


class SpeechRecognitionEngine(ASREngine):
    """SpeechRecognition引擎"""
    
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.logger = logging.getLogger(__name__)
    
    def is_available(self) -> bool:
        """检查SpeechRecognition是否可用"""
        return True  # 基本总是可用
    
    async def transcribe(self, audio_data: Union[bytes, np.ndarray], 
                        config: ASRConfig) -> ASRResult:
        """使用SpeechRecognition转录音频"""
        start_time = time.time()
        
        try:
            # 处理音频数据
            if isinstance(audio_data, bytes):
                audio = sr.AudioData(audio_data, config.sample_rate, 2)
            else:
                # 转换numpy数组为AudioData
                audio_bytes = (audio_data * 32767).astype(np.int16).tobytes()
                audio = sr.AudioData(audio_bytes, config.sample_rate, 2)
            
            # 根据引擎选择识别方法
            if config.sr_engine == "google":
                text = self.recognizer.recognize_google(audio, language=config.language)
                confidence = 0.9
            elif config.sr_engine == "google_cloud":
                # 需要Google Cloud API密钥
                if not config.sr_api_key:
                    raise ValueError("需要Google Cloud API密钥")
                text = self.recognizer.recognize_google_cloud(
                    audio, 
                    language=config.language,
                    credentials_json=config.sr_api_key
                )
                confidence = 0.9
            else:
                text = self.recognizer.recognize_sphinx(audio)
                confidence = 0.7
            
            processing_time = time.time() - start_time
            
            return ASRResult(
                text=text,
                confidence=confidence,
                language=config.language,
                duration=0.0,  # SpeechRecognition不提供时长
                timestamp=datetime.now(),
                engine_used=f"speech_recognition_{config.sr_engine}",
                processing_time=processing_time,
                metadata={
                    "engine": config.sr_engine
                }
            )
            
        except sr.UnknownValueError:
            # 无法识别语音
            return ASRResult(
                text="",
                confidence=0.0,
                language=config.language,
                duration=0.0,
                timestamp=datetime.now(),
                engine_used=f"speech_recognition_{config.sr_engine}",
                processing_time=time.time() - start_time,
                metadata={"error": "无法识别语音"}
            )
        except Exception as e:
            self.logger.error(f"SpeechRecognition转录失败: {e}")
            raise


class FasterWhisperEngine(ASREngine):
    """Faster Whisper引擎(优化版本)"""
    
    def __init__(self):
        self.model = None
        self.logger = logging.getLogger(__name__)
    
    def is_available(self) -> bool:
        """检查Faster Whisper是否可用"""
        try:
            from faster_whisper import WhisperModel
            return True
        except ImportError:
            return False
    
    async def transcribe(self, audio_data: Union[bytes, np.ndarray], 
                        config: ASRConfig) -> ASRResult:
        """使用Faster Whisper转录音频"""
        start_time = time.time()
        
        try:
            from faster_whisper import WhisperModel
            
            # 加载模型
            if self.model is None:
                self.model = WhisperModel(
                    config.whisper_model,
                    device=config.whisper_device,
                    compute_type="float16"
                )
            
            # 处理音频数据
            if isinstance(audio_data, bytes):
                temp_path = Path("/tmp/temp_audio_faster.wav")
                with open(temp_path, 'wb') as f:
                    f.write(audio_data)
                audio_path = str(temp_path)
            else:
                audio_path = audio_data
            
            # 转录
            segments, info = self.model.transcribe(
                audio_path,
                language=config.language,
                vad_filter=True,
                vad_parameters=dict(
                    min_silence_duration_ms=500
                )
            )
            
            # 收集结果
            full_text = []
            segment_list = []
            
            for segment in segments:
                full_text.append(segment.text)
                segment_list.append({
                    'start': segment.start,
                    'end': segment.end,
                    'text': segment.text,
                    'confidence': segment.avg_logprob
                })
            
            processing_time = time.time() - start_time
            
            return ASRResult(
                text=" ".join(full_text).strip(),
                confidence=1.0,
                language=info.language,
                duration=info.duration,
                timestamp=datetime.now(),
                engine_used="faster_whisper",
                processing_time=processing_time,
                segments=segment_list,
                metadata={
                    "model": config.whisper_model,
                    "device": config.whisper_device,
                    "language_probability": info.language_probability
                }
            )
            
        except Exception as e:
            self.logger.error(f"Faster Whisper转录失败: {e}")
            raise


class VADProcessor:
    """语音活动检测处理器"""
    
    def __init__(self, config: ASRConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
    
    async def detect_speech_segments(self, audio_data: np.ndarray) -> List[Dict]:
        """检测语音片段"""
        try:
            # 使用librosa进行VAD
            # 这里使用简单的能量检测作为示例
            frame_length = int(self.config.sample_rate * 0.025)  # 25ms帧
            hop_length = int(self.config.sample_rate * 0.010)    # 10ms跳跃
            
            # 计算RMS能量
            rms = librosa.feature.rms(
                y=audio_data,
                frame_length=frame_length,
                hop_length=hop_length
            )[0]
            
            # 动态阈值
            threshold = np.mean(rms) * self.config.vad_threshold
            
            # 检测语音片段
            speech_frames = rms > threshold
            
            # 转换为时间片段
            time_per_frame = hop_length / self.config.sample_rate
            speech_segments = []
            
            start_frame = None
            for i, is_speech in enumerate(speech_frames):
                if is_speech and start_frame is None:
                    start_frame = i
                elif not is_speech and start_frame is not None:
                    end_frame = i
                    duration = (end_frame - start_frame) * time_per_frame
                    
                    if duration >= self.config.min_speech_duration:
                        speech_segments.append({
                            'start': start_frame * time_per_frame,
                            'end': end_frame * time_per_frame,
                            'duration': duration
                        })
                    
                    start_frame = None
            
            return speech_segments
            
        except Exception as e:
            self.logger.error(f"VAD检测失败: {e}")
            return []


class ASRFramework:
    """ASR框架主类"""
    
    def __init__(self, config: ASRConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # 初始化引擎
        self.engines = {
            "whisper": WhisperEngine(),
            "speech_recognition": SpeechRecognitionEngine(),
            "faster_whisper": FasterWhisperEngine()
        }
        
        # VAD处理器
        self.vad_processor = VADProcessor(config)
        
        # 集成框架
        self.integration_framework = None
        if config.integration_enabled:
            self.integration_framework = IntegrationFramework()
        
        # 工作记忆
        self.working_memory = None
        if config.memory_sync_enabled:
            self.working_memory = WorkingMemory()
    
    async def transcribe_audio(self, audio_data: Union[bytes, np.ndarray], 
                             engine: Optional[str] = None) -> ASRResult:
        """转录音频数据"""
        if engine is None:
            engine = self.config.engine
        
        # 检查引擎可用性
        if engine not in self.engines:
            raise ValueError(f"不支持的ASR引擎: {engine}")
        
        asr_engine = self.engines[engine]
        if not asr_engine.is_available():
            raise RuntimeError(f"ASR引擎不可用: {engine}")
        
        # 预处理音频
        processed_audio = await self._preprocess_audio(audio_data)
        
        # VAD检测
        if self.config.enable_vad:
            speech_segments = await self.vad_processor.detect_speech_segments(processed_audio)
            if not speech_segments:
                return ASRResult(
                    text="",
                    confidence=0.0,
                    language=self.config.language,
                    duration=0.0,
                    timestamp=datetime.now(),
                    engine_used=engine,
                    processing_time=0.0,
                    metadata={"error": "未检测到语音"}
                )
        
        # 转录
        result = await asr_engine.transcribe(processed_audio, self.config)
        
        # 同步到记忆系统
        if self.working_memory:
            await self._sync_to_memory(result)
        
        # 集成到框架
        if self.integration_framework:
            await self._integrate_result(result)
        
        return result
    
    async def transcribe_file(self, file_path: Union[str, Path], 
                             engine: Optional[str] = None) -> ASRResult:
        """转录音频文件"""
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"音频文件不存在: {file_path}")
        
        # 读取音频文件
        async with aiofiles.open(file_path, 'rb') as f:
            audio_data = await f.read()
        
        return await self.transcribe_audio(audio_data, engine)
    
    async def transcribe_stream(self, audio_stream, engine: Optional[str] = None) -> ASRResult:
        """转录音频流"""
        # 收集音频流数据
        audio_chunks = []
        async for chunk in audio_stream:
            audio_chunks.append(chunk)
        
        # 合并音频数据
        full_audio = b''.join(audio_chunks)
        
        return await self.transcribe_audio(full_audio, engine)
    
    async def batch_transcribe(self, audio_files: List[Union[str, Path]], 
                              engine: Optional[str] = None) -> List[ASRResult]:
        """批量转录"""
        tasks = []
        semaphore = asyncio.Semaphore(self.config.max_concurrent_requests)
        
        async def transcribe_with_semaphore(file_path):
            async with semaphore:
                return await self.transcribe_file(file_path, engine)
        
        for file_path in audio_files:
            task = transcribe_with_semaphore(file_path)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理异常结果
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                self.logger.error(f"文件 {audio_files[i]} 转录失败: {result}")
                processed_results.append(None)
            else:
                processed_results.append(result)
        
        return processed_results
    
    async def _preprocess_audio(self, audio_data: Union[bytes, np.ndarray]) -> np.ndarray:
        """预处理音频数据"""
        if isinstance(audio_data, bytes):
            # 从字节数据加载音频
            audio_array, sample_rate = librosa.load(
                audio_data, 
                sr=self.config.sample_rate,
                mono=True
            )
        else:
            audio_array = audio_data
            sample_rate = self.config.sample_rate
        
        # 重采样
        if sample_rate != self.config.sample_rate:
            audio_array = librosa.resample(
                audio_array, 
                orig_sr=sample_rate, 
                target_sr=self.config.sample_rate
            )
        
        # 噪声减少
        if self.config.enable_noise_reduction:
            audio_array = await self._reduce_noise(audio_array)
        
        # 归一化
        if self.config.enable_normalization:
            audio_array = librosa.util.normalize(audio_array)
        
        return audio_array
    
    async def _reduce_noise(self, audio_array: np.ndarray) -> np.ndarray:
        """简单的噪声减少"""
        # 使用谱减法进行噪声减少
        # 这里实现一个简单的版本
        try:
            # 计算噪声估计(前0.5秒作为噪声)
            noise_duration = min(0.5, len(audio_array) / self.config.sample_rate)
            noise_frames = int(noise_duration * self.config.sample_rate)
            noise_sample = audio_array[:noise_frames]
            
            # 简单的频域滤波
            stft = librosa.stft(audio_array)
            magnitude = np.abs(stft)
            phase = np.angle(stft)
            
            # 噪声估计
            noise_magnitude = np.abs(librosa.stft(noise_sample))
            noise_profile = np.mean(noise_magnitude, axis=1, keepdims=True)
            
            # 谱减法
            alpha = 2.0  # 过减因子
            enhanced_magnitude = magnitude - alpha * noise_profile
            enhanced_magnitude = np.maximum(enhanced_magnitude, 0.1 * magnitude)
            
            # 重构音频
            enhanced_stft = enhanced_magnitude * np.exp(1j * phase)
            enhanced_audio = librosa.istft(enhanced_stft)
            
            return enhanced_audio
            
        except Exception as e:
            self.logger.warning(f"噪声减少失败: {e}")
            return audio_array
    
    async def _sync_to_memory(self, result: ASRResult):
        """同步结果到记忆系统"""
        try:
            memory_data = {
                'type': 'asr_result',
                'text': result.text,
                'confidence': result.confidence,
                'timestamp': result.timestamp.isoformat(),
                'engine': result.engine_used
            }
            
            await self.working_memory.add(memory_data)
            
        except Exception as e:
            self.logger.error(f"记忆同步失败: {e}")
    
    async def _integrate_result(self, result: ASRResult):
        """集成结果到框架"""
        try:
            if self.integration_framework:
                # 通知其他组件ASR结果
                await self.integration_framework.broadcast_event(
                    'asr_completed',
                    {
                        'text': result.text,
                        'confidence': result.confidence,
                        'engine': result.engine_used
                    }
                )
                
        except Exception as e:
            self.logger.error(f"框架集成失败: {e}")
    
    def get_available_engines(self) -> List[str]:
        """获取可用的ASR引擎"""
        available = []
        for name, engine in self.engines.items():
            if engine.is_available():
                available.append(name)
        return available
    
    def get_transcription_stats(self) -> Dict[str, Any]:
        """获取转录统计信息"""
        return {
            'available_engines': self.get_available_engines(),
            'current_engine': self.config.engine,
            'language': self.config.language,
            'sample_rate': self.config.sample_rate,
            'vad_enabled': self.config.enable_vad,
            'noise_reduction': self.config.enable_noise_reduction
        }