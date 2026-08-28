"""
语音交互系统框架 - Voice Interaction Framework
================================================

提供完整的语音交互解决方案，包括：
- 语音识别(ASR)
- 语音合成(TTS)
- 声纹识别和情感分析
- 语音交互控制接口

与Agno-BMAD框架和NeuralAgent视觉模块深度集成。

Author: HC20251027
Date: 2025-11-06
"""

from .asr_framework import ASRFramework, ASRResult, ASRConfig
from .tts_framework import TTSFramework, TTSResult, TTSConfig
from .voice_biometrics_emotion import (
    VoiceBiometricsEmotion, 
    VoiceprintResult, 
    EmotionResult,
    BiometricsConfig
)
from .voice_control_interface import (
    VoiceControlInterface,
    VoiceCommand,
    VoiceSession,
    VoiceControlConfig
)

__all__ = [
    'ASRFramework',
    'ASRResult', 
    'ASRConfig',
    'TTSFramework',
    'TTSResult',
    'TTSConfig', 
    'VoiceBiometricsEmotion',
    'VoiceprintResult',
    'EmotionResult',
    'BiometricsConfig',
    'VoiceControlInterface',
    'VoiceCommand',
    'VoiceSession',
    'VoiceControlConfig'
]

__version__ = '1.0.0'
__author__ = 'HC20251027'