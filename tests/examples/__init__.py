"""
示例代码模块 - Examples
======================

提供各种使用示例和代码片段：
- 基础使用示例
- 高级功能示例
- 最佳实践示例
- 故障排除示例

Author: HC20251027
"""

# 示例配置
EXAMPLE_CONFIGS = {
    'basic_usage': {
        'description': '基础使用示例',
        'features': ['基本功能', '简单配置', '快速入门']
    },
    'advanced_usage': {
        'description': '高级使用示例', 
        'features': ['高级配置', '性能优化', '扩展功能']
    },
    'best_practices': {
        'description': '最佳实践示例',
        'features': ['代码规范', '性能优化', '错误处理']
    }
}

# 快速开始示例
def quick_start_example():
    """快速开始示例"""
    example_code = '''
# 快速开始示例
from NeuralAgent_Complete_Framework import SystemIntegration

async def main():
    # 初始化系统
    system = SystemIntegration()
    await system.initialize()
    
    # 处理多模态输入
    result = await system.process_multimodal_input(
        text_input="你好，世界！"
    )
    
    # 执行智能体工作流
    workflow_tasks = [
        {
            'id': 'task_1',
            'role': 'analyst',
            'description': '分析数据',
            'input_data': {'data': 'sample'},
            'priority': 1
        }
    ]
    
    agent_results = await system.execute_agent_workflow(workflow_tasks)
    
    # 关闭系统
    await system.shutdown()
    
    return result, agent_results

# 运行示例
# asyncio.run(main())
'''
    return example_code

# API使用示例
def api_usage_example():
    """API使用示例"""
    example_code = '''
# API使用示例
import requests
import base64

# 图像分析API
def analyze_image_api(image_path):
    with open(image_path, 'rb') as f:
        image_data = base64.b64encode(f.read()).decode()
    
    response = requests.post('http://localhost:8000/api/vision/analyze', json={
        'image_data': image_data
    })
    
    return response.json()

# 语音识别API
def recognize_speech_api(audio_path):
    with open(audio_path, 'rb') as f:
        audio_data = base64.b64encode(f.read()).decode()
    
    response = requests.post('http://localhost:8000/api/audio/recognize', json={
        'audio_data': audio_data
    })
    
    return response.json()

# 多模态处理API
def multimodal_process_api(image_path, audio_path, text):
    with open(image_path, 'rb') as f:
        image_data = base64.b64encode(f.read()).decode()
    
    with open(audio_path, 'rb') as f:
        audio_data = base64.b64encode(f.read()).decode()
    
    response = requests.post('http://localhost:8000/api/multimodal/process', json={
        'image_data': image_data,
        'audio_data': audio_data,
        'text_input': text
    })
    
    return response.json()
'''
    return example_code

# 配置示例
def configuration_example():
    """配置示例"""
    example_code = '''
# 配置示例
import os
from NeuralAgent_Complete_Framework import ASRConfig, VisionApproach

# 数据库配置
os.environ['DB_HOST'] = 'localhost'
os.environ['DB_PORT'] = '5432'
os.environ['DB_NAME'] = 'ai_agents'
os.environ['DB_USER'] = 'postgres'
os.environ['DB_PASSWORD'] = 'your_password'

# ASR配置
asr_config = ASRConfig(
    engine="whisper",
    language="zh-CN",
    sample_rate=16000,
    whisper_model="base",
    enable_vad=True,
    enable_noise_reduction=True
)

# 视觉配置
vision_config = {
    'approach': VisionApproach.OCR_ENHANCED,
    'confidence_threshold': 0.7,
    'enable_text_recognition': True,
    'enable_color_analysis': True
}

# 智能体配置
agent_config = {
    'collaboration_mode': 'parallel',
    'timeout': 30,
    'max_concurrent_tasks': 5
}
'''
    return example_code

# 导出
__all__ = [
    'EXAMPLE_CONFIGS',
    'quick_start_example',
    'api_usage_example', 
    'configuration_example'
]