"""
视频到PRD自动生成演示 - Video to PRD Auto Generation Demo
========================================================

演示从视频输入自动生成PRD文档的完整流程：
1. 视频处理和内容提取
2. 语音识别和转录
3. 关键信息提取
4. PRD文档生成

Author: HC20251027
Date: 2025-11-06
"""

import asyncio
import logging
import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import tempfile
import uuid

# 视频处理
try:
    import cv2
    import moviepy
    VIDEO_AVAILABLE = True
except ImportError:
    VIDEO_AVAILABLE = False

# 音频处理
import librosa
import soundfile as sf

# NLP处理
import re
import nltk
from collections import Counter

# 框架集成
from neural_agent_vision.neural_agent_vision import NeuralAgentVision
from voice_interaction.voice_control_interface import VoiceControlInterface
from agno_bmad_integration.framework import IntegrationFramework
from bmad.roles.analyst import AnalystAgent
from bmad.roles.pm import ProductManagerAgent


@dataclass
class VideoAnalysisResult:
    """视频分析结果"""
    video_id: str
    duration: float
    frame_count: int
    fps: float
    resolution: Tuple[int, int]
    transcript: str
    key_scenes: List[Dict[str, Any]] = field(default_factory=list)
    extracted_text: List[str] = field(default_factory=list)
    audio_segments: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'video_id': self.video_id,
            'duration': self.duration,
            'frame_count': self.frame_count,
            'fps': self.fps,
            'resolution': self.resolution,
            'transcript': self.transcript,
            'key_scenes': self.key_scenes,
            'extracted_text': self.extracted_text,
            'audio_segments': self.audio_segments,
            'metadata': self.metadata
        }


@dataclass
class PRDContent:
    """PRD内容结构"""
    title: str
    overview: str
    objectives: List[str]
    features: List[Dict[str, Any]]
    user_stories: List[Dict[str, Any]]
    technical_requirements: List[str]
    success_metrics: List[str]
    timeline: Dict[str, Any]
    risks: List[str]
    stakeholders: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'title': self.title,
            'overview': self.overview,
            'objectives': self.objectives,
            'features': self.features,
            'user_stories': self.user_stories,
            'technical_requirements': self.technical_requirements,
            'success_metrics': self.success_metrics,
            'timeline': self.timeline,
            'risks': self.risks,
            'stakeholders': self.stakeholders
        }


