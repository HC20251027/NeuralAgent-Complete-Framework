"""
集成测试框架 - Integration Testing Framework
============================================

提供完整的集成测试解决方案：
- 测试用例管理
- 测试执行引擎
- 测试报告生成
- 性能测试

Author: MiniMax Agent
Date: 2025-11-06
"""

import asyncio
import logging
import json
import time
import traceback
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass, field
from datetime import datetime
import statistics
import tempfile
import shutil

# 测试框架
import pytest
import aiohttp
import numpy as np

# 音频处理
import librosa
import soundfile as sf

# 数据库测试
import psycopg2
import redis

# 配置管理
from agno_bmad_integration.framework import IntegrationFramework


@dataclass
class TestCase:
    """测试用例类"""
    test_id: str
    name: str
    description: str
    category: str  # unit, integration, system, performance
    priority: str  # high, medium, low
    test_function: Callable
    parameters: Dict[str, Any] = field(default_factory=dict)
    expected_result: Any = None
    timeout: int = 60
    retry_count: int = 0
    dependencies: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'test_id': self.test_id,
            'name': self.name,
            'description': self.description,
            'category': self.category,
            'priority': self.priority,
            'parameters': self.parameters,
            'expected_result': self.expected_result,
            'timeout': self.timeout,
            'retry_count': self.retry_count,
            'dependencies': self.dependencies,
            'tags': self.tags
        }


@dataclass
class TestResult:
    """测试结果类"""
    test_id: str
    test_name: str
    status: str  # passed, failed, skipped, error
    start_time: datetime
    end_time: Optional[datetime] = None
    duration: float = 0.0
    error_message: Optional[str] = None
    error_traceback: Optional[str] = None
    output: Any = None
    metrics: Dict[str, float] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'test_id': self.test_id,
            'test_name': self.test_name,
            'status': self.status,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'duration': self.duration,
            'error_message': self.error_message,
            'error_traceback': self.error_traceback,
            'output': self.output,
            'metrics': self.metrics,
            'metadata': self.metadata
        }


@dataclass
class TestSuite:
    """测试套件类"""
    suite_id: str
    name: str
    description: str
    test_cases: List[TestCase] = field(default_factory=list)
    setup_function: Optional[Callable] = None
    teardown_function: Optional[Callable] = None
    parallel_execution: bool = False
    max_concurrent: int = 5
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'suite_id': self.suite_id,
            'name': self.name,
            'description': self.description,
            'test_cases': [tc.to_dict() for tc in self.test_cases],
            'parallel_execution': self.parallel_execution,
            'max_concurrent': self.max_concurrent
        }


class DatabaseTestHelper:
    """数据库测试助手"""
    
    def __init__(self, db_config: Dict[str, Any]):
        self.db_config = db_config
        self.logger = logging.getLogger(__name__)
        self.connection = None
    
    async def connect(self):
        """连接数据库"""
        try:
            self.connection = psycopg2.connect(
                host=self.db_config.get('host', 'localhost'),
                port=self.db_config.get('port', 5432),
                database=self.db_config.get('database', 'test_db'),
                user=self.db_config.get('user', 'postgres'),
                password=self.db_config.get('password', 'password')
            )
        except Exception as e:
            self.logger.error(f"数据库连接失败: {e}")
            raise
    
    async def disconnect(self):
        """断开数据库连接"""
        if self.connection:
            self.connection.close()
    
    async def execute_query(self, query: str, params: tuple = None) -> List[Dict]:
        """执行查询"""
        if not self.connection:
            await self.connect()
        
        cursor = self.connection.cursor()
        try:
            cursor.execute(query, params)
            if cursor.description:
                columns = [desc[0] for desc in cursor.description]
                results = [dict(zip(columns, row)) for row in cursor.fetchall()]
                return results
            else:
                self.connection.commit()
                return []
        finally:
            cursor.close()
    
    async def create_test_data(self, table_name: str, data: List[Dict]) -> bool:
        """创建测试数据"""
        if not data:
            return True
        
        try:
            # 获取列名
            columns = list(data[0].keys())
            placeholders = ', '.join(['%s'] * len(columns))
            column_names = ', '.join(columns)
            
            # 构建插入语句
            query = f"INSERT INTO {table_name} ({column_names}) VALUES ({placeholders})"
            
            # 执行批量插入
            cursor = self.connection.cursor()
            cursor.executemany(query, [tuple(item[col] for col in columns) for item in data])
            self.connection.commit()
            cursor.close()
            
            return True
        except Exception as e:
            self.logger.error(f"创建测试数据失败: {e}")
            return False
    
    async def cleanup_test_data(self, table_name: str, condition: str = "") -> bool:
        """清理测试数据"""
        try:
            query = f"DELETE FROM {table_name}"
            if condition:
                query += f" WHERE {condition}"
            
            cursor = self.connection.cursor()
            cursor.execute(query)
            self.connection.commit()
            cursor.close()
            
            return True
        except Exception as e:
            self.logger.error(f"清理测试数据失败: {e}")
            return False


