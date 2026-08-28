"""
三种协作模式示例 - Three Collaboration Modes Examples
====================================================

演示三种不同的智能体协作模式：
1. 串行协作模式 (Sequential Collaboration)
2. 并行协作模式 (Parallel Collaboration)  
3. 混合协作模式 (Hybrid Collaboration)

Author: HC20251027
Date: 2025-11-06
"""

import asyncio
import logging
import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import uuid

# 框架集成
from agno_bmad_integration.framework import IntegrationFramework
from bmad.roles.analyst import AnalystAgent
from bmad.roles.pm import ProductManagerAgent
from bmad.roles.architect import ArchitectAgent
from bmad.roles.dev import DeveloperAgent
from bmad.roles.qa import QAAgent
from bmad.flows.workflow_engine import WorkflowEngine
from agno.memory.working import WorkingMemory


@dataclass
class CollaborationTask:
    """协作任务"""
    task_id: str
    name: str
    description: str
    assigned_agent: str
    input_data: Dict[str, Any] = field(default_factory=dict)
    output_data: Dict[str, Any] = field(default_factory=dict)
    status: str = "pending"  # pending, in_progress, completed, failed
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    dependencies: List[str] = field(default_factory=list)
    priority: str = "medium"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'task_id': self.task_id,
            'name': self.name,
            'description': self.description,
            'assigned_agent': self.assigned_agent,
            'input_data': self.input_data,
            'output_data': self.output_data,
            'status': self.status,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'dependencies': self.dependencies,
            'priority': self.priority
        }


@dataclass
class CollaborationSession:
    """协作会话"""
    session_id: str
    mode: str  # sequential, parallel, hybrid
    tasks: List[CollaborationTask] = field(default_factory=list)
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    status: str = "active"  # active, completed, failed
    results: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'session_id': self.session_id,
            'mode': self.mode,
            'tasks': [task.to_dict() for task in self.tasks],
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'status': self.status,
            'results': self.results
        }


