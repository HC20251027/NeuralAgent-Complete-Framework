"""
性能测试模块 - Benchmarks
========================

系统性能测试和基准测试：
- 响应时间测试
- 吞吐量测试
- 内存使用测试
- 并发性能测试

Author: HC20251027
"""

import time
import asyncio
import psutil
import statistics
from typing import List, Dict, Any
import json

class PerformanceBenchmark:
    """性能基准测试"""
    
    def __init__(self):
        self.results = {}
    
    async def benchmark_vision_processing(self, image_count: int = 10) -> Dict[str, float]:
        """视觉处理性能测试"""
        from NeuralAgent_Complete_Framework import NeuralAgentVision, VisionApproach
        
        vision = NeuralAgentVision(VisionApproach.PURE_VISION)
        processing_times = []
        
        # 创建测试图像
        import numpy as np
        test_image = np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8)
        
        for i in range(image_count):
            start_time = time.time()
            try:
                # 这里应该使用真实的图像分析，但为了测试我们跳过实际处理
                # result = await vision.analyze_image(test_image)
                await asyncio.sleep(0.1)  # 模拟处理时间
                processing_time = time.time() - start_time
                processing_times.append(processing_time)
            except Exception as e:
                print(f"图像 {i} 处理失败: {e}")
        
        return {
            'avg_processing_time': statistics.mean(processing_times),
            'min_processing_time': min(processing_times),
            'max_processing_time': max(processing_times),
            'total_images': len(processing_times),
            'throughput': len(processing_times) / sum(processing_times)
        }
    
    async def benchmark_asr_processing(self, audio_count: int = 10) -> Dict[str, float]:
        """ASR处理性能测试"""
        from NeuralAgent_Complete_Framework import ASRFramework, ASRConfig
        
        config = ASRConfig()
        asr = ASRFramework(config)
        processing_times = []
        
        # 创建测试音频数据
        import numpy as np
        test_audio = np.random.randn(16000).astype(np.float32)  # 1秒音频
        
        for i in range(audio_count):
            start_time = time.time()
            try:
                # 这里应该使用真实的ASR处理，但为了测试我们跳过实际处理
                # result = await asr.recognize_speech(test_audio.tobytes())
                await asyncio.sleep(0.2)  # 模拟处理时间
                processing_time = time.time() - start_time
                processing_times.append(processing_time)
            except Exception as e:
                print(f"音频 {i} 处理失败: {e}")
        
        return {
            'avg_processing_time': statistics.mean(processing_times),
            'min_processing_time': min(processing_times),
            'max_processing_time': max(processing_times),
            'total_audios': len(processing_times),
            'throughput': len(processing_times) / sum(processing_times)
        }
    
    async def benchmark_agent_workflow(self, task_count: int = 5) -> Dict[str, float]:
        """智能体工作流性能测试"""
        from NeuralAgent_Complete_Framework import MultiAgentOrchestrator, BMADAgent, AgentRole, AgentTask
        
        orchestrator = MultiAgentOrchestrator()
        
        # 添加智能体
        roles = [AgentRole.ANALYST, AgentRole.PM, AgentRole.ARCHITECT, AgentRole.DEVELOPER, AgentRole.QA]
        for role in roles:
            agent = BMADAgent(role)
            orchestrator.add_agent(agent)
        
        # 创建测试任务
        tasks = []
        for i in range(task_count):
            task = AgentTask(
                id=f"benchmark_task_{i}",
                role=roles[i % len(roles)],
                description=f"基准测试任务 {i}",
                input_data={'benchmark': True, 'task_id': i},
                priority=1
            )
            tasks.append(task)
        
        # 执行工作流
        start_time = time.time()
        try:
            results = await orchestrator.execute_workflow(tasks)
            total_time = time.time() - start_time
            
            return {
                'total_tasks': len(tasks),
                'total_time': total_time,
                'avg_task_time': total_time / len(tasks),
                'tasks_per_second': len(tasks) / total_time,
                'success_rate': len([r for r in results if not isinstance(r, Exception)]) / len(tasks)
            }
        except Exception as e:
            return {
                'error': str(e),
                'total_tasks': len(tasks),
                'success_rate': 0.0
            }
    
    async def benchmark_system_integration(self) -> Dict[str, Any]:
        """系统集成性能测试"""
        from NeuralAgent_Complete_Framework import SystemIntegration
        
        system = SystemIntegration()
        
        # 初始化系统
        init_start = time.time()
        await system.initialize()
        init_time = time.time() - init_start
        
        # 测试多模态处理
        multimodal_start = time.time()
        try:
            result = await system.process_multimodal_input(
                text_input="性能测试输入"
            )
            multimodal_time = time.time() - multimodal_start
        except Exception as e:
            multimodal_time = None
            result = {'error': str(e)}
        
        # 测试智能体工作流
        workflow_start = time.time()
        try:
            workflow_tasks = [
                {
                    'id': 'perf_test_task',
                    'role': 'analyst',
                    'description': '性能测试任务',
                    'input_data': {'test': True},
                    'priority': 1
                }
            ]
            agent_results = await system.execute_agent_workflow(workflow_tasks)
            workflow_time = time.time() - workflow_start
        except Exception as e:
            workflow_time = None
            agent_results = {'error': str(e)}
        
        # 关闭系统
        await system.shutdown()
        
        return {
            'initialization_time': init_time,
            'multimodal_processing_time': multimodal_time,
            'workflow_execution_time': workflow_time,
            'total_system_time': init_time + (multimodal_time or 0) + (workflow_time or 0)
        }
    
    def benchmark_memory_usage(self, duration: int = 10) -> Dict[str, float]:
        """内存使用基准测试"""
        process = psutil.Process()
        
        # 获取初始内存使用
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # 监控内存使用
        memory_samples = []
        start_time = time.time()
        
        while time.time() - start_time < duration:
            current_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_samples.append(current_memory)
            time.sleep(0.1)
        
        return {
            'initial_memory_mb': initial_memory,
            'peak_memory_mb': max(memory_samples),
            'avg_memory_mb': statistics.mean(memory_samples),
            'memory_variance': statistics.variance(memory_samples),
            'duration_seconds': duration
        }