class APITestHelper:
    """API测试助手"""
    
    def __init__(self, base_url: str = "http://localhost:8080"):
        self.base_url = base_url
        self.logger = logging.getLogger(__name__)
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def get(self, endpoint: str, params: Dict = None, headers: Dict = None) -> Dict[str, Any]:
        """GET请求"""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        async with self.session.get(url, params=params, headers=headers) as response:
            return {
                'status': response.status,
                'headers': dict(response.headers),
                'data': await response.json() if response.content_type == 'application/json' else await response.text()
            }
    
    async def post(self, endpoint: str, data: Dict = None, json_data: Dict = None, headers: Dict = None) -> Dict[str, Any]:
        """POST请求"""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        async with self.session.post(url, data=data, json=json_data, headers=headers) as response:
            return {
                'status': response.status,
                'headers': dict(response.headers),
                'data': await response.json() if response.content_type == 'application/json' else await response.text()
            }
    
    async def put(self, endpoint: str, data: Dict = None, json_data: Dict = None, headers: Dict = None) -> Dict[str, Any]:
        """PUT请求"""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        async with self.session.put(url, data=data, json=json_data, headers=headers) as response:
            return {
                'status': response.status,
                'headers': dict(response.headers),
                'data': await response.json() if response.content_type == 'application/json' else await response.text()
            }
    
    async def delete(self, endpoint: str, headers: Dict = None) -> Dict[str, Any]:
        """DELETE请求"""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        async with self.session.delete(url, headers=headers) as response:
            return {
                'status': response.status,
                'headers': dict(response.headers),
                'data': await response.json() if response.content_type == 'application/json' else await response.text()
            }


class AudioTestHelper:
    """音频测试助手"""
    
    def __init__(self, sample_rate: int = 16000):
        self.sample_rate = sample_rate
        self.logger = logging.getLogger(__name__)
    
    def generate_test_audio(self, duration: float = 1.0, frequency: float = 440.0) -> np.ndarray:
        """生成测试音频"""
        t = np.linspace(0, duration, int(self.sample_rate * duration))
        audio = 0.5 * np.sin(2 * np.pi * frequency * t)
        return audio
    
    def generate_speech_like_audio(self, duration: float = 2.0) -> np.ndarray:
        """生成类似语音的音频"""
        # 生成多频率成分来模拟语音
        t = np.linspace(0, duration, int(self.sample_rate * duration))
        
        # 基频变化
        f0 = 100 + 50 * np.sin(2 * np.pi * 0.5 * t)  # 基频在100-150Hz变化
        
        # 生成语音信号
        audio = np.zeros_like(t)
        for i, freq in enumerate(f0):
            # 谐波叠加
            for harmonic in range(1, 6):
                audio[i] += 0.1 * np.sin(2 * np.pi * harmonic * freq * t[i]) / harmonic
        
        # 添加包络
        envelope = np.exp(-t / duration) + 0.1 * np.random.random(len(t))
        audio *= envelope
        
        # 归一化
        audio = audio / np.max(np.abs(audio)) * 0.8
        
        return audio
    
    def save_test_audio(self, audio: np.ndarray, filename: str) -> str:
        """保存测试音频"""
        filepath = Path(tempfile.gettempdir()) / f"{filename}_{int(time.time())}.wav"
        sf.write(str(filepath), audio, self.sample_rate)
        return str(filepath)
    
    def load_audio(self, filepath: str) -> np.ndarray:
        """加载音频文件"""
        audio, sr = librosa.load(filepath, sr=self.sample_rate)
        return audio