class BaseCollaborationMode:
    """协作模式基类"""
    
    def __init__(self, mode_name: str):
        self.mode_name = mode_name
        self.logger = logging.getLogger(__name__)
        self.agents = self._initialize_agents()
        self.workflow_engine = WorkflowEngine()
        self.integration_framework = IntegrationFramework()
    
    def _initialize_agents(self) -> Dict[str, Any]:
        """初始化智能体"""
        return {
            'analyst': AnalystAgent(),
            'pm': ProductManagerAgent(),
            'architect': ArchitectAgent(),
            'developer': DeveloperAgent(),
            'qa': QAAgent()
        }
    
    async def execute_task(self, task: CollaborationTask) -> Dict[str, Any]:
        """执行单个任务"""
        start_time = time.time()
        
        try:
            task.status = "in_progress"
            task.start_time = datetime.now()
            
            self.logger.info(f"开始执行任务: {task.name} (智能体: {task.assigned_agent})")
            
            # 获取智能体
            agent = self.agents.get(task.assigned_agent)
            if not agent:
                raise ValueError(f"未找到智能体: {task.assigned_agent}")
            
            # 执行任务
            if hasattr(agent, 'analyze') and task.assigned_agent == 'analyst':
                result = await agent.analyze(task.input_data.get('prompt', ''))
            elif hasattr(agent, 'create_prd') and task.assigned_agent == 'pm':
                result = await agent.create_prd(task.input_data.get('prompt', ''))
            elif hasattr(agent, 'design_architecture') and task.assigned_agent == 'architect':
                result = await agent.design_architecture(task.input_data.get('requirements', ''))
            elif hasattr(agent, 'generate_code') and task.assigned_agent == 'developer':
                result = await agent.generate_code(task.input_data.get('specification', ''))
            elif hasattr(agent, 'create_test_plan') and task.assigned_agent == 'qa':
                result = await agent.create_test_plan(task.input_data.get('requirements', ''))
            else:
                # 默认执行
                result = f"任务 {task.name} 由 {task.assigned_agent} 执行完成"
            
            # 更新任务状态
            task.output_data = {'result': result}
            task.status = "completed"
            task.end_time = datetime.now()
            
            execution_time = time.time() - start_time
            self.logger.info(f"任务 {task.name} 完成，耗时: {execution_time:.2f}秒")
            
            return {
                'success': True,
                'task_id': task.task_id,
                'result': result,
                'execution_time': execution_time
            }
            
        except Exception as e:
            task.status = "failed"
            task.end_time = datetime.now()
            task.output_data = {'error': str(e)}
            
            self.logger.error(f"任务 {task.name} 执行失败: {e}")
            
            return {
                'success': False,
                'task_id': task.task_id,
                'error': str(e),
                'execution_time': time.time() - start_time
            }
    
    async def execute_session(self, session: CollaborationSession) -> Dict[str, Any]:
        """执行协作会话"""
        self.logger.info(f"开始执行 {self.mode_name} 协作会话: {session.session_id}")
        
        start_time = time.time()
        
        try:
            # 根据模式执行
            if self.mode_name == "sequential":
                result = await self._execute_sequential_mode(session)
            elif self.mode_name == "parallel":
                result = await self._execute_parallel_mode(session)
            elif self.mode_name == "hybrid":
                result = await self._execute_hybrid_mode(session)
            else:
                raise ValueError(f"不支持的协作模式: {self.mode_name}")
            
            # 更新会话状态
            session.status = "completed"
            session.end_time = datetime.now()
            session.results = result
            
            total_time = time.time() - start_time
            result['total_execution_time'] = total_time
            
            self.logger.info(f"{self.mode_name} 协作会话完成，耗时: {total_time:.2f}秒")
            
            return result
            
        except Exception as e:
            session.status = "failed"
            session.end_time = datetime.now()
            session.results = {'error': str(e)}
            
            self.logger.error(f"协作会话执行失败: {e}")
            
            return {
                'success': False,
                'error': str(e),
                'total_execution_time': time.time() - start_time
            }
    
    async def _execute_sequential_mode(self, session: CollaborationSession) -> Dict[str, Any]:
        """执行串行模式"""
        results = []
        
        for task in session.tasks:
            # 检查依赖
            if not self._check_dependencies(task, results):
                task.status = "failed"
                task.output_data = {'error': '依赖任务未完成'}
                continue
            
            result = await self.execute_task(task)
            results.append(result)
        
        return {
            'mode': 'sequential',
            'task_count': len(session.tasks),
            'completed_tasks': len([r for r in results if r.get('success')]),
            'failed_tasks': len([r for r in results if not r.get('success')]),
            'task_results': results
        }
    
    async def _execute_parallel_mode(self, session: CollaborationSession) -> Dict[str, Any]:
        """执行并行模式"""
        # 识别可以并行执行的任务
        parallel_task_groups = self._group_parallel_tasks(session.tasks)
        
        all_results = []
        
        for group in parallel_task_groups:
            if len(group) == 1:
                # 单个任务串行执行
                result = await self.execute_task(group[0])
                all_results.append(result)
            else:
                # 多个任务并行执行
                tasks = [self.execute_task(task) for task in group]
                group_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for i, result in enumerate(group_results):
                    if isinstance(result, Exception):
                        all_results.append({
                            'success': False,
                            'task_id': group[i].task_id,
                            'error': str(result)
                        })
                    else:
                        all_results.append(result)
        
        return {
            'mode': 'parallel',
            'task_count': len(session.tasks),
            'parallel_groups': len(parallel_task_groups),
            'completed_tasks': len([r for r in all_results if r.get('success')]),
            'failed_tasks': len([r for r in all_results if not r.get('success')]),
            'task_results': all_results
        }
    
    async def _execute_hybrid_mode(self, session: CollaborationSession) -> Dict[str, Any]:
        """执行混合模式"""
        # 智能分析任务依赖关系，动态决定执行策略
        execution_plan = self._create_hybrid_execution_plan(session.tasks)
        
        results = []
        
        for phase in execution_plan:
            if phase['type'] == 'parallel':
                # 并行执行阶段
                tasks = [self.execute_task(task) for task in phase['tasks']]
                phase_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for i, result in enumerate(phase_results):
                    if isinstance(result, Exception):
                        results.append({
                            'success': False,
                            'task_id': phase['tasks'][i].task_id,
                            'error': str(result)
                        })
                    else:
                        results.append(result)
            
            elif phase['type'] == 'sequential':
                # 串行执行阶段
                for task in phase['tasks']:
                    result = await self.execute_task(task)
                    results.append(result)
        
        return {
            'mode': 'hybrid',
            'task_count': len(session.tasks),
            'execution_phases': len(execution_plan),
            'completed_tasks': len([r for r in results if r.get('success')]),
            'failed_tasks': len([r for r in results if not r.get('success')]),
            'task_results': results,
            'execution_plan': execution_plan
        }
    
    def _check_dependencies(self, task: CollaborationTask, previous_results: List[Dict]) -> bool:
        """检查任务依赖"""
        if not task.dependencies:
            return True
        
        # 检查依赖的任务是否已完成
        completed_task_ids = {r['task_id'] for r in previous_results if r.get('success')}
        
        for dep_id in task.dependencies:
            if dep_id not in completed_task_ids:
                return False
        
        return True
    
    def _group_parallel_tasks(self, tasks: List[CollaborationTask]) -> List[List[CollaborationTask]]:
        """分组可以并行执行的任务"""
        groups = []
        remaining_tasks = tasks.copy()
        
        while remaining_tasks:
            current_group = []
            
            for task in remaining_tasks[:]:
                # 检查是否可以加入当前组
                can_add = True
                
                for group_task in current_group:
                    # 检查依赖关系
                    if (task.task_id in group_task.dependencies or 
                        group_task.task_id in task.dependencies):
                        can_add = False
                        break
                
                if can_add:
                    current_group.append(task)
                    remaining_tasks.remove(task)
            
            if current_group:
                groups.append(current_group)
            else:
                # 如果没有可并行的任务，单独执行
                groups.append([remaining_tasks.pop(0)])
        
        return groups
    
    def _create_hybrid_execution_plan(self, tasks: List[CollaborationTask]) -> List[Dict[str, Any]]:
        """创建混合执行计划"""
        # 分析任务图
        task_graph = self._build_task_graph(tasks)
        
        # 拓扑排序
        execution_order = self._topological_sort(task_graph)
        
        # 创建执行阶段
        phases = []
        current_phase = []
        
        for task_id in execution_order:
            task = next(t for t in tasks if t.task_id == task_id)
            
            # 检查是否可以并行执行
            can_parallel = self._can_execute_parallel(task, current_phase)
            
            if can_parallel and current_phase:
                # 完成当前阶段，开始新阶段
                phases.append({
                    'type': 'parallel' if len(current_phase) > 1 else 'sequential',
                    'tasks': current_phase.copy()
                })
                current_phase = [task]
            else:
                current_phase.append(task)
        
        # 添加最后一个阶段
        if current_phase:
            phases.append({
                'type': 'parallel' if len(current_phase) > 1 else 'sequential',
                'tasks': current_phase.copy()
            })
        
        return phases
    
    def _build_task_graph(self, tasks: List[CollaborationTask]) -> Dict[str, List[str]]:
        """构建任务依赖图"""
        graph = {task.task_id: [] for task in tasks}
        
        for task in tasks:
            for dep in task.dependencies:
                if dep in graph:
                    graph[dep].append(task.task_id)
        
        return graph
    
    def _topological_sort(self, graph: Dict[str, List[str]]) -> List[str]:
        """拓扑排序"""
        in_degree = {node: 0 for node in graph}
        for node in graph:
            for neighbor in graph[node]:
                in_degree[neighbor] = in_degree.get(neighbor, 0) + 1
        
        queue = [node for node in in_degree if in_degree[node] == 0]
        result = []
        
        while queue:
            node = queue.pop(0)
            result.append(node)
            
            for neighbor in graph[node]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        return result
    
    def _can_execute_parallel(self, task: CollaborationTask, current_phase: List[CollaborationTask]) -> bool:
        """检查任务是否可以在当前阶段并行执行"""
        # 检查依赖关系
        for phase_task in current_phase:
            if (task.task_id in phase_task.dependencies or 
                phase_task.task_id in task.dependencies):
                return False
        
        return True