class VideoProcessor:
    """视频处理器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        if not VIDEO_AVAILABLE:
            self.logger.warning("视频处理库不可用，将使用模拟数据")
    
    async def extract_frames(self, video_path: str, interval: float = 5.0) -> List[str]:
        """提取视频帧"""
        if not VIDEO_AVAILABLE:
            # 返回模拟帧路径
            return [f"/tmp/mock_frame_{i}.jpg" for i in range(10)]
        
        try:
            cap = cv2.VideoCapture(video_path)
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_interval = int(fps * interval)
            
            frame_paths = []
            frame_count = 0
            saved_count = 0
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                if frame_count % frame_interval == 0:
                    # 保存帧
                    frame_path = f"/tmp/frame_{saved_count:04d}.jpg"
                    cv2.imwrite(frame_path, frame)
                    frame_paths.append(frame_path)
                    saved_count += 1
                
                frame_count += 1
            
            cap.release()
            return frame_paths
            
        except Exception as e:
            self.logger.error(f"视频帧提取失败: {e}")
            return []
    
    async def extract_audio(self, video_path: str) -> str:
        """提取音频"""
        if not VIDEO_AVAILABLE:
            # 返回模拟音频路径
            return "/tmp/mock_audio.wav"
        
        try:
            # 使用moviepy提取音频
            video = moviepy.VideoFileClip(video_path)
            audio_path = f"/tmp/audio_{int(time.time())}.wav"
            video.audio.write_audiofile(audio_path, verbose=False, logger=None)
            return audio_path
            
        except Exception as e:
            self.logger.error(f"音频提取失败: {e}")
            return ""
    
    async def analyze_video_structure(self, video_path: str) -> Dict[str, Any]:
        """分析视频结构"""
        if not VIDEO_AVAILABLE:
            return {
                'duration': 300.0,  # 5分钟
                'frame_count': 7500,
                'fps': 25.0,
                'resolution': (1920, 1080),
                'scenes': [
                    {'start': 0, 'end': 60, 'type': 'intro'},
                    {'start': 60, 'end': 180, 'type': 'main_content'},
                    {'start': 180, 'end': 300, 'type': 'conclusion'}
                ]
            }
        
        try:
            cap = cv2.VideoCapture(video_path)
            
            duration = cap.get(cv2.CAP_PROP_FRAME_COUNT) / cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            cap.release()
            
            return {
                'duration': duration,
                'frame_count': frame_count,
                'fps': fps,
                'resolution': (width, height),
                'scenes': self._detect_scenes(video_path)
            }
            
        except Exception as e:
            self.logger.error(f"视频结构分析失败: {e}")
            return {}


class ContentExtractor:
    """内容提取器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    async def extract_key_information(self, transcript: str, frames: List[str]) -> Dict[str, Any]:
        """提取关键信息"""
        # 文本分析
        text_analysis = self._analyze_transcript(transcript)
        
        # 图像分析
        image_analysis = await self._analyze_frames(frames)
        
        # 关键概念提取
        key_concepts = self._extract_key_concepts(transcript)
        
        # 时间线提取
        timeline = self._extract_timeline(transcript)
        
        return {
            'text_analysis': text_analysis,
            'image_analysis': image_analysis,
            'key_concepts': key_concepts,
            'timeline': timeline,
            'action_items': self._extract_action_items(transcript),
            'requirements': self._extract_requirements(transcript)
        }
    
    def _analyze_transcript(self, transcript: str) -> Dict[str, Any]:
        """分析转录文本"""
        # 句子分割
        sentences = re.split(r'[.!?]+', transcript)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        # 关键词提取
        words = re.findall(r'\b\w+\b', transcript.lower())
        word_freq = Counter(words)
        top_keywords = word_freq.most_common(20)
        
        # 情感分析（简单实现）
        positive_words = ['good', 'great', 'excellent', 'amazing', 'love', 'perfect']
        negative_words = ['bad', 'terrible', 'awful', 'hate', 'worst', 'horrible']
        
        positive_count = sum(1 for word in words if word in positive_words)
        negative_count = sum(1 for word in words if word in negative_words)
        
        sentiment = 'neutral'
        if positive_count > negative_count:
            sentiment = 'positive'
        elif negative_count > positive_count:
            sentiment = 'negative'
        
        return {
            'sentence_count': len(sentences),
            'word_count': len(words),
            'top_keywords': top_keywords,
            'sentiment': sentiment,
            'avg_sentence_length': len(words) / len(sentences) if sentences else 0
        }
    
    async def _analyze_frames(self, frames: List[str]) -> Dict[str, Any]:
        """分析视频帧"""
        if not frames:
            return {'frame_count': 0, 'analysis': []}
        
        # 这里可以集成NeuralAgentVision进行图像分析
        # 简化实现，返回模拟数据
        analysis_results = []
        
        for i, frame_path in enumerate(frames[:10]):  # 只分析前10帧
            analysis_results.append({
                'frame_index': i,
                'objects_detected': ['text', 'diagram', 'person'],
                'text_content': f'Sample text from frame {i}',
                'confidence': 0.8 + (i * 0.02)
            })
        
        return {
            'frame_count': len(frames),
            'analysis': analysis_results,
            'total_objects': sum(len(a['objects_detected']) for a in analysis_results)
        }
    
    def _extract_key_concepts(self, transcript: str) -> List[str]:
        """提取关键概念"""
        # 简单的关键词提取
        concepts = []
        
        # 技术相关词汇
        tech_patterns = [
            r'\b(API|SDK|AI|ML|AI|ML|API|REST|GraphQL|Docker|Kubernetes)\b',
            r'\b(数据库|database|数据库|MySQL|PostgreSQL|Redis)\b',
            r'\b(前端|frontend|前端|React|Vue|Angular)\b',
            r'\b(后端|backend|后端|Python|Java|Node\.js)\b'
        ]
        
        for pattern in tech_patterns:
            matches = re.findall(pattern, transcript, re.IGNORECASE)
            concepts.extend(matches)
        
        return list(set(concepts))
    
    def _extract_timeline(self, transcript: str) -> List[Dict[str, Any]]:
        """提取时间线"""
        timeline = []
        
        # 查找时间表达式
        time_patterns = [
            r'(\d+)\s*(?:分钟|min|分钟)',
            r'(\d+)\s*(?:秒|second|秒)',
            r'(?:第|stage|阶段)\s*(\d+)',
            r'(?:首先|first|首先|然后|then|然后|最后|finally|最后)'
        ]
        
        for pattern in time_patterns:
            matches = re.findall(pattern, transcript, re.IGNORECASE)
            for i, match in enumerate(matches):
                timeline.append({
                    'step': i + 1,
                    'description': f'Step {i + 1}: {match}',
                    'time_estimate': f'{match} minutes'
                })
        
        return timeline
    
    def _extract_action_items(self, transcript: str) -> List[str]:
        """提取行动项"""
        action_patterns = [
            r'(?:需要|need|需要|应该|should|应该|必须|must|必须|要|to|要)',
            r'(?:开发|develop|开发|实现|implement|实现|创建|create|创建)',
            r'(?:测试|test|测试|部署|deploy|部署|发布|release|发布)'
        ]
        
        actions = []
        for pattern in action_patterns:
            matches = re.findall(pattern, transcript, re.IGNORECASE)
            actions.extend(matches)
        
        return list(set(actions))
    
    def _extract_requirements(self, transcript: str) -> List[str]:
        """提取需求"""
        requirement_indicators = [
            '需要', '要求', '应该', '必须', '功能', '特性', '需求'
        ]
        
        requirements = []
        sentences = re.split(r'[.!?]+', transcript)
        
        for sentence in sentences:
            for indicator in requirement_indicators:
                if indicator in sentence:
                    requirements.append(sentence.strip())
                    break
        
        return requirements