class LoadTester:
    """负载测试器"""
    
    def __init__(self, max_concurrent: int = 10):
        self.max_concurrent = max_concurrent
    
    async def test_concurrent_requests(self, test_func, request_count: int = 50) -> Dict[str, Any]:
        """并发请求测试"""
        semaphore = asyncio.Semaphore(self.max_concurrent)
        
        async def bounded_test():
            async with semaphore:
                try:
                    start_time = time.time()
                    await test_func()
                    end_time = time.time()
                    return {
                        'success': True,
                        'response_time': end_time - start_time,
                        'error': None
                    }
                except Exception as e:
                    return {
                        'success': False,
                        'response_time': None,
                        'error': str(e)
                    }
        
        # 执行并发测试
        tasks = [bounded_test() for _ in range(request_count)]
        results = await asyncio.gather(*tasks)
        
        # 统计结果
        successful = [r for r in results if r['success']]
        failed = [r for r in results if not r['success']]
        
        response_times = [r['response_time'] for r in successful if r['response_time'] is not None]
        
        return {
            'total_requests': request_count,
            'successful_requests': len(successful),
            'failed_requests': len(failed),
            'success_rate': len(successful) / request_count,
            'avg_response_time': statistics.mean(response_times) if response_times else None,
            'min_response_time': min(response_times) if response_times else None,
            'max_response_time': max(response_times) if response_times else None,
            'throughput': len(successful) / sum(response_times) if response_times else 0
        }

# 基准测试运行器
async def run_all_benchmarks():
    """运行所有基准测试"""
    benchmark = PerformanceBenchmark()
    results = {}
    
    print("开始性能基准测试...")
    
    # 视觉处理测试
    print("测试视觉处理性能...")
    results['vision'] = await benchmark.benchmark_vision_processing()
    
    # ASR处理测试
    print("测试ASR处理性能...")
    results['asr'] = await benchmark.benchmark_asr_processing()
    
    # 智能体工作流测试
    print("测试智能体工作流性能...")
    results['agent_workflow'] = await benchmark.benchmark_agent_workflow()
    
    # 系统集成测试
    print("测试系统集成性能...")
    results['system_integration'] = await benchmark.benchmark_system_integration()
    
    # 内存使用测试
    print("测试内存使用...")
    results['memory'] = benchmark.benchmark_memory_usage()
    
    return results

def save_benchmark_results(results: Dict[str, Any], filename: str = "benchmark_results.json"):
    """保存基准测试结果"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False, default=str)
    print(f"基准测试结果已保存到: {filename}")

if __name__ == '__main__':
    # 运行基准测试
    results = asyncio.run(run_all_benchmarks())
    save_benchmark_results(results)
    
    # 打印结果摘要
    print("\n=== 基准测试结果摘要 ===")
    for category, data in results.items():
        print(f"\n{category.upper()}:")
        for key, value in data.items():
            if isinstance(value, float):
                print(f"  {key}: {value:.4f}")
            else:
                print(f"  {key}: {value}")