class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.metrics = {
            'response_times': [],
            'memory_usage': [],
            'cpu_usage': [],
            'throughput': []
        }
    
    async def measure_response_time(self, func: Callable, *args, **kwargs) -> tuple[Any, float]:
        """测量响应时间"""
        start_time = time.time()
        result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
        end_time = time.time()
        response_time = end_time - start_time
        
        self.metrics['response_times'].append(response_time)
        return result, response_time
    
    async def measure_memory_usage(self, func: Callable, *args, **kwargs) -> tuple[Any, Dict[str, float]]:
        """测量内存使用"""
        import psutil
        import gc
        
        # 获取初始内存
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # 执行函数
        result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
        
        # 获取最终内存
        gc.collect()  # 强制垃圾回收
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_diff = final_memory - initial_memory
        
        self.metrics['memory_usage'].append(memory_diff)
        
        memory_stats = {
            'initial_mb': initial_memory,
            'final_mb': final_memory,
            'diff_mb': memory_diff
        }
        
        return result, memory_stats
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """获取性能摘要"""
        summary = {}
        
        for metric_name, values in self.metrics.items():
            if values:
                summary[metric_name] = {
                    'count': len(values),
                    'mean': statistics.mean(values),
                    'median': statistics.median(values),
                    'min': min(values),
                    'max': max(values),
                    'std': statistics.stdev(values) if len(values) > 1 else 0
                }
            else:
                summary[metric_name] = {'count': 0}
        
        return summary


