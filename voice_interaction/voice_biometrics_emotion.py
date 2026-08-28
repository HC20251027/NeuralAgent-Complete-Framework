"""
声纹识别和情感分析模块 - Voice Biometrics and Emotion Analysis
==============================================================

功能包括：
- 声纹识别 (Voiceprint Recognition)
- 情感分析 (Emotion Analysis)
- 语音特征提取
- 说话人识别
- 情感状态检测

Author: HC20251027
Date: 2025-11-06
"""

import asyncio
import logging
import numpy as np
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, List, Dict, Any, Union, Tuple
from pathlib import Path
import json
import time
from datetime import datetime
import pickle
import hashlib

# 音频处理和机器学习
import librosa
import soundfile as sf
from sklearn.mixture import GaussianMixture
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.metrics.pairwise import cosine_similarity
import joblib

# 深度学习
try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    from transformers import AutoTokenizer, AutoModel
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

# 异步支持
import aiofiles

# 配置管理
from agno_bmad_integration.framework import IntegrationFramework
from agno.memory.working import WorkingMemory


@dataclass
class BiometricsConfig:
    """声纹识别配置类"""
    # 基本配置
    sample_rate: int = 16000
    n_mfcc: int = 13
    n_fft: int = 2048
    hop_length: int = 512
    window_length: int = 1024
    
    # 声纹识别配置
    voiceprint_length: int = 256
    threshold_similarity: float = 0.8
    max_enrollment_samples: int = 5
    min_enrollment_duration: float = 3.0
    
    # 情感分析配置
    emotion_classes: List[str] = None
    emotion_confidence_threshold: float = 0.6
    enable_real_time_analysis: bool = True
    
    # 模型配置
    use_deep_features: bool = True
    deep_model_name: str = "hfl/chinese-roberta-wwm-ext"
    use_pretrained_voice_model: bool = False
    
    # 性能配置
    batch_size: int = 32
    max_audio_length: float = 30.0
    overlap_ratio: float = 0.5
    
    # 存储配置
    voiceprint_db_path: str = "/tmp/voiceprints.pkl"
    model_cache_dir: str = "/tmp/biometrics_models"
    
    # 集成配置
    integration_enabled: bool = True
    memory_sync_enabled: bool = True


@dataclass
class VoiceprintResult:
    """声纹识别结果"""
    speaker_id: Optional[str]
    confidence: float
    similarity_score: float
    is_enrolled: bool
    voiceprint_vector: np.ndarray
    timestamp: datetime
    processing_time: float
    metadata: Optional[Dict] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'speaker_id': self.speaker_id,
            'confidence': self.confidence,
            'similarity_score': self.similarity_score,
            'is_enrolled': self.is_enrolled,
            'timestamp': self.timestamp.isoformat(),
            'processing_time': self.processing_time,
            'metadata': self.metadata
        }


@dataclass
class EmotionResult:
    """情感分析结果"""
    primary_emotion: str
    confidence: float
    emotion_scores: Dict[str, float]
    arousal: float  # 唤醒度 (0-1)
    valence: float  # 效价 (0-1)
    dominance: float  # 支配度 (0-1)
    timestamp: datetime
    processing_time: float
    metadata: Optional[Dict] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'primary_emotion': self.primary_emotion,
            'confidence': self.confidence,
            'emotion_scores': self.emotion_scores,
            'arousal': self.arousal,
            'valence': self.valence,
            'dominance': self.dominance,
            'timestamp': self.timestamp.isoformat(),
            'processing_time': self.processing_time,
            'metadata': self.metadata
        }


