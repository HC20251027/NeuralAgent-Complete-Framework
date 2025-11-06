"""
Agno多智能体框架 - 上下文管理器
负责管理智能体的上下文状态和对话历史
"""

import asyncio
import json
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import logging

from .memory_manager import MemoryManager

logger = logging.getLogger(__name__)


class ContextScope:
    """上下文范围枚举"""
    GLOBAL = "global"      # 全局上下文
    CONVERSATION = "conversation"  # 对话上下文
    TASK = "task"          # 任务上下文
    SESSION = "session"    # 会话上下文


class ContextManager:
    """上下文管理器"""
    
    def __init__(self, memory_manager: Optional[MemoryManager] = None):
        self.memory_manager = memory_manager or MemoryManager()
        
        # 上下文存储
        self.contexts: Dict[str, Dict[str, Any]] = {}
        self.context_stack: List[str] = []  # 上下文栈
        self.active_contexts: Dict[str, str] = {}  # 活跃上下文映射
        
        # 上下文配置
        self.context_config = {
            "max_context_size": 10,        # 最大上下文大小
            "context_ttl": 3600,           # 上下文生存时间（秒）
            "auto_cleanup": True,          # 自动清理
            "compression_threshold": 5,    # 压缩阈值
            "persistence_enabled": True    # 持久化启用
        }
        
        # 统计信息
        self.stats = {
            "total_contexts": 0,
            "active_contexts": 0,
            "context_switches": 0,
            "compression_count": 0,
            "cleanup_count": 0
        }
    
    async def initialize(self) -> None:
        """初始化上下文管理器"""
        try:
            # 初始化内存管理器
            await self.memory_manager.initialize()
            
            # 启动后台清理任务
            if self.context_config["auto_cleanup"]:
                asyncio.create_task(self._context_cleanup_task())
            
            logger.info("上下文管理器初始化完成")
        except Exception as e:
            logger.error(f"上下文管理器初始化失败: {e}")
            raise
    
    async def create_context(
        self,
        context_id: str,
        scope: str = ContextScope.SESSION,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """创建上下文"""
        try:
            if context_id in self.contexts:
                logger.warning(f"上下文已存在: {context_id}")
                return False
            
            context = {
                "id": context_id,
                "scope": scope,
                "metadata": metadata or {},
                "created_at": datetime.now(),
                "last_accessed": datetime.now(),
                "access_count": 0,
                "data": {},
                "history": [],
                "compressed": False
            }
            
            self.contexts[context_id] = context
            self.active_contexts[scope] = context_id
            
            # 更新统计
            self.stats["total_contexts"] += 1
            self.stats["active_contexts"] += 1
            
            # 持久化
            if self.context_config["persistence_enabled"]:
                await self._persist_context(context)
            
            logger.debug(f"上下文已创建: {context_id} ({scope})")
            return True
            
        except Exception as e:
            logger.error(f"创建上下文失败: {context_id} - {e}")
            return False
    
    async def get_context(self, context_id: str) -> Optional[Dict[str, Any]]:
        """获取上下文"""
        try:
            if context_id not in self.contexts:
                return None
            
            context = self.contexts[context_id]
            
            # 更新访问信息
            await self._update_context_access(context)
            
            # 检查是否需要压缩
            if len(context["history"]) > self.context_config["compression_threshold"]:
                await self._compress_context(context)
            
            return context
            
        except Exception as e:
            logger.error(f"获取上下文失败: {context_id} - {e}")
            return None
    
    async def update_context(
        self,
        context_id: str,
        data: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """更新上下文"""
        try:
            context = await self.get_context(context_id)
            if not context:
                return False
            
            # 更新数据
            if data:
                context["data"].update(data)
            
            # 更新元数据
            if metadata:
                context["metadata"].update(metadata)
            
            context["last_accessed"] = datetime.now()
            
            # 持久化更新
            if self.context_config["persistence_enabled"]:
                await self._persist_context(context)
            
            logger.debug(f"上下文已更新: {context_id}")
            return True
            
        except Exception as e:
            logger.error(f"更新上下文失败: {context_id} - {e}")
            return False
    
    async def add_to_context_history(
        self,
        context_id: str,
        entry: Dict[str, Any]
    ) -> bool:
        """添加上下文历史记录"""
        try:
            context = await self.get_context(context_id)
            if not context:
                return False
            
            # 添加时间戳
            entry["timestamp"] = datetime.now()
            entry["id"] = entry.get("id", f"entry_{len(context['history'])}")
            
            context["history"].append(entry)
            
            # 检查大小限制
            if len(context["history"]) > self.context_config["max_context_size"]:
                await self._compress_context(context)
            
            # 持久化
            if self.context_config["persistence_enabled"]:
                await self._persist_context(context)
            
            logger.debug(f"上下文历史已更新: {context_id}")
            return True
            
        except Exception as e:
            logger.error(f"添加上下文历史失败: {context_id} - {e}")
            return False
    
    async def get_context_history(
        self,
        context_id: str,
        limit: Optional[int] = None,
        filter_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """获取上下文历史"""
        try:
            context = await self.get_context(context_id)
            if not context:
                return []
            
            history = context["history"]
            
            # 应用过滤器
            if filter_type:
                history = [entry for entry in history if entry.get("type") == filter_type]
            
            # 应用限制
            if limit:
                history = history[-limit:]
            
            return history
            
        except Exception as e:
            logger.error(f"获取上下文历史失败: {context_id} - {e}")
            return []
    
    async def switch_context(
        self,
        from_context_id: str,
        to_context_id: str
    ) -> bool:
        """切换上下文"""
        try:
            if from_context_id not in self.contexts:
                logger.warning(f"源上下文不存在: {from_context_id}")
                return False
            
            if to_context_id not in self.contexts:
                logger.warning(f"目标上下文不存在: {to_context_id}")
                return False
            
            # 保存当前上下文状态
            from_context = self.contexts[from_context_id]
            from_context["last_accessed"] = datetime.now()
            
            # 切换到新上下文
            to_context = self.contexts[to_context_id]
            await self._update_context_access(to_context)
            
            # 更新上下文栈
            if from_context_id in self.context_stack:
                self.context_stack.remove(from_context_id)
            self.context_stack.append(to_context_id)
            
            # 更新活跃上下文映射
            from_scope = from_context["scope"]
            to_scope = to_context["scope"]
            
            if from_scope in self.active_contexts:
                self.active_contexts[from_scope] = to_context_id
            
            # 更新统计
            self.stats["context_switches"] += 1
            
            logger.debug(f"上下文切换: {from_context_id} -> {to_context_id}")
            return True
            
        except Exception as e:
            logger.error(f"上下文切换失败: {from_context_id} -> {to_context_id} - {e}")
            return False
    
    async def push_context(self, context_id: str) -> bool:
        """推入上下文栈"""
        try:
            if context_id not in self.contexts:
                return False
            
            if context_id not in self.context_stack:
                self.context_stack.append(context_id)
            
            logger.debug(f"上下文已推入栈: {context_id}")
            return True
            
        except Exception as e:
            logger.error(f"推入上下文失败: {context_id} - {e}")
            return False
    
    async def pop_context(self) -> Optional[str]:
        """弹出上下文栈"""
        try:
            if not self.context_stack:
                return None
            
            context_id = self.context_stack.pop()
            logger.debug(f"上下文已弹出栈: {context_id}")
            return context_id
            
        except Exception as e:
            logger.error(f"弹出上下文失败: {e}")
            return None
    
    async def get_active_context(self, scope: str) -> Optional[Dict[str, Any]]:
        """获取活跃上下文"""
        try:
            context_id = self.active_contexts.get(scope)
            if context_id:
                return await self.get_context(context_id)
            return None
            
        except Exception as e:
            logger.error(f"获取活跃上下文失败: {scope} - {e}")
            return None
    
    async def delete_context(self, context_id: str) -> bool:
        """删除上下文"""
        try:
            if context_id not in self.contexts:
                return False
            
            context = self.contexts[context_id]
            scope = context["scope"]
            
            # 从各种映射中移除
            del self.contexts[context_id]
            
            if scope in self.active_contexts and self.active_contexts[scope] == context_id:
                del self.active_contexts[scope]
            
            if context_id in self.context_stack:
                self.context_stack.remove(context_id)
            
            # 从持久化存储中删除
            if self.context_config["persistence_enabled"]:
                await self._delete_persisted_context(context_id)
            
            # 更新统计
            self.stats["active_contexts"] -= 1
            
            logger.debug(f"上下文已删除: {context_id}")
            return True
            
        except Exception as e:
            logger.error(f"删除上下文失败: {context_id} - {e}")
            return False
    
    async def get_context_summary(self, context_id: str) -> Optional[Dict[str, Any]]:
        """获取上下文摘要"""
        try:
            context = await self.get_context(context_id)
            if not context:
                return None
            
            # 生成摘要
            summary = {
                "id": context_id,
                "scope": context["scope"],
                "created_at": context["created_at"].isoformat(),
                "last_accessed": context["last_accessed"].isoformat(),
                "access_count": context["access_count"],
                "data_keys": list(context["data"].keys()),
                "history_count": len(context["history"]),
                "compressed": context["compressed"],
                "metadata": context["metadata"]
            }
            
            # 添加最近的活动
            recent_history = context["history"][-3:] if context["history"] else []
            summary["recent_activity"] = [
                {
                    "type": entry.get("type"),
                    "timestamp": entry.get("timestamp").isoformat(),
                    "summary": entry.get("content", "")[:100] + "..." if len(entry.get("content", "")) > 100 else entry.get("content", "")
                }
                for entry in recent_history
            ]
            
            return summary
            
        except Exception as e:
            logger.error(f"获取上下文摘要失败: {context_id} - {e}")
            return None
    
    async def get_all_contexts(self) -> List[Dict[str, Any]]:
        """获取所有上下文"""
        try:
            summaries = []
            for context_id in self.contexts.keys():
                summary = await self.get_context_summary(context_id)
                if summary:
                    summaries.append(summary)
            
            return summaries
            
        except Exception as e:
            logger.error(f"获取所有上下文失败: {e}")
            return []
    
    async def cleanup_expired_contexts(self) -> int:
        """清理过期上下文"""
        try:
            current_time = datetime.now()
            ttl = timedelta(seconds=self.context_config["context_ttl"])
            expired_contexts = []
            
            for context_id, context in self.contexts.items():
                if current_time - context["last_accessed"] > ttl:
                    expired_contexts.append(context_id)
            
            # 删除过期上下文
            for context_id in expired_contexts:
                await self.delete_context(context_id)
            
            self.stats["cleanup_count"] += 1
            
            logger.info(f"清理过期上下文完成: {len(expired_contexts)} 个上下文")
            return len(expired_contexts)
            
        except Exception as e:
            logger.error(f"清理过期上下文失败: {e}")
            return 0
    
    async def _update_context_access(self, context: Dict[str, Any]) -> None:
        """更新上下文访问信息"""
        context["last_accessed"] = datetime.now()
        context["access_count"] += 1
    
    async def _compress_context(self, context: Dict[str, Any]) -> None:
        """压缩上下文"""
        try:
            if context["compressed"]:
                return
            
            # 保留最近的条目和重要的条目
            history = context["history"]
            if len(history) <= self.context_config["compression_threshold"]:
                return
            
            # 压缩策略：保留最近的一半和重要的一半
            keep_count = self.context_config["compression_threshold"]
            recent_half = history[-keep_count//2:]
            
            # 选择重要条目
            important_entries = [
                entry for entry in history[:-keep_count//2]
                if entry.get("importance", 0) > 0.7
            ]
            
            # 合并重要条目
            compressed_history = recent_half + important_entries[-keep_count//2:]
            
            # 添加压缩标记
            compression_summary = {
                "id": "compression_summary",
                "type": "compression",
                "timestamp": datetime.now(),
                "original_count": len(history),
                "compressed_count": len(compressed_history),
                "content": f"上下文已压缩: {len(history)} -> {len(compressed_history)} 条记录"
            }
            
            context["history"] = compressed_history + [compression_summary]
            context["compressed"] = True
            
            # 更新统计
            self.stats["compression_count"] += 1
            
            logger.debug(f"上下文已压缩: {len(history)} -> {len(compressed_history)}")
            
        except Exception as e:
            logger.error(f"压缩上下文失败: {e}")
    
    async def _persist_context(self, context: Dict[str, Any]) -> None:
        """持久化上下文"""
        try:
            # 将上下文存储到记忆系统
            context_data = {
                "id": context["id"],
                "scope": context["scope"],
                "data": context["data"],
                "history": context["history"],
                "metadata": context["metadata"],
                "compressed": context["compressed"]
            }
            
            await self.memory_manager.store_memory(
                agent_id="context_manager",
                content=json.dumps(context_data, default=str),
                memory_type="context",
                importance=0.6
            )
            
        except Exception as e:
            logger.error(f"持久化上下文失败: {context['id']} - {e}")
    
    async def _delete_persisted_context(self, context_id: str) -> None:
        """删除持久化的上下文"""
        try:
            # 从记忆系统中删除对应的记忆
            # 这里需要实现具体的删除逻辑
            pass
            
        except Exception as e:
            logger.error(f"删除持久化上下文失败: {context_id} - {e}")
    
    async def _context_cleanup_task(self) -> None:
        """上下文清理后台任务"""
        while True:
            try:
                await asyncio.sleep(3600)  # 每小时执行一次
                await self.cleanup_expired_contexts()
                
            except Exception as e:
                logger.error(f"上下文清理任务错误: {e}")
    
    async def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "total_contexts": self.stats["total_contexts"],
            "active_contexts": self.stats["active_contexts"],
            "context_switches": self.stats["context_switches"],
            "compression_count": self.stats["compression_count"],
            "cleanup_count": self.stats["cleanup_count"],
            "context_stack_size": len(self.context_stack),
            "active_contexts_by_scope": dict(self.active_contexts),
            "config": self.context_config
        }