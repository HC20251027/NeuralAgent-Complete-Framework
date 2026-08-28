"""
单元测试模块 - Unit Tests
========================

测试各个核心组件的独立功能：
- 数据库操作测试
- 视觉处理测试  
- 语音识别测试
- 智能体功能测试

Author: MiniMax Agent
"""

import unittest
import asyncio
import tempfile
import os
from pathlib import Path

# 测试基类
class BaseTestCase(unittest.TestCase):
    """测试基类"""
    
    def setUp(self):
        """设置测试环境"""
        self.test_dir = tempfile.mkdtemp()
        self.test_config = {
            'database': {
                'host': 'localhost',
                'port': 5432,
                'database': 'ai_agents_test',
                'user': 'postgres',
                'password': ''
            }
        }
    
    def tearDown(self):
        """清理测试环境"""
        import shutil
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

class AsyncTestCase(BaseTestCase):
    """异步测试基类"""
    
    def setUp(self):
        super().setUp()
        self.loop = asyncio.get_event_loop()
    
    async def async_test(self, test_func):
        """运行异步测试"""
        return await test_func()

# 数据库测试
class TestDatabaseOperations(BaseTestCase):
    """数据库操作测试"""
    
    def test_database_config(self):
        """测试数据库配置"""
        from NeuralAgent_Complete_Framework import DatabaseConnection
        
        db = DatabaseConnection()
        config = db._load_config()
        
        self.assertIsInstance(config, dict)
        self.assertIn('host', config)
        self.assertIn('port', config)
        self.assertIn('database', config)
    
    def test_vector_database(self):
        """测试向量数据库"""
        from NeuralAgent_Complete_Framework import VectorDatabase, DatabaseConnection
        
        # 模拟数据库连接
        mock_db = DatabaseConnection()
        
        # 这里应该使用mock来避免真实的数据库连接
        vector_db = VectorDatabase(mock_db)
        self.assertEqual(vector_db.embedding_dim, 1536)

# 视觉处理测试
class TestVisionProcessing(AsyncTestCase):
    """视觉处理测试"""
    
    async def test_neural_agent_vision(self):
        """测试NeuralAgent视觉模块"""
        from NeuralAgent_Complete_Framework import NeuralAgentVision, VisionApproach
        
        vision = NeuralAgentVision(VisionApproach.PURE_VISION)
        
        # 创建测试图像
        import numpy as np
        test_image = np.zeros((100, 100, 3), dtype=np.uint8)
        
        # 这里应该使用mock图像进行分析
        # result = await vision.analyze_image(test_image)
        
        # 验证基本属性
        self.assertEqual(vision.approach, VisionApproach.PURE_VISION)
        self.assertIsInstance(vision.elements, list)

# 语音识别测试
class TestSpeechRecognition(AsyncTestCase):
    """语音识别测试"""
    
    async def test_asr_framework(self):
        """测试ASR框架"""
        from NeuralAgent_Complete_Framework import ASRFramework, ASRConfig
        
        config = ASRConfig()
        asr = ASRFramework(config)
        
        # 验证配置
        self.assertEqual(config.engine, "whisper")
        self.assertEqual(config.language, "zh-CN")
        
        # 验证ASR实例
        self.assertIsNotNone(asr.recognizer)

# 智能体测试
class TestAgents(AsyncTestCase):
    """智能体功能测试"""
    
    async def test_bmad_agent(self):
        """测试BMAD智能体"""
        from NeuralAgent_Complete_Framework import BMADAgent, AgentRole, AgentTask
        
        agent = BMADAgent(AgentRole.ANALYST)
        
        # 验证智能体属性
        self.assertEqual(agent.role, AgentRole.ANALYST)
        self.assertIsNotNone(agent.agent_id)
        self.assertIsInstance(agent.capabilities, dict)
        
        # 创建测试任务
        task = AgentTask(
            id="test_task",
            role=AgentRole.ANALYST,
            description="测试任务",
            input_data={"test": "data"}
        )
        
        # 验证任务属性
        self.assertEqual(task.role, AgentRole.ANALYST)
        self.assertEqual(task.status, "pending")
    
    async def test_multi_agent_orchestrator(self):
        """测试多智能体协调器"""
        from NeuralAgent_Complete_Framework import MultiAgentOrchestrator, BMADAgent, AgentRole
        
        orchestrator = MultiAgentOrchestrator()
        
        # 添加智能体
        analyst = BMADAgent(AgentRole.ANALYST)
        orchestrator.add_agent(analyst)
        
        # 验证智能体已添加
        self.assertIn(AgentRole.ANALYST, orchestrator.agents)
        self.assertEqual(orchestrator.agents[AgentRole.ANALYST], analyst)

# 运行测试的函数
def run_unit_tests():
    """运行所有单元测试"""
    import unittest
    
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加测试类
    suite.addTests(loader.loadTestsFromTestCase(TestDatabaseOperations))
    suite.addTests(loader.loadTestsFromTestCase(TestVisionProcessing))
    suite.addTests(loader.loadTestsFromTestCase(TestSpeechRecognition))
    suite.addTests(loader.loadTestsFromTestCase(TestAgents))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()

if __name__ == '__main__':
    run_unit_tests()