class SequentialCollaborationMode(BaseCollaborationMode):
    """串行协作模式"""
    
    def __init__(self):
        super().__init__("sequential")
        self.logger.info("初始化串行协作模式")


class ParallelCollaborationMode(BaseCollaborationMode):
    """并行协作模式"""
    
    def __init__(self):
        super().__init__("parallel")
        self.logger.info("初始化并行协作模式")


class HybridCollaborationMode(BaseCollaborationMode):
    """混合协作模式"""
    
    def __init__(self):
        super().__init__("hybrid")
        self.logger.info("初始化混合协作模式")


class CollaborationModeDemo:
    """协作模式演示主类"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # 初始化协作模式
        self.modes = {
            'sequential': SequentialCollaborationMode(),
            'parallel': ParallelCollaborationMode(),
            'hybrid': HybridCollaborationMode()
        }
        
        # 演示项目数据
        self.demo_project = self._create_demo_project()
        
        # 集成框架
        self.integration_framework = IntegrationFramework()
    
    def _create_demo_project(self) -> Dict[str, Any]:
        """创建演示项目"""
        return {
            'name': '智能客服系统',
            'description': '基于AI的智能客服系统，支持多轮对话和情感分析',
            'requirements': [
                '用户可以通过文本或语音与系统交互',
                '系统能够理解用户意图并提供准确回答',
                '支持情感分析，根据用户情绪调整回复策略',
                '具备学习能力，能够从对话中不断优化',
                '提供管理后台，用于监控和配置'
            ]
        }
    
    async def run_sequential_demo(self) -> Dict[str, Any]:
        """运行串行协作演示"""
        self.logger.info("开始串行协作模式演示")
        
        # 创建串行任务
        tasks = [
            CollaborationTask(
                task_id="task_001",
                name="需求分析",
                description="分析智能客服系统的功能需求",
                assigned_agent="analyst",
                input_data={'prompt': f"请分析以下需求：{self.demo_project['requirements']}"}
            ),
            CollaborationTask(
                task_id="task_002", 
                name="产品设计",
                description="基于需求分析设计产品功能",
                assigned_agent="pm",
                dependencies=["task_001"],
                input_data={'prompt': '基于需求分析结果，设计产品功能架构'}
            ),
            CollaborationTask(
                task_id="task_003",
                name="技术架构设计",
                description="设计系统技术架构",
                assigned_agent="architect",
                dependencies=["task_002"],
                input_data={'requirements': '智能客服系统技术架构要求'}
            ),
            CollaborationTask(
                task_id="task_004",
                name="代码实现",
                description="实现系统核心功能",
                assigned_agent="developer",
                dependencies=["task_003"],
                input_data={'specification': '智能客服系统功能规格说明'}
            ),
            CollaborationTask(
                task_id="task_005",
                name="测试计划",
                description="制定系统测试计划",
                assigned_agent="qa",
                dependencies=["task_004"],
                input_data={'requirements': '智能客服系统测试要求'}
            )
        ]
        
        # 创建会话
        session = CollaborationSession(
            session_id=str(uuid.uuid4()),
            mode="sequential",
            tasks=tasks
        )
        
        # 执行会话
        result = await self.modes['sequential'].execute_session(session)
        
        return {
            'mode': 'sequential',
            'project': self.demo_project,
            'session': session.to_dict(),
            'result': result
        }
    
    async def run_parallel_demo(self) -> Dict[str, Any]:
        """运行并行协作演示"""
        self.logger.info("开始并行协作模式演示")
        
        # 创建并行任务（无依赖关系）
        tasks = [
            CollaborationTask(
                task_id="parallel_001",
                name="竞品分析",
                description="分析市场上现有的智能客服产品",
                assigned_agent="analyst",
                input_data={'prompt': '分析智能客服市场的竞品情况'}
            ),
            CollaborationTask(
                task_id="parallel_002",
                name="用户调研",
                description="调研目标用户的需求和痛点",
                assigned_agent="pm",
                input_data={'prompt': '进行智能客服系统用户需求调研'}
            ),
            CollaborationTask(
                task_id="parallel_003",
                name="技术选型",
                description="确定系统技术栈和架构方案",
                assigned_agent="architect",
                input_data={'requirements': '智能客服系统技术选型要求'}
            ),
            CollaborationTask(
                task_id="parallel_004",
                name="原型设计",
                description="设计系统用户界面原型",
                assigned_agent="developer",
                input_data={'specification': '智能客服系统界面设计要求'}
            )
        ]
        
        # 创建会话
        session = CollaborationSession(
            session_id=str(uuid.uuid4()),
            mode="parallel",
            tasks=tasks
        )
        
        # 执行会话
        result = await self.modes['parallel'].execute_session(session)
        
        return {
            'mode': 'parallel',
            'project': self.demo_project,
            'session': session.to_dict(),
            'result': result
        }
    
    async def run_hybrid_demo(self) -> Dict[str, Any]:
        """运行混合协作演示"""
        self.logger.info("开始混合协作模式演示")
        
        # 创建混合任务（有部分依赖关系）
        tasks = [
            CollaborationTask(
                task_id="hybrid_001",
                name="需求收集",
                description="收集和分析系统需求",
                assigned_agent="analyst",
                input_data={'prompt': f"收集智能客服系统需求：{self.demo_project['requirements']}"}
            ),
            CollaborationTask(
                task_id="hybrid_002",
                name="市场调研",
                description="调研市场和用户需求",
                assigned_agent="pm",
                input_data={'prompt': '进行智能客服市场和用户调研'}
            ),
            CollaborationTask(
                task_id="hybrid_003",
                name="产品规划",
                description="基于需求和市场调研制定产品规划",
                assigned_agent="pm",
                dependencies=["hybrid_001", "hybrid_002"],
                input_data={'prompt': '制定智能客服系统产品规划'}
            ),
            CollaborationTask(
                task_id="hybrid_004",
                name="架构设计",
                description="设计系统技术架构",
                assigned_agent="architect",
                dependencies=["hybrid_003"],
                input_data={'requirements': '智能客服系统技术架构设计'}
            ),
            CollaborationTask(
                task_id="hybrid_005",
                name="API设计",
                description="设计系统API接口",
                assigned_agent="architect",
                dependencies=["hybrid_004"],
                input_data={'requirements': '智能客服系统API设计要求'}
            ),
            CollaborationTask(
                task_id="hybrid_006",
                name="核心模块开发",
                description="开发系统核心功能模块",
                assigned_agent="developer",
                dependencies=["hybrid_004", "hybrid_005"],
                input_data={'specification': '智能客服系统核心功能开发'}
            ),
            CollaborationTask(
                task_id="hybrid_007",
                name="界面开发",
                description="开发用户界面",
                assigned_agent="developer",
                dependencies=["hybrid_005"],
                input_data={'specification': '智能客服系统界面开发'}
            ),
            CollaborationTask(
                task_id="hybrid_008",
                name="测试计划",
                description="制定系统测试计划",
                assigned_agent="qa",
                dependencies=["hybrid_006", "hybrid_007"],
                input_data={'requirements': '智能客服系统测试计划'}
            )
        ]
        
        # 创建会话
        session = CollaborationSession(
            session_id=str(uuid.uuid4()),
            mode="hybrid",
            tasks=tasks
        )
        
        # 执行会话
        result = await self.modes['hybrid'].execute_session(session)
        
        return {
            'mode': 'hybrid',
            'project': self.demo_project,
            'session': session.to_dict(),
            'result': result
        }
    
    async def run_all_demos(self) -> Dict[str, Any]:
        """运行所有协作模式演示"""
        self.logger.info("开始运行所有协作模式演示")
        
        results = {}
        
        # 串行模式演示
        try:
            results['sequential'] = await self.run_sequential_demo()
        except Exception as e:
            self.logger.error(f"串行模式演示失败: {e}")
            results['sequential'] = {'error': str(e)}
        
        # 并行模式演示
        try:
            results['parallel'] = await self.run_parallel_demo()
        except Exception as e:
            self.logger.error(f"并行模式演示失败: {e}")
            results['parallel'] = {'error': str(e)}
        
        # 混合模式演示
        try:
            results['hybrid'] = await self.run_hybrid_demo()
        except Exception as e:
            self.logger.error(f"混合模式演示失败: {e}")
            results['hybrid'] = {'error': str(e)}
        
        # 生成对比分析
        comparison = self._generate_comparison_analysis(results)
        
        return {
            'timestamp': datetime.now().isoformat(),
            'demo_project': self.demo_project,
            'results': results,
            'comparison': comparison
        }
    
    def _generate_comparison_analysis(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """生成对比分析"""
        comparison = {
            'execution_time': {},
            'task_completion': {},
            'efficiency_analysis': {},
            'use_case_recommendations': {}
        }
        
        for mode, result in results.items():
            if 'result' in result and 'total_execution_time' in result['result']:
                comparison['execution_time'][mode] = result['result']['total_execution_time']
                comparison['task_completion'][mode] = {
                    'completed': result['result'].get('completed_tasks', 0),
                    'failed': result['result'].get('failed_tasks', 0),
                    'total': result['result'].get('task_count', 0)
                }
        
        # 效率分析
        if comparison['execution_time']:
            fastest_mode = min(comparison['execution_time'], key=comparison['execution_time'].get)
            comparison['efficiency_analysis'] = {
                'fastest_mode': fastest_mode,
                'speed_comparison': comparison['execution_time']
            }
        
        # 使用场景推荐
        comparison['use_case_recommendations'] = {
            'sequential': {
                'description': '适用于任务间有严格依赖关系的项目',
                'best_for': ['复杂系统设计', '需要严格流程控制的项目', '高风险项目'],
                'advantages': ['流程清晰', '质量控制好', '风险可控'],
                'disadvantages': ['执行时间长', '资源利用不充分']
            },
            'parallel': {
                'description': '适用于任务间相互独立的项目',
                'best_for': ['市场调研', '竞品分析', '独立功能开发'],
                'advantages': ['执行速度快', '资源利用充分', '可扩展性好'],
                'disadvantages': ['协调复杂', '依赖管理困难']
            },
            'hybrid': {
                'description': '适用于复杂项目，平衡效率和风险',
                'best_for': ['大型项目', '敏捷开发', '迭代开发'],
                'advantages': ['灵活高效', '风险可控', '适应性强'],
                'disadvantages': ['复杂度高', '需要经验丰富的团队']
            }
        }
        
        return comparison
    
    def get_demo_statistics(self) -> Dict[str, Any]:
        """获取演示统计信息"""
        return {
            'supported_modes': ['sequential', 'parallel', 'hybrid'],
            'available_agents': ['analyst', 'pm', 'architect', 'developer', 'qa'],
            'demo_capabilities': [
                '智能任务分配',
                '依赖关系管理',
                '动态执行策略',
                '性能监控',
                '结果分析'
            ],
            'collaboration_features': {
                'sequential': ['严格流程控制', '质量保证', '风险控制'],
                'parallel': ['快速执行', '资源优化', '并行处理'],
                'hybrid': ['智能调度', '灵活适应', '效率平衡']
            }
        }