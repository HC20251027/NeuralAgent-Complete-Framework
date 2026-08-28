"""
模拟数据测试接口 - Mock Data Testing Interface
==============================================

提供完整的模拟数据生成和测试接口：
- 音频数据模拟
- 文本数据模拟
- 图像数据模拟
- 数据库模拟数据

Author: MiniMax Agent
Date: 2025-11-06
"""

import asyncio
import logging
import json
import random
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import tempfile
import csv
import uuid

# 音频处理
import librosa
import soundfile as sf
from pydub import AudioSegment

# 图像处理
try:
    from PIL import Image, ImageDraw, ImageFont
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

# 数据库模拟
import sqlite3

# 配置管理
from agno_bmad_integration.framework import IntegrationFramework


@dataclass
class MockDataConfig:
    """模拟数据配置类"""
    # 基础配置
    output_dir: str = "/workspace/mock_data"
    data_format: str = "json"  # json, csv, sqlite
    
    # 音频配置
    audio_sample_rate: int = 16000
    audio_duration_range: Tuple[float, float] = (1.0, 10.0)
    audio_channels: int = 1
    
    # 文本配置
    text_min_length: int = 10
    text_max_length: int = 1000
    languages: List[str] = field(default_factory=lambda: ['zh', 'en'])
    
    # 图像配置
    image_size_range: Tuple[int, int] = (64, 1024)
    image_formats: List[str] = field(default_factory=lambda: ['RGB'])
    
    # 数据库配置
    db_tables: List[str] = field(default_factory=lambda: ['users', 'agents', 'tasks'])
    records_per_table: int = 100
    
    # 数量配置
    audio_count: int = 50
    text_count: int = 100
    image_count: int = 30
    database_records: int = 1000
    
    # 随机种子
    random_seed: int = 42


@dataclass
class MockDataRecord:
    """模拟数据记录类"""
    record_id: str
    data_type: str  # audio, text, image, database
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)
    file_path: Optional[str] = None
    data: Any = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'record_id': self.record_id,
            'data_type': self.data_type,
            'timestamp': self.timestamp.isoformat(),
            'metadata': self.metadata,
            'file_path': self.file_path,
            'data': self.data
        }


