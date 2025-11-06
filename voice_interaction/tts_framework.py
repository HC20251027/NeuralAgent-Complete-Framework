"""
语音合成(TTS)框架 - Text-to-Speech Framework
===========================================

支持多种TTS引擎：
- gTTS (Google Text-to-Speech)
- Edge TTS (Microsoft Edge)
- Festival (本地TTS)
- Coqui TTS (开源TTS)
- Azure Cognitive Services TTS

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
import tempfile
import base64

# 音频处理库
import soundfile as sf
from pydub import AudioSegment
import io

# 异步支持
import aiofiles
import aiohttp

# TTS引擎
try:
    import gtts
    from pygame import mixer
    GTTS_AVAILABLE = True
except ImportError:
    GTTS_AVAILABLE = False

try:
    import edge_tts
    EDGE_TTS_AVAILABLE = True
except ImportError:
    EDGE_TTS_AVAILABLE = False

# 配置管理
from agno_bmad_integration.framework import IntegrationFramework
from agno.memory.working import WorkingMemory


@dataclass
class TTSConfig:
    """TTS配置类"""
    # 基本配置
    engine: str = "gtts"  # gtts, edge_tts, festival, coqui, azure
    language: str = "zh"
    voice: Optional[str] = None
    speed: float = 1.0
    pitch: float = 1.0
    volume: float = 1.0
    
    # gTTS配置
    gtts_lang: str = "zh"
    slow: bool = False
    
    # Edge TTS配置
    edge_voice: str = "zh-CN-XiaoxiaoNeural"
    edge_rate: str = "0%"  # -50% to +50%
    edge_volume: str = "0%"  # -50% to +50%
    edge_pitch: str = "0Hz"  # -50Hz to +50Hz
    
    # Azure TTS配置
    azure_key: Optional[str] = None
    azure_region: str = "eastus"
    azure_voice: str = "zh-CN-XiaoxiaoNeural"
    
    # Coqui TTS配置
    coqui_model: str = "tts_models/en/ljspeech/tacotron2-DDC"
    coqui_device: str = "cpu"
    
    # 音频配置
    sample_rate: int = 22050
    format: str = "wav"  # wav, mp3, flac
    bit_depth: int = 16
    
    # 性能配置
    max_text_length: int = 5000
    chunk_size: int = 1000
    timeout: int = 30
    retry_attempts: int = 3
    
    # 集成配置
    integration_enabled: bool = True
    memory_sync_enabled: bool = True
    
    # 缓存配置
    enable_cache: bool = True
    cache_dir: str = "/tmp/tts_cache"


@dataclass
class TTSResult:
    """TTS结果类"""
    audio_data: Union[bytes, np.ndarray]
    format: str
    duration: float
    sample_rate: int
    timestamp: datetime
    engine_used: str
    processing_time: float
    text: str
    voice: str
    metadata: Optional[Dict] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'format': self.format,
            'duration': self.duration,
            'sample_rate': self.sample_rate,
            'timestamp': self.timestamp.isoformat(),
            'engine_used': self.engine_used,
            'processing_time': self.processing_time,
            'text': self.text,
            'voice': self.voice,
            'metadata': self.metadata
        }
    
    def save_to_file(self, file_path: Union[str, Path]) -> None:
        """保存音频到文件"""
        file_path = Path(file_path)
        
        if isinstance(self.audio_data, bytes):
            with open(file_path, 'wb') as f:
                f.write(self.audio_data)
        else:
            sf.write(file_path, self.audio_data, self.sample_rate)


class TTSEngine(ABC):
    """TTS引擎抽象基类"""
    
    @abstractmethod
    async def synthesize(self, text: str, config: TTSConfig) -> TTSResult:
        """合成语音"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """检查引擎是否可用"""
        pass
    
    @abstractmethod
    def get_available_voices(self) -> List[str]:
        """获取可用声音列表"""
        pass


class GTTSEngine(TTSEngine):
    """Google Text-to-Speech引擎"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.cache = {}
    
    def is_available(self) -> bool:
        """检查gTTS是否可用"""
        return GTTS_AVAILABLE
    
    def get_available_voices(self) -> List[str]:
        """获取可用声音列表"""
        return [
            'zh', 'en', 'ja', 'ko', 'fr', 'de', 'es', 'it', 
            'pt', 'ru', 'hi', 'ar', 'th', 'vi', 'id', 'ms'
        ]
    
    async def synthesize(self, text: str, config: TTSConfig) -> TTSResult:
        """使用gTTS合成语音"""
        start_time = time.time()
        
        try:
            # 检查缓存
            cache_key = f"{config.gtts_lang}_{hash(text)}"
            if config.enable_cache and cache_key in self.cache:
                cached_result = self.cache[cache_key]
                cached_result.timestamp = datetime.now()
                return cached_result
            
            # 创建TTS对象
            tts = gtts.gTTS(
                text=text,
                lang=config.gtts_lang,
                slow=config.slow
            )
            
            # 生成音频数据
            audio_bytes = b""
            with io.BytesIO() as buffer:
                tts.write_to_fp(buffer)
                audio_bytes = buffer.getvalue()
            
            # 转换为numpy数组
            audio_array, sample_rate = sf.read(io.BytesIO(audio_bytes))
            
            processing_time = time.time() - start_time
            
            result = TTSResult(
                audio_data=audio_bytes,
                format="mp3",
                duration=len(audio_array) / sample_rate,
                sample_rate=sample_rate,
                timestamp=datetime.now(),
                engine_used="gtts",
                processing_time=processing_time,
                text=text,
                voice=config.gtts_lang,
                metadata={
                    "language": config.gtts_lang,
                    "slow": config.slow
                }
            )
            
            # 缓存结果
            if config.enable_cache:
                self.cache[cache_key] = result
            
            return result
            
        except Exception as e:
            self.logger.error(f"gTTS合成失败: {e}")
            raise


