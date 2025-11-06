"""
Agno多智能体框架 - 基础智能体类
所有智能体的基类，提供通用功能
"""

import asyncio
import uuid
import json
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from abc import ABC, abstractmethod
import logging

from ..memory.memory_manager import MemoryManager
from ..tools.tool_registry import ToolRegistry

logger = logging.getLogger(__name__)


class AgentStatus:
    """智能体状态枚举"""
    IDLE = "idle"
    BUSY = "busy"
    WAITING = "waiting"
    ERROR = "error"
    OFFLINE = "offline"


class BaseAgent(ABC):
    """基础智能体类"""
    
    def __init__(
        self,
        agent_id: Optional[str] = None,
        name: str = "BaseAgent",
        description: str = "基础智能体",
        capabilities: Optional[List[str]] = None,
        memory_manager: Optional[MemoryManager] = None,
        tool_registry: Optional[ToolRegistry] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        self.agent_id = agent_id or str(uuid.uuid4())
        self.name = name
        self.description = description
        self.capabilities = capabilities or []
        self.memory_manager = memory_manager or MemoryManager()
        self.tool_registry = tool_registry or ToolRegistry()
        self.config = config or {}
        
        # 状态管理
        self.status = AgentStatus.IDLE
        self.current_task: Optional[str] = None
        self.created_at = datetime.now()
        self.last_active = datetime.now()
        
        # 性能指标
        self.tasks_completed = 0
        self.tasks_failed = 0
        self.total_execution_time = 0.0
        
        # 消息队列
        self.message_queue: List[Dict[str, Any]] = []
        self.message_handlers: Dict[str, callable] = {}
        
        logger.info(f"智能体初始化: {self.name} ({self.agent_id})")
    
    async def initialize(self) -> None:
        """初始化智能体"""
        try:
            # 初始化内存管理器
            await self.memory_manager.initialize()
            
            # 初始化工具注册表
            await self.tool_registry.initialize()
            
            # 注册默认消息处理器
            self._register_default_handlers()
            
            # 加载历史记忆
            await self._load_memories()
            
            self.status = AgentStatus.IDLE
            logger.info(f"智能体初始化完成: {self.name}")
            
        except Exception as e:
            self.status = AgentStatus.ERROR
            logger.error(f"智能体初始化失败: {self.name} - {e}")
            raise
    
    async def shutdown(self) -> None:
        """关闭智能体"""
        try:
            # 保存当前状态到记忆
            await self._save_current_state()
            
            # 清理资源
            await self.memory_manager.cleanup()
            await self.tool_registry.cleanup()
            
            self.status = AgentStatus.OFFLINE
            logger.info(f"智能体已关闭: {self.name}")
            
        except Exception as e:
            logger.error(f"智能体关闭失败: {self.name} - {e}")
    
    async def process_message(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """处理消息"""
        try:
            self.last_active = datetime.now()
            
            # 验证消息格式
            if not self._validate_message(message):
                logger.warning(f"消息格式无效: {message}")
                return None
            
            # 添加到消息队列
            self.message_queue.append(message)
            
            # 处理消息
            response = await self._handle_message(message)
            
            # 保存交互记录
            await self._save_interaction(message, response)
            
            return response
            
        except Exception as e:
            self.status = AgentStatus.ERROR
            logger.error(f"消息处理失败: {e}")
            return {"error": str(e), "agent_id": self.agent_id}
    
    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """执行任务"""
        start_time = datetime.now()
        
        try:
            self.status = AgentStatus.BUSY
            self.current_task = task.get("task_id", str(uuid.uuid4()))
            
            # 验证任务
            if not self._validate_task(task):
                raise ValueError("任务格式无效")
            
            # 检查能力匹配
            if not self._can_handle_task(task):
                raise ValueError("智能体不具备处理此任务的能力")
            
            # 执行任务
            result = await self._execute_task_impl(task)
            
            # 更新统计
            execution_time = (datetime.now() - start_time).total_seconds()
            self.tasks_completed += 1
            self.total_execution_time += execution_time
            
            # 保存任务结果
            await self._save_task_result(task, result, execution_time)
            
            self.status = AgentStatus.IDLE
            self.current_task = None
            
            logger.info(f"任务执行完成: {self.name} - {task.get('type', 'unknown')}")
            return result
            
        except Exception as e:
            self.tasks_failed += 1
            self.status = AgentStatus.ERROR
            self.current_task = None
            
            error_result = {
                "task_id": task.get("task_id"),
                "status": "failed",
                "error": str(e),
                "agent_id": self.agent_id,
                "execution_time": (datetime.now() - start_time).total_seconds()
            }
            
            logger.error(f"任务执行失败: {self.name} - {e}")
            return error_result
    
    async def get_status(self) -> Dict[str, Any]:
        """获取智能体状态"""
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "description": self.description,
            "status": self.status,
            "current_task": self.current_task,
            "capabilities": self.capabilities,
            "created_at": self.created_at.isoformat(),
            "last_active": self.last_active.isoformat(),
            "metrics": {
                "tasks_completed": self.tasks_completed,
                "tasks_failed": self.tasks_failed,
                "success_rate": self.tasks_completed / max(1, self.tasks_completed + self.tasks_failed),
                "average_execution_time": self.total_execution_time / max(1, self.tasks_completed)
            },
            "queue_size": len(self.message_queue),
            "memory_usage": await self.memory_manager.get_memory_usage(),
            "tool_count": len(self.tool_registry.get_available_tools())
        }
    
    async def register_tool(self, tool_name: str, tool_function: callable, description: str = "") -> bool:
        """注册工具"""
        try:
            await self.tool_registry.register_tool(tool_name, tool_function, description)
            logger.info(f"工具注册成功: {tool_name} -> {self.name}")
            return True
        except Exception as e:
            logger.error(f"工具注册失败: {tool_name} - {e}")
            return False
    
    async def use_tool(self, tool_name: str, **kwargs) -> Any:
        """使用工具"""
        try:
            return await self.tool_registry.execute_tool(tool_name, **kwargs)
        except Exception as e:
            logger.error(f"工具使用失败: {tool_name} - {e}")
            raise
    
    async def remember(self, content: str, memory_type: str = "general", importance: float = 0.5) -> str:
        """保存记忆"""
        try:
            memory_id = await self.memory_manager.store_memory(
                agent_id=self.agent_id,
                content=content,
                memory_type=memory_type,
                importance=importance
            )
            return memory_id
        except Exception as e:
            logger.error(f"保存记忆失败: {e}")
            raise
    
    async def recall(self, query: str, memory_type: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """回忆记忆"""
        try:
            return await self.memory_manager.search_memories(
                agent_id=self.agent_id,
                query=query,
                memory_type=memory_type,
                limit=limit
            )
        except Exception as e:
            logger.error(f"回忆记忆失败: {e}")
            return []
    
    def _register_default_handlers(self) -> None:
        """注册默认消息处理器"""
        self.message_handlers["ping"] = self._handle_ping
        self.message_handlers["status"] = self._handle_status_request
        self.message_handlers["capabilities"] = self._handle_capabilities_request
        self.message_handlers["task"] = self._handle_task_message
    
    def _validate_message(self, message: Dict[str, Any]) -> bool:
        """验证消息格式"""
        required_fields = ["type", "content"]
        return all(field in message for field in required_fields)
    
    def _validate_task(self, task: Dict[str, Any]) -> bool:
        """验证任务格式"""
        required_fields = ["type", "content"]
        return all(field in task for field in required_fields)
    
    def _can_handle_task(self, task: Dict[str, Any]) -> bool:
        """检查是否能处理任务"""
        task_type = task.get("type", "")
        required_capabilities = task.get("required_capabilities", [])
        
        # 检查任务类型是否匹配
        if task_type not in [cap.split(":")[0] for cap in self.capabilities]:
            return False
        
        # 检查必需能力
        for capability in required_capabilities:
            if capability not in self.capabilities:
                return False
        
        return True
    
    async def _handle_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """处理消息"""
        message_type = message.get("type")
        
        if message_type in self.message_handlers:
            return await self.message_handlers[message_type](message)
        else:
            return await self._handle_unknown_message(message)
    
    async def _handle_ping(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """处理ping消息"""
        return {
            "type": "pong",
            "agent_id": self.agent_id,
            "name": self.name,
            "status": self.status,
            "timestamp": datetime.now().isoformat()
        }
    
    async def _handle_status_request(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """处理状态请求"""
        return await self.get_status()
    
    async def _handle_capabilities_request(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """处理能力请求"""
        return {
            "type": "capabilities_response",
            "agent_id": self.agent_id,
            "capabilities": self.capabilities,
            "tools": list(self.tool_registry.get_available_tools().keys())
        }
    
    async def _handle_task_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """处理任务消息"""
        task = message.get("content", {})
        return await self.execute_task(task)
    
    async def _handle_unknown_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """处理未知消息"""
        return {
            "type": "error",
            "error": f"未知消息类型: {message.get('type')}",
            "agent_id": self.agent_id
        }
    
    async def _execute_task_impl(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """执行任务的具体实现（子类重写）"""
        task_type = task.get("type")
        
        # 默认实现
        return {
            "task_id": task.get("task_id"),
            "status": "completed",
            "result": f"任务类型 {task_type} 已处理",
            "agent_id": self.agent_id,
            "timestamp": datetime.now().isoformat()
        }
    
    async def _save_interaction(self, message: Dict[str, Any], response: Optional[Dict[str, Any]]) -> None:
        """保存交互记录"""
        interaction = {
            "timestamp": datetime.now().isoformat(),
            "message": message,
            "response": response,
            "agent_id": self.agent_id
        }
        
        await self.remember(
            content=json.dumps(interaction),
            memory_type="interaction",
            importance=0.3
        )
    
    async def _save_task_result(self, task: Dict[str, Any], result: Dict[str, Any], execution_time: float) -> None:
        """保存任务结果"""
        task_record = {
            "task": task,
            "result": result,
            "execution_time": execution_time,
            "timestamp": datetime.now().isoformat()
        }
        
        importance = 0.8 if result.get("status") == "completed" else 0.6
        
        await self.remember(
            content=json.dumps(task_record),
            memory_type="task",
            importance=importance
        )
    
    async def _save_current_state(self) -> None:
        """保存当前状态"""
        state = {
            "status": self.status,
            "current_task": self.current_task,
            "tasks_completed": self.tasks_completed,
            "tasks_failed": self.tasks_failed,
            "last_active": self.last_active.isoformat(),
            "config": self.config
        }
        
        await self.remember(
            content=json.dumps(state),
            memory_type="state",
            importance=0.9
        )
    
    async def _load_memories(self) -> None:
        """加载历史记忆"""
        try:
            memories = await self.memory_manager.get_agent_memories(
                agent_id=self.agent_id,
                memory_type="state",
                limit=1
            )
            
            if memories:
                state_data = json.loads(memories[0]["content"])
                self.status = state_data.get("status", AgentStatus.IDLE)
                self.tasks_completed = state_data.get("tasks_completed", 0)
                self.tasks_failed = state_data.get("tasks_failed", 0)
                
                logger.info(f"已加载历史状态: {self.name}")
                
        except Exception as e:
            logger.warning(f"加载历史记忆失败: {e}")
    
    @abstractmethod
    async def get_specialized_capabilities(self) -> List[str]:
        """获取专业能力（子类重写）"""
        pass