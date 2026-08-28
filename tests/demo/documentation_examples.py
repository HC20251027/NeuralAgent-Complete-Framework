"""
框架使用文档和示例 - Framework Documentation and Examples
========================================================

提供完整的框架使用文档和示例：
1. 快速开始指南
2. API参考文档
3. 配置说明
4. 最佳实践
5. 故障排除

Author: MiniMax Agent
Date: 2025-11-06
"""

import asyncio
import logging
import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from datetime import datetime

# 框架组件导入
from agno_bmad_integration.framework import IntegrationFramework
from bmad.roles.analyst import AnalystAgent
from bmad.roles.pm import ProductManagerAgent
from neural_agent_vision.neural_agent_vision import NeuralAgentVision
from voice_interaction.voice_control_interface import VoiceControlInterface


@dataclass
class DocumentationSection:
    """文档章节"""
    section_id: str
    title: str
    content: str
    examples: List[Dict[str, Any]] = field(default_factory=list)
    code_samples: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'section_id': self.section_id,
            'title': self.title,
            'content': self.content,
            'examples': self.examples,
            'code_samples': self.code_samples
        }


class QuickStartGuide:
    """快速开始指南"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def get_quick_start_content(self) -> Dict[str, Any]:
        """获取快速开始内容"""
        return {
            'title': 'NeuralAgent × Agno-BMAD-LM Studio 快速开始指南',
            'description': '5分钟快速上手全功能本地化AI智能体大整合方案',
            'prerequisites': [
                'Python 3.8+',
                '4GB+ RAM',
                '2GB+ 磁盘空间',
                '可选：GPU支持（用于AI模型加速）'
            ],
            'installation_steps': [
                {
                    'step': 1,
                    'title': '环境准备',
                    'command': 'python -m venv venv && source venv/bin/activate  # Linux/Mac',
                    'description': '创建并激活Python虚拟环境'
                },
                {
                    'step': 2,
                    'title': '安装依赖',
                    'command': 'pip install -r requirements.txt',
                    'description': '安装所有必需的Python包'
                },
                {
                    'step': 3,
                    'title': '配置环境',
                    'command': 'cp config/config_template.yaml config/config.yaml',
                    'description': '复制并修改配置文件'
                },
                {
                    'step': 4,
                    'title': '启动系统',
                    'command': 'python scripts/start_system.py',
                    'description': '启动完整的系统服务'
                }
            ],
            'first_example': {
                'title': '第一个示例：视频分析',
                'description': '上传一个产品演示视频，自动生成PRD文档',
                'code': '''
# 导入必要的模块
from workflow_demonstration.video_to_prd_demo import VideoToPRDDemo

# 创建演示实例
demo = VideoToPRDDemo()

# 处理视频
result = await demo.process_video_to_prd("demo_video.mp4")

# 检查结果
if result['success']:
    print(f"处理成功！耗时: {result['processing_time']:.2f}秒")
    print(f"生成的PRD标题: {result['prd_content']['title']}")
else:
    print(f"处理失败: {result['error']}")
                ''',
                'expected_output': '''
处理成功！耗时: 45.67秒
生成的PRD标题: 基于视频的产品需求文档 - 20251106
                '''
            },
            'next_steps': [
                '学习协作模式演示',
                '体验语音交互功能',
                '探索视觉处理能力',
                '自定义配置和扩展'
            ]
        }


class APIReference:
    """API参考文档"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def get_api_reference(self) -> Dict[str, Any]:
        """获取API参考文档"""
        return {
            'title': 'API参考文档',
            'description': 'NeuralAgent × Agno-BMAD 框架完整API参考',
            'modules': {
                'integration_framework': {
                    'description': '核心集成框架',
                    'class': 'IntegrationFramework',
                    'methods': {
                        'broadcast_event': {
                            'signature': 'async def broadcast_event(self, event_type: str, data: Dict[str, Any]) -> bool',
                            'description': '广播事件到所有注册的组件',
                            'parameters': [
                                {'name': 'event_type', 'type': 'str', 'description': '事件类型'},
                                {'name': 'data', 'type': 'Dict[str, Any]', 'description': '事件数据'}
                            ],
                            'returns': 'bool - 广播是否成功',
                            'example': '''
framework = IntegrationFramework()
success = await framework.broadcast_event('task_completed', {
    'task_id': 'task_001',
    'result': '分析完成'
})
                            '''
                        },
                        'register_component': {
                            'signature': 'def register_component(self, component_id: str, component: Any) -> bool',
                            'description': '注册组件到框架',
                            'parameters': [
                                {'name': 'component_id', 'type': 'str', 'description': '组件ID'},
                                {'name': 'component', 'type': 'Any', 'description': '组件实例'}
                            ],
                            'returns': 'bool - 注册是否成功'
                        }
                    }
                },
                'bmad_roles': {
                    'description': 'BMAD角色智能体',
                    'agents': {
                        'AnalystAgent': {
                            'description': '分析师智能体，负责需求分析',
                            'methods': {
                                'analyze': {
                                    'signature': 'async def analyze(self, prompt: str) -> str',
                                    'description': '执行需求分析',
                                    'parameters': [
                                        {'name': 'prompt', 'type': 'str', 'description': '分析提示'}
                                    ],
                                    'returns': 'str - 分析结果'
                                }
                            }
                        },
                        'ProductManagerAgent': {
                            'description': '产品经理智能体，负责产品设计',
                            'methods': {
                                'create_prd': {
                                    'signature': 'async def create_prd(self, requirements: str) -> str',
                                    'description': '创建产品需求文档',
                                    'parameters': [
                                        {'name': 'requirements', 'type': 'str', 'description': '需求描述'}
                                    ],
                                    'returns': 'str - PRD内容'
                                }
                            }
                        }
                    }
                },
                'neural_agent_vision': {
                    'description': 'NeuralAgent视觉处理模块',
                    'class': 'NeuralAgentVision',
                    'methods': {
                        'process_image_route1': {
                            'signature': 'async def process_image_route1(self, image_path: str) -> Dict[str, Any]',
                            'description': '使用路线1处理图像（Grounding DINO + EasyOCR）',
                            'parameters': [
                                {'name': 'image_path', 'type': 'str', 'description': '图像文件路径'}
                            ],
                            'returns': 'Dict[str, Any] - 处理结果'
                        },
                        'detect_ui_elements': {
                            'signature': 'async def detect_ui_elements(self, image_path: str) -> List[Dict[str, Any]]',
                            'description': '检测UI元素',
                            'parameters': [
                                {'name': 'image_path', 'type': 'str', 'description': '图像文件路径'}
                            ],
                            'returns': 'List[Dict[str, Any]] - 检测到的UI元素列表'
                        }
                    }
                },
                'voice_interaction': {
                    'description': '语音交互系统',
                    'class': 'VoiceControlInterface',
                    'methods': {
                        'start_session': {
                            'signature': 'async def start_session(self, speaker_id: Optional[str] = None) -> str',
                            'description': '开始语音会话',
                            'parameters': [
                                {'name': 'speaker_id', 'type': 'Optional[str]', 'description': '说话人ID（可选）'}
                            ],
                            'returns': 'str - 会话ID'
                        },
                        'process_voice_input': {
                            'signature': 'async def process_voice_input(self, session_id: str, audio_data: np.ndarray) -> Dict[str, Any]',
                            'description': '处理语音输入',
                            'parameters': [
                                {'name': 'session_id', 'type': 'str', 'description': '会话ID'},
                                {'name': 'audio_data', 'type': 'np.ndarray', 'description': '音频数据'}
                            ],
                            'returns': 'Dict[str, Any] - 处理结果'
                        }
                    }
                }
            },
            'common_patterns': {
                'async_initialization': {
                    'description': '异步初始化模式',
                    'code': '''
# 正确的方式
framework = IntegrationFramework()
await framework.initialize()

# 错误的方式
framework = IntegrationFramework()
framework.initialize()  # 这会返回协程对象
                    '''
                },
                'error_handling': {
                    'description': '错误处理模式',
                    'code': '''
try:
    result = await demo.process_video_to_prd("video.mp4")
    if result['success']:
        print("处理成功")
    else:
        print(f"处理失败: {result['error']}")
except Exception as e:
    print(f"异常: {e}")
                    '''
                },
                'configuration': {
                    'description': '配置管理模式',
                    'code': '''
from dataclasses import dataclass

@dataclass
class MyConfig:
    video_path: str = "demo.mp4"
    output_dir: str = "./output"
    enable_cache: bool = True

config = MyConfig()
demo = VideoToPRDDemo()
                    '''
                }
            }
        }