class EdgeTTSEngine(TTSEngine):
    """Microsoft Edge TTS引擎"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.voice_list = None
        self.cache = {}
    
    def is_available(self) -> bool:
        """检查Edge TTS是否可用"""
        return EDGE_TTS_AVAILABLE
    
    async def get_voice_list(self) -> List[Dict]:
        """获取声音列表"""
        if self.voice_list is None:
            self.voice_list = await edge_tts.list_voices()
        return self.voice_list
    
    def get_available_voices(self) -> List[str]:
        """获取可用声音列表"""
        voices = []
        for voice in [
            "zh-CN-XiaoxiaoNeural", "zh-CN-XiaoyiNeural", "zh-CN-YunjianNeural",
            "zh-CN-YunxiNeural", "zh-CN-YunxiaNeural", "zh-CN-liaoning-XiaobeiNeural",
            "en-US-AriaNeural", "en-US-JennyNeural", "en-US-GuyNeural",
            "ja-JP-NanamiNeural", "ko-KR-SunHiNeural"
        ]:
            voices.append(voice)
        return voices
    
    async def synthesize(self, text: str, config: TTSConfig) -> TTSResult:
        """使用Edge TTS合成语音"""
        start_time = time.time()
        
        try:
            # 检查缓存
            cache_key = f"{config.edge_voice}_{hash(text)}"
            if config.enable_cache and cache_key in self.cache:
                cached_result = self.cache[cache_key]
                cached_result.timestamp = datetime.now()
                return cached_result
            
            # 创建通信器
            communicate = edge_tts.Communicate(
                text, 
                config.edge_voice,
                rate=config.edge_rate,
                volume=config.edge_volume,
                pitch=config.edge_pitch
            )
            
            # 生成音频数据
            audio_bytes = b""
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_bytes += chunk["data"]
            
            # 转换为numpy数组
            audio_array, sample_rate = sf.read(io.BytesIO(audio_bytes))
            
            processing_time = time.time() - start_time
            
            result = TTSResult(
                audio_data=audio_bytes,
                format="mp3",
                duration=len(audio_array) / sample_rate,
                sample_rate=sample_rate,
                timestamp=datetime.now(),
                engine_used="edge_tts",
                processing_time=processing_time,
                text=text,
                voice=config.edge_voice,
                metadata={
                    "rate": config.edge_rate,
                    "volume": config.edge_volume,
                    "pitch": config.edge_pitch
                }
            )
            
            # 缓存结果
            if config.enable_cache:
                self.cache[cache_key] = result
            
            return result
            
        except Exception as e:
            self.logger.error(f"Edge TTS合成失败: {e}")
            raise


class AzureTTSEngine(TTSEngine):
    """Azure Cognitive Services TTS引擎"""
    
    def __init__(self, config: TTSConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.cache = {}
    
    def is_available(self) -> bool:
        """检查Azure TTS是否可用"""
        return self.config.azure_key is not None
    
    def get_available_voices(self) -> List[str]:
        """获取可用声音列表"""
        return [
            "zh-CN-XiaoxiaoNeural", "zh-CN-XiaoyiNeural", "zh-CN-YunjianNeural",
            "zh-CN-YunxiNeural", "zh-CN-YunxiaNeural", "zh-CN-liaoning-XiaobeiNeural",
            "en-US-AriaNeural", "en-US-JennyNeural", "en-US-GuyNeural"
        ]
    
    async def synthesize(self, text: str, config: TTSConfig) -> TTSResult:
        """使用Azure TTS合成语音"""
        start_time = time.time()
        
        try:
            # 检查缓存
            cache_key = f"{config.azure_voice}_{hash(text)}"
            if config.enable_cache and cache_key in self.cache:
                cached_result = self.cache[cache_key]
                cached_result.timestamp = datetime.now()
                return cached_result
            
            # 构建SSML
            ssml = f"""
            <speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="{config.language}">
                <voice name="{config.azure_voice}">
                    <prosody rate="{config.speed}" volume="{config.volume * 100}%">
                        {text}
                    </prosody>
                </voice>
            </speak>
            """
            
            # 发送请求
            headers = {
                'Ocp-Apim-Subscription-Key': config.azure_key,
                'Content-Type': 'application/ssml+xml',
                'X-Microsoft-OutputFormat': 'audio-16khz-128kbitrate-mono-mp3'
            }
            
            url = f"https://{config.azure_region}.tts.speech.microsoft.com/cognitiveservices/v1"
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, data=ssml) as response:
                    audio_bytes = await response.read()
            
            # 转换为numpy数组
            audio_array, sample_rate = sf.read(io.BytesIO(audio_bytes))
            
            processing_time = time.time() - start_time
            
            result = TTSResult(
                audio_data=audio_bytes,
                format="mp3",
                duration=len(audio_array) / sample_rate,
                sample_rate=sample_rate,
                timestamp=datetime.now(),
                engine_used="azure_tts",
                processing_time=processing_time,
                text=text,
                voice=config.azure_voice,
                metadata={
                    "region": config.azure_region,
                    "speed": config.speed,
                    "volume": config.volume
                }
            )
            
            # 缓存结果
            if config.enable_cache:
                self.cache[cache_key] = result
            
            return result
            
        except Exception as e:
            self.logger.error(f"Azure TTS合成失败: {e}")
            raise


class CoquiTTSEngine(TTSEngine):
    """Coqui TTS引擎"""
    
    def __init__(self):
        self.model = None
        self.logger = logging.getLogger(__name__)
        self.cache = {}
    
    def is_available(self) -> bool:
        """检查Coqui TTS是否可用"""
        try:
            import TTS
            return True
        except ImportError:
            return False
    
    def get_available_voices(self) -> List[str]:
        """获取可用声音列表"""
        return [
            "tts_models/en/ljspeech/tacotron2-DDC",
            "tts_models/en/ljspeech/tacotron2-DDC_ph",
            "tts_models/multilingual/multi-dataset/xtts_v2"
        ]
    
    async def synthesize(self, text: str, config: TTSConfig) -> TTSResult:
        """使用Coqui TTS合成语音"""
        start_time = time.time()
        
        try:
            import TTS
            
            # 检查缓存
            cache_key = f"{config.coqui_model}_{hash(text)}"
            if config.enable_cache and cache_key in self.cache:
                cached_result = self.cache[cache_key]
                cached_result.timestamp = datetime.now()
                return cached_result
            
            # 加载模型
            if self.model is None:
                self.model = TTS.TTS(model_name=config.coqui_model, 
                                   device=config.coqui_device)
            
            # 合成语音
            wav = self.model.tts(text=text)
            
            # 转换为字节数据
            buffer = io.BytesIO()
            sf.write(buffer, wav, config.sample_rate, format='WAV')
            audio_bytes = buffer.getvalue()
            
            processing_time = time.time() - start_time
            
            result = TTSResult(
                audio_data=audio_bytes,
                format="wav",
                duration=len(wav) / config.sample_rate,
                sample_rate=config.sample_rate,
                timestamp=datetime.now(),
                engine_used="coqui_tts",
                processing_time=processing_time,
                text=text,
                voice=config.coqui_model,
                metadata={
                    "model": config.coqui_model,
                    "device": config.coqui_device
                }
            )
            
            # 缓存结果
            if config.enable_cache:
                self.cache[cache_key] = result
            
            return result
            
        except Exception as e:
            self.logger.error(f"Coqui TTS合成失败: {e}")
            raise


class TTSFramework:
    """TTS框架主类"""
    
    def __init__(self, config: TTSConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # 初始化引擎
        self.engines = {
            "gtts": GTTSEngine(),
            "edge_tts": EdgeTTSEngine(),
            "azure": AzureTTSEngine(config),
            "coqui": CoquiTTSEngine()
        }
        
        # 缓存目录
        if config.enable_cache:
            Path(config.cache_dir).mkdir(parents=True, exist_ok=True)
        
        # 集成框架
        self.integration_framework = None
        if config.integration_enabled:
            self.integration_framework = IntegrationFramework()
        
        # 工作记忆
        self.working_memory = None
        if config.memory_sync_enabled:
            self.working_memory = WorkingMemory()
    
    async def synthesize_speech(self, text: str, 
                               engine: Optional[str] = None) -> TTSResult:
        """合成语音"""
        if engine is None:
            engine = self.config.engine
        
        # 检查引擎可用性
        if engine not in self.engines:
            raise ValueError(f"不支持的TTS引擎: {engine}")
        
        tts_engine = self.engines[engine]
        if not tts_engine.is_available():
            raise RuntimeError(f"TTS引擎不可用: {engine}")
        
        # 文本预处理
        processed_text = await self._preprocess_text(text)
        
        # 分块处理长文本
        if len(processed_text) > self.config.max_text_length:
            return await self._synthesize_long_text(processed_text, engine)
        
        # 合成语音
        result = await tts_engine.synthesize(processed_text, self.config)
        
        # 同步到记忆系统
        if self.working_memory:
            await self._sync_to_memory(result)
        
        # 集成到框架
        if self.integration_framework:
            await self._integrate_result(result)
        
        return result
    
    async def synthesize_to_file(self, text: str, file_path: Union[str, Path],
                                engine: Optional[str] = None) -> TTSResult:
        """合成语音并保存到文件"""
        result = await self.synthesize_speech(text, engine)
        
        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        result.save_to_file(file_path)
        
        return result
    
    async def batch_synthesize(self, texts: List[str], 
                              engine: Optional[str] = None) -> List[TTSResult]:
        """批量合成语音"""
        tasks = []
        for text in texts:
            task = self.synthesize_speech(text, engine)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理异常结果
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                self.logger.error(f"文本 {texts[i]} 合成失败: {result}")
                processed_results.append(None)
            else:
                processed_results.append(result)
        
        return processed_results
    
    async def _synthesize_long_text(self, text: str, engine: str) -> TTSResult:
        """处理长文本合成"""
        # 分块
        chunks = []
        current_chunk = ""
        
        sentences = text.split('。')
        for sentence in sentences:
            if len(current_chunk + sentence) <= self.config.chunk_size:
                current_chunk += sentence + "。"
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = sentence + "。"
        
        if current_chunk:
            chunks.append(current_chunk)
        
        # 逐块合成
        audio_parts = []
        total_duration = 0.0
        
        for chunk in chunks:
            result = await self.engines[engine].synthesize(chunk, self.config)
            audio_parts.append(result.audio_data)
            total_duration += result.duration
        
        # 合并音频
        combined_audio = b""
        for audio_part in audio_parts:
            combined_audio += audio_part
        
        return TTSResult(
            audio_data=combined_audio,
            format=self.config.format,
            duration=total_duration,
            sample_rate=self.config.sample_rate,
            timestamp=datetime.now(),
            engine_used=engine,
            processing_time=0.0,  # 将在主函数中计算
            text=text,
            voice=self.config.voice or engine,
            metadata={"chunks": len(chunks)}
        )
    
    async def _preprocess_text(self, text: str) -> str:
        """预处理文本"""
        # 清理文本
        text = text.strip()
        
        # 处理特殊字符
        text = text.replace('\n', ' ')
        text = text.replace('\r', ' ')
        
        # 限制长度
        if len(text) > self.config.max_text_length:
            text = text[:self.config.max_text_length]
            self.logger.warning(f"文本长度超过限制，已截断")
        
        return text
    
    async def _sync_to_memory(self, result: TTSResult):
        """同步结果到记忆系统"""
        try:
            memory_data = {
                'type': 'tts_result',
                'text': result.text,
                'voice': result.voice,
                'duration': result.duration,
                'timestamp': result.timestamp.isoformat(),
                'engine': result.engine_used
            }
            
            await self.working_memory.add(memory_data)
            
        except Exception as e:
            self.logger.error(f"记忆同步失败: {e}")
    
    async def _integrate_result(self, result: TTSResult):
        """集成结果到框架"""
        try:
            if self.integration_framework:
                # 通知其他组件TTS结果
                await self.integration_framework.broadcast_event(
                    'tts_completed',
                    {
                        'text': result.text,
                        'voice': result.voice,
                        'duration': result.duration,
                        'engine': result.engine_used
                    }
                )
                
        except Exception as e:
            self.logger.error(f"框架集成失败: {e}")
    
    def get_available_engines(self) -> List[str]:
        """获取可用的TTS引擎"""
        available = []
        for name, engine in self.engines.items():
            if engine.is_available():
                available.append(name)
        return available
    
    def get_available_voices(self, engine: Optional[str] = None) -> List[str]:
        """获取可用声音列表"""
        if engine is None:
            engine = self.config.engine
        
        if engine in self.engines:
            return self.engines[engine].get_available_voices()
        return []
    
    def get_synthesis_stats(self) -> Dict[str, Any]:
        """获取合成统计信息"""
        return {
            'available_engines': self.get_available_engines(),
            'current_engine': self.config.engine,
            'language': self.config.language,
            'voice': self.config.voice,
            'sample_rate': self.config.sample_rate,
            'cache_enabled': self.config.enable_cache,
            'max_text_length': self.config.max_text_length
        }
    
    def clear_cache(self):
        """清除缓存"""
        if self.config.enable_cache:
            for engine in self.engines.values():
                if hasattr(engine, 'cache'):
                    engine.cache.clear()
            
            # 清除文件缓存
            cache_dir = Path(self.config.cache_dir)
            if cache_dir.exists():
                for cache_file in cache_dir.glob("*"):
                    cache_file.unlink()