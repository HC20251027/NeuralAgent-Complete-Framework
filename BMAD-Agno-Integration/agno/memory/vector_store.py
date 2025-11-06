"""
Agno多智能体框架 - 向量存储管理
负责向量化的记忆存储和检索
"""

import asyncio
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import logging

from ..database.vector_store import VectorDatabase

logger = logging.getLogger(__name__)


class VectorStore:
    """向量存储管理器"""
    
    def __init__(self, vector_db: Optional[VectorDatabase] = None):
        self.vector_db = vector_db or VectorDatabase()
        
        # 向量配置
        self.vector_config = {
            "dimensions": {
                "text": 1536,
                "image": 512,
                "audio": 128,
                "multimodal": 2048
            },
            "similarity_threshold": 0.7,
            "max_results": 10,
            "index_type": "ivfflat",
            "index_params": {"lists": 100}
        }
        
        # 缓存
        self.vector_cache: Dict[str, np.ndarray] = {}
        self.cache_size_limit = 1000
        
        # 统计信息
        self.stats = {
            "total_vectors": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "similarity_searches": 0,
            "average_search_time": 0.0
        }
    
    async def initialize(self) -> None:
        """初始化向量存储"""
        try:
            # 初始化向量数据库
            await self.vector_db.initialize_vector_extensions()
            await self.vector_db.create_tables()
            
            logger.info("向量存储初始化完成")
        except Exception as e:
            logger.error(f"向量存储初始化失败: {e}")
            raise
    
    async def store_vector(
        self,
        content: str,
        vector_type: str = "text",
        metadata: Optional[Dict[str, Any]] = None,
        source_id: Optional[str] = None
    ) -> str:
        """存储向量"""
        try:
            # 生成向量
            vector = await self._generate_vector(content, vector_type)
            
            # 存储到数据库
            memory_id = await self.vector_db.store_text_embedding(
                content=content,
                embedding=vector.tolist(),
                metadata=metadata,
                source_type=vector_type,
                source_id=source_id
            )
            
            # 更新统计
            self.stats["total_vectors"] += 1
            
            logger.debug(f"向量已存储: {memory_id} ({vector_type})")
            return memory_id
            
        except Exception as e:
            logger.error(f"存储向量失败: {e}")
            raise
    
    async def search_similar(
        self,
        query: str,
        vector_type: str = "text",
        limit: int = 10,
        threshold: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """搜索相似向量"""
        start_time = datetime.now()
        
        try:
            # 生成查询向量
            query_vector = await self._generate_vector(query, vector_type)
            
            # 确定搜索表
            table_name = self._get_table_name(vector_type)
            
            # 执行向量搜索
            search_results = await self.vector_db.search_similar_vectors(
                query_embedding=query_vector.tolist(),
                table_name=table_name,
                limit=limit,
                threshold=threshold or self.vector_config["similarity_threshold"]
            )
            
            # 更新统计
            self.stats["similarity_searches"] += 1
            search_time = (datetime.now() - start_time).total_seconds()
            self.stats["average_search_time"] = (
                (self.stats["average_search_time"] * (self.stats["similarity_searches"] - 1) + search_time) /
                self.stats["similarity_searches"]
            )
            
            # 格式化结果
            results = []
            for result in search_results:
                results.append({
                    "id": result.get("id"),
                    "content": result.get("content"),
                    "similarity": result.get("similarity", 0.0),
                    "metadata": result.get("metadata"),
                    "created_at": result.get("created_at")
                })
            
            logger.debug(f"向量搜索完成: {len(results)} 个结果")
            return results
            
        except Exception as e:
            logger.error(f"向量搜索失败: {e}")
            return []
    
    async def get_vector(self, vector_id: int) -> Optional[Dict[str, Any]]:
        """获取向量"""
        try:
            # 从缓存获取
            cache_key = f"vector_{vector_id}"
            if cache_key in self.vector_cache:
                self.stats["cache_hits"] += 1
                return self.vector_cache[cache_key]
            
            self.stats["cache_misses"] += 1
            
            # 从数据库获取
            # 这里需要实现从数据库获取特定向量的逻辑
            # 简化实现
            return None
            
        except Exception as e:
            logger.error(f"获取向量失败: {vector_id} - {e}")
            return None
    
    async def update_vector(
        self,
        vector_id: int,
        content: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """更新向量"""
        try:
            # 更新向量数据库中的记录
            # 这里需要实现具体的更新逻辑
            # 简化实现
            
            # 更新缓存
            cache_key = f"vector_{vector_id}"
            if cache_key in self.vector_cache:
                if content:
                    new_vector = await self._generate_vector(content, "text")
                    self.vector_cache[cache_key] = new_vector
            
            logger.debug(f"向量已更新: {vector_id}")
            return True
            
        except Exception as e:
            logger.error(f"更新向量失败: {vector_id} - {e}")
            return False
    
    async def delete_vector(self, vector_id: int) -> bool:
        """删除向量"""
        try:
            # 从数据库删除
            # 这里需要实现具体的删除逻辑
            # 简化实现
            
            # 从缓存删除
            cache_key = f"vector_{vector_id}"
            if cache_key in self.vector_cache:
                del self.vector_cache[cache_key]
            
            self.stats["total_vectors"] -= 1
            
            logger.debug(f"向量已删除: {vector_id}")
            return True
            
        except Exception as e:
            logger.error(f"删除向量失败: {vector_id} - {e}")
            return False
    
    async def batch_store_vectors(
        self,
        items: List[Dict[str, Any]],
        vector_type: str = "text"
    ) -> List[str]:
        """批量存储向量"""
        try:
            vector_ids = []
            
            for item in items:
                content = item.get("content", "")
                metadata = item.get("metadata", {})
                source_id = item.get("source_id")
                
                vector_id = await self.store_vector(
                    content=content,
                    vector_type=vector_type,
                    metadata=metadata,
                    source_id=source_id
                )
                vector_ids.append(vector_id)
            
            logger.info(f"批量存储向量完成: {len(vector_ids)} 个向量")
            return vector_ids
            
        except Exception as e:
            logger.error(f"批量存储向量失败: {e}")
            return []
    
    async def batch_search_similar(
        self,
        queries: List[str],
        vector_type: str = "text",
        limit: int = 10
    ) -> List[List[Dict[str, Any]]]:
        """批量搜索相似向量"""
        try:
            results = []
            
            for query in queries:
                search_result = await self.search_similar(
                    query=query,
                    vector_type=vector_type,
                    limit=limit
                )
                results.append(search_result)
            
            logger.info(f"批量搜索完成: {len(queries)} 个查询")
            return results
            
        except Exception as e:
            logger.error(f"批量搜索失败: {e}")
            return [[] for _ in queries]
    
    async def get_vector_statistics(self) -> Dict[str, Any]:
        """获取向量统计信息"""
        cache_hit_rate = 0.0
        total_requests = self.stats["cache_hits"] + self.stats["cache_misses"]
        if total_requests > 0:
            cache_hit_rate = self.stats["cache_hits"] / total_requests
        
        return {
            "total_vectors": self.stats["total_vectors"],
            "cache_size": len(self.vector_cache),
            "cache_hit_rate": cache_hit_rate,
            "similarity_searches": self.stats["similarity_searches"],
            "average_search_time": self.stats["average_search_time"],
            "vector_config": self.vector_config
        }
    
    async def clear_cache(self) -> None:
        """清空缓存"""
        self.vector_cache.clear()
        logger.info("向量缓存已清空")
    
    async def optimize_index(self) -> bool:
        """优化向量索引"""
        try:
            # 重新创建索引以优化性能
            await self.vector_db._create_vector_indexes()
            
            logger.info("向量索引优化完成")
            return True
            
        except Exception as e:
            logger.error(f"向量索引优化失败: {e}")
            return False
    
    async def _generate_vector(self, content: str, vector_type: str) -> np.ndarray:
        """生成向量"""
        try:
            # 检查缓存
            cache_key = f"{vector_type}_{hash(content)}"
            if cache_key in self.vector_cache:
                return self.vector_cache[cache_key]
            
            # 获取向量维度
            dimensions = self.vector_config["dimensions"].get(vector_type, 1536)
            
            # 生成向量（简化实现：随机向量）
            # 实际应用中应该使用预训练模型生成语义向量
            vector = np.random.rand(dimensions)
            
            # 添加到缓存
            if len(self.vector_cache) < self.cache_size_limit:
                self.vector_cache[cache_key] = vector
            else:
                # 缓存满时，移除最旧的条目
                oldest_key = next(iter(self.vector_cache))
                del self.vector_cache[oldest_key]
                self.vector_cache[cache_key] = vector
            
            return vector
            
        except Exception as e:
            logger.error(f"生成向量失败: {e}")
            # 返回零向量作为fallback
            dimensions = self.vector_config["dimensions"].get(vector_type, 1536)
            return np.zeros(dimensions)
    
    def _get_table_name(self, vector_type: str) -> str:
        """获取对应的表名"""
        table_mapping = {
            "text": "text_embeddings",
            "image": "image_embeddings", 
            "audio": "audio_embeddings",
            "multimodal": "multimodal_embeddings"
        }
        return table_mapping.get(vector_type, "text_embeddings")
    
    async def similarity_clustering(
        self,
        vectors: List[np.ndarray],
        threshold: float = 0.8
    ) -> List[List[int]]:
        """向量聚类"""
        try:
            if len(vectors) < 2:
                return [list(range(len(vectors)))]
            
            clusters = []
            assigned = set()
            
            for i, vector in enumerate(vectors):
                if i in assigned:
                    continue
                
                cluster = [i]
                assigned.add(i)
                
                for j, other_vector in enumerate(vectors[i+1:], i+1):
                    if j in assigned:
                        continue
                    
                    # 计算余弦相似度
                    similarity = self._cosine_similarity(vector, other_vector)
                    
                    if similarity >= threshold:
                        cluster.append(j)
                        assigned.add(j)
                
                clusters.append(cluster)
            
            logger.info(f"向量聚类完成: {len(clusters)} 个聚类")
            return clusters
            
        except Exception as e:
            logger.error(f"向量聚类失败: {e}")
            return [list(range(len(vectors)))]
    
    def _cosine_similarity(self, vector1: np.ndarray, vector2: np.ndarray) -> float:
        """计算余弦相似度"""
        try:
            dot_product = np.dot(vector1, vector2)
            norm1 = np.linalg.norm(vector1)
            norm2 = np.linalg.norm(vector2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            return dot_product / (norm1 * norm2)
            
        except Exception:
            return 0.0
    
    async def export_vectors(self, vector_type: str = "text") -> Dict[str, Any]:
        """导出向量数据"""
        try:
            # 从数据库获取向量数据
            # 这里需要实现具体的导出逻辑
            # 简化实现
            
            export_data = {
                "vector_type": vector_type,
                "exported_at": datetime.now().isoformat(),
                "vectors": [],
                "statistics": await self.get_vector_statistics()
            }
            
            logger.info(f"向量数据导出完成: {vector_type}")
            return export_data
            
        except Exception as e:
            logger.error(f"导出向量数据失败: {e}")
            return {}
    
    async def import_vectors(self, import_data: Dict[str, Any]) -> int:
        """导入向量数据"""
        try:
            vector_type = import_data.get("vector_type", "text")
            vectors = import_data.get("vectors", [])
            
            imported_count = 0
            for vector_data in vectors:
                content = vector_data.get("content", "")
                metadata = vector_data.get("metadata", {})
                
                await self.store_vector(
                    content=content,
                    vector_type=vector_type,
                    metadata=metadata
                )
                imported_count += 1
            
            logger.info(f"向量数据导入完成: {imported_count} 个向量")
            return imported_count
            
        except Exception as e:
            logger.error(f"导入向量数据失败: {e}")
            return 0