class ConfigurationGuide:
    """配置说明"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def get_configuration_guide(self) -> Dict[str, Any]:
        """获取配置指南"""
        return {
            'title': '配置说明',
            'description': 'NeuralAgent × Agno-BMAD 框架配置详解',
            'config_files': {
                'config.yaml': {
                    'description': '主配置文件',
                    'location': 'config/config.yaml',
                    'structure': {
                        'database': {
                            'host': 'localhost',
                            'port': 5432,
                            'name': 'neural_agent_db',
                            'user': 'postgres',
                            'password': 'your_password',
                            'pool_size': 10
                        },
                        'redis': {
                            'host': 'localhost',
                            'port': 6379,
                            'db': 0,
                            'password': None
                        },
                        'apisix': {
                            'gateway_url': 'http://localhost:9080',
                            'admin_key': 'your_admin_key'
                        },
                        'voice': {
                            'asr_engine': 'whisper',
                            'tts_engine': 'gtts',
                            'sample_rate': 16000
                        },
                        'vision': {
                            'model_route': 'route1',
                            'confidence_threshold': 0.5
                        },
                        'logging': {
                            'level': 'INFO',
                            'file': 'logs/system.log',
                            'max_size': '100MB',
                            'backup_count': 5
                        }
                    }
                },
                'environment.env': {
                    'description': '环境变量配置',
                    'location': 'config/environment.env',
                    'variables': {
                        'DATABASE_URL': 'postgresql://user:pass@localhost:5432/db',
                        'REDIS_URL': 'redis://localhost:6379',
                        'OPENAI_API_KEY': 'your_openai_key',
                        'MODEL_CACHE_DIR': '/tmp/models',
                        'LOG_LEVEL': 'INFO'
                    }
                }
            },
            'configuration_sections': {
                'database': {
                    'description': '数据库配置',
                    'options': {
                        'host': '数据库主机地址',
                        'port': '数据库端口',
                        'name': '数据库名称',
                        'user': '数据库用户',
                        'password': '数据库密码',
                        'pool_size': '连接池大小',
                        'timeout': '连接超时时间'
                    }
                },
                'redis': {
                    'description': 'Redis缓存配置',
                    'options': {
                        'host': 'Redis主机地址',
                        'port': 'Redis端口',
                        'db': 'Redis数据库编号',
                        'password': 'Redis密码',
                        'timeout': '连接超时时间'
                    }
                },
                'voice': {
                    'description': '语音系统配置',
                    'options': {
                        'asr_engine': 'ASR引擎 (whisper, speech_recognition)',
                        'tts_engine': 'TTS引擎 (gtts, edge_tts, azure)',
                        'sample_rate': '音频采样率',
                        'language': '默认语言',
                        'enable_voiceprint': '是否启用声纹识别',
                        'enable_emotion': '是否启用情感分析'
                    }
                },
                'vision': {
                    'description': '视觉系统配置',
                    'options': {
                        'model_route': '视觉处理路线 (route1, route2, route3)',
                        'confidence_threshold': '置信度阈值',
                        'enable_ui_detection': '是否启用UI检测',
                        'enable_color_analysis': '是否启用颜色分析'
                    }
                }
            },
            'environment_specific': {
                'development': {
                    'description': '开发环境配置',
                    'settings': {
                        'log_level': 'DEBUG',
                        'enable_debug': True,
                        'cache_enabled': False,
                        'model_device': 'cpu'
                    }
                },
                'production': {
                    'description': '生产环境配置',
                    'settings': {
                        'log_level': 'INFO',
                        'enable_debug': False,
                        'cache_enabled': True,
                        'model_device': 'cuda'
                    }
                },
                'testing': {
                    'description': '测试环境配置',
                    'settings': {
                        'log_level': 'WARNING',
                        'enable_debug': False,
                        'cache_enabled': False,
                        'mock_services': True
                    }
                }
            }
        }


class BestPractices:
    """最佳实践"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def get_best_practices(self) -> Dict[str, Any]:
        """获取最佳实践"""
        return {
            'title': '最佳实践指南',
            'description': 'NeuralAgent × Agno-BMAD 框架使用最佳实践',
            'categories': {
                'performance': {
                    'title': '性能优化',
                    'practices': [
                        {
                            'title': '使用连接池',
                            'description': '数据库和Redis连接使用连接池',
                            'code': '''
# 正确：使用连接池
from database.connection import get_connection_pool
pool = get_connection_pool()
async with pool.acquire() as conn:
    await conn.execute("SELECT * FROM users")

# 错误：频繁创建连接
async with connect("postgresql://...") as conn:
    await conn.execute("SELECT * FROM users")
                            '''
                        },
                        {
                            'title': '启用缓存',
                            'description': '对频繁访问的数据启用缓存',
                            'code': '''
from agno.memory.working import WorkingMemory

# 启用缓存
memory = WorkingMemory(cache_enabled=True)

# 缓存会自动管理
result = await memory.get("user_profile_123")
                            '''
                        },
                        {
                            'title': '异步编程',
                            'description': '充分利用异步编程提高并发性能',
                            'code': '''
# 正确：异步处理
async def process_multiple_videos(video_paths):
    tasks = [process_video(path) for path in video_paths]
    results = await asyncio.gather(*tasks)
    return results

# 错误：同步处理
def process_multiple_videos(video_paths):
    results = []
    for path in video_paths:
        results.append(process_video(path))  # 阻塞执行
    return results
                            '''
                        }
                    ]
                },
                'reliability': {
                    'title': '可靠性保证',
                    'practices': [
                        {
                            'title': '错误处理',
                            'description': '完善的错误处理和重试机制',
                            'code': '''
import asyncio
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential())
async def robust_api_call():
    try:
        result = await api_client.call()
        return result
    except Exception as e:
        logger.error(f"API调用失败: {e}")
        raise
                            '''
                        },
                        {
                            'title': '健康检查',
                            'description': '定期执行健康检查',
                            'code': '''
from system_integration_testing.health_monitoring import SystemHealthMonitor

monitor = SystemHealthMonitor()
await monitor.start_monitoring()

# 定期检查
while True:
    status = await monitor.perform_health_check()
    if status['overall_status'] == 'critical':
        await send_alert(status)
    await asyncio.sleep(60)  # 每分钟检查一次
                            '''
                        }
                    ]
                },
                'scalability': {
                    'title': '可扩展性',
                    'practices': [
                        {
                            'title': '模块化设计',
                            'description': '保持组件独立和可替换',
                            'code': '''
# 好的设计：接口抽象
from abc import ABC, abstractmethod

class ASREngine(ABC):
    @abstractmethod
    async def transcribe(self, audio: bytes) -> str:
        pass

# 可以轻松替换不同的ASR实现
class WhisperEngine(ASREngine):
    async def transcribe(self, audio: bytes) -> str:
        # Whisper实现
        pass

class GoogleASREngine(ASREngine):
    async def transcribe(self, audio: bytes) -> str:
        # Google ASR实现
        pass
                            '''
                        },
                        {
                            'title': '配置外部化',
                            'description': '将配置从代码中分离出来',
                            'code': '''
# 使用配置文件
from dataclasses import dataclass
import yaml

@dataclass
class AppConfig:
    database_url: str
    redis_url: str
    model_path: str

def load_config(config_path: str) -> AppConfig:
    with open(config_path) as f:
        config_data = yaml.safe_load(f)
    return AppConfig(**config_data)

config = load_config("config.yaml")
                            '''
                        }
                    ]
                },
                'security': {
                    'title': '安全实践',
                    'practices': [
                        {
                            'title': '敏感信息保护',
                            'description': '不将敏感信息硬编码在代码中',
                            'code': '''
# 错误：硬编码密码
DATABASE_URL = "postgresql://user:password123@localhost/db"

# 正确：使用环境变量
import os
DATABASE_URL = os.getenv("DATABASE_URL")

# 或使用密钥管理
from keyring import get_password
password = get_password("service", "database")
                            '''
                        },
                        {
                            'title': '输入验证',
                            'description': '验证所有外部输入',
                            'code': '''
from pydantic import BaseModel, validator

class VideoProcessRequest(BaseModel):
    video_path: str
    output_format: str
    
    @validator('video_path')
    def validate_path(cls, v):
        if not Path(v).exists():
            raise ValueError("视频文件不存在")
        return v
    
    @validator('output_format')
    def validate_format(cls, v):
        allowed_formats = ['json', 'markdown', 'pdf']
        if v not in allowed_formats:
            raise ValueError(f"不支持的格式: {v}")
        return v
                            '''
                        }
                    ]
                }
            },
            'architecture_patterns': {
                'microservices': {
                    'description': '微服务架构模式',
                    'benefits': ['独立部署', '技术栈灵活', '故障隔离'],
                    'implementation': '''
# 服务注册
framework.register_component('video_service', VideoService())
framework.register_component('voice_service', VoiceService())
framework.register_component('vision_service', VisionService())

# 服务发现
video_service = framework.get_component('video_service')
result = await video_service.process_video("video.mp4")
                    '''
                },
                'event_driven': {
                    'description': '事件驱动架构',
                    'benefits': ['松耦合', '可扩展', '异步处理'],
                    'implementation': '''
# 事件发布
await framework.broadcast_event('video_processed', {
    'video_id': 'vid_001',
    'result': 'success'
})

# 事件监听
@framework.on_event('video_processed')
async def handle_video_processed(event_data):
    # 触发后续处理
    await trigger_prd_generation(event_data['video_id'])
                    '''
                },
                'pipeline': {
                    'description': '流水线处理模式',
                    'benefits': ['清晰的数据流', '易于监控', '可组合'],
                    'implementation': '''
# 流水线定义
pipeline = Pipeline([
    VideoExtractor(),
    SpeechRecognizer(),
    ContentAnalyzer(),
    PRDGenerator()
])

# 流水线执行
result = await pipeline.execute("input_video.mp4")
                    '''
                }
            }
        }


