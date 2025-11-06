"""
Agno多智能体框架 - 记忆管理器
负责管理智能体的三级记忆系统
"""

import asyncio
import json
import uuid
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import numpy as np
import logging

from ..database.vector_store import VectorDatabase
from .context_manager import ContextManager

logger = logging.getLogger(__name__)


class MemoryLevel:
    """记忆层级枚举"""
    WORKING = "working"      # 工作记忆 - 短期，当前会话
    EPISODIC = "episodic"    # 情节记忆 - 中期，相关事件
    SEMANTIC = "semantic"    # 语义记忆 - 长期，知识概念


class MemoryManager:
    """记忆管理器"""
    
    def __init__(self, vector_db: Optional[VectorDatabase] = None):
        self.vector_db = vector_db or VectorDatabase()
        self.context_manager = ContextManager()
        
        # 记忆配置
        self.memory_config = {
            "working_memory_limit": 7,      # 工作记忆容量
            "episodic_memory_limit": 100,   # 情节记忆容量
            "semantic_memory_limit": 1000,  # 语义记忆容量
            "memory_decay_rate": 0.1,       # 记忆衰减率
            "importance_threshold": 0.5,    # 重要性阈值
            "consolidation_interval": 3600, # 记忆巩固间隔（秒）
            "cleanup_interval": 86400       # 清理间隔（秒）
        }
        
        # 内存缓存
        self.working_memory: Dict[str, Dict[str, Any]] = {}
        self.memory_index: Dict[str, Dict[str, Any]] = {}  # 记忆索引
        
        # 统计信息
        self.memory_stats = {
            "total_memories": 0,
            "working_memories": 0,
            "episodic_memories": 0,
            "semantic_memories": 0,
            "consolidation_count": 0,
            "cleanup_count": 0
        }
    
    async def initialize(self) -> None:
        """初始化记忆管理器"""
        try:
            # 初始化向量数据库
            await self.vector_db.initialize_vector_extensions()
            
            # 初始化上下文管理器
            await self.context_manager.initialize()
            
            # 启动后台任务
            asyncio.create_task(self._memory_consolidation_task())
            asyncio.create_task(self._memory_cleanup_task())
            
            logger.info("记忆管理器初始化完成")
        except Exception as e:
            logger.error(f"记忆管理器初始化失败: {e}")
            raise
    
    async def store_memory(
        self,
        agent_id: str,
        content: str,
        memory_type: str = "general",
        importance: float = 0.5,
        metadata: Optional[Dict[str, Any]] = None,
        embedding: Optional[List[float]] = None
    ) -> str:
        """存储记忆"""
        try:
            memory_id = str(uuid.uuid4())
            timestamp = datetime.now()
            
            # 创建记忆对象
            memory = {
                "id": memory_id,
                "agent_id": agent_id,
                "content": content,
                "memory_type": memory_type,
                "importance": importance,
                "metadata": metadata or {},
                "created_at": timestamp,
                "last_accessed": timestamp,
                "access_count": 0,
                "embedding": embedding,
                "level": self._determine_memory_level(importance, memory_type)
            }
            
            # 确定存储层级
            level = memory["level"]
            
            if level == MemoryLevel.WORKING:
                await self._store_working_memory(memory)
            elif level == MemoryLevel.EPISODIC:
                await self._store_episodic_memory(memory)
            else:  # SEMANTIC
                await self._store_semantic_memory(memory)
            
            # 更新统计
            self.memory_stats["total_memories"] += 1
            if level == MemoryLevel.WORKING:
                self.memory_stats["working_memories"] += 1
            elif level == MemoryLevel.EPISODIC:
                self.memory_stats["episodic_memories"] += 1
            else:
                self.memory_stats["semantic_memories"] += 1
            
            # 更新索引
            self.memory_index[memory_id] = {
                "level": level,
                "agent_id": agent_id,
                "memory_type": memory_type,
                "importance": importance,
                "created_at": timestamp
            }
            
            logger.debug(f"记忆已存储: {memory_id} ({level})")
            return memory_id
            
        except Exception as e:
            logger.error(f"存储记忆失败: {e}")
            raise
    
    async def retrieve_memory(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """检索记忆"""
        try:
            # 检查工作记忆
            if memory_id in self.working_memory:
                memory = self.working_memory[memory_id]
                await self._update_memory_access(memory)
                return memory
            
            # 检查情节记忆
            episodic_memory = await self._retrieve_episodic_memory(memory_id)
            if episodic_memory:
                await self._update_memory_access(episodic_memory)
                return episodic_memory
            
            # 检查语义记忆
            semantic_memory = await self._retrieve_semantic_memory(memory_id)
            if semantic_memory:
                await self._update_memory_access(semantic_memory)
                return semantic_memory
            
            return None
            
        except Exception as e:
            logger.error(f"检索记忆失败: {memory_id} - {e}")
            return None
    
    async def search_memories(
        self,
        agent_id: str,
        query: str,
        memory_type: Optional[str] = None,
        level: Optional[str] = None,
        importance_threshold: Optional[float] = None,
        limit: int = 10,
        use_embedding: bool = True
    ) -> List[Dict[str, Any]]:
        """搜索记忆"""
        try:
            results = []
            
            # 生成查询向量
            query_embedding = None
            if use_embedding:
                query_embedding = await self._generate_embedding(query)
            
            # 搜索不同层级的记忆
            if level is None or level == MemoryLevel.WORKING:
                working_results = await self._search_working_memory(
                    agent_id, query, memory_type, importance_threshold, limit, query_embedding
                )
                results.extend(working_results)
            
            if level is None or level == MemoryLevel.EPISODIC:
                episodic_results = await self._search_episodic_memory(
                    agent_id, query, memory_type, importance_threshold, limit, query_embedding
                )
                results.extend(episodic_results)
            
            if level is None or level == MemoryLevel.SEMANTIC:
                semantic_results = await self._search_semantic_memory(
                    agent_id, query, memory_type, importance_threshold, limit, query_embedding
                )
                results.extend(semantic_results)
            
            # 按相关性和重要性排序
            results.sort(key=lambda x: (x.get("relevance_score", 0), x.get("importance", 0)), reverse=True)
            
            # 限制结果数量
            return results[:limit]
            
        except Exception as e:
            logger.error(f"搜索记忆失败: {e}")
            return []
    
    async def get_agent_memories(
        self,
        agent_id: str,
        memory_type: Optional[str] = None,
        level: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """获取智能体的所有记忆"""
        try:
            results = []
            
            # 获取工作记忆
            if level is None or level == MemoryLevel.WORKING:
                working_memories = await self._get_working_memories(agent_id, memory_type, limit)
                results.extend(working_memories)
            
            # 获取情节记忆
            if level is None or level == MemoryLevel.EPISODIC:
                episodic_memories = await self._get_episodic_memories(agent_id, memory_type, limit)
                results.extend(episodic_memories)
            
            # 获取语义记忆
            if level is None or level == MemoryLevel.SEMANTIC:
                semantic_memories = await self._get_semantic_memories(agent_id, memory_type, limit)
                results.extend(semantic_memories)
            
            # 按时间和重要性排序
            results.sort(key=lambda x: (x.get("importance", 0), x.get("created_at", datetime.min)), reverse=True)
            
            return results[:limit]
            
        except Exception as e:
            logger.error(f"获取智能体记忆失败: {agent_id} - {e}")
            return []
    
    async def update_memory(self, memory_id: str, updates: Dict[str, Any]) -> bool:
        """更新记忆"""
        try:
            memory = await self.retrieve_memory(memory_id)
            if not memory:
                return False
            
            # 更新记忆内容
            memory.update(updates)
            memory["updated_at"] = datetime.now()
            
            # 重新存储
            level = memory.get("level", MemoryLevel.EPISODIC)
            
            if level == MemoryLevel.WORKING:
                self.working_memory[memory_id] = memory
            elif level == MemoryLevel.EPISODIC:
                await self._update_episodic_memory(memory)
            else:
                await self._update_semantic_memory(memory)
            
            logger.debug(f"记忆已更新: {memory_id}")
            return True
            
        except Exception as e:
            logger.error(f"更新记忆失败: {memory_id} - {e}")
            return False
    
    async def delete_memory(self, memory_id: str) -> bool:
        """删除记忆"""
        try:
            # 从工作记忆中删除
            if memory_id in self.working_memory:
                del self.working_memory[memory_id]
                self.memory_stats["working_memories"] -= 1
            
            # 从情节记忆中删除
            await self._delete_episodic_memory(memory_id)
            
            # 从语义记忆中删除
            await self._delete_semantic_memory(memory_id)
            
            # 从索引中删除
            if memory_id in self.memory_index:
                level = self.memory_index[memory_id]["level"]
                if level == MemoryLevel.EPISODIC:
                    self.memory_stats["episodic_memories"] -= 1
                elif level == MemoryLevel.SEMANTIC:
                    self.memory_stats["semantic_memories"] -= 1
                
                del self.memory_index[memory_id]
            
            self.memory_stats["total_memories"] -= 1
            
            logger.debug(f"记忆已删除: {memory_id}")
            return True
            
        except Exception as e:
            logger.error(f"删除记忆失败: {memory_id} - {e}")
            return False
    
    async def consolidate_memories(self, agent_id: str) -> int:
        """记忆巩固"""
        try:
            consolidated_count = 0
            
            # 巩固工作记忆到情节记忆
            working_memories_to_consolidate = [
                memory for memory in self.working_memory.values()
                if memory["agent_id"] == agent_id and 
                   memory["importance"] > self.memory_config["importance_threshold"]
            ]
            
            for memory in working_memories_to_consolidate:
                await self._consolidate_working_to_episodic(memory)
                consolidated_count += 1
            
            # 巩固情节记忆到语义记忆
            await self._consolidate_episodic_to_semantic(agent_id)
            
            self.memory_stats["consolidation_count"] += 1
            logger.info(f"记忆巩固完成: {agent_id} - {consolidated_count} 条记忆")
            
            return consolidated_count
            
        except Exception as e:
            logger.error(f"记忆巩固失败: {agent_id} - {e}")
            return 0
    
    async def get_memory_usage(self) -> Dict[str, Any]:
        """获取内存使用情况"""
        return {
            "working_memory_count": len(self.working_memory),
            "working_memory_size": len(json.dumps(self.working_memory)),
            "total_memories": self.memory_stats["total_memories"],
            "memory_levels": {
                "working": self.memory_stats["working_memories"],
                "episodic": self.memory_stats["episodic_memories"],
                "semantic": self.memory_stats["semantic_memories"]
            },
            "config": self.memory_config
        }
    
    def _determine_memory_level(self, importance: float, memory_type: str) -> str:
        """确定记忆层级"""
        # 基于重要性和类型确定层级
        if importance > 0.8 or memory_type in ["critical", "preference", "identity"]:
            return MemoryLevel.SEMANTIC
        elif importance > 0.5 or memory_type in ["task", "interaction", "event"]:
            return MemoryLevel.EPISODIC
        else:
            return MemoryLevel.WORKING
    
    async def _store_working_memory(self, memory: Dict[str, Any]) -> None:
        """存储工作记忆"""
        memory_id = memory["id"]
        
        # 检查容量限制
        if len(self.working_memory) >= self.memory_config["working_memory_limit"]:
            # 移除最不重要的记忆
            oldest_memory = min(
                self.working_memory.values(),
                key=lambda x: (x["importance"], x["last_accessed"])
            )
            await self._promote_working_memory(oldest_memory)
        
        self.working_memory[memory_id] = memory
    
    async def _store_episodic_memory(self, memory: Dict[str, Any]) -> None:
        """存储情节记忆"""
        memory_id = memory["id"]
        
        # 存储到向量数据库
        await self.vector_db.store_agent_memory(
            agent_id=memory["agent_id"],
            memory_type="episodic",
            content={
                "id": memory_id,
                "content": memory["content"],
                "metadata": memory["metadata"]
            },
            embedding=memory.get("embedding"),
            importance_score=memory["importance"]
        )
    
    async def _store_semantic_memory(self, memory: Dict[str, Any]) -> None:
        """存储语义记忆"""
        memory_id = memory["id"]
        
        # 存储到向量数据库
        await self.vector_db.store_agent_memory(
            agent_id=memory["agent_id"],
            memory_type="semantic",
            content={
                "id": memory_id,
                "content": memory["content"],
                "metadata": memory["metadata"]
            },
            embedding=memory.get("embedding"),
            importance_score=memory["importance"]
        )
    
    async def _retrieve_episodic_memory(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """检索情节记忆"""
        # 从向量数据库检索
        memories = await self.vector_db.get_agent_memories(
            agent_id="",  # 需要从记忆ID推断
            memory_type="episodic"
        )
        
        for memory in memories:
            content = memory.get("content", {})
            if isinstance(content, dict) and content.get("id") == memory_id:
                return {
                    "id": memory_id,
                    "content": content.get("content"),
                    "metadata": content.get("metadata"),
                    "importance": memory.get("importance_score", 0.5),
                    "created_at": memory.get("created_at"),
                    "level": MemoryLevel.EPISODIC
                }
        
        return None
    
    async def _retrieve_semantic_memory(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """检索语义记忆"""
        # 从向量数据库检索
        memories = await self.vector_db.get_agent_memories(
            agent_id="",
            memory_type="semantic"
        )
        
        for memory in memories:
            content = memory.get("content", {})
            if isinstance(content, dict) and content.get("id") == memory_id:
                return {
                    "id": memory_id,
                    "content": content.get("content"),
                    "metadata": content.get("metadata"),
                    "importance": memory.get("importance_score", 0.5),
                    "created_at": memory.get("created_at"),
                    "level": MemoryLevel.SEMANTIC
                }
        
        return None
    
    async def _search_working_memory(
        self,
        agent_id: str,
        query: str,
        memory_type: Optional[str],
        importance_threshold: Optional[float],
        limit: int,
        query_embedding: Optional[List[float]]
    ) -> List[Dict[str, Any]]:
        """搜索工作记忆"""
        results = []
        
        for memory in self.working_memory.values():
            if memory["agent_id"] != agent_id:
                continue
            
            if memory_type and memory["memory_type"] != memory_type:
                continue
            
            if importance_threshold and memory["importance"] < importance_threshold:
                continue
            
            # 简单的文本匹配
            if query.lower() in memory["content"].lower():
                relevance_score = 1.0  # 简化计算
                results.append({
                    **memory,
                    "relevance_score": relevance_score
                })
        
        return results[:limit]
    
    async def _search_episodic_memory(
        self,
        agent_id: str,
        query: str,
        memory_type: Optional[str],
        importance_threshold: Optional[float],
        limit: int,
        query_embedding: Optional[List[float]]
    ) -> List[Dict[str, Any]]:
        """搜索情节记忆"""
        try:
            if query_embedding:
                # 使用向量搜索
                search_results = await self.vector_db.search_similar_vectors(
                    query_embedding=query_embedding,
                    table_name="agent_memories",
                    limit=limit
                )
                
                results = []
                for result in search_results:
                    content = result.get("content", {})
                    if isinstance(content, dict):
                        memory = {
                            "id": content.get("id"),
                            "content": content.get("content"),
                            "metadata": content.get("metadata"),
                            "importance": result.get("importance_score", 0.5),
                            "created_at": result.get("created_at"),
                            "level": MemoryLevel.EPISODIC,
                            "relevance_score": result.get("similarity", 0.0)
                        }
                        
                        if memory["agent_id"] == agent_id and \
                           (not memory_type or memory["memory_type"] == memory_type) and \
                           (not importance_threshold or memory["importance"] >= importance_threshold):
                            results.append(memory)
                
                return results[:limit]
            else:
                # 文本搜索
                memories = await self.vector_db.get_agent_memories(
                    agent_id=agent_id,
                    memory_type="episodic",
                    limit=limit
                )
                
                results = []
                for memory in memories:
                    content = memory.get("content", {})
                    if isinstance(content, dict) and query.lower() in content.get("content", "").lower():
                        results.append({
                            "id": content.get("id"),
                            "content": content.get("content"),
                            "metadata": content.get("metadata"),
                            "importance": memory.get("importance_score", 0.5),
                            "created_at": memory.get("created_at"),
                            "level": MemoryLevel.EPISODIC,
                            "relevance_score": 1.0
                        })
                
                return results[:limit]
                
        except Exception as e:
            logger.error(f"搜索情节记忆失败: {e}")
            return []
    
    async def _search_semantic_memory(self, agent_id: str, query: str, 
                                    memory_type: Optional[str], importance_threshold: Optional[float],
                                    limit: int, query_embedding: Optional[List[float]]) -> List[Dict[str, Any]]:
        """搜索语义记忆"""
        # 类似于情节记忆的搜索，但使用语义记忆类型
        try:
            if query_embedding:
                search_results = await self.vector_db.search_similar_vectors(
                    query_embedding=query_embedding,
                    table_name="agent_memories",
                    limit=limit
                )
                
                results = []
                for result in search_results:
                    content = result.get("content", {})
                    if isinstance(content, dict):
                        memory = {
                            "id": content.get("id"),
                            "content": content.get("content"),
                            "metadata": content.get("metadata"),
                            "importance": result.get("importance_score", 0.5),
                            "created_at": result.get("created_at"),
                            "level": MemoryLevel.SEMANTIC,
                            "relevance_score": result.get("similarity", 0.0)
                        }
                        
                        if memory["agent_id"] == agent_id and \
                           (not memory_type or memory["memory_type"] == memory_type) and \
                           (not importance_threshold or memory["importance"] >= importance_threshold):
                            results.append(memory)
                
                return results[:limit]
            else:
                return []
                
        except Exception as e:
            logger.error(f"搜索语义记忆失败: {e}")
            return []
    
    async def _update_memory_access(self, memory: Dict[str, Any]) -> None:
        """更新记忆访问信息"""
        memory["last_accessed"] = datetime.now()
        memory["access_count"] = memory.get("access_count", 0) + 1
    
    async def _generate_embedding(self, text: str) -> List[float]:
        """生成文本向量（简化实现）"""
        # 这里应该调用实际的嵌入模型
        # 简化实现：随机向量
        return np.random.rand(1536).tolist()
    
    async def _memory_consolidation_task(self) -> None:
        """记忆巩固后台任务"""
        while True:
            try:
                await asyncio.sleep(self.memory_config["consolidation_interval"])
                
                # 对所有智能体执行记忆巩固
                agent_ids = set(memory["agent_id"] for memory in self.working_memory.values())
                for agent_id in agent_ids:
                    await self.consolidate_memories(agent_id)
                    
            except Exception as e:
                logger.error(f"记忆巩固任务错误: {e}")
    
    async def _memory_cleanup_task(self) -> None:
        """记忆清理后台任务"""
        while True:
            try:
                await asyncio.sleep(self.memory_config["cleanup_interval"])
                
                # 清理过期的情节和语义记忆
                await self._cleanup_expired_memories()
                
                self.memory_stats["cleanup_count"] += 1
                
            except Exception as e:
                logger.error(f"记忆清理任务错误: {e}")
    
    async def _cleanup_expired_memories(self) -> None:
        """清理过期记忆"""
        # 清理过期的向量数据库记忆
        await self.vector_db.cleanup_expired_memories()
    
    async def _promote_working_memory(self, memory: Dict[str, Any]) -> None:
        """提升工作记忆"""
        # 将工作记忆提升到情节记忆
        await self._store_episodic_memory(memory)
        memory_id = memory["id"]
        if memory_id in self.working_memory:
            del self.working_memory[memory_id]
    
    async def _consolidate_working_to_episodic(self, memory: Dict[str, Any]) -> None:
        """将工作记忆巩固到情节记忆"""
        await self._store_episodic_memory(memory)
        memory_id = memory["id"]
        if memory_id in self.working_memory:
            del self.working_memory[memory_id]
    
    async def _consolidate_episodic_to_semantic(self, agent_id: str) -> None:
        """将情节记忆巩固到语义记忆"""
        # 简化的巩固逻辑
        pass
    
    async def _get_working_memories(self, agent_id: str, memory_type: Optional[str], limit: int) -> List[Dict[str, Any]]:
        """获取工作记忆"""
        memories = []
        for memory in self.working_memory.values():
            if memory["agent_id"] == agent_id and (not memory_type or memory["memory_type"] == memory_type):
                memories.append(memory)
        return memories[:limit]
    
    async def _get_episodic_memories(self, agent_id: str, memory_type: Optional[str], limit: int) -> List[Dict[str, Any]]:
        """获取情节记忆"""
        try:
            memories = await self.vector_db.get_agent_memories(
                agent_id=agent_id,
                memory_type="episodic",
                limit=limit
            )
            
            results = []
            for memory in memories:
                content = memory.get("content", {})
                if isinstance(content, dict):
                    results.append({
                        "id": content.get("id"),
                        "content": content.get("content"),
                        "metadata": content.get("metadata"),
                        "importance": memory.get("importance_score", 0.5),
                        "created_at": memory.get("created_at"),
                        "level": MemoryLevel.EPISODIC
                    })
            
            return results
            
        except Exception as e:
            logger.error(f"获取情节记忆失败: {e}")
            return []
    
    async def _get_semantic_memories(self, agent_id: str, memory_type: Optional[str], limit: int) -> List[Dict[str, Any]]:
        """获取语义记忆"""
        try:
            memories = await self.vector_db.get_agent_memories(
                agent_id=agent_id,
                memory_type="semantic",
                limit=limit
            )
            
            results = []
            for memory in memories:
                content = memory.get("content", {})
                if isinstance(content, dict):
                    results.append({
                        "id": content.get("id"),
                        "content": content.get("content"),
                        "metadata": content.get("metadata"),
                        "importance": memory.get("importance_score", 0.5),
                        "created_at": memory.get("created_at"),
                        "level": MemoryLevel.SEMANTIC
                    })
            
            return results
            
        except Exception as e:
            logger.error(f"获取语义记忆失败: {e}")
            return []
    
    async def _update_episodic_memory(self, memory: Dict[str, Any]) -> None:
        """更新情节记忆"""
        # 简化实现
        pass
    
    async def _update_semantic_memory(self, memory: Dict[str, Any]) -> None:
        """更新语义记忆"""
        # 简化实现
        pass
    
    async def _delete_episodic_memory(self, memory_id: str) -> None:
        """删除情节记忆"""
        # 简化实现
        pass
    
    async def _delete_semantic_memory(self, memory_id: str) -> None:
        """删除语义记忆"""
        # 简化实现
        pass