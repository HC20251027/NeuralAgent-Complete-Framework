"""
NeuralAgent × Agno-BMAD 融合框架 - 测试套件
==============================================

完整的测试框架，包含：
- 单元测试 (unit/)
- 集成测试 (integration/) 
- 演示代码 (demo/)
- 示例代码 (examples/)
- 性能测试 (benchmarks/)

Author: MiniMax Agent
Date: 2025-11-06
Version: 1.0.0
"""

from .unit import *
from .integration import *
from .demo import *
from .examples import *
from .benchmarks import *

__version__ = '1.0.0'
__author__ = 'MiniMax Agent'

# 测试配置
TEST_CONFIG = {
    'database': {
        'host': 'localhost',
        'port': 5432,
        'database': 'ai_agents_test',
        'user': 'postgres',
        'password': ''
    },
    'vision': {
        'approach': 'ocr_enhanced',
        'confidence_threshold': 0.7
    },
    'asr': {
        'engine': 'whisper',
        'language': 'zh-CN',
        'sample_rate': 16000
    },
    'agents': {
        'collaboration_mode': 'parallel',
        'timeout': 30
    }
}

# 测试工具函数
def setup_test_environment():
    """设置测试环境"""
    import os
    os.environ['DB_HOST'] = TEST_CONFIG['database']['host']
    os.environ['DB_PORT'] = str(TEST_CONFIG['database']['port'])
    os.environ['DB_NAME'] = TEST_CONFIG['database']['database']
    os.environ['DB_USER'] = TEST_CONFIG['database']['user']
    os.environ['DB_PASSWORD'] = TEST_CONFIG['database']['password']

def cleanup_test_environment():
    """清理测试环境"""
    import os
    # 清理环境变量
    test_env_vars = ['DB_HOST', 'DB_PORT', 'DB_NAME', 'DB_USER', 'DB_PASSWORD']
    for var in test_env_vars:
        if var in os.environ:
            del os.environ[var]

# 快速测试函数
async def quick_test():
    """快速测试所有核心功能"""
    try:
        from NeuralAgent_Complete_Framework import SystemIntegration
        
        # 初始化系统
        system = SystemIntegration()
        await system.initialize()
        
        # 测试多模态处理
        result = await system.process_multimodal_input(
            text_input="测试输入"
        )
        
        # 测试智能体工作流
        workflow_tasks = [
            {
                'id': 'test_task_1',
                'role': 'analyst',
                'description': '分析测试数据',
                'input_data': {'data': 'test'},
                'priority': 1
            }
        ]
        
        agent_results = await system.execute_agent_workflow(workflow_tasks)
        
        # 清理
        await system.shutdown()
        
        return {
            'success': True,
            'multimodal_result': result,
            'agent_results': agent_results
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

# 导出主要测试类
__all__ = [
    'TEST_CONFIG',
    'setup_test_environment', 
    'cleanup_test_environment',
    'quick_test'
]