class Troubleshooting:
    """故障排除"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def get_troubleshooting_guide(self) -> Dict[str, Any]:
        """获取故障排除指南"""
        return {
            'title': '故障排除指南',
            'description': '常见问题诊断和解决方案',
            'categories': {
                'installation': {
                    'title': '安装问题',
                    'issues': [
                        {
                            'problem': 'pip安装依赖失败',
                            'symptoms': ['ERROR: Could not find a version', 'Permission denied'],
                            'causes': ['Python版本不兼容', '权限不足', '网络问题'],
                            'solutions': [
                                '检查Python版本: python --version (需要3.8+)',
                                '使用虚拟环境: python -m venv venv',
                                '升级pip: pip install --upgrade pip',
                                '使用国内镜像: pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt'
                            ]
                        },
                        {
                            'problem': 'GPU相关库安装失败',
                            'symptoms': ['CUDA版本不匹配', 'torch安装失败'],
                            'causes': ['CUDA版本不兼容', '驱动版本过低'],
                            'solutions': [
                                '检查CUDA版本: nvcc --version',
                                '安装对应版本的PyTorch: pip install torch torchvision torchaudio',
                                '使用CPU版本: pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu'
                            ]
                        }
                    ]
                },
                'runtime': {
                    'title': '运行时问题',
                    'issues': [
                        {
                            'problem': '数据库连接失败',
                            'symptoms': ['Connection refused', 'Authentication failed'],
                            'causes': ['数据库服务未启动', '配置错误', '网络问题'],
                            'solutions': [
                                '检查数据库服务: sudo systemctl status postgresql',
                                '启动数据库: sudo systemctl start postgresql',
                                '验证配置: 检查config.yaml中的数据库配置',
                                '测试连接: psql -h localhost -U postgres -d neural_agent_db'
                            ]
                        },
                        {
                            'problem': '内存不足',
                            'symptoms': ['OutOfMemoryError', '系统卡顿'],
                            'causes': ['模型过大', '并发请求过多', '内存泄漏'],
                            'solutions': [
                                '减少批处理大小',
                                '使用模型量化: model.half()',
                                '启用垃圾回收: gc.collect()',
                                '监控内存使用: psutil.virtual_memory()'
                            ]
                        }
                    ]
                },
                'performance': {
                    'title': '性能问题',
                    'issues': [
                        {
                            'problem': '处理速度慢',
                            'symptoms': ['响应时间长', 'CPU使用率低'],
                            'causes': ['未使用GPU', 'I/O阻塞', '算法复杂度高'],
                            'solutions': [
                                '启用GPU加速: model.to("cuda")',
                                '使用异步处理: asyncio.gather()',
                                '优化算法: 选择更高效的模型',
                                '增加并发: 调整线程池大小'
                            ]
                        }
                    ]
                },
                'integration': {
                    'title': '集成问题',
                    'issues': [
                        {
                            'problem': '组件间通信失败',
                            'symptoms': ['事件广播失败', '组件未注册'],
                            'causes': ['框架未初始化', '组件ID冲突', '网络问题'],
                            'solutions': [
                                '检查框架初始化: await framework.initialize()',
                                '验证组件注册: framework.list_components()',
                                '检查事件类型: 确保事件类型正确',
                                '调试日志: 启用DEBUG级别日志'
                            ]
                        }
                    ]
                }
            },
            'debugging_tools': {
                'logging': {
                    'description': '日志调试',
                    'code': '''
import logging

# 配置详细日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('debug.log'),
        logging.StreamHandler()
    ]
)

# 在代码中使用
logger = logging.getLogger(__name__)
logger.debug("调试信息")
logger.info("普通信息")
logger.warning("警告信息")
logger.error("错误信息")
                    '''
                },
                'profiling': {
                    'description': '性能分析',
                    'code': '''
import cProfile
import pstats

def profile_function():
    # 要分析的函数
    result = some_expensive_operation()
    return result

# 运行分析
cProfile.run('profile_function()', 'profile_stats')

# 查看结果
stats = pstats.Stats('profile_stats')
stats.sort_stats('cumulative')
stats.print_stats(10)
                    '''
                },
                'monitoring': {
                    'description': '系统监控',
                    'code': '''
import psutil
import time

def monitor_system():
    while True:
        cpu_percent = psutil.cpu_percent()
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        print(f"CPU: {cpu_percent}%, Memory: {memory.percent}%, Disk: {disk.percent}%")
        
        time.sleep(5)

monitor_system()
                    '''
                }
            },
            'common_errors': {
                'ImportError': {
                    'description': '模块导入错误',
                    'solution': '检查PYTHONPATH和包安装'
                },
                'FileNotFoundError': {
                    'description': '文件未找到',
                    'solution': '检查文件路径和权限'
                },
                'TimeoutError': {
                    'description': '操作超时',
                    'solution': '增加超时时间或检查网络'
                },
                'ConnectionError': {
                    'description': '连接错误',
                    'solution': '检查服务状态和网络连接'
                }
            }
        }


class DocumentationExamples:
    """文档示例主类"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # 初始化各个组件
        self.quick_start = QuickStartGuide()
        self.api_reference = APIReference()
        self.config_guide = ConfigurationGuide()
        self.best_practices = BestPractices()
        self.troubleshooting = Troubleshooting()
    
    def generate_complete_documentation(self) -> Dict[str, Any]:
        """生成完整文档"""
        return {
            'title': 'NeuralAgent × Agno-BMAD-LM Studio 完整文档',
            'version': '1.0.0',
            'generated_at': datetime.now().isoformat(),
            'sections': {
                'quick_start': self.quick_start.get_quick_start_content(),
                'api_reference': self.api_reference.get_api_reference(),
                'configuration': self.config_guide.get_configuration_guide(),
                'best_practices': self.best_practices.get_best_practices(),
                'troubleshooting': self.troubleshooting.get_troubleshooting_guide()
            }
        }
    
    def save_documentation(self, output_dir: str) -> str:
        """保存文档到文件"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # 生成完整文档
        documentation = self.generate_complete_documentation()
        
        # 保存为JSON格式
        json_path = output_path / "complete_documentation.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(documentation, f, indent=2, ensure_ascii=False)
        
        # 生成Markdown格式的快速开始指南
        self._generate_markdown_docs(output_path)
        
        return str(output_path)
    
    def _generate_markdown_docs(self, output_path: Path):
        """生成Markdown格式文档"""
        
        # 快速开始指南
        quick_start_content = self.quick_start.get_quick_start_content()
        
        md_content = f"""# {quick_start_content['title']}