class VoiceFeatureExtractor:
    """语音特征提取器"""
    
    def __init__(self, config: BiometricsConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.scaler = StandardScaler()
        self.pca = PCA(n_components=config.voiceprint_length)
        self.is_fitted = False
    
    def extract_mfcc_features(self, audio: np.ndarray) -> np.ndarray:
        """提取MFCC特征"""
        # 计算MFCC
        mfccs = librosa.feature.mfcc(
            y=audio,
            sr=self.config.sample_rate,
            n_mfcc=self.config.n_mfcc,
            n_fft=self.config.n_fft,
            hop_length=self.config.hop_length,
            window_length=self.config.window_length
        )
        
        # 计算一阶和二阶差分
        mfcc_delta1 = librosa.feature.delta(mfccs)
        mfcc_delta2 = librosa.feature.delta(mfccs, order=2)
        
        # 拼接特征
        features = np.vstack([mfccs, mfcc_delta1, mfcc_delta2])
        
        return features
    
    def extract_spectral_features(self, audio: np.ndarray) -> np.ndarray:
        """提取频谱特征"""
        features = []
        
        # 频谱质心
        spectral_centroids = librosa.feature.spectral_centroid(y=audio, sr=self.config.sample_rate)
        features.append(spectral_centroids.mean())
        
        # 频谱带宽
        spectral_bandwidth = librosa.feature.spectral_bandwidth(y=audio, sr=self.config.sample_rate)
        features.append(spectral_bandwidth.mean())
        
        # 频谱对比度
        spectral_contrast = librosa.feature.spectral_contrast(y=audio, sr=self.config.sample_rate)
        features.append(spectral_contrast.mean())
        
        # 频谱滚降
        spectral_rolloff = librosa.feature.spectral_rolloff(y=audio, sr=self.config.sample_rate)
        features.append(spectral_rolloff.mean())
        
        # 零交叉率
        zcr = librosa.feature.zero_crossing_rate(audio)
        features.append(zcr.mean())
        
        # 梅尔频谱
        mel_spectrogram = librosa.feature.melspectrogram(y=audio, sr=self.config.sample_rate)
        features.append(mel_spectrogram.mean())
        
        return np.array(features)
    
    def extract_temporal_features(self, audio: np.ndarray) -> np.ndarray:
        """提取时域特征"""
        features = []
        
        # 能量
        energy = np.sum(audio ** 2) / len(audio)
        features.append(energy)
        
        # 均值
        features.append(np.mean(audio))
        
        # 标准差
        features.append(np.std(audio))
        
        # 偏度
        features.append(float(np.mean(((audio - np.mean(audio)) / np.std(audio)) ** 3)))
        
        # 峰度
        features.append(float(np.mean(((audio - np.mean(audio)) / np.std(audio)) ** 4)))
        
        # 过零率
        zcr = np.sum(np.diff(np.sign(audio)) != 0) / len(audio)
        features.append(zcr)
        
        return np.array(features)
    
    def extract_voiceprint_features(self, audio: np.ndarray) -> np.ndarray:
        """提取声纹特征"""
        # MFCC特征
        mfcc_features = self.extract_mfcc_features(audio)
        
        # 频谱特征
        spectral_features = self.extract_spectral_features(audio)
        
        # 时域特征
        temporal_features = self.extract_temporal_features(audio)
        
        # 拼接所有特征
        mfcc_mean = np.mean(mfcc_features, axis=1)
        mfcc_std = np.std(mfcc_features, axis=1)
        
        all_features = np.concatenate([
            mfcc_mean, mfcc_std, spectral_features, temporal_features
        ])
        
        # 标准化和降维
        if not self.is_fitted:
            all_features_scaled = self.scaler.fit_transform(all_features.reshape(1, -1))
            all_features_reduced = self.pca.fit_transform(all_features_scaled)
            self.is_fitted = True
        else:
            all_features_scaled = self.scaler.transform(all_features.reshape(1, -1))
            all_features_reduced = self.pca.transform(all_features_scaled)
        
        return all_features_reduced.flatten()
    
    def extract_emotion_features(self, audio: np.ndarray) -> np.ndarray:
        """提取情感特征"""
        # 基础特征
        mfcc_features = self.extract_mfcc_features(audio)
        
        # 情感相关的统计特征
        features = []
        
        # MFCC统计特征
        for i in range(self.config.n_mfcc):
            mfcc_coeff = mfcc_features[i]
            features.extend([
                np.mean(mfcc_coeff),
                np.std(mfcc_coeff),
                np.median(mfcc_coeff),
                np.max(mfcc_coeff) - np.min(mfcc_coeff)
            ])
        
        # 频谱特征
        spectral_features = self.extract_spectral_features(audio)
        features.extend(spectral_features)
        
        # 时域特征
        temporal_features = self.extract_temporal_features(audio)
        features.extend(temporal_features)
        
        # 韵律特征
        # 基频
        f0, _, _ = librosa.pyin(
            audio, 
            fmin=librosa.note_to_hz('C2'), 
            fmax=librosa.note_to_hz('C7')
        )
        f0_mean = np.nanmean(f0[f0 > 0]) if not np.isnan(f0).all() else 0
        f0_std = np.nanstd(f0[f0 > 0]) if not np.isnan(f0).all() else 0
        
        features.extend([f0_mean, f0_std])
        
        # 语速 (基于过零率变化)
        zcr = librosa.feature.zero_crossing_rate(audio)
        features.extend([np.mean(zcr), np.std(zcr)])
        
        return np.array(features)


class VoiceprintDatabase:
    """声纹数据库"""
    
    def __init__(self, db_path: str):
        self.db_path = Path(db_path)
        self.voiceprints = {}
        self._load_database()
    
    def _load_database(self):
        """加载数据库"""
        if self.db_path.exists():
            try:
                with open(self.db_path, 'rb') as f:
                    self.voiceprints = pickle.load(f)
            except Exception as e:
                logging.warning(f"无法加载声纹数据库: {e}")
                self.voiceprints = {}
    
    def _save_database(self):
        """保存数据库"""
        try:
            with open(self.db_path, 'wb') as f:
                pickle.dump(self.voiceprints, f)
        except Exception as e:
            logging.error(f"无法保存声纹数据库: {e}")
    
    def enroll_speaker(self, speaker_id: str, voiceprint_vector: np.ndarray) -> bool:
        """注册说话人"""
        try:
            if speaker_id not in self.voiceprints:
                self.voiceprints[speaker_id] = {
                    'voiceprints': [],
                    'enrollment_count': 0,
                    'last_updated': datetime.now()
                }
            
            # 添加声纹向量
            self.voiceprints[speaker_id]['voiceprints'].append(voiceprint_vector)
            self.voiceprints[speaker_id]['enrollment_count'] += 1
            self.voiceprints[speaker_id]['last_updated'] = datetime.now()
            
            # 限制样本数量
            if len(self.voiceprints[speaker_id]['voiceprints']) > 10:
                self.voiceprints[speaker_id]['voiceprints'] = \
                    self.voiceprints[speaker_id]['voiceprints'][-10:]
            
            self._save_database()
            return True
            
        except Exception as e:
            logging.error(f"注册说话人失败: {e}")
            return False
    
    def get_speaker_voiceprint(self, speaker_id: str) -> Optional[np.ndarray]:
        """获取说话人声纹"""
        if speaker_id not in self.voiceprints:
            return None
        
        voiceprints = self.voiceprints[speaker_id]['voiceprints']
        if not voiceprints:
            return None
        
        # 返回平均声纹
        return np.mean(voiceprints, axis=0)
    
    def get_all_speakers(self) -> List[str]:
        """获取所有说话人ID"""
        return list(self.voiceprints.keys())
    
    def delete_speaker(self, speaker_id: str) -> bool:
        """删除说话人"""
        try:
            if speaker_id in self.voiceprints:
                del self.voiceprints[speaker_id]
                self._save_database()
                return True
            return False
        except Exception as e:
            logging.error(f"删除说话人失败: {e}")
            return False
    
    def get_database_stats(self) -> Dict[str, Any]:
        """获取数据库统计信息"""
        stats = {
            'total_speakers': len(self.voiceprints),
            'speaker_details': {}
        }
        
        for speaker_id, data in self.voiceprints.items():
            stats['speaker_details'][speaker_id] = {
                'enrollment_count': data['enrollment_count'],
                'last_updated': data['last_updated'].isoformat()
            }
        
        return stats


class VoiceprintRecognizer:
    """声纹识别器"""
    
    def __init__(self, config: BiometricsConfig):
        self.config = config
        self.feature_extractor = VoiceFeatureExtractor(config)
        self.database = VoiceprintDatabase(config.voiceprint_db_path)
        self.logger = logging.getLogger(__name__)
    
    async def recognize_speaker(self, audio: np.ndarray) -> VoiceprintResult:
        """识别说话人"""
        start_time = time.time()
        
        try:
            # 提取声纹特征
            voiceprint_vector = self.feature_extractor.extract_voiceprint_features(audio)
            
            # 计算与数据库中所有声纹的相似度
            best_match = None
            best_similarity = 0.0
            best_speaker_id = None
            
            for speaker_id in self.database.get_all_speakers():
                stored_voiceprint = self.database.get_speaker_voiceprint(speaker_id)
                if stored_voiceprint is not None:
                    # 计算余弦相似度
                    similarity = cosine_similarity(
                        voiceprint_vector.reshape(1, -1),
                        stored_voiceprint.reshape(1, -1)
                    )[0][0]
                    
                    if similarity > best_similarity:
                        best_similarity = similarity
                        best_speaker_id = speaker_id
                        best_match = stored_voiceprint
            
            processing_time = time.time() - start_time
            
            # 判断是否识别成功
            is_recognized = (best_speaker_id is not None and 
                           best_similarity >= self.config.threshold_similarity)
            
            return VoiceprintResult(
                speaker_id=best_speaker_id if is_recognized else None,
                confidence=best_similarity if is_recognized else 0.0,
                similarity_score=best_similarity,
                is_enrolled=is_recognized,
                voiceprint_vector=voiceprint_vector,
                timestamp=datetime.now(),
                processing_time=processing_time,
                metadata={
                    'threshold': self.config.threshold_similarity,
                    'total_speakers': len(self.database.get_all_speakers())
                }
            )
            
        except Exception as e:
            self.logger.error(f"声纹识别失败: {e}")
            raise
    
    async def enroll_speaker(self, speaker_id: str, audio: np.ndarray) -> bool:
        """注册说话人"""
        try:
            # 提取声纹特征
            voiceprint_vector = self.feature_extractor.extract_voiceprint_features(audio)
            
            # 注册到数据库
            success = self.database.enroll_speaker(speaker_id, voiceprint_vector)
            
            return success
            
        except Exception as e:
            self.logger.error(f"说话人注册失败: {e}")
            return False
    
    def get_enrollment_status(self, speaker_id: str) -> Dict[str, Any]:
        """获取注册状态"""
        if speaker_id in self.database.voiceprints:
            data = self.database.voiceprints[speaker_id]
            return {
                'enrolled': True,
                'enrollment_count': data['enrollment_count'],
                'last_updated': data['last_updated'].isoformat()
            }
        else:
            return {'enrolled': False}


class EmotionAnalyzer:
    """情感分析器"""
    
    def __init__(self, config: BiometricsConfig):
        self.config = config
        self.feature_extractor = VoiceFeatureExtractor(config)
        self.emotion_model = None
        self.emotion_labels = config.emotion_classes or [
            'neutral', 'happy', 'sad', 'angry', 'fearful', 'disgusted', 'surprised'
        ]
        self.scaler = StandardScaler()
        self.classifier = None
        self.is_trained = False
        self.logger = logging.getLogger(__name__)
        
        # 初始化模型
        self._initialize_models()
    
    def _initialize_models(self):
        """初始化模型"""
        try:
            # 简单的基于规则的情感分析
            # 在实际应用中，这里可以加载预训练的深度学习模型
            self.is_trained = True
            
        except Exception as e:
            self.logger.warning(f"模型初始化失败: {e}")
    
    async def analyze_emotion(self, audio: np.ndarray) -> EmotionResult:
        """分析情感"""
        start_time = time.time()
        
        try:
            # 提取情感特征
            emotion_features = self.feature_extractor.extract_emotion_features(audio)
            
            # 基于规则的情感分析
            emotion_scores = self._rule_based_emotion_analysis(emotion_features)
            
            # 找出主要情感
            primary_emotion = max(emotion_scores, key=emotion_scores.get)
            confidence = emotion_scores[primary_emotion]
            
            # 计算PAD模型参数 (Pleasure-Arousal-Dominance)
            pad_scores = self._calculate_pad_scores(emotion_scores)
            
            processing_time = time.time() - start_time
            
            return EmotionResult(
                primary_emotion=primary_emotion,
                confidence=confidence,
                emotion_scores=emotion_scores,
                arousal=pad_scores['arousal'],
                valence=pad_scores['valence'],
                dominance=pad_scores['dominance'],
                timestamp=datetime.now(),
                processing_time=processing_time,
                metadata={
                    'feature_dimensions': len(emotion_features),
                    'analysis_method': 'rule_based'
                }
            )
            
        except Exception as e:
            self.logger.error(f"情感分析失败: {e}")
            raise
    
    def _rule_based_emotion_analysis(self, features: np.ndarray) -> Dict[str, float]:
        """基于规则的情感分析"""
        # 简化的规则系统
        scores = {emotion: 0.0 for emotion in self.emotion_labels}
        
        # 特征索引映射
        # 假设前13个是MFCC均值，接下来13个是MFCC标准差等
        if len(features) >= 26:
            # 基频相关特征
            f0_mean = features[-4] if len(features) > 26 else 0
            f0_std = features[-3] if len(features) > 26 else 0
            
            # 能量相关特征
            energy = features[-6] if len(features) > 26 else 0
            
            # 频谱特征
            spectral_centroid = features[13] if len(features) > 13 else 0
            
            # 基于规则的评分
            # 快乐: 高能量, 中等基频变化
            scores['happy'] = min(1.0, (energy + abs(f0_std)) / 2)
            
            # 悲伤: 低能量, 低基频变化
            scores['sad'] = min(1.0, (1 - energy) + (1 - abs(f0_std)) / 2)
            
            # 愤怒: 高能量, 高基频变化
            scores['angry'] = min(1.0, energy + abs(f0_std))
            
            # 恐惧: 中等能量, 高基频变化
            scores['fearful'] = min(1.0, 0.5 + abs(f0_std) / 2)
            
            # 惊讶: 高频谱质心
            scores['surprised'] = min(1.0, spectral_centroid)
            
            # 中性: 其他情感都较低
            scores['neutral'] = 1.0 - max(scores['happy'], scores['sad'], 
                                         scores['angry'], scores['fearful'], 
                                         scores['surprised'])
            
            # 厌恶: 基于特定频谱特征
            scores['disgusted'] = 0.3  # 默认较低分数
        
        # 归一化分数
        total_score = sum(scores.values())
        if total_score > 0:
            scores = {k: v / total_score for k, v in scores.items()}
        
        return scores
    
    def _calculate_pad_scores(self, emotion_scores: Dict[str, float]) -> Dict[str, float]:
        """计算PAD模型分数"""
        # PAD映射 (基于心理学研究)
        pad_mapping = {
            'happy': {'valence': 0.8, 'arousal': 0.7, 'dominance': 0.6},
            'sad': {'valence': -0.8, 'arousal': -0.3, 'dominance': -0.4},
            'angry': {'valence': -0.6, 'arousal': 0.8, 'dominance': 0.7},
            'fearful': {'valence': -0.7, 'arousal': 0.6, 'dominance': -0.3},
            'disgusted': {'valence': -0.6, 'arousal': -0.2, 'dominance': 0.3},
            'surprised': {'valence': 0.4, 'arousal': 0.8, 'dominance': 0.4},
            'neutral': {'valence': 0.0, 'arousal': 0.0, 'dominance': 0.0}
        }
        
        # 加权计算PAD分数
        valence = sum(emotion_scores[emotion] * pad_mapping[emotion]['valence'] 
                     for emotion in emotion_scores)
        arousal = sum(emotion_scores[emotion] * pad_mapping[emotion]['arousal'] 
                     for emotion in emotion_scores)
        dominance = sum(emotion_scores[emotion] * pad_mapping[emotion]['dominance'] 
                       for emotion in emotion_scores)
        
        # 归一化到0-1范围
        valence = (valence + 1) / 2
        arousal = (arousal + 1) / 2
        dominance = (dominance + 1) / 2
        
        return {
            'valence': max(0, min(1, valence)),
            'arousal': max(0, min(1, arousal)),
            'dominance': max(0, min(1, dominance))
        }


class VoiceBiometricsEmotion:
    """声纹识别和情感分析主类"""
    
    def __init__(self, config: BiometricsConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # 初始化组件
        self.voiceprint_recognizer = VoiceprintRecognizer(config)
        self.emotion_analyzer = EmotionAnalyzer(config)
        
        # 集成框架
        self.integration_framework = None
        if config.integration_enabled:
            self.integration_framework = IntegrationFramework()
        
        # 工作记忆
        self.working_memory = None
        if config.memory_sync_enabled:
            self.working_memory = WorkingMemory()
    
    async def analyze_voice(self, audio: np.ndarray, 
                          enable_voiceprint: bool = True,
                          enable_emotion: bool = True) -> Dict[str, Any]:
        """综合分析语音"""
        results = {}
        
        # 声纹识别
        if enable_voiceprint:
            try:
                voiceprint_result = await self.voiceprint_recognizer.recognize_speaker(audio)
                results['voiceprint'] = voiceprint_result.to_dict()
                
                # 同步到记忆系统
                if self.working_memory:
                    await self._sync_voiceprint_to_memory(voiceprint_result)
                
            except Exception as e:
                self.logger.error(f"声纹识别失败: {e}")
                results['voiceprint'] = {'error': str(e)}
        
        # 情感分析
        if enable_emotion:
            try:
                emotion_result = await self.emotion_analyzer.analyze_emotion(audio)
                results['emotion'] = emotion_result.to_dict()
                
                # 同步到记忆系统
                if self.working_memory:
                    await self._sync_emotion_to_memory(emotion_result)
                
            except Exception as e:
                self.logger.error(f"情感分析失败: {e}")
                results['emotion'] = {'error': str(e)}
        
        # 集成到框架
        if self.integration_framework:
            await self._integrate_results(results)
        
        return results
    
    async def enroll_speaker(self, speaker_id: str, audio: np.ndarray) -> bool:
        """注册说话人"""
        try:
            success = await self.voiceprint_recognizer.enroll_speaker(speaker_id, audio)
            
            if success and self.working_memory:
                memory_data = {
                    'type': 'speaker_enrollment',
                    'speaker_id': speaker_id,
                    'timestamp': datetime.now().isoformat()
                }
                await self.working_memory.add(memory_data)
            
            return success
            
        except Exception as e:
            self.logger.error(f"说话人注册失败: {e}")
            return False
    
    async def batch_analyze(self, audio_list: List[np.ndarray],
                          enable_voiceprint: bool = True,
                          enable_emotion: bool = True) -> List[Dict[str, Any]]:
        """批量分析"""
        tasks = []
        for audio in audio_list:
            task = self.analyze_voice(audio, enable_voiceprint, enable_emotion)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理异常结果
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                self.logger.error(f"音频 {i} 分析失败: {result}")
                processed_results.append({'error': str(result)})
            else:
                processed_results.append(result)
        
        return processed_results
    
    async def _sync_voiceprint_to_memory(self, result: VoiceprintResult):
        """同步声纹结果到记忆系统"""
        try:
            memory_data = {
                'type': 'voiceprint_result',
                'speaker_id': result.speaker_id,
                'confidence': result.confidence,
                'timestamp': result.timestamp.isoformat()
            }
            
            await self.working_memory.add(memory_data)
            
        except Exception as e:
            self.logger.error(f"声纹记忆同步失败: {e}")
    
    async def _sync_emotion_to_memory(self, result: EmotionResult):
        """同步情感结果到记忆系统"""
        try:
            memory_data = {
                'type': 'emotion_result',
                'primary_emotion': result.primary_emotion,
                'confidence': result.confidence,
                'arousal': result.arousal,
                'valence': result.valence,
                'timestamp': result.timestamp.isoformat()
            }
            
            await self.working_memory.add(memory_data)
            
        except Exception as e:
            self.logger.error(f"情感记忆同步失败: {e}")
    
    async def _integrate_results(self, results: Dict[str, Any]):
        """集成结果到框架"""
        try:
            if self.integration_framework:
                await self.integration_framework.broadcast_event(
                    'voice_analysis_completed',
                    results
                )
                
        except Exception as e:
            self.logger.error(f"框架集成失败: {e}")
    
    def get_database_stats(self) -> Dict[str, Any]:
        """获取数据库统计信息"""
        return self.voiceprint_recognizer.database.get_database_stats()
    
    def get_analysis_stats(self) -> Dict[str, Any]:
        """获取分析统计信息"""
        return {
            'voiceprint_enabled': True,
            'emotion_enabled': True,
            'emotion_classes': self.emotion_analyzer.emotion_labels,
            'database_stats': self.get_database_stats()
        }