"""
Agno多智能体框架 - 协调员智能体
负责协调多个智能体的工作和任务分配
"""

import asyncio
import json
from typing import Dict, List, Optional, Any, Set
from datetime import datetime
import logging

from .base_agent import BaseAgent, AgentStatus
from ..workflows.workflow_engine import WorkflowEngine

logger = logging.getLogger(__name__)


class CoordinatorAgent(BaseAgent):
    """协调员智能体"""
    
    def __init__(
        self,
        agent_id: Optional[str] = None,
        name: str = "Coordinator",
        description: str = "智能体协调员，负责任务分配和流程协调",
        **kwargs
    ):
        super().__init__(
            agent_id=agent_id,
            name=name,
            description=description,
            capabilities=[
                "coordination:task_assignment",
                "coordination:workflow_management", 
                "coordination:resource_allocation",
                "coordination:conflict_resolution",
                "monitoring:performance_tracking"
            ],
            **kwargs
        )
        
        # 管理的智能体
        self.managed_agents: Dict[str, BaseAgent] = {}
        self.agent_capabilities: Dict[str, List[str]] = {}
        
        # 任务管理
        self.active_tasks: Dict[str, Dict[str, Any]] = {}
        self.task_queue: List[Dict[str, Any]] = []
        self.completed_tasks: List[Dict[str, Any]] = []
        
        # 工作流引擎
        self.workflow_engine = WorkflowEngine()
        
        # 性能监控
        self.performance_metrics = {
            "total_tasks": 0,
            "successful_tasks": 0,
            "failed_tasks": 0,
            "average_completion_time": 0.0,
            "agent_utilization": {}
        }
    
    async def initialize(self) -> None:
        """初始化协调员"""
        await super().initialize()
        
        # 初始化工作流引擎
        await self.workflow_engine.initialize()
        
        # 注册协调相关工具
        await self._register_coordination_tools()
        
        logger.info(f"协调员初始化完成: {self.name}")
    
    async def register_agent(self, agent: BaseAgent) -> bool:
        """注册智能体"""
        try:
            # 检查智能体是否已注册
            if agent.agent_id in self.managed_agents:
                logger.warning(f"智能体已注册: {agent.name}")
                return False
            
            # 初始化智能体
            await agent.initialize()
            
            # 获取智能体能力
            capabilities = await agent.get_specialized_capabilities()
            
            # 注册智能体
            self.managed_agents[agent.agent_id] = agent
            self.agent_capabilities[agent.agent_id] = capabilities
            
            # 更新性能监控
            self.performance_metrics["agent_utilization"][agent.agent_id] = {
                "tasks_assigned": 0,
                "tasks_completed": 0,
                "tasks_failed": 0,
                "current_load": 0
            }
            
            logger.info(f"智能体注册成功: {agent.name} ({agent.agent_id})")
            return True
            
        except Exception as e:
            logger.error(f"智能体注册失败: {agent.name} - {e}")
            return False
    
    async def unregister_agent(self, agent_id: str) -> bool:
        """注销智能体"""
        try:
            if agent_id not in self.managed_agents:
                logger.warning(f"智能体未注册: {agent_id}")
                return False
            
            agent = self.managed_agents[agent_id]
            
            # 关闭智能体
            await agent.shutdown()
            
            # 从注册表中移除
            del self.managed_agents[agent_id]
            del self.agent_capabilities[agent_id]
            
            # 从性能监控中移除
            if agent_id in self.performance_metrics["agent_utilization"]:
                del self.performance_metrics["agent_utilization"][agent_id]
            
            logger.info(f"智能体已注销: {agent.name}")
            return True
            
        except Exception as e:
            logger.error(f"智能体注销失败: {agent_id} - {e}")
            return False
    
    async def assign_task(self, task: Dict[str, Any]) -> str:
        """分配任务"""
        try:
            # 生成任务ID
            task_id = task.get("task_id") or f"task_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
            task["task_id"] = task_id
            
            # 分析任务需求
            required_capabilities = self._analyze_task_requirements(task)
            
            # 选择合适的智能体
            selected_agent_id = await self._select_agent_for_task(task, required_capabilities)
            
            if not selected_agent_id:
                # 如果没有合适的智能体，添加到队列
                self.task_queue.append(task)
                logger.info(f"任务已加入队列: {task_id}")
                return task_id
            
            # 分配任务
            await self._assign_task_to_agent(task, selected_agent_id)
            
            logger.info(f"任务分配成功: {task_id} -> {selected_agent_id}")
            return task_id
            
        except Exception as e:
            logger.error(f"任务分配失败: {e}")
            raise
    
    async def monitor_task_progress(self, task_id: str) -> Dict[str, Any]:
        """监控任务进度"""
        try:
            # 检查活跃任务
            if task_id in self.active_tasks:
                task_info = self.active_tasks[task_id]
                agent_id = task_info["agent_id"]
                
                if agent_id in self.managed_agents:
                    agent = self.managed_agents[agent_id]
                    agent_status = await agent.get_status()
                    
                    return {
                        "task_id": task_id,
                        "status": agent_status["status"],
                        "progress": task_info.get("progress", 0),
                        "agent_id": agent_id,
                        "agent_status": agent_status,
                        "assigned_at": task_info["assigned_at"],
                        "estimated_completion": task_info.get("estimated_completion")
                    }
            
            # 检查已完成任务
            for task in self.completed_tasks:
                if task["task_id"] == task_id:
                    return {
                        "task_id": task_id,
                        "status": "completed",
                        "result": task["result"],
                        "completed_at": task["completed_at"],
                        "execution_time": task["execution_time"]
                    }
            
            # 检查队列中的任务
            for task in self.task_queue:
                if task["task_id"] == task_id:
                    return {
                        "task_id": task_id,
                        "status": "queued",
                        "position": self.task_queue.index(task) + 1
                    }
            
            return {"task_id": task_id, "status": "not_found"}
            
        except Exception as e:
            logger.error(f"任务监控失败: {task_id} - {e}")
            return {"task_id": task_id, "status": "error", "error": str(e)}
    
    async def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        try:
            # 从活跃任务中移除
            if task_id in self.active_tasks:
                task_info = self.active_tasks[task_id]
                agent_id = task_info["agent_id"]
                
                if agent_id in self.managed_agents:
                    agent = self.managed_agents[agent_id]
                    # 发送取消消息
                    await agent.process_message({
                        "type": "cancel_task",
                        "content": {"task_id": task_id}
                    })
                
                del self.active_tasks[task_id]
                logger.info(f"活跃任务已取消: {task_id}")
                return True
            
            # 从队列中移除
            for i, task in enumerate(self.task_queue):
                if task["task_id"] == task_id:
                    self.task_queue.pop(i)
                    logger.info(f"队列任务已取消: {task_id}")
                    return True
            
            logger.warning(f"任务未找到: {task_id}")
            return False
            
        except Exception as e:
            logger.error(f"任务取消失败: {task_id} - {e}")
            return False
    
    async def get_coordination_status(self) -> Dict[str, Any]:
        """获取协调状态"""
        try:
            # 收集所有智能体状态
            agent_statuses = {}
            for agent_id, agent in self.managed_agents.items():
                agent_statuses[agent_id] = await agent.get_status()
            
            # 计算统计信息
            total_agents = len(self.managed_agents)
            active_agents = sum(1 for status in agent_statuses.values() 
                              if status["status"] == AgentStatus.BUSY)
            idle_agents = sum(1 for status in agent_statuses.values() 
                            if status["status"] == AgentStatus.IDLE)
            
            return {
                "coordinator_id": self.agent_id,
                "total_agents": total_agents,
                "active_agents": active_agents,
                "idle_agents": idle_agents,
                "active_tasks": len(self.active_tasks),
                "queued_tasks": len(self.task_queue),
                "completed_tasks": len(self.completed_tasks),
                "agent_statuses": agent_statuses,
                "performance_metrics": self.performance_metrics,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"获取协调状态失败: {e}")
            return {"error": str(e)}
    
    async def optimize_performance(self) -> Dict[str, Any]:
        """性能优化"""
        try:
            optimization_suggestions = []
            
            # 分析任务分配效率
            for agent_id, metrics in self.performance_metrics["agent_utilization"].items():
                if metrics["tasks_failed"] > metrics["tasks_completed"]:
                    optimization_suggestions.append({
                        "agent_id": agent_id,
                        "issue": "high_failure_rate",
                        "suggestion": "考虑重新分配任务类型或提供额外培训"
                    })
                
                if metrics["current_load"] == 0 and metrics["tasks_assigned"] > 0:
                    optimization_suggestions.append({
                        "agent_id": agent_id,
                        "issue": "low_utilization",
                        "suggestion": "增加任务分配或检查智能体健康状态"
                    })
            
            # 检查任务队列
            if len(self.task_queue) > 10:
                optimization_suggestions.append({
                    "issue": "large_queue",
                    "suggestion": "考虑增加更多智能体或优化任务分配算法"
                })
            
            # 检查负载均衡
            loads = [metrics["current_load"] for metrics in self.performance_metrics["agent_utilization"].values()]
            if loads:
                max_load = max(loads)
                min_load = min(loads)
                if max_load > min_load * 2:
                    optimization_suggestions.append({
                        "issue": "load_imbalance",
                        "suggestion": "重新平衡任务分配"
                    })
            
            return {
                "optimization_suggestions": optimization_suggestions,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"性能优化失败: {e}")
            return {"error": str(e)}
    
    def _analyze_task_requirements(self, task: Dict[str, Any]) -> List[str]:
        """分析任务需求"""
        requirements = []
        
        task_type = task.get("type", "")
        if task_type:
            requirements.append(task_type)
        
        # 从任务内容中提取能力需求
        content = task.get("content", {})
        if isinstance(content, dict):
            required_capabilities = content.get("required_capabilities", [])
            requirements.extend(required_capabilities)
        
        # 优先级要求
        priority = task.get("priority", "normal")
        if priority == "high":
            requirements.append("high_priority_handling")
        
        return list(set(requirements))  # 去重
    
    async def _select_agent_for_task(self, task: Dict[str, Any], requirements: List[str]) -> Optional[str]:
        """为任务选择智能体"""
        suitable_agents = []
        
        for agent_id, capabilities in self.agent_capabilities.items():
            agent = self.managed_agents[agent_id]
            
            # 检查智能体状态
            if agent.status != AgentStatus.IDLE:
                continue
            
            # 检查能力匹配
            if self._capabilities_match(requirements, capabilities):
                suitable_agents.append(agent_id)
        
        if not suitable_agents:
            return None
        
        # 选择负载最低的智能体
        best_agent = min(suitable_agents, key=lambda a: 
                        self.performance_metrics["agent_utilization"][a]["current_load"])
        
        return best_agent
    
    def _capabilities_match(self, requirements: List[str], agent_capabilities: List[str]) -> bool:
        """检查能力是否匹配"""
        for requirement in requirements:
            if not any(requirement in cap for cap in agent_capabilities):
                return False
        return True
    
    async def _assign_task_to_agent(self, task: Dict[str, Any], agent_id: str) -> None:
        """分配任务给智能体"""
        agent = self.managed_agents[agent_id]
        
        # 添加到活跃任务
        self.active_tasks[task["task_id"]] = {
            "agent_id": agent_id,
            "assigned_at": datetime.now(),
            "progress": 0
        }
        
        # 更新智能体负载
        self.performance_metrics["agent_utilization"][agent_id]["current_load"] += 1
        self.performance_metrics["agent_utilization"][agent_id]["tasks_assigned"] += 1
        
        # 发送任务给智能体
        response = await agent.execute_task(task)
        
        # 处理任务结果
        await self._handle_task_completion(task["task_id"], response)
    
    async def _handle_task_completion(self, task_id: str, result: Dict[str, Any]) -> None:
        """处理任务完成"""
        if task_id not in self.active_tasks:
            return
        
        task_info = self.active_tasks[task_id]
        agent_id = task_info["agent_id"]
        
        # 从活跃任务中移除
        del self.active_tasks[task_id]
        
        # 更新智能体负载
        self.performance_metrics["agent_utilization"][agent_id]["current_load"] -= 1
        
        # 更新统计
        self.performance_metrics["total_tasks"] += 1
        
        if result.get("status") == "completed":
            self.performance_metrics["successful_tasks"] += 1
            self.performance_metrics["agent_utilization"][agent_id]["tasks_completed"] += 1
        else:
            self.performance_metrics["failed_tasks"] += 1
            self.performance_metrics["agent_utilization"][agent_id]["tasks_failed"] += 1
        
        # 添加到已完成任务
        self.completed_tasks.append({
            "task_id": task_id,
            "result": result,
            "completed_at": datetime.now(),
            "execution_time": result.get("execution_time", 0)
        })
        
        # 保持最近100个已完成任务
        if len(self.completed_tasks) > 100:
            self.completed_tasks.pop(0)
        
        logger.info(f"任务处理完成: {task_id} -> {result.get('status')}")
    
    async def _register_coordination_tools(self) -> None:
        """注册协调工具"""
        await self.register_tool("assign_task", self.assign_task, "分配任务给智能体")
        await self.register_tool("monitor_task", self.monitor_task_progress, "监控任务进度")
        await self.register_tool("cancel_task", self.cancel_task, "取消任务")
        await self.register_tool("get_status", self.get_coordination_status, "获取协调状态")
        await self.register_tool("optimize_performance", self.optimize_performance, "性能优化")
    
    async def get_specialized_capabilities(self) -> List[str]:
        """获取专业能力"""
        return self.capabilities + [
            "coordination:multi_agent_management",
            "coordination:task_optimization",
            "coordination:load_balancing"
        ]