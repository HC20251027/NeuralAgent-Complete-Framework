"""
Agno多智能体框架 - 任务调度器
负责任务的调度和分发
"""

import asyncio
import uuid
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from enum import Enum
import heapq
import logging

from ..agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)


class TaskPriority(Enum):
    """任务优先级"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4
    CRITICAL = 5


class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"
    SCHEDULED = "scheduled"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class ScheduledTask:
    """调度任务"""
    
    def __init__(
        self,
        task_id: str,
        task_data: Dict[str, Any],
        priority: TaskPriority,
        scheduled_time: datetime,
        timeout: Optional[int] = None,
        retry_count: int = 0,
        max_retries: int = 3,
        callback: Optional[Callable] = None
    ):
        self.id = task_id
        self.data = task_data
        self.priority = priority
        self.scheduled_time = scheduled_time
        self.timeout = timeout
        self.retry_count = retry_count
        self.max_retries = max_retries
        self.callback = callback
        
        # 状态
        self.status = TaskStatus.PENDING
        self.created_at = datetime.now()
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.result: Optional[Dict[str, Any]] = None
        self.error: Optional[str] = None
        
        # 调度优先级（用于堆排序）
        self._scheduling_key = (scheduled_time.timestamp(), -priority.value)
    
    def __lt__(self, other):
        """比较操作符，用于优先队列排序"""
        return self._scheduling_key < other._scheduling_key
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "data": self.data,
            "priority": self.priority.name,
            "scheduled_time": self.scheduled_time.isoformat(),
            "timeout": self.timeout,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "result": self.result,
            "error": self.error
        }


class TaskScheduler:
    """任务调度器"""
    
    def __init__(self):
        # 任务存储
        self.pending_tasks: List[ScheduledTask] = []  # 优先队列
        self.running_tasks: Dict[str, ScheduledTask] = {}
        self.completed_tasks: Dict[str, ScheduledTask] = {}
        
        # 智能体池
        self.available_agents: Dict[str, BaseAgent] = {}
        self.busy_agents: Dict[str, BaseAgent] = {}
        
        # 调度配置
        self.config = {
            "max_concurrent_tasks": 10,
            "task_timeout": 300,  # 5分钟
            "agent_check_interval": 1,  # 1秒
            "cleanup_interval": 3600,  # 1小时
            "max_completed_tasks": 1000
        }
        
        # 统计信息
        self.stats = {
            "total_scheduled": 0,
            "total_completed": 0,
            "total_failed": 0,
            "total_cancelled": 0,
            "average_execution_time": 0.0,
            "agent_utilization": {}
        }
        
        # 后台任务
        self._scheduler_task: Optional[asyncio.Task] = None
        self._cleanup_task: Optional[asyncio.Task] = None
        self._running = False
    
    async def initialize(self) -> None:
        """初始化调度器"""
        try:
            self._running = True
            
            # 启动后台任务
            self._scheduler_task = asyncio.create_task(self._scheduler_loop())
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
            
            logger.info("任务调度器初始化完成")
        except Exception as e:
            logger.error(f"任务调度器初始化失败: {e}")
            raise
    
    async def shutdown(self) -> None:
        """关闭调度器"""
        try:
            self._running = False
            
            # 取消后台任务
            if self._scheduler_task:
                self._scheduler_task.cancel()
            if self._cleanup_task:
                self._cleanup_task.cancel()
            
            # 等待任务完成
            if self._scheduler_task:
                try:
                    await self._scheduler_task
                except asyncio.CancelledError:
                    pass
            
            if self._cleanup_task:
                try:
                    await self._cleanup_task
                except asyncio.CancelledError:
                    pass
            
            # 取消所有运行中的任务
            for task in list(self.running_tasks.values()):
                await self.cancel_task(task.id)
            
            logger.info("任务调度器已关闭")
        except Exception as e:
            logger.error(f"任务调度器关闭失败: {e}")
    
    async def schedule_task(
        self,
        task_data: Dict[str, Any],
        priority: TaskPriority = TaskPriority.NORMAL,
        delay: Optional[int] = None,
        scheduled_time: Optional[datetime] = None,
        timeout: Optional[int] = None,
        max_retries: int = 3,
        callback: Optional[Callable] = None
    ) -> str:
        """调度任务"""
        try:
            task_id = str(uuid.uuid4())
            
            # 确定调度时间
            if scheduled_time:
                schedule_time = scheduled_time
            elif delay:
                schedule_time = datetime.now() + timedelta(seconds=delay)
            else:
                schedule_time = datetime.now()
            
            # 创建调度任务
            scheduled_task = ScheduledTask(
                task_id=task_id,
                task_data=task_data,
                priority=priority,
                scheduled_time=schedule_time,
                timeout=timeout or self.config["task_timeout"],
                max_retries=max_retries,
                callback=callback
            )
            
            # 添加到待执行队列
            heapq.heappush(self.pending_tasks, scheduled_task)
            
            # 更新统计
            self.stats["total_scheduled"] += 1
            
            logger.info(f"任务已调度: {task_id} (优先级: {priority.name})")
            return task_id
            
        except Exception as e:
            logger.error(f"调度任务失败: {e}")
            raise
    
    async def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        try:
            # 检查待执行队列
            for i, task in enumerate(self.pending_tasks):
                if task.id == task_id:
                    task.status = TaskStatus.CANCELLED
                    task.end_time = datetime.now()
                    heapq.heappop(self.pending_tasks)
                    
                    self.stats["total_cancelled"] += 1
                    logger.info(f"任务已取消: {task_id}")
                    return True
            
            # 检查运行中的任务
            if task_id in self.running_tasks:
                task = self.running_tasks[task_id]
                task.status = TaskStatus.CANCELLED
                task.end_time = datetime.now()
                
                # 释放智能体
                agent_id = task.data.get("agent_id")
                if agent_id and agent_id in self.busy_agents:
                    self.available_agents[agent_id] = self.busy_agents.pop(agent_id)
                
                self.stats["total_cancelled"] += 1
                logger.info(f"运行中的任务已取消: {task_id}")
                return True
            
            logger.warning(f"任务未找到: {task_id}")
            return False
            
        except Exception as e:
            logger.error(f"取消任务失败: {task_id} - {e}")
            return False
    
    async def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务状态"""
        try:
            # 检查待执行队列
            for task in self.pending_tasks:
                if task.id == task_id:
                    return task.to_dict()
            
            # 检查运行中的任务
            if task_id in self.running_tasks:
                return self.running_tasks[task_id].to_dict()
            
            # 检查已完成的任务
            if task_id in self.completed_tasks:
                return self.completed_tasks[task_id].to_dict()
            
            return None
            
        except Exception as e:
            logger.error(f"获取任务状态失败: {task_id} - {e}")
            return None
    
    async def get_pending_tasks(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取待执行任务"""
        try:
            return [task.to_dict() for task in self.pending_tasks[:limit]]
        except Exception as e:
            logger.error(f"获取待执行任务失败: {e}")
            return []
    
    async def get_running_tasks(self) -> List[Dict[str, Any]]:
        """获取运行中的任务"""
        try:
            return [task.to_dict() for task in self.running_tasks.values()]
        except Exception as e:
            logger.error(f"获取运行任务失败: {e}")
            return []
    
    async def register_agent(self, agent: BaseAgent) -> None:
        """注册智能体"""
        self.available_agents[agent.agent_id] = agent
        logger.info(f"智能体已注册到调度器: {agent.name} ({agent.agent_id})")
    
    async def unregister_agent(self, agent_id: str) -> bool:
        """注销智能体"""
        try:
            # 从可用智能体中移除
            if agent_id in self.available_agents:
                del self.available_agents[agent_id]
            # 从忙碌智能体中移除
            elif agent_id in self.busy_agents:
                del self.busy_agents[agent_id]
            else:
                return False
            
            logger.info(f"智能体已从调度器注销: {agent_id}")
            return True
            
        except Exception as e:
            logger.error(f"注销智能体失败: {agent_id} - {e}")
            return False
    
    async def get_scheduler_statistics(self) -> Dict[str, Any]:
        """获取调度器统计信息"""
        return {
            "pending_tasks": len(self.pending_tasks),
            "running_tasks": len(self.running_tasks),
            "completed_tasks": len(self.completed_tasks),
            "available_agents": len(self.available_agents),
            "busy_agents": len(self.busy_agents),
            "statistics": self.stats,
            "config": self.config
        }
    
    async def _scheduler_loop(self) -> None:
        """调度器主循环"""
        while self._running:
            try:
                await self._check_and_dispatch_tasks()
                await asyncio.sleep(self.config["agent_check_interval"])
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"调度器循环错误: {e}")
                await asyncio.sleep(5)
    
    async def _check_and_dispatch_tasks(self) -> None:
        """检查并分发任务"""
        try:
            current_time = datetime.now()
            
            # 检查是否有可用智能体
            if not self.available_agents:
                return
            
            # 检查是否有待执行的任务
            if not self.pending_tasks:
                return
            
            # 检查并发限制
            if len(self.running_tasks) >= self.config["max_concurrent_tasks"]:
                return
            
            # 获取当前时间应该执行的任务
            tasks_to_execute = []
            temp_queue = []
            
            while self.pending_tasks:
                task = heapq.heappop(self.pending_tasks)
                
                if task.scheduled_time <= current_time:
                    tasks_to_execute.append(task)
                else:
                    temp_queue.append(task)
            
            # 将未到时间的任务放回队列
            for task in temp_queue:
                heapq.heappush(self.pending_tasks, task)
            
            # 分发任务
            available_slots = self.config["max_concurrent_tasks"] - len(self.running_tasks)
            for task in tasks_to_execute[:available_slots]:
                await self._dispatch_task(task)
                
        except Exception as e:
            logger.error(f"任务分发失败: {e}")
    
    async def _dispatch_task(self, task: ScheduledTask) -> None:
        """分发任务"""
        try:
            # 选择智能体
            agent = await self._select_agent_for_task(task)
            if not agent:
                # 没有可用智能体，将任务放回队列
                heapq.heappush(self.pending_tasks, task)
                return
            
            # 更新任务状态
            task.status = TaskStatus.RUNNING
            task.start_time = datetime.now()
            
            # 标记智能体为忙碌
            self.available_agents.pop(agent.agent_id)
            self.busy_agents[agent.agent_id] = agent
            
            # 添加到运行任务
            self.running_tasks[task.id] = task
            
            # 异步执行任务
            asyncio.create_task(self._execute_task(agent, task))
            
            logger.info(f"任务已分发: {task.id} -> {agent.name}")
            
        except Exception as e:
            logger.error(f"分发任务失败: {task.id} - {e}")
    
    async def _select_agent_for_task(self, task: ScheduledTask) -> Optional[BaseAgent]:
        """为任务选择智能体"""
        try:
            task_type = task.data.get("type", "general")
            required_capabilities = task.data.get("required_capabilities", [])
            
            # 查找匹配的智能体
            suitable_agents = []
            for agent_id, agent in self.available_agents.items():
                # 检查能力匹配
                if self._agent_matches_requirements(agent, task_type, required_capabilities):
                    suitable_agents.append(agent)
            
            if not suitable_agents:
                return None
            
            # 选择负载最低的智能体
            best_agent = min(suitable_agents, key=lambda a: self._get_agent_load(a))
            
            return best_agent
            
        except Exception as e:
            logger.error(f"选择智能体失败: {e}")
            return None
    
    def _agent_matches_requirements(self, agent: BaseAgent, task_type: str, 
                                  required_capabilities: List[str]) -> bool:
        """检查智能体是否匹配任务需求"""
        # 检查任务类型
        if task_type != "general":
            agent_capabilities = agent.capabilities
            if not any(task_type in cap for cap in agent_capabilities):
                return False
        
        # 检查必需能力
        for capability in required_capabilities:
            if capability not in agent.capabilities:
                return False
        
        return True
    
    def _get_agent_load(self, agent: BaseAgent) -> float:
        """获取智能体负载（简化实现）"""
        # 这里可以根据智能体的当前任务数、响应时间等计算负载
        return 0.0
    
    async def _execute_task(self, agent: BaseAgent, task: ScheduledTask) -> None:
        """执行任务"""
        try:
            logger.info(f"开始执行任务: {task.id} -> {agent.name}")
            
            # 执行任务
            result = await agent.execute_task(task.data)
            
            # 处理结果
            task.result = result
            task.status = TaskStatus.COMPLETED
            task.end_time = datetime.now()
            
            # 更新统计
            execution_time = (task.end_time - task.start_time).total_seconds()
            self._update_execution_stats(execution_time, True)
            
            # 调用回调
            if task.callback:
                try:
                    await task.callback(task.id, result)
                except Exception as e:
                    logger.error(f"任务回调执行失败: {task.id} - {e}")
            
            logger.info(f"任务执行完成: {task.id}")
            
        except Exception as e:
            logger.error(f"任务执行失败: {task.id} - {e}")
            
            task.error = str(e)
            
            # 检查重试次数
            if task.retry_count < task.max_retries:
                task.retry_count += 1
                task.status = TaskStatus.PENDING
                task.start_time = None
                task.end_time = None
                
                # 重新调度
                heapq.heappush(self.pending_tasks, task)
                
                logger.info(f"任务将重试: {task.id} ({task.retry_count}/{task.max_retries})")
            else:
                task.status = TaskStatus.FAILED
                task.end_time = datetime.now()
                
                # 更新统计
                self._update_execution_stats(0, False)
        
        finally:
            # 释放智能体
            if agent.agent_id in self.busy_agents:
                self.busy_agents.pop(agent.agent_id)
                self.available_agents[agent.agent_id] = agent
            
            # 移动到已完成任务
            self.completed_tasks[task.id] = task
            if task.id in self.running_tasks:
                del self.running_tasks[task.id]
            
            # 清理过多的已完成任务
            if len(self.completed_tasks) > self.config["max_completed_tasks"]:
                oldest_task_id = min(self.completed_tasks.keys())
                del self.completed_tasks[oldest_task_id]
    
    def _update_execution_stats(self, execution_time: float, success: bool) -> None:
        """更新执行统计"""
        if success:
            self.stats["total_completed"] += 1
            # 更新平均执行时间
            total_completed = self.stats["total_completed"]
            current_avg = self.stats["average_execution_time"]
            self.stats["average_execution_time"] = (
                (current_avg * (total_completed - 1) + execution_time) / total_completed
            )
        else:
            self.stats["total_failed"] += 1
    
    async def _cleanup_loop(self) -> None:
        """清理循环"""
        while self._running:
            try:
                await asyncio.sleep(self.config["cleanup_interval"])
                
                # 清理过期的已完成任务
                cutoff_time = datetime.now() - timedelta(hours=24)
                expired_tasks = [
                    task_id for task_id, task in self.completed_tasks.items()
                    if task.end_time and task.end_time < cutoff_time
                ]
                
                for task_id in expired_tasks:
                    del self.completed_tasks[task_id]
                
                # 清理超时的运行任务
                current_time = datetime.now()
                timeout_tasks = []
                for task_id, task in self.running_tasks.items():
                    if task.timeout and task.start_time:
                        elapsed = (current_time - task.start_time).total_seconds()
                        if elapsed > task.timeout:
                            timeout_tasks.append(task_id)
                
                for task_id in timeout_tasks:
                    task = self.running_tasks[task_id]
                    task.status = TaskStatus.TIMEOUT
                    task.end_time = current_time
                    
                    # 释放智能体
                    agent_id = task.data.get("agent_id")
                    if agent_id and agent_id in self.busy_agents:
                        self.available_agents[agent_id] = self.busy_agents.pop(agent_id)
                    
                    # 移动到已完成任务
                    self.completed_tasks[task_id] = task
                    del self.running_tasks[task_id]
                    
                    logger.warning(f"任务超时: {task_id}")
                
                logger.info(f"清理完成: 删除了 {len(expired_tasks)} 个过期任务，"
                          f"处理了 {len(timeout_tasks)} 个超时任务")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"清理循环错误: {e}")
                await asyncio.sleep(60)  # 出错时等待更长时间