class IntegrationTestFramework:
    """集成测试框架主类"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # 测试套件
        self.test_suites: Dict[str, TestSuite] = {}
        
        # 测试结果
        self.test_results: List[TestResult] = []
        
        # 测试助手
        self.db_helper = DatabaseTestHelper(self.config.get('database', {}))
        self.audio_helper = AudioTestHelper()
        self.performance_monitor = PerformanceMonitor()
        
        # 集成框架
        self.integration_framework = IntegrationFramework()
        
        # 创建默认测试套件
        self._create_default_test_suites()
    
    def _create_default_test_suites(self):
        """创建默认测试套件"""
        # 数据库测试套件
        db_suite = TestSuite(
            suite_id="database_tests",
            name="数据库测试套件",
            description="测试数据库连接和基本操作",
            test_cases=[
                TestCase(
                    test_id="db_connection",
                    name="数据库连接测试",
                    description="测试数据库连接是否正常",
                    category="integration",
                    priority="high",
                    test_function=self._test_database_connection
                ),
                TestCase(
                    test_id="db_operations",
                    name="数据库操作测试",
                    description="测试基本的数据库CRUD操作",
                    category="integration", 
                    priority="high",
                    test_function=self._test_database_operations
                )
            ]
        )
        
        # API测试套件
        api_suite = TestSuite(
            suite_id="api_tests",
            name="API测试套件",
            description="测试API接口功能",
            test_cases=[
                TestCase(
                    test_id="api_health",
                    name="API健康检查",
                    description="测试API服务是否正常运行",
                    category="integration",
                    priority="high",
                    test_function=self._test_api_health
                ),
                TestCase(
                    test_id="api_agno",
                    name="Agno框架API测试",
                    description="测试Agno框架API接口",
                    category="integration",
                    priority="medium",
                    test_function=self._test_agno_api
                )
            ]
        )
        
        # 音频处理测试套件
        audio_suite = TestSuite(
            suite_id="audio_tests",
            name="音频处理测试套件",
            description="测试音频处理功能",
            test_cases=[
                TestCase(
                    test_id="audio_generation",
                    name="音频生成测试",
                    description="测试音频生成功能",
                    category="unit",
                    priority="medium",
                    test_function=self._test_audio_generation
                ),
                TestCase(
                    test_id="audio_processing",
                    name="音频处理测试",
                    description="测试音频处理功能",
                    category="integration",
                    priority="medium",
                    test_function=self._test_audio_processing
                )
            ]
        )
        
        # 性能测试套件
        performance_suite = TestSuite(
            suite_id="performance_tests",
            name="性能测试套件",
            description="测试系统性能",
            test_cases=[
                TestCase(
                    test_id="response_time",
                    name="响应时间测试",
                    description="测试API响应时间",
                    category="performance",
                    priority="medium",
                    test_function=self._test_response_time
                )
            ],
            parallel_execution=True
        )
        
        # 注册测试套件
        self.test_suites = {
            "database_tests": db_suite,
            "api_tests": api_suite,
            "audio_tests": audio_suite,
            "performance_tests": performance_suite
        }
    
    async def run_test_suite(self, suite_id: str, parallel: bool = False) -> Dict[str, Any]:
        """运行测试套件"""
        if suite_id not in self.test_suites:
            raise ValueError(f"测试套件不存在: {suite_id}")
        
        suite = self.test_suites[suite_id]
        self.logger.info(f"开始运行测试套件: {suite.name}")
        
        # 套件设置
        if suite.setup_function:
            await suite.setup_function()
        
        # 运行测试用例
        if parallel and suite.parallel_execution:
            results = await self._run_tests_parallel(suite.test_cases)
        else:
            results = await self._run_tests_sequential(suite.test_cases)
        
        # 套件清理
        if suite.teardown_function:
            await suite.teardown_function()
        
        # 生成套件结果
        suite_result = {
            'suite_id': suite_id,
            'suite_name': suite.name,
            'total_tests': len(suite.test_cases),
            'passed': len([r for r in results if r.status == 'passed']),
            'failed': len([r for r in results if r.status == 'failed']),
            'skipped': len([r for r in results if r.status == 'skipped']),
            'errors': len([r for r in results if r.status == 'error']),
            'results': [r.to_dict() for r in results],
            'start_time': datetime.now().isoformat(),
            'end_time': datetime.now().isoformat()
        }
        
        self.logger.info(f"测试套件 {suite.name} 运行完成: "
                        f"通过 {suite_result['passed']}, "
                        f"失败 {suite_result['failed']}, "
                        f"跳过 {suite_result['skipped']}")
        
        return suite_result
    
    async def run_all_tests(self, parallel: bool = True) -> Dict[str, Any]:
        """运行所有测试"""
        self.logger.info("开始运行所有测试套件")
        
        all_results = []
        suite_results = {}
        
        if parallel:
            # 并行运行所有套件
            tasks = []
            for suite_id in self.test_suites.keys():
                task = self.run_test_suite(suite_id, parallel=True)
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for i, suite_id in enumerate(self.test_suites.keys()):
                if isinstance(results[i], Exception):
                    suite_results[suite_id] = {'error': str(results[i])}
                else:
                    suite_results[suite_id] = results[i]
                    all_results.extend(results[i]['results'])
        else:
            # 串行运行所有套件
            for suite_id in self.test_suites.keys():
                result = await self.run_test_suite(suite_id, parallel=False)
                suite_results[suite_id] = result
                all_results.extend(result['results'])
        
        # 生成总体结果
        total_result = {
            'total_suites': len(self.test_suites),
            'total_tests': len(all_results),
            'passed': len([r for r in all_results if r['status'] == 'passed']),
            'failed': len([r for r in all_results if r['status'] == 'failed']),
            'skipped': len([r for r in all_results if r['status'] == 'skipped']),
            'errors': len([r for r in all_results if r['status'] == 'error']),
            'suite_results': suite_results,
            'performance_summary': self.performance_monitor.get_performance_summary(),
            'start_time': datetime.now().isoformat(),
            'end_time': datetime.now().isoformat()
        }
        
        self.logger.info(f"所有测试运行完成: "
                        f"通过 {total_result['passed']}, "
                        f"失败 {total_result['failed']}")
        
        return total_result
    
    async def _run_tests_sequential(self, test_cases: List[TestCase]) -> List[TestResult]:
        """串行运行测试用例"""
        results = []
        for test_case in test_cases:
            result = await self._run_single_test(test_case)
            results.append(result)
        return results
    
    async def _run_tests_parallel(self, test_cases: List[TestCase]) -> List[TestResult]:
        """并行运行测试用例"""
        semaphore = asyncio.Semaphore(5)  # 限制并发数
        
        async def run_test_with_semaphore(test_case):
            async with semaphore:
                return await self._run_single_test(test_case)
        
        tasks = [run_test_with_semaphore(tc) for tc in test_cases]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理异常结果
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                test_case = test_cases[i]
                error_result = TestResult(
                    test_id=test_case.test_id,
                    test_name=test_case.name,
                    status="error",
                    start_time=datetime.now(),
                    end_time=datetime.now(),
                    error_message=str(result),
                    error_traceback=traceback.format_exc()
                )
                processed_results.append(error_result)
            else:
                processed_results.append(result)
        
        return processed_results
    
    async def _run_single_test(self, test_case: TestCase) -> TestResult:
        """运行单个测试用例"""
        result = TestResult(
            test_id=test_case.test_id,
            test_name=test_case.name,
            status="skipped",
            start_time=datetime.now()
        )
        
        try:
            # 检查依赖
            if not self._check_dependencies(test_case):
                result.status = "skipped"
                result.error_message = "依赖测试未通过"
                return result
            
            # 执行测试
            self.logger.info(f"运行测试: {test_case.name}")
            
            # 设置超时
            test_task = asyncio.create_task(
                self._execute_test_function(test_case)
            )
            
            try:
                output = await asyncio.wait_for(test_task, timeout=test_case.timeout)
                result.output = output
                result.status = "passed"
            except asyncio.TimeoutError:
                result.status = "failed"
                result.error_message = f"测试超时 ({test_case.timeout}秒)"
            
        except Exception as e:
            result.status = "error"
            result.error_message = str(e)
            result.error_traceback = traceback.format_exc()
            self.logger.error(f"测试 {test_case.name} 执行失败: {e}")
        
        finally:
            result.end_time = datetime.now()
            result.duration = (result.end_time - result.start_time).total_seconds()
        
        return result
    
    def _check_dependencies(self, test_case: TestCase) -> bool:
        """检查测试依赖"""
        for dep_id in test_case.dependencies:
            dep_result = next((r for r in self.test_results if r.test_id == dep_id), None)
            if not dep_result or dep_result.status != "passed":
                return False
        return True
    
    async def _execute_test_function(self, test_case: TestCase) -> Any:
        """执行测试函数"""
        if asyncio.iscoroutinefunction(test_case.test_function):
            return await test_case.test_function(**test_case.parameters)
        else:
            return test_case.test_function(**test_case.parameters)
    
    # 默认测试函数
    async def _test_database_connection(self) -> bool:
        """测试数据库连接"""
        try:
            await self.db_helper.connect()
            await self.db_helper.disconnect()
            return True
        except Exception as e:
            self.logger.error(f"数据库连接测试失败: {e}")
            return False
    
    async def _test_database_operations(self) -> Dict[str, Any]:
        """测试数据库操作"""
        try:
            await self.db_helper.connect()
            
            # 创建测试表
            await self.db_helper.execute_query("""
                CREATE TABLE IF NOT EXISTS test_table (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(100),
                    value INTEGER
                )
            """)
            
            # 插入测试数据
            test_data = [
                {'name': 'test1', 'value': 100},
                {'name': 'test2', 'value': 200}
            ]
            success = await self.db_helper.create_test_data('test_table', test_data)
            
            # 查询数据
            results = await self.db_helper.execute_query("SELECT * FROM test_table")
            
            # 清理数据
            await self.db_helper.cleanup_test_data('test_table')
            
            await self.db_helper.disconnect()
            
            return {
                'insert_success': success,
                'query_results': results,
                'record_count': len(results)
            }
        except Exception as e:
            self.logger.error(f"数据库操作测试失败: {e}")
            raise
    
    async def _test_api_health(self) -> Dict[str, Any]:
        """测试API健康状态"""
        try:
            async with APITestHelper() as api_helper:
                # 测试健康检查端点
                health_result = await api_helper.get('health')
                
                return {
                    'status_code': health_result['status'],
                    'response': health_result['data']
                }
        except Exception as e:
            self.logger.error(f"API健康检查失败: {e}")
            raise
    
    async def _test_agno_api(self) -> Dict[str, Any]:
        """测试Agno框架API"""
        try:
            async with APITestHelper("http://localhost:8000") as api_helper:
                # 测试Agno特定端点
                result = await api_helper.get('agents')
                
                return {
                    'status_code': result['status'],
                    'agents_count': len(result['data']) if isinstance(result['data'], list) else 0
                }
        except Exception as e:
            self.logger.error(f"Agno API测试失败: {e}")
            raise
    
    async def _test_audio_generation(self) -> Dict[str, Any]:
        """测试音频生成"""
        try:
            # 生成测试音频
            audio = self.audio_helper.generate_test_audio(duration=1.0, frequency=440.0)
            
            # 保存音频文件
            filepath = self.audio_helper.save_test_audio(audio, "test_audio")
            
            return {
                'audio_length': len(audio),
                'sample_rate': self.audio_helper.sample_rate,
                'saved_file': filepath
            }
        except Exception as e:
            self.logger.error(f"音频生成测试失败: {e}")
            raise
    
    async def _test_audio_processing(self) -> Dict[str, Any]:
        """测试音频处理"""
        try:
            # 生成测试音频
            audio = self.audio_helper.generate_speech_like_audio(duration=2.0)
            
            # 提取特征
            mfccs = librosa.feature.mfcc(y=audio, sr=self.audio_helper.sample_rate, n_mfcc=13)
            
            return {
                'audio_duration': len(audio) / self.audio_helper.sample_rate,
                'mfcc_shape': mfccs.shape,
                'mfcc_mean': float(np.mean(mfccs))
            }
        except Exception as e:
            self.logger.error(f"音频处理测试失败: {e}")
            raise
    
    async def _test_response_time(self) -> Dict[str, Any]:
        """测试响应时间"""
        try:
            async with APITestHelper() as api_helper:
                # 测量多次请求的响应时间
                response_times = []
                
                for _ in range(5):
                    start_time = time.time()
                    result = await api_helper.get('health')
                    end_time = time.time()
                    
                    response_times.append(end_time - start_time)
                
                return {
                    'min_response_time': min(response_times),
                    'max_response_time': max(response_times),
                    'avg_response_time': statistics.mean(response_times),
                    'requests_count': len(response_times)
                }
        except Exception as e:
            self.logger.error(f"响应时间测试失败: {e}")
            raise
    
    def add_test_suite(self, test_suite: TestSuite):
        """添加测试套件"""
        self.test_suites[test_suite.suite_id] = test_suite
    
    def add_test_case(self, suite_id: str, test_case: TestCase):
        """添加测试用例"""
        if suite_id in self.test_suites:
            self.test_suites[suite_id].test_cases.append(test_case)
        else:
            raise ValueError(f"测试套件不存在: {suite_id}")
    
    def get_test_results(self) -> List[Dict[str, Any]]:
        """获取测试结果"""
        return [result.to_dict() for result in self.test_results]
    
    def generate_test_report(self, output_path: str) -> str:
        """生成测试报告"""
        report_data = {
            'framework_info': {
                'name': 'Integration Test Framework',
                'version': '1.0.0',
                'timestamp': datetime.now().isoformat()
            },
            'test_suites': {suite_id: suite.to_dict() 
                          for suite_id, suite in self.test_suites.items()},
            'test_results': self.get_test_results(),
            'performance_summary': self.performance_monitor.get_performance_summary()
        }
        
        report_path = Path(output_path)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        
        return str(report_path)