class AudioMockDataGenerator:
    """音频模拟数据生成器"""
    
    def __init__(self, config: MockDataConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # 设置随机种子
        random.seed(config.random_seed)
        np.random.seed(config.random_seed)
    
    async def generate_audio_sample(self, duration: Optional[float] = None) -> Tuple[np.ndarray, str]:
        """生成音频样本"""
        if duration is None:
            duration = random.uniform(*self.config.audio_duration_range)
        
        # 生成不同类型的音频
        audio_type = random.choice(['sine', 'noise', 'speech_like', 'mixed'])
        
        if audio_type == 'sine':
            audio = self._generate_sine_wave(duration)
        elif audio_type == 'noise':
            audio = self._generate_noise(duration)
        elif audio_type == 'speech_like':
            audio = self._generate_speech_like(duration)
        else:  # mixed
            audio = self._generate_mixed_signal(duration)
        
        # 保存音频文件
        filename = f"audio_{uuid.uuid4().hex[:8]}.wav"
        file_path = Path(self.config.output_dir) / "audio" / filename
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        sf.write(str(file_path), audio, self.config.audio_sample_rate)
        
        return audio, str(file_path)
    
    async def generate_audio_batch(self, count: int) -> List[MockDataRecord]:
        """批量生成音频数据"""
        records = []
        
        for i in range(count):
            audio, file_path = await self.generate_audio_sample()
            
            record = MockDataRecord(
                record_id=str(uuid.uuid4()),
                data_type="audio",
                timestamp=datetime.now(),
                file_path=file_path,
                metadata={
                    'duration': len(audio) / self.config.audio_sample_rate,
                    'sample_rate': self.config.audio_sample_rate,
                    'channels': self.config.audio_channels,
                    'file_size': Path(file_path).stat().st_size
                }
            )
            
            records.append(record)
        
        return records
    
    def _generate_sine_wave(self, duration: float) -> np.ndarray:
        """生成正弦波"""
        t = np.linspace(0, duration, int(self.config.audio_sample_rate * duration))
        
        # 随机选择频率
        frequency = random.uniform(100, 1000)
        amplitude = random.uniform(0.1, 0.8)
        
        # 添加一些谐波
        audio = amplitude * np.sin(2 * np.pi * frequency * t)
        
        # 添加一些泛音
        for harmonic in range(2, 4):
            audio += (amplitude / harmonic) * np.sin(2 * np.pi * frequency * harmonic * t)
        
        return audio
    
    def _generate_noise(self, duration: float) -> np.ndarray:
        """生成噪声"""
        samples = int(self.config.audio_sample_rate * duration)
        
        # 生成白噪声
        noise = np.random.normal(0, 0.1, samples)
        
        # 添加低通滤波效果
        from scipy import signal
        b, a = signal.butter(3, 0.1, 'low')
        filtered_noise = signal.filtfilt(b, a, noise)
        
        return filtered_noise
    
    def _generate_speech_like(self, duration: float) -> np.ndarray:
        """生成类似语音的信号"""
        samples = int(self.config.audio_sample_rate * duration)
        t = np.linspace(0, duration, samples)
        
        # 基频变化
        base_freq = 120 + 50 * np.sin(2 * np.pi * 0.5 * t)
        
        # 生成语音信号
        audio = np.zeros(samples)
        
        # 添加共振峰
        for i, freq in enumerate(base_freq):
            # 主要频率成分
            audio[i] += 0.3 * np.sin(2 * np.pi * freq * t[i])
            
            # 谐波
            for harmonic in range(2, 6):
                audio[i] += 0.1 * np.sin(2 * np.pi * freq * harmonic * t[i]) / harmonic
        
        # 添加包络
        envelope = np.exp(-t / (duration * 0.8)) + 0.1 * np.random.random(samples)
        audio *= envelope
        
        # 添加噪声
        audio += 0.05 * np.random.normal(0, 1, samples)
        
        return audio
    
    def _generate_mixed_signal(self, duration: float) -> np.ndarray:
        """生成混合信号"""
        # 组合多种信号
        sine_audio = self._generate_sine_wave(duration)
        noise_audio = self._generate_noise(duration)
        speech_audio = self._generate_speech_like(duration)
        
        # 按权重混合
        weights = [0.4, 0.3, 0.3]
        mixed = (weights[0] * sine_audio + 
                weights[1] * noise_audio + 
                weights[2] * speech_audio)
        
        return mixed


class TextMockDataGenerator:
    """文本模拟数据生成器"""
    
    def __init__(self, config: MockDataConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # 设置随机种子
        random.seed(config.random_seed)
        
        # 预定义的文本模板
        self.text_templates = {
            'zh': [
                "今天天气很好，适合出去走走。",
                "人工智能技术发展很快，给我们的生活带来了很多便利。",
                "我们需要不断学习新知识来适应时代的变化。",
                "团队合作是非常重要的，每个人都有自己的优势。",
                "创新是推动社会进步的重要动力。"
            ],
            'en': [
                "The weather is nice today, perfect for a walk.",
                "Artificial intelligence technology is developing rapidly.",
                "We need to continuously learn new knowledge.",
                "Teamwork is very important in achieving goals.",
                "Innovation drives social progress."
            ]
        }
        
        # 关键词库
        self.keywords = {
            'zh': ['人工智能', '机器学习', '深度学习', '神经网络', '自然语言处理', '计算机视觉'],
            'en': ['AI', 'machine learning', 'deep learning', 'neural network', 'NLP', 'computer vision']
        }
    
    async def generate_text_sample(self, language: Optional[str] = None) -> str:
        """生成文本样本"""
        if language is None:
            language = random.choice(self.config.languages)
        
        # 选择模板
        if language in self.text_templates:
            base_text = random.choice(self.text_templates[language])
        else:
            base_text = "This is a sample text."
        
        # 添加随机扩展
        extensions = [
            f" This is additional content about {random.choice(self.keywords.get(language, ['']))}.",
            " The system is working properly.",
            " All components are functioning as expected.",
            " Performance metrics are within normal ranges."
        ]
        
        # 随机决定是否添加扩展
        if random.random() < 0.7:
            base_text += random.choice(extensions)
        
        # 控制长度
        if len(base_text) > self.config.text_max_length:
            base_text = base_text[:self.config.text_max_length]
        elif len(base_text) < self.config.text_min_length:
            # 如果太短，重复或添加内容
            base_text = base_text * 2
        
        return base_text
    
    async def generate_text_batch(self, count: int) -> List[MockDataRecord]:
        """批量生成文本数据"""
        records = []
        
        for i in range(count):
            text = await self.generate_text_sample()
            
            record = MockDataRecord(
                record_id=str(uuid.uuid4()),
                data_type="text",
                timestamp=datetime.now(),
                data=text,
                metadata={
                    'length': len(text),
                    'language': random.choice(self.config.languages),
                    'word_count': len(text.split()),
                    'character_count': len(text)
                }
            )
            
            records.append(record)
        
        return records


class ImageMockDataGenerator:
    """图像模拟数据生成器"""
    
    def __init__(self, config: MockDataConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        if not PIL_AVAILABLE:
            self.logger.warning("PIL不可用，图像生成功能受限")
        
        # 设置随机种子
        random.seed(config.random_seed)
    
    async def generate_image_sample(self, size: Optional[Tuple[int, int]] = None) -> Tuple[Image.Image, str]:
        """生成图像样本"""
        if not PIL_AVAILABLE:
            raise ImportError("PIL库不可用，无法生成图像")
        
        if size is None:
            width = random.randint(*self.config.image_size_range)
            height = random.randint(*self.config.image_size_range)
            size = (width, height)
        
        # 创建图像
        image = Image.new(random.choice(self.config.image_formats), size)
        draw = ImageDraw.Draw(image)
        
        # 生成不同类型的图像
        image_type = random.choice(['geometric', 'gradient', 'pattern', 'noise'])
        
        if image_type == 'geometric':
            self._draw_geometric_shapes(draw, size)
        elif image_type == 'gradient':
            self._draw_gradient(image, size)
        elif image_type == 'pattern':
            self._draw_pattern(draw, size)
        else:  # noise
            self._draw_noise(image, size)
        
        # 保存图像文件
        filename = f"image_{uuid.uuid4().hex[:8]}.png"
        file_path = Path(self.config.output_dir) / "image" / filename
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        image.save(file_path)
        
        return image, str(file_path)
    
    async def generate_image_batch(self, count: int) -> List[MockDataRecord]:
        """批量生成图像数据"""
        records = []
        
        for i in range(count):
            image, file_path = await self.generate_image_sample()
            
            record = MockDataRecord(
                record_id=str.uuid4(),
                data_type="image",
                timestamp=datetime.now(),
                file_path=file_path,
                metadata={
                    'width': image.width,
                    'height': image.height,
                    'mode': image.mode,
                    'format': 'PNG',
                    'file_size': Path(file_path).stat().st_size
                }
            )
            
            records.append(record)
        
        return records
    
    def _draw_geometric_shapes(self, draw: ImageDraw.Draw, size: Tuple[int, int]):
        """绘制几何图形"""
        width, height = size
        
        # 绘制随机几何图形
        for _ in range(random.randint(3, 8)):
            shape_type = random.choice(['rectangle', 'ellipse', 'line'])
            color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
            
            if shape_type == 'rectangle':
                x1 = random.randint(0, width // 2)
                y1 = random.randint(0, height // 2)
                x2 = random.randint(x1, width)
                y2 = random.randint(y1, height)
                draw.rectangle([x1, y1, x2, y2], fill=color)
            
            elif shape_type == 'ellipse':
                x1 = random.randint(0, width)
                y1 = random.randint(0, height)
                x2 = random.randint(x1, width)
                y2 = random.randint(y1, height)
                draw.ellipse([x1, y1, x2, y2], fill=color)
            
            elif shape_type == 'line':
                x1 = random.randint(0, width)
                y1 = random.randint(0, height)
                x2 = random.randint(0, width)
                y2 = random.randint(0, height)
                draw.line([x1, y1, x2, y2], fill=color, width=random.randint(1, 5))
    
    def _draw_gradient(self, image: Image.Image, size: Tuple[int, int]):
        """绘制渐变"""
        width, height = size
        
        for y in range(height):
            # 创建水平渐变
            color_value = int(255 * (y / height))
            color = (color_value, color_value // 2, 255 - color_value)
            
            for x in range(width):
                image.putpixel((x, y), color)
    
    def _draw_pattern(self, draw: ImageDraw.Draw, size: Tuple[int, int]):
        """绘制图案"""
        width, height = size
        
        # 绘制棋盘格图案
        square_size = random.randint(10, 50)
        
        for y in range(0, height, square_size):
            for x in range(0, width, square_size):
                if (x // square_size + y // square_size) % 2 == 0:
                    color = (255, 255, 255)
                else:
                    color = (0, 0, 0)
                
                draw.rectangle([x, y, x + square_size, y + square_size], fill=color)
    
    def _draw_noise(self, image: Image.Image, size: Tuple[int, int]):
        """绘制噪声"""
        width, height = size
        
        for y in range(height):
            for x in range(width):
                # 生成随机噪声像素
                noise_value = random.randint(0, 255)
                color = (noise_value, noise_value, noise_value)
                image.putpixel((x, y), color)


class DatabaseMockDataGenerator:
    """数据库模拟数据生成器"""
    
    def __init__(self, config: MockDataConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # 设置随机种子
        random.seed(config.random_seed)
        
        # 表结构定义
        self.table_schemas = {
            'users': {
                'columns': ['id', 'username', 'email', 'created_at', 'status', 'role'],
                'types': ['INTEGER', 'TEXT', 'TEXT', 'TEXT', 'TEXT', 'TEXT']
            },
            'agents': {
                'columns': ['id', 'name', 'type', 'status', 'created_at', 'config'],
                'types': ['INTEGER', 'TEXT', 'TEXT', 'TEXT', 'TEXT', 'TEXT']
            },
            'tasks': {
                'columns': ['id', 'title', 'description', 'status', 'priority', 'assigned_to', 'created_at'],
                'types': ['INTEGER', 'TEXT', 'TEXT', 'TEXT', 'TEXT', 'INTEGER', 'TEXT']
            },
            'sessions': {
                'columns': ['id', 'user_id', 'start_time', 'end_time', 'duration', 'status'],
                'types': ['INTEGER', 'INTEGER', 'TEXT', 'TEXT', 'REAL', 'TEXT']
            },
            'logs': {
                'columns': ['id', 'level', 'message', 'timestamp', 'component'],
                'types': ['INTEGER', 'TEXT', 'TEXT', 'TEXT', 'TEXT']
            }
        }
    
    async def generate_database_data(self) -> str:
        """生成数据库数据"""
        # 创建SQLite数据库
        db_path = Path(self.config.output_dir) / "mock_data.db"
        db_path.parent.mkdir(parents=True, exist_ok=True)
        
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        try:
            # 创建表
            for table_name, schema in self.table_schemas.items():
                columns_def = ', '.join([f"{col} {typ}" for col, typ in zip(schema['columns'], schema['types'])])
                cursor.execute(f"CREATE TABLE IF NOT EXISTS {table_name} ({columns_def})")
            
            # 插入模拟数据
            for table_name, schema in self.table_schemas.items():
                records_count = self.config.records_per_table
                await self._insert_mock_data(cursor, table_name, schema, records_count)
            
            conn.commit()
            
            self.logger.info(f"数据库模拟数据生成完成: {db_path}")
            return str(db_path)
        
        except Exception as e:
            self.logger.error(f"数据库数据生成失败: {e}")
            raise
        finally:
            conn.close()
    
    async def _insert_mock_data(self, cursor, table_name: str, schema: Dict, count: int):
        """插入模拟数据"""
        for i in range(count):
            record = self._generate_record_data(table_name, schema)
            
            placeholders = ', '.join(['?' for _ in schema['columns']])
            columns = ', '.join(schema['columns'])
            
            cursor.execute(
                f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})",
                record
            )
    
    def _generate_record_data(self, table_name: str, schema: Dict) -> List[Any]:
        """生成单条记录数据"""
        data = []
        
        for col, typ in zip(schema['columns'], schema['types']):
            if col == 'id':
                data.append(None)  # 自增ID
            elif 'email' in col:
                data.append(f"user_{random.randint(1000, 9999)}@example.com")
            elif 'username' in col:
                data.append(f"user_{random.randint(1000, 9999)}")
            elif 'name' in col:
                data.append(f"Agent_{random.randint(1, 100)}")
            elif 'type' in col:
                data.append(random.choice(['analyst', 'pm', 'architect', 'developer', 'qa']))
            elif 'status' in col:
                data.append(random.choice(['active', 'inactive', 'pending', 'completed']))
            elif 'role' in col:
                data.append(random.choice(['admin', 'user', 'guest']))
            elif 'priority' in col:
                data.append(random.choice(['high', 'medium', 'low']))
            elif 'level' in col:
                data.append(random.choice(['INFO', 'WARNING', 'ERROR', 'DEBUG']))
            elif 'title' in col:
                data.append(f"Task {random.randint(1, 1000)}")
            elif 'description' in col:
                data.append(f"Description for task {random.randint(1, 1000)}")
            elif 'config' in col:
                config_data = {
                    'param1': random.randint(1, 100),
                    'param2': random.choice(['option1', 'option2', 'option3']),
                    'enabled': random.choice([True, False])
                }
                data.append(json.dumps(config_data))
            elif 'created_at' in col or 'start_time' in col or 'end_time' in col or 'timestamp' in col:
                # 生成时间戳
                base_time = datetime.now() - timedelta(days=random.randint(0, 30))
                data.append(base_time.isoformat())
            elif 'duration' in col:
                data.append(random.uniform(1.0, 3600.0))  # 1秒到1小时
            elif 'message' in col:
                data.append(f"Log message {random.randint(1, 1000)}")
            elif 'component' in col:
                data.append(random.choice(['agno', 'bmad', 'vision', 'voice', 'gateway']))
            elif 'assigned_to' in col:
                data.append(random.randint(1, 50))  # 用户ID
            elif typ == 'INTEGER':
                data.append(random.randint(1, 1000))
            elif typ == 'REAL':
                data.append(random.uniform(0.0, 100.0))
            else:  # TEXT
                data.append(f"Value_{random.randint(1, 100)}")
        
        return data


class MockDataInterface:
    """模拟数据接口主类"""
    
    def __init__(self, config: Optional[MockDataConfig] = None):
        self.config = config or self._create_default_config()
        self.logger = logging.getLogger(__name__)
        
        # 初始化生成器
        self.audio_generator = AudioMockDataGenerator(self.config)
        self.text_generator = TextMockDataGenerator(self.config)
        self.image_generator = ImageMockDataGenerator(self.config)
        self.database_generator = DatabaseMockDataGenerator(self.config)
        
        # 生成的记录
        self.generated_records: List[MockDataRecord] = []
        
        # 创建输出目录
        Path(self.config.output_dir).mkdir(parents=True, exist_ok=True)
        
        # 集成框架
        self.integration_framework = IntegrationFramework()
    
    def _create_default_config(self) -> MockDataConfig:
        """创建默认配置"""
        return MockDataConfig(
            output_dir="/workspace/mock_data",
            audio_count=50,
            text_count=100,
            image_count=30,
            records_per_table=100,
            random_seed=42
        )
    
    async def generate_all_mock_data(self) -> Dict[str, Any]:
        """生成所有模拟数据"""
        self.logger.info("开始生成模拟数据...")
        
        generation_results = {
            'start_time': datetime.now().isoformat(),
            'audio': {'count': 0, 'records': []},
            'text': {'count': 0, 'records': []},
            'image': {'count': 0, 'records': []},
            'database': {'file_path': None},
            'errors': []
        }
        
        try:
            # 生成音频数据
            try:
                audio_records = await self.audio_generator.generate_audio_batch(self.config.audio_count)
                generation_results['audio']['count'] = len(audio_records)
                generation_results['audio']['records'] = [r.to_dict() for r in audio_records]
                self.generated_records.extend(audio_records)
                self.logger.info(f"生成音频数据: {len(audio_records)}条")
            except Exception as e:
                error_msg = f"音频数据生成失败: {e}"
                self.logger.error(error_msg)
                generation_results['errors'].append(error_msg)
            
            # 生成文本数据
            try:
                text_records = await self.text_generator.generate_text_batch(self.config.text_count)
                generation_results['text']['count'] = len(text_records)
                generation_results['text']['records'] = [r.to_dict() for r in text_records]
                self.generated_records.extend(text_records)
                self.logger.info(f"生成文本数据: {len(text_records)}条")
            except Exception as e:
                error_msg = f"文本数据生成失败: {e}"
                self.logger.error(error_msg)
                generation_results['errors'].append(error_msg)
            
            # 生成图像数据
            try:
                image_records = await self.image_generator.generate_image_batch(self.config.image_count)
                generation_results['image']['count'] = len(image_records)
                generation_results['image']['records'] = [r.to_dict() for r in image_records]
                self.generated_records.extend(image_records)
                self.logger.info(f"生成图像数据: {len(image_records)}条")
            except Exception as e:
                error_msg = f"图像数据生成失败: {e}"
                self.logger.error(error_msg)
                generation_results['errors'].append(error_msg)
            
            # 生成数据库数据
            try:
                db_path = await self.database_generator.generate_database_data()
                generation_results['database']['file_path'] = db_path
                self.logger.info(f"生成数据库数据: {db_path}")
            except Exception as e:
                error_msg = f"数据库数据生成失败: {e}"
                self.logger.error(error_msg)
                generation_results['errors'].append(error_msg)
            
            generation_results['end_time'] = datetime.now().isoformat()
            generation_results['total_records'] = len(self.generated_records)
            
            # 保存生成记录
            await self._save_generation_log(generation_results)
            
            # 集成到框架
            if self.integration_framework:
                await self._integrate_mock_data(generation_results)
            
            self.logger.info("模拟数据生成完成")
            
            return generation_results
        
        except Exception as e:
            self.logger.error(f"模拟数据生成异常: {e}")
            generation_results['errors'].append(str(e))
            return generation_results
    
    async def generate_audio_data(self, count: int) -> List[MockDataRecord]:
        """生成音频数据"""
        records = await self.audio_generator.generate_audio_batch(count)
        self.generated_records.extend(records)
        return records
    
    async def generate_text_data(self, count: int) -> List[MockDataRecord]:
        """生成文本数据"""
        records = await self.text_generator.generate_text_batch(count)
        self.generated_records.extend(records)
        return records
    
    async def generate_image_data(self, count: int) -> List[MockDataRecord]:
        """生成图像数据"""
        records = await self.image_generator.generate_image_batch(count)
        self.generated_records.extend(records)
        return records
    
    async def generate_database_data(self) -> str:
        """生成数据库数据"""
        db_path = await self.database_generator.generate_database_data()
        return db_path
    
    async def _save_generation_log(self, results: Dict[str, Any]):
        """保存生成日志"""
        log_path = Path(self.config.output_dir) / "generation_log.json"
        
        with open(log_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
    
    async def _integrate_mock_data(self, results: Dict[str, Any]):
        """集成模拟数据到框架"""
        try:
            if self.integration_framework:
                await self.integration_framework.broadcast_event(
                    'mock_data_generated',
                    {
                        'results': results,
                        'total_records': len(self.generated_records),
                        'timestamp': datetime.now().isoformat()
                    }
                )
        except Exception as e:
            self.logger.error(f"模拟数据集成失败: {e}")
    
    def get_generated_records(self) -> List[MockDataRecord]:
        """获取已生成的记录"""
        return self.generated_records.copy()
    
    def export_records_to_csv(self, output_path: str) -> str:
        """导出记录到CSV文件"""
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # 写入头部
            writer.writerow(['record_id', 'data_type', 'timestamp', 'file_path', 'metadata'])
            
            # 写入数据
            for record in self.generated_records:
                writer.writerow([
                    record.record_id,
                    record.data_type,
                    record.timestamp.isoformat(),
                    record.file_path or '',
                    json.dumps(record.metadata, ensure_ascii=False)
                ])
        
        return str(output_file)
    
    def get_data_summary(self) -> Dict[str, Any]:
        """获取数据摘要"""
        summary = {
            'total_records': len(self.generated_records),
            'by_type': {},
            'file_sizes': {},
            'time_range': {}
        }
        
        if self.generated_records:
            # 按类型统计
            type_counts = {}
            for record in self.generated_records:
                type_counts[record.data_type] = type_counts.get(record.data_type, 0) + 1
            summary['by_type'] = type_counts
            
            # 时间范围
            timestamps = [record.timestamp for record in self.generated_records]
            summary['time_range'] = {
                'earliest': min(timestamps).isoformat(),
                'latest': max(timestamps).isoformat()
            }
            
            # 文件大小统计
            file_sizes = {}
            for record in self.generated_records:
                if record.file_path and Path(record.file_path).exists():
                    size = Path(record.file_path).stat().st_size
                    file_sizes[record.record_id] = size
            summary['file_sizes'] = file_sizes
        
        return summary
    
    def cleanup_generated_data(self):
        """清理生成的数据"""
        try:
            # 删除生成的文件
            for record in self.generated_records:
                if record.file_path and Path(record.file_path).exists():
                    Path(record.file_path).unlink()
            
            # 清空记录列表
            self.generated_records.clear()
            
            self.logger.info("已清理生成的模拟数据")
        
        except Exception as e:
            self.logger.error(f"清理模拟数据失败: {e}")