{quick_start_content['description']}

## 前置要求

{chr(10).join(f"- {req}" for req in quick_start_content['prerequisites'])}

## 安装步骤

{chr(10).join(f"### {step['step']}. {step['title']}{chr(10)}{step['description']}{chr(10)}```bash{chr(10)}{step['command']}{chr(10)}```" for step in quick_start_content['installation_steps'])}

## 第一个示例

### {quick_start_content['first_example']['title']}

{quick_start_content['first_example']['description']}

```python
{quick_start_content['first_example']['code'].strip()}
```

预期输出：
```
{quick_start_content['first_example']['expected_output'].strip()}
```

## 下一步

{chr(10).join(f"- {step}" for step in quick_start_content['next_steps'])}

---
*文档生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
        
        quick_start_path = output_path / "quick_start.md"
        with open(quick_start_path, 'w', encoding='utf-8') as f:
            f.write(md_content)
        
        # API参考文档
        api_content = self._generate_api_markdown()
        api_path = output_path / "api_reference.md"
        with open(api_path, 'w', encoding='utf-8') as f:
            f.write(api_content)
        
        # 配置指南
        config_content = self._generate_config_markdown()
        config_path = output_path / "configuration.md"
        with open(config_path, 'w', encoding='utf-8') as f:
            f.write(config_content)
        
        # 最佳实践
        practices_content = self._generate_practices_markdown()
        practices_path = output_path / "best_practices.md"
        with open(practices_path, 'w', encoding='utf-8') as f:
            f.write(practices_content)
    
    def _generate_api_markdown(self) -> str:
        """生成API参考Markdown"""
        api_data = self.api_reference.get_api_reference()
        
        content = f"""# {api_data['title']}

{api_data['description']}

## 模块参考

"""
        
        for module_id, module_info in api_data['modules'].items():
            content += f"### {module_info['class'] if 'class' in module_info else module_id}{chr(10)}{module_info['description']}{chr(10)}{chr(10)}"
            
            if 'methods' in module_info:
                for method_name, method_info in module_info['methods'].items():
                    content += f"#### {method_name}{chr(10}"
                    content += f"```python{chr(10)}{method_info['signature']}{chr(10)}```{chr(10)}{chr(10)}"
                    content += f"{method_info['description']}{chr(10)}{chr(10)}"
                    
                    if 'parameters' in method_info:
                        content += "**参数:**" + chr(10)
                        for param in method_info['parameters']:
                            content += f"- `{param['name']}` ({param['type']}): {param['description']}" + chr(10)
                        content += chr(10)
                    
                    content += f"**返回:** {method_info['returns']}" + chr(10)
                    
                    if 'example' in method_info:
                        content += f"**示例:**{chr(10)```python{chr(10)}{method_info['example'].strip()}{chr(10)}```{chr(10)}"
                    
                    content += chr(10)
        
        return content
    
    def _generate_config_markdown(self) -> str:
        """生成配置指南Markdown"""
        config_data = self.config_guide.get_configuration_guide()
        
        content = f"""# {config_data['title']}

{config_data['description']}

## 配置文件

"""
        
        for config_file, file_info in config_data['config_files'].items():
            content += f"### {config_file}{chr(10}"
            content += f"**位置:** `{file_info['location']}`{chr(10)}{chr(10)}"
            content += f"{file_info['description']}{chr(10)}{chr(10)}"
            
            if 'structure' in file_info:
                content += "```yaml" + chr(10)
                content += self._dict_to_yaml(file_info['structure'])
                content += "```" + chr(10) + chr(10)
        
        return content
    
    def _generate_practices_markdown(self) -> str:
        """生成最佳实践Markdown"""
        practices_data = self.best_practices.get_best_practices()
        
        content = f"""# {practices_data['title']}

{practices_data['description']}

"""
        
        for category_id, category_info in practices_data['categories'].items():
            content += f"## {category_info['title']}{chr(10){chr(10)}"
            
            for practice in category_info['practices']:
                content += f"### {practice['title']}{chr(10}"
                content += f"{practice['description']}{chr(10)}{chr(10)}"
                content += f"```python{chr(10)}{practice['code'].strip()}{chr(10)}```{chr(10)}{chr(10)}"
        
        return content
    
    def _dict_to_yaml(self, d: Dict[str, Any], indent: int = 0) -> str:
        """将字典转换为YAML格式"""
        yaml_str = ""
        spaces = "  " * indent
        
        for key, value in d.items():
            if isinstance(value, dict):
                yaml_str += f"{spaces}{key}:" + chr(10)
                yaml_str += self._dict_to_yaml(value, indent + 1)
            elif isinstance(value, list):
                yaml_str += f"{spaces}{key}:" + chr(10)
                for item in value:
                    yaml_str += f"{spaces}- {item}" + chr(10)
            else:
                yaml_str += f"{spaces}{key}: {value}" + chr(10)
        
        return yaml_str
    
    def get_documentation_stats(self) -> Dict[str, Any]:
        """获取文档统计信息"""
        doc_data = self.generate_complete_documentation()
        
        stats = {
            'total_sections': len(doc_data['sections']),
            'section_breakdown': {},
            'total_examples': 0,
            'code_samples': 0
        }
        
        for section_name, section_data in doc_data['sections'].items():
            if 'examples' in section_data:
                stats['total_examples'] += len(section_data['examples'])
            
            if 'code_samples' in section_data:
                stats['code_samples'] += len(section_data['code_samples'])
            
            stats['section_breakdown'][section_name] = {
                'title': section_data.get('title', 'Unknown'),
                'has_examples': 'examples' in section_data,
                'has_code': 'code_samples' in section_data
            }
        
        return stats