"""
Agno多智能体框架 - 工作流引擎
负责任务流的编排、执行和监控
"""

import asyncio
import json
import uuid
from typing import Dict, List, Optional, Any, Callable, Set
from datetime import datetime, timedelta
from enum import Enum
import logging
from abc import ABC, abstractmethod

from ..agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)


class WorkflowStatus(Enum):
    """工作流状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    SKIPPED = "skipped"


class WorkflowStep:
    """工作流步骤"""
    
    def __init__(
        self,
        step_id: str,
        name: str,
        step_type: str,
        config: Dict[str, Any],
        dependencies: Optional[List[str]] = None,
        timeout: Optional[int] = None,
        retry_count: int = 0,
        on_failure: Optional[str] = None
    ):
        self.id = step_id
        self.name = name
        self.type = step_type
        self.config = config
        self.dependencies = dependencies or []
        self.timeout = timeout
        self.retry_count = retry_count
        self.on_failure = on_failure
        
        # 状态
        self.status = TaskStatus.PENDING
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.result: Optional[Dict[str, Any]] = None
        self.error: Optional[str] = None
        self.attempt_count = 0
        
        # 执行上下文
        self.context: Dict[str, Any] = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "config": self.config,
            "dependencies": self.dependencies,
            "timeout": self.timeout,
            "retry_count": self.retry_count,
            "on_failure": self.on_failure,
            "status": self.status.value,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "result": self.result,
            "error": self.error,
            "attempt_count": self.attempt_count,
            "context": self.context
        }


class Workflow:
    """工作流"""
    
    def __init__(
        self,
        workflow_id: str,
        name: str,
        description: str = "",
        steps: Optional[List[WorkflowStep]] = None
    ):
        self.id = workflow_id
        self.name = name
        self.description = description
        self.steps = steps or []
        
        # 状态
        self.status = WorkflowStatus.PENDING
        self.created_at = datetime.now()
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        
        # 执行上下文
        self.context: Dict[str, Any] = {}
        self.global_variables: Dict[str, Any] = {}
        
        # 统计信息
        self.completed_steps = 0
        self.failed_steps = 0
        self.total_execution_time = 0.0
        
        # 监听器
        self.listeners: List[Callable] = []
    
    def add_step(self, step: WorkflowStep) -> None:
        """添加步骤"""
        self.steps.append(step)
    
    def get_step(self, step_id: str) -> Optional[WorkflowStep]:
        """获取步骤"""
        for step in self.steps:
            if step.id == step_id:
                return step
        return None
    
    def get_ready_steps(self) -> List[WorkflowStep]:
        """获取可执行的步骤"""
        ready_steps = []
        
        for step in self.steps:
            if step.status != TaskStatus.PENDING:
                continue
            
            # 检查依赖
            dependencies_met = True
            for dep_id in step.dependencies:
                dep_step = self.get_step(dep_id)
                if not dep_step or dep_step.status != TaskStatus.COMPLETED:
                    dependencies_met = False
                    break
            
            if dependencies_met:
                ready_steps.append(step)
        
        return ready_steps
    
    def is_completed(self) -> bool:
        """检查是否完成"""
        return self.status in [WorkflowStatus.COMPLETED, WorkflowStatus.FAILED, WorkflowStatus.CANCELLED]
    
    def get_progress(self) -> Dict[str, Any]:
        """获取进度"""
        total_steps = len(self.steps)
        if total_steps == 0:
            return {"progress": 0.0, "completed": 0, "total": 0}
        
        completed = sum(1 for step in self.steps if step.status == TaskStatus.COMPLETED)
        failed = sum(1 for step in self.steps if step.status == TaskStatus.FAILED)
        
        return {
            "progress": (completed + failed) / total_steps,
            "completed": completed,
            "failed": failed,
            "total": total_steps
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "context": self.context,
            "global_variables": self.global_variables,
            "steps": [step.to_dict() for step in self.steps],
            "progress": self.get_progress(),
            "statistics": {
                "completed_steps": self.completed_steps,
                "failed_steps": self.failed_steps,
                "total_execution_time": self.total_execution_time
            }
        }


class WorkflowEngine:
    """工作流引擎"""
    
    def __init__(self):
        self.workflows: Dict[str, Workflow] = {}
        self.active_workflows: Dict[str, Workflow] = {}
        self.agents: Dict[str, BaseAgent] = {}
        self.step_executors: Dict[str, Callable] = {}
        
        # 配置
        self.config = {
            "max_concurrent_workflows": 10,
            "max_concurrent_steps": 5,
            "step_timeout": 300,  # 5分钟
            "workflow_timeout": 3600,  # 1小时
            "retry_delay": 5,  # 5秒
            "cleanup_interval": 3600  # 1小时
        }
        
        # 统计信息
        self.stats = {
            "total_workflows": 0,
            "completed_workflows": 0,
            "failed_workflows": 0,
            "total_steps": 0,
            "completed_steps": 0,
            "failed_steps": 0,
            "average_execution_time": 0.0
        }
        
        # 后台任务
        self._cleanup_task: Optional[asyncio.Task] = None
    
    async def initialize(self) -> None:
        """初始化工作流引擎"""
        try:
            # 注册默认步骤执行器
            await self._register_default_executors()
            
            # 启动清理任务
            self._cleanup_task = asyncio.create_task(self._cleanup_task_loop())
            
            logger.info("工作流引擎初始化完成")
        except Exception as e:
            logger.error(f"工作流引擎初始化失败: {e}")
            raise
    
    async def shutdown(self) -> None:
        """关闭工作流引擎"""
        try:
            # 取消清理任务
            if self._cleanup_task:
                self._cleanup_task.cancel()
            
            # 等待所有工作流完成
            for workflow in list(self.active_workflows.values()):
                await self.cancel_workflow(workflow.id)
            
            logger.info("工作流引擎已关闭")
        except Exception as e:
            logger.error(f"工作流引擎关闭失败: {e}")
    
    async def create_workflow(
        self,
        name: str,
        description: str = "",
        steps: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """创建工作流"""
        try:
            workflow_id = str(uuid.uuid4())
            
            # 创建步骤对象
            workflow_steps = []
            if steps:
                for step_config in steps:
                    step = WorkflowStep(
                        step_id=step_config.get("id", str(uuid.uuid4())),
                        name=step_config.get("name", "Step"),
                        step_type=step_config.get("type", "task"),
                        config=step_config.get("config", {}),
                        dependencies=step_config.get("dependencies", []),
                        timeout=step_config.get("timeout"),
                        retry_count=step_config.get("retry_count", 0),
                        on_failure=step_config.get("on_failure")
                    )
                    workflow_steps.append(step)
            
            # 创建工作流
            workflow = Workflow(
                workflow_id=workflow_id,
                name=name,
                description=description,
                steps=workflow_steps
            )
            
            self.workflows[workflow_id] = workflow
            self.stats["total_workflows"] += 1
            self.stats["total_steps"] += len(workflow_steps)
            
            logger.info(f"工作流已创建: {name} ({workflow_id})")
            return workflow_id
            
        except Exception as e:
            logger.error(f"创建工作流失败: {e}")
            raise
    
    async def start_workflow(self, workflow_id: str) -> bool:
        """启动工作流"""
        try:
            if workflow_id not in self.workflows:
                logger.error(f"工作流不存在: {workflow_id}")
                return False
            
            if len(self.active_workflows) >= self.config["max_concurrent_workflows"]:
                logger.error("达到最大并发工作流限制")
                return False
            
            workflow = self.workflows[workflow_id]
            
            if workflow.status != WorkflowStatus.PENDING:
                logger.warning(f"工作流状态不正确: {workflow.status}")
                return False
            
            # 启动工作流
            workflow.status = WorkflowStatus.RUNNING
            workflow.start_time = datetime.now()
            self.active_workflows[workflow_id] = workflow
            
            # 异步执行工作流
            asyncio.create_task(self._execute_workflow(workflow))
            
            logger.info(f"工作流已启动: {workflow.name} ({workflow_id})")
            return True
            
        except Exception as e:
            logger.error(f"启动工作流失败: {workflow_id} - {e}")
            return False
    
    async def execute_workflow(self, name: str, description: str = "", 
                             steps: Optional[List[Dict[str, Any]]] = None) -> str:
        """创建并执行工作流"""
        try:
            # 创建工作流
            workflow_id = await self.create_workflow(name, description, steps)
            
            # 启动工作流
            success = await self.start_workflow(workflow_id)
            if not success:
                raise Exception("工作流启动失败")
            
            return workflow_id
            
        except Exception as e:
            logger.error(f"执行工作流失败: {e}")
            raise
    
    async def get_workflow_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """获取工作流状态"""
        try:
            if workflow_id in self.workflows:
                return self.workflows[workflow_id].to_dict()
            return None
            
        except Exception as e:
            logger.error(f"获取工作流状态失败: {workflow_id} - {e}")
            return None
    
    async def cancel_workflow(self, workflow_id: str) -> bool:
        """取消工作流"""
        try:
            if workflow_id not in self.workflows:
                return False
            
            workflow = self.workflows[workflow_id]
            
            if workflow.status not in [WorkflowStatus.RUNNING, WorkflowStatus.PAUSED]:
                return False
            
            # 取消工作流
            workflow.status = WorkflowStatus.CANCELLED
            workflow.end_time = datetime.now()
            
            # 从活跃工作流中移除
            if workflow_id in self.active_workflows:
                del self.active_workflows[workflow_id]
            
            # 取消所有正在运行的任务
            for step in workflow.steps:
                if step.status == TaskStatus.RUNNING:
                    step.status = TaskStatus.CANCELLED
                    step.end_time = datetime.now()
            
            logger.info(f"工作流已取消: {workflow.name} ({workflow_id})")
            return True
            
        except Exception as e:
            logger.error(f"取消工作流失败: {workflow_id} - {e}")
            return False
    
    async def pause_workflow(self, workflow_id: str) -> bool:
        """暂停工作流"""
        try:
            if workflow_id not in self.workflows:
                return False
            
            workflow = self.workflows[workflow_id]
            
            if workflow.status != WorkflowStatus.RUNNING:
                return False
            
            workflow.status = WorkflowStatus.PAUSED
            
            logger.info(f"工作流已暂停: {workflow.name} ({workflow_id})")
            return True
            
        except Exception as e:
            logger.error(f"暂停工作流失败: {workflow_id} - {e}")
            return False
    
    async def resume_workflow(self, workflow_id: str) -> bool:
        """恢复工作流"""
        try:
            if workflow_id not in self.workflows:
                return False
            
            workflow = self.workflows[workflow_id]
            
            if workflow.status != WorkflowStatus.PAUSED:
                return False
            
            workflow.status = WorkflowStatus.RUNNING
            
            # 重新执行工作流
            asyncio.create_task(self._execute_workflow(workflow))
            
            logger.info(f"工作流已恢复: {workflow.name} ({workflow_id})")
            return True
            
        except Exception as e:
            logger.error(f"恢复工作流失败: {workflow_id} - {e}")
            return False
    
    async def register_agent(self, agent: BaseAgent) -> None:
        """注册智能体"""
        self.agents[agent.agent_id] = agent
        logger.info(f"智能体已注册: {agent.name} ({agent.agent_id})")
    
    async def unregister_agent(self, agent_id: str) -> bool:
        """注销智能体"""
        if agent_id in self.agents:
            del self.agents[agent_id]
            logger.info(f"智能体已注销: {agent_id}")
            return True
        return False
    
    async def register_step_executor(self, step_type: str, executor: Callable) -> None:
        """注册步骤执行器"""
        self.step_executors[step_type] = executor
        logger.info(f"步骤执行器已注册: {step_type}")
    
    async def get_workflow_statistics(self) -> Dict[str, Any]:
        """获取工作流统计信息"""
        return {
            "total_workflows": self.stats["total_workflows"],
            "active_workflows": len(self.active_workflows),
            "completed_workflows": self.stats["completed_workflows"],
            "failed_workflows": self.stats["failed_workflows"],
            "total_steps": self.stats["total_steps"],
            "completed_steps": self.stats["completed_steps"],
            "failed_steps": self.stats["failed_steps"],
            "average_execution_time": self.stats["average_execution_time"],
            "config": self.config,
            "registered_agents": len(self.agents),
            "registered_executors": len(self.step_executors)
        }
    
    async def _execute_workflow(self, workflow: Workflow) -> None:
        """执行工作流"""
        try:
            logger.info(f"开始执行工作流: {workflow.name}")
            
            while workflow.status == WorkflowStatus.RUNNING:
                # 检查工作流超时
                if workflow.start_time:
                    elapsed = (datetime.now() - workflow.start_time).total_seconds()
                    if elapsed > self.config["workflow_timeout"]:
                        workflow.status = WorkflowStatus.FAILED
                        workflow.end_time = datetime.now()
                        break
                
                # 获取可执行的步骤
                ready_steps = workflow.get_ready_steps()
                
                if not ready_steps:
                    # 没有可执行的步骤，检查是否完成
                    if all(step.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED] 
                           for step in workflow.steps):
                        # 工作流完成
                        failed_steps = [step for step in workflow.steps if step.status == TaskStatus.FAILED]
                        if failed_steps:
                            workflow.status = WorkflowStatus.FAILED
                        else:
                            workflow.status = WorkflowStatus.COMPLETED
                        workflow.end_time = datetime.now()
                        break
                    else:
                        # 等待
                        await asyncio.sleep(1)
                        continue
                
                # 限制并发步骤数
                running_steps = [step for step in workflow.steps if step.status == TaskStatus.RUNNING]
                if len(running_steps) >= self.config["max_concurrent_steps"]:
                    await asyncio.sleep(1)
                    continue
                
                # 执行可用的步骤
                available_slots = self.config["max_concurrent_steps"] - len(running_steps)
                steps_to_execute = ready_steps[:available_slots]
                
                for step in steps_to_execute:
                    asyncio.create_task(self._execute_step(workflow, step))
            
            # 更新统计
            if workflow.status == WorkflowStatus.COMPLETED:
                self.stats["completed_workflows"] += 1
            elif workflow.status == WorkflowStatus.FAILED:
                self.stats["failed_workflows"] += 1
            
            # 从活跃工作流中移除
            if workflow.id in self.active_workflows:
                del self.active_workflows[workflow.id]
            
            logger.info(f"工作流执行完成: {workflow.name} - {workflow.status.value}")
            
        except Exception as e:
            logger.error(f"工作流执行异常: {workflow.name} - {e}")
            workflow.status = WorkflowStatus.FAILED
            workflow.end_time = datetime.now()
    
    async def _execute_step(self, workflow: Workflow, step: WorkflowStep) -> None:
        """执行步骤"""
        try:
            step.status = TaskStatus.RUNNING
            step.start_time = datetime.now()
            step.attempt_count += 1
            
            logger.info(f"开始执行步骤: {step.name} ({step.id})")
            
            # 检查是否有对应的执行器
            if step.type not in self.step_executors:
                raise Exception(f"未找到步骤执行器: {step.type}")
            
            # 执行步骤
            executor = self.step_executors[step.type]
            result = await executor(workflow, step)
            
            # 处理结果
            step.result = result
            step.status = TaskStatus.COMPLETED
            step.end_time = datetime.now()
            
            # 更新工作流上下文
            workflow.context.update(result.get("context", {}))
            
            workflow.completed_steps += 1
            self.stats["completed_steps"] += 1
            
            logger.info(f"步骤执行完成: {step.name}")
            
        except Exception as e:
            logger.error(f"步骤执行失败: {step.name} - {e}")
            
            step.error = str(e)
            
            # 检查重试次数
            if step.attempt_count <= step.retry_count:
                # 重试
                step.status = TaskStatus.PENDING
                await asyncio.sleep(self.config["retry_delay"])
                await self._execute_step(workflow, step)
            else:
                # 失败
                step.status = TaskStatus.FAILED
                step.end_time = datetime.now()
                
                workflow.failed_steps += 1
                self.stats["failed_steps"] += 1
                
                # 处理失败策略
                if step.on_failure == "cancel_workflow":
                    workflow.status = WorkflowStatus.FAILED
                    workflow.end_time = datetime.now()
                elif step.on_failure == "skip":
                    step.status = TaskStatus.SKIPPED
    
    async def _register_default_executors(self) -> None:
        """注册默认执行器"""
        # 任务执行器
        await self.register_step_executor("task", self._execute_task_step)
        
        # 条件执行器
        await self.register_step_executor("condition", self._execute_condition_step)
        
        # 并行执行器
        await self.register_step_executor("parallel", self._execute_parallel_step)
        
        # 循环执行器
        await self.register_step_executor("loop", self._execute_loop_step)
        
        # 等待执行器
        await self.register_step_executor("wait", self._execute_wait_step)
        
        # 通知执行器
        await self.register_step_executor("notify", self._execute_notify_step)
    
    async def _execute_task_step(self, workflow: Workflow, step: WorkflowStep) -> Dict[str, Any]:
        """执行任务步骤"""
        # 获取智能体
        agent_id = step.config.get("agent_id")
        if agent_id not in self.agents:
            raise Exception(f"智能体未注册: {agent_id}")
        
        agent = self.agents[agent_id]
        
        # 创建任务
        task = {
            "task_id": step.id,
            "type": step.config.get("task_type", "general"),
            "content": step.config.get("content", {}),
            "priority": step.config.get("priority", "normal")
        }
        
        # 执行任务
        result = await agent.execute_task(task)
        
        return {
            "status": "completed",
            "result": result,
            "context": {f"step_{step.id}_result": result}
        }
    
    async def _execute_condition_step(self, workflow: Workflow, step: WorkflowStep) -> Dict[str, Any]:
        """执行条件步骤"""
        condition = step.config.get("condition", "")
        
        # 简单的条件评估（实际应用中应该使用更复杂的表达式引擎）
        try:
            # 在工作流上下文中评估条件
            context = {**workflow.context, **workflow.global_variables}
            result = eval(condition, {"__builtins__": {}}, context)
            
            return {
                "status": "completed",
                "result": {"condition_result": result},
                "context": {f"step_{step.id}_condition": result}
            }
        except Exception as e:
            raise Exception(f"条件评估失败: {e}")
    
    async def _execute_parallel_step(self, workflow: Workflow, step: WorkflowStep) -> Dict[str, Any]:
        """执行并行步骤"""
        sub_steps_config = step.config.get("steps", [])
        
        # 创建子工作流
        sub_workflow_id = await self.create_workflow(
            name=f"{workflow.name}_sub_{step.id}",
            steps=sub_steps_config
        )
        
        # 启动子工作流
        await self.start_workflow(sub_workflow_id)
        
        # 等待子工作流完成
        while True:
            sub_status = await self.get_workflow_status(sub_workflow_id)
            if sub_status and sub_status["status"] in ["completed", "failed", "cancelled"]:
                break
            await asyncio.sleep(1)
        
        return {
            "status": "completed",
            "result": sub_status,
            "context": {f"step_{step.id}_sub_workflow": sub_workflow_id}
        }
    
    async def _execute_loop_step(self, workflow: Workflow, step: WorkflowStep) -> Dict[str, Any]:
        """执行循环步骤"""
        loop_config = step.config.get("loop", {})
        loop_type = loop_config.get("type", "count")  # count, condition, collection
        max_iterations = loop_config.get("max_iterations", 10)
        
        results = []
        
        if loop_type == "count":
            for i in range(max_iterations):
                iteration_result = await self._execute_loop_iteration(workflow, step, i)
                results.append(iteration_result)
        
        elif loop_type == "condition":
            iteration = 0
            while iteration < max_iterations:
                condition_result = await self._execute_condition_step(workflow, step)
                if not condition_result["result"]["condition_result"]:
                    break
                
                iteration_result = await self._execute_loop_iteration(workflow, step, iteration)
                results.append(iteration_result)
                iteration += 1
        
        return {
            "status": "completed",
            "result": {"iterations": results},
            "context": {f"step_{step.id}_loop_results": results}
        }
    
    async def _execute_loop_iteration(self, workflow: Workflow, step: WorkflowStep, iteration: int) -> Dict[str, Any]:
        """执行循环迭代"""
        iteration_steps = step.config.get("iteration_steps", [])
        
        # 创建迭代工作流
        iteration_workflow_id = await self.create_workflow(
            name=f"{workflow.name}_iteration_{iteration}",
            steps=iteration_steps
        )
        
        # 启动迭代工作流
        await self.start_workflow(iteration_workflow_id)
        
        # 等待完成
        while True:
            status = await self.get_workflow_status(iteration_workflow_id)
            if status and status["status"] in ["completed", "failed", "cancelled"]:
                return status
            await asyncio.sleep(1)
    
    async def _execute_wait_step(self, workflow: Workflow, step: WorkflowStep) -> Dict[str, Any]:
        """执行等待步骤"""
        wait_config = step.config.get("wait", {})
        duration = wait_config.get("duration", 5)  # 秒
        
        await asyncio.sleep(duration)
        
        return {
            "status": "completed",
            "result": {"waited_duration": duration},
            "context": {f"step_{step.id}_waited": duration}
        }
    
    async def _execute_notify_step(self, workflow: Workflow, step: WorkflowStep) -> Dict[str, Any]:
        """执行通知步骤"""
        notify_config = step.config.get("notify", {})
        message = notify_config.get("message", "")
        recipients = notify_config.get("recipients", [])
        
        # 这里应该实现实际的通知逻辑
        logger.info(f"通知: {message} -> {recipients}")
        
        return {
            "status": "completed",
            "result": {"message": message, "recipients": recipients},
            "context": {f"step_{step.id}_notified": True}
        }
    
    async def _cleanup_task_loop(self) -> None:
        """清理任务循环"""
        while True:
            try:
                await asyncio.sleep(self.config["cleanup_interval"])
                
                # 清理已完成的工作流
                completed_workflows = [
                    workflow_id for workflow_id, workflow in self.workflows.items()
                    if workflow.is_completed() and workflow_id not in self.active_workflows
                ]
                
                for workflow_id in completed_workflows:
                    # 保留最近的工作流记录
                    workflow = self.workflows[workflow_id]
                    if (datetime.now() - workflow.end_time).days > 1:
                        del self.workflows[workflow_id]
                
                logger.info(f"清理完成，移除了 {len(completed_workflows)} 个工作流")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"清理任务错误: {e}")