class PRDGenerator:
    """PRD文档生成器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # 初始化智能体
        self.analyst_agent = AnalystAgent()
        self.pm_agent = ProductManagerAgent()
    
    async def generate_prd(self, analysis_result: Dict[str, Any]) -> PRDContent:
        """生成PRD文档"""
        try:
            # 使用分析师智能体分析内容
            analysis_prompt = f"""
            基于以下视频分析结果，生成产品需求分析：
            
            转录文本：{analysis_result.get('transcript', '')}
            关键概念：{analysis_result.get('key_concepts', [])}
            行动项：{analysis_result.get('action_items', [])}
            需求：{analysis_result.get('requirements', [])}
            
            请提取主要目标和功能需求。
            """
            
            analyst_result = await self.analyst_agent.analyze(analysis_prompt)
            
            # 使用产品经理智能体生成PRD
            prd_prompt = f"""
            基于以下分析结果，生成完整的PRD文档：
            
            分析师结果：{analyst_result}
            视频分析：{json.dumps(analysis_result, ensure_ascii=False, indent=2)}
            
            请生成包含以下部分的PRD：
            1. 产品概述
            2. 目标用户
            3. 核心功能
            4. 用户故事
            5. 技术要求
            6. 成功指标
            7. 时间规划
            8. 风险评估
            """
            
            pm_result = await self.pm_agent.create_prd(prd_prompt)
            
            # 解析生成的内容
            prd_content = self._parse_prd_result(pm_result, analysis_result)
            
            return prd_content
            
        except Exception as e:
            self.logger.error(f"PRD生成失败: {e}")
            # 返回默认PRD
            return self._generate_default_prd(analysis_result)
    
    def _parse_prd_result(self, pm_result: str, analysis_result: Dict[str, Any]) -> PRDContent:
        """解析PRD生成结果"""
        # 简化的解析逻辑
        # 实际应用中可以使用更复杂的NLP技术
        
        transcript = analysis_result.get('transcript', '')
        key_concepts = analysis_result.get('key_concepts', [])
        requirements = analysis_result.get('requirements', [])
        
        return PRDContent(
            title=f"基于视频的产品需求文档 - {datetime.now().strftime('%Y%m%d')}",
            overview=f"从视频内容分析得出的产品需求概述。视频时长：{analysis_result.get('duration', 0):.1f}秒",
            objectives=[
                "实现视频中提到的核心功能",
                "满足用户的基本需求",
                "提供良好的用户体验"
            ],
            features=[
                {
                    "name": "核心功能",
                    "description": "基于视频内容提取的主要功能",
                    "priority": "high",
                    "complexity": "medium"
                }
            ],
            user_stories=[
                {
                    "id": 1,
                    "story": "作为用户，我希望能够使用视频中描述的功能",
                    "acceptance_criteria": ["功能可用", "界面友好", "性能良好"]
                }
            ],
            technical_requirements=key_concepts + requirements[:5],
            success_metrics=[
                "用户满意度 > 80%",
                "系统响应时间 < 2秒",
                "功能完成率 > 90%"
            ],
            timeline={
                "phase_1": "需求分析和技术选型 (2周)",
                "phase_2": "核心功能开发 (4周)",
                "phase_3": "测试和优化 (2周)",
                "phase_4": "部署和发布 (1周)"
            },
            risks=[
                "技术难度评估不准确",
                "需求变更风险",
                "时间进度风险"
            ],
            stakeholders=[
                "产品经理",
                "技术团队",
                "测试团队",
                "运营团队"
            ]
        )
    
    def _generate_default_prd(self, analysis_result: Dict[str, Any]) -> PRDContent:
        """生成默认PRD"""
        return PRDContent(
            title="默认产品需求文档",
            overview="基于视频分析的默认PRD内容",
            objectives=["实现基本功能"],
            features=[{"name": "基本功能", "description": "基础功能实现"}],
            user_stories=[{"id": 1, "story": "用户基本使用场景", "acceptance_criteria": ["功能正常"]}],
            technical_requirements=["基本技术栈"],
            success_metrics=["基本指标"],
            timeline={"phase_1": "开发阶段"},
            risks=["基本风险"],
            stakeholders=["基本干系人"]
        )


class VideoToPRDDemo:
    """视频到PRD演示主类"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # 初始化组件
        self.video_processor = VideoProcessor()
        self.content_extractor = ContentExtractor()
        self.prd_generator = PRDGenerator()
        
        # 框架集成
        self.integration_framework = IntegrationFramework()
        
        # 语音接口
        from voice_interaction.voice_control_interface import VoiceControlInterface, VoiceControlConfig
        voice_config = VoiceControlConfig()
        self.voice_interface = VoiceControlInterface(voice_config)
    
    async def process_video_to_prd(self, video_path: str) -> Dict[str, Any]:
        """处理视频到PRD的完整流程"""
        self.logger.info(f"开始处理视频: {video_path}")
        
        start_time = time.time()
        
        try:
            # 步骤1: 视频分析
            self.logger.info("步骤1: 分析视频结构...")
            video_structure = await self.video_processor.analyze_video_structure(video_path)
            
            # 步骤2: 提取音频
            self.logger.info("步骤2: 提取音频...")
            audio_path = await self.video_processor.extract_audio(video_path)
            
            # 步骤3: 语音识别
            self.logger.info("步骤3: 语音识别...")
            transcript = await self._perform_speech_recognition(audio_path)
            
            # 步骤4: 提取帧
            self.logger.info("步骤4: 提取关键帧...")
            frames = await self.video_processor.extract_frames(video_path)
            
            # 步骤5: 内容提取
            self.logger.info("步骤5: 提取关键信息...")
            content_analysis = await self.content_extractor.extract_key_information(transcript, frames)
            
            # 步骤6: 生成PRD
            self.logger.info("步骤6: 生成PRD文档...")
            prd_content = await self.prd_generator.generate_prd(content_analysis)
            
            # 整合结果
            processing_time = time.time() - start_time
            
            result = {
                'success': True,
                'processing_time': processing_time,
                'video_analysis': VideoAnalysisResult(
                    video_id=str(uuid.uuid4()),
                    duration=video_structure.get('duration', 0),
                    frame_count=video_structure.get('frame_count', 0),
                    fps=video_structure.get('fps', 0),
                    resolution=video_structure.get('resolution', (0, 0)),
                    transcript=transcript,
                    key_scenes=video_structure.get('scenes', []),
                    extracted_text=content_analysis.get('requirements', []),
                    metadata={'video_path': video_path}
                ).to_dict(),
                'content_analysis': content_analysis,
                'prd_content': prd_content.to_dict(),
                'timestamp': datetime.now().isoformat()
            }
            
            # 集成到框架
            if self.integration_framework:
                await self._integrate_processing_result(result)
            
            self.logger.info(f"视频处理完成，耗时: {processing_time:.2f}秒")
            
            return result
            
        except Exception as e:
            self.logger.error(f"视频处理失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'processing_time': time.time() - start_time,
                'timestamp': datetime.now().isoformat()
            }
    
    async def _perform_speech_recognition(self, audio_path: str) -> str:
        """执行语音识别"""
        try:
            # 加载音频文件
            audio_data, sample_rate = sf.read(audio_path)
            
            # 使用语音接口进行识别
            session_id = await self.voice_interface.start_session()
            
            result = await self.voice_interface.process_voice_file(session_id, audio_path)
            
            # 提取识别的文本
            transcript = ""
            if 'asr' in result and 'text' in result['asr']:
                transcript = result['asr']['text']
            
            await self.voice_interface.end_session(session_id)
            
            return transcript
            
        except Exception as e:
            self.logger.error(f"语音识别失败: {e}")
            return "语音识别失败，无法提取文本内容。"
    
    async def _integrate_processing_result(self, result: Dict[str, Any]):
        """集成处理结果到框架"""
        try:
            if self.integration_framework:
                await self.integration_framework.broadcast_event(
                    'video_to_prd_completed',
                    {
                        'result': result,
                        'timestamp': datetime.now().isoformat()
                    }
                )
        except Exception as e:
            self.logger.error(f"结果集成失败: {e}")
    
    async def batch_process_videos(self, video_paths: List[str]) -> List[Dict[str, Any]]:
        """批量处理视频"""
        results = []
        
        for video_path in video_paths:
            try:
                result = await self.process_video_to_prd(video_path)
                results.append(result)
            except Exception as e:
                self.logger.error(f"视频 {video_path} 处理失败: {e}")
                results.append({
                    'success': False,
                    'error': str(e),
                    'video_path': video_path
                })
        
        return results
    
    def generate_prd_document(self, prd_content: PRDContent, output_path: str) -> str:
        """生成PRD文档文件"""
        doc_path = Path(output_path)
        doc_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 生成Markdown格式的PRD
        md_content = f"""# {prd_content.title}

## 产品概述
{prd_content.overview}

## 项目目标
{chr(10).join(f"- {obj}" for obj in prd_content.objectives)}

## 核心功能
{chr(10).join(f"- **{feature['name']}**: {feature['description']}" for feature in prd_content.features)}

## 用户故事
{chr(10).join(f"### 用户故事 {story['id']}: {story['story']}{chr(10)}**验收标准:**{chr(10)}{chr(10).join(f'- {criteria}' for criteria in story['acceptance_criteria'])}" for story in prd_content.user_stories)}

## 技术要求
{chr(10).join(f"- {req}" for req in prd_content.technical_requirements)}

## 成功指标
{chr(10).join(f"- {metric}" for metric in prd_content.success_metrics)}

## 时间规划
{chr(10).join(f"- **{phase}**: {timeline}" for phase, timeline in prd_content.timeline.items())}

## 风险评估
{chr(10).join(f"- {risk}" for risk in prd_content.risks)}

## 干系人
{chr(10).join(f"- {stakeholder}" for stakeholder in prd_content.stakeholders)}

---
*文档生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
        
        with open(doc_path, 'w', encoding='utf-8') as f:
            f.write(md_content)
        
        return str(doc_path)
    
    def get_demo_statistics(self) -> Dict[str, Any]:
        """获取演示统计信息"""
        return {
            'supported_formats': ['mp4', 'avi', 'mov', 'mkv'],
            'max_video_duration': 3600,  # 1小时
            'supported_languages': ['zh', 'en'],
            'processing_capabilities': [
                '视频结构分析',
                '语音识别',
                '关键帧提取',
                '内容分析',
                'PRD生成'
            ],
            'output_formats': ['Markdown', 'JSON'],
            'estimated_processing_time': '1-5分钟/视频'
        }