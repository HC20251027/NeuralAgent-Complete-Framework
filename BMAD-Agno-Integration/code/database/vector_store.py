"""
向量数据库操作模块
基于PgVector的向量存储和检索功能
"""

import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import json
import logging

from .connection import db_connection

logger = logging.getLogger(__name__)


class VectorDatabase:
    """向量数据库操作类"""
    
    # 向量维度配置
    VECTOR_DIMENSIONS = {
        'text': 1536,  # OpenAI text-embedding-ada-002
        'image': 512,  # 图像特征向量维度
        'audio': 128,  # 音频特征向量维度
        'multimodal': 2048  # 多模态融合向量维度
    }
    
    def __init__(self):
        self.db = db_connection
    
    async def initialize_vector_extensions(self) -> None:
        """初始化向量扩展"""
        try:
            # 启用pgvector扩展
            await self.db.execute_command("CREATE EXTENSION IF NOT EXISTS vector;")
            
            # 创建向量索引（如果不存在）
            await self._create_vector_indexes()
            
            logger.info("向量数据库扩展初始化成功")
        except Exception as e:
            logger.error(f"向量数据库扩展初始化失败: {e}")
            raise
    
    async def _create_vector_indexes(self) -> None:
        """创建向量索引"""
        indexes = [
            # 文本向量索引
            "CREATE INDEX IF NOT EXISTS idx_text_embeddings_vector ON text_embeddings USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);",
            # 图像向量索引
            "CREATE INDEX IF NOT EXISTS idx_image_embeddings_vector ON image_embeddings USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);",
            # 音频向量索引
            "CREATE INDEX IF NOT EXISTS idx_audio_embeddings_vector ON audio_embeddings USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);",
            # 多模态向量索引
            "CREATE INDEX IF NOT EXISTS idx_multimodal_embeddings_vector ON multimodal_embeddings USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);"
        ]
        
        for index_sql in indexes:
            try:
                await self.db.execute_command(index_sql)
            except Exception as e:
                logger.warning(f"创建索引失败: {e}")
    
    async def create_tables(self) -> None:
        """创建向量存储表"""
        tables = [
            # 文本嵌入表
            """
            CREATE TABLE IF NOT EXISTS text_embeddings (
                id SERIAL PRIMARY KEY,
                content TEXT NOT NULL,
                embedding vector(1536),
                metadata JSONB,
                source_type VARCHAR(50),
                source_id VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """,
            # 图像嵌入表
            """
            CREATE TABLE IF NOT EXISTS image_embeddings (
                id SERIAL PRIMARY KEY,
                image_path TEXT NOT NULL,
                image_data BYTEA,
                embedding vector(512),
                metadata JSONB,
                source_type VARCHAR(50),
                source_id VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """,
            # 音频嵌入表
            """
            CREATE TABLE IF NOT EXISTS audio_embeddings (
                id SERIAL PRIMARY KEY,
                audio_path TEXT NOT NULL,
                audio_data BYTEA,
                embedding vector(128),
                metadata JSONB,
                source_type VARCHAR(50),
                source_id VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """,
            # 多模态嵌入表
            """
            CREATE TABLE IF NOT EXISTS multimodal_embeddings (
                id SERIAL PRIMARY KEY,
                content TEXT,
                image_path TEXT,
                audio_path TEXT,
                embedding vector(2048),
                metadata JSONB,
                source_type VARCHAR(50),
                source_id VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """,
            # 记忆存储表
            """
            CREATE TABLE IF NOT EXISTS agent_memories (
                id SERIAL PRIMARY KEY,
                agent_id VARCHAR(100) NOT NULL,
                memory_type VARCHAR(50) NOT NULL,
                content JSONB NOT NULL,
                embedding vector(1536),
                importance_score FLOAT DEFAULT 0.0,
                access_count INTEGER DEFAULT 0,
                last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP
            );
            """
        ]
        
        for table_sql in tables:
            try:
                await self.db.execute_command(table_sql)
            except Exception as e:
                logger.error(f"创建表失败: {e}")
                raise
    
    async def store_text_embedding(
        self, 
        content: str, 
        embedding: List[float], 
        metadata: Optional[Dict[str, Any]] = None,
        source_type: str = 'general',
        source_id: Optional[str] = None
    ) -> int:
        """存储文本嵌入"""
        try:
            query = """
            INSERT INTO text_embeddings (content, embedding, metadata, source_type, source_id)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING id;
            """
            
            result = await self.db.execute_query(
                query, 
                content, 
                embedding, 
                json.dumps(metadata) if metadata else None,
                source_type,
                source_id
            )
            
            return result[0]['id'] if result else None
        except Exception as e:
            logger.error(f"存储文本嵌入失败: {e}")
            raise
    
    async def store_image_embedding(
        self,
        image_path: str,
        embedding: List[float],
        image_data: Optional[bytes] = None,
        metadata: Optional[Dict[str, Any]] = None,
        source_type: str = 'image',
        source_id: Optional[str] = None
    ) -> int:
        """存储图像嵌入"""
        try:
            query = """
            INSERT INTO image_embeddings (image_path, image_data, embedding, metadata, source_type, source_id)
            VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING id;
            """
            
            result = await self.db.execute_query(
                query,
                image_path,
                image_data,
                embedding,
                json.dumps(metadata) if metadata else None,
                source_type,
                source_id
            )
            
            return result[0]['id'] if result else None
        except Exception as e:
            logger.error(f"存储图像嵌入失败: {e}")
            raise
    
    async def search_similar_vectors(
        self,
        query_embedding: List[float],
        table_name: str,
        limit: int = 10,
        threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """搜索相似向量"""
        try:
            valid_tables = ['text_embeddings', 'image_embeddings', 'audio_embeddings', 'multimodal_embeddings']
            if table_name not in valid_tables:
                raise ValueError(f"无效的表名: {table_name}")
            
            query = f"""
            SELECT *, 1 - (embedding <=> $1) as similarity
            FROM {table_name}
            WHERE 1 - (embedding <=> $1) > $2
            ORDER BY embedding <=> $1
            LIMIT $3;
            """
            
            results = await self.db.execute_query(
                query,
                query_embedding,
                threshold,
                limit
            )
            
            return results
        except Exception as e:
            logger.error(f"向量搜索失败: {e}")
            raise
    
    async def store_agent_memory(
        self,
        agent_id: str,
        memory_type: str,
        content: Dict[str, Any],
        embedding: Optional[List[float]] = None,
        importance_score: float = 0.0,
        expires_at: Optional[datetime] = None
    ) -> int:
        """存储智能体记忆"""
        try:
            query = """
            INSERT INTO agent_memories (agent_id, memory_type, content, embedding, importance_score, expires_at)
            VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING id;
            """
            
            result = await self.db.execute_query(
                query,
                agent_id,
                memory_type,
                json.dumps(content),
                embedding,
                importance_score,
                expires_at
            )
            
            return result[0]['id'] if result else None
        except Exception as e:
            logger.error(f"存储智能体记忆失败: {e}")
            raise
    
    async def get_agent_memories(
        self,
        agent_id: str,
        memory_type: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """获取智能体记忆"""
        try:
            if memory_type:
                query = """
                SELECT * FROM agent_memories
                WHERE agent_id = $1 AND memory_type = $2
                AND (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP)
                ORDER BY importance_score DESC, last_accessed DESC
                LIMIT $3;
                """
                results = await self.db.execute_query(query, agent_id, memory_type, limit)
            else:
                query = """
                SELECT * FROM agent_memories
                WHERE agent_id = $1
                AND (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP)
                ORDER BY importance_score DESC, last_accessed DESC
                LIMIT $2;
                """
                results = await self.db.execute_query(query, agent_id, limit)
            
            return results
        except Exception as e:
            logger.error(f"获取智能体记忆失败: {e}")
            raise
    
    async def update_memory_access(self, memory_id: int) -> None:
        """更新记忆访问信息"""
        try:
            query = """
            UPDATE agent_memories
            SET access_count = access_count + 1, last_accessed = CURRENT_TIMESTAMP
            WHERE id = $1;
            """
            await self.db.execute_command(query, memory_id)
        except Exception as e:
            logger.error(f"更新记忆访问信息失败: {e}")
            raise
    
    async def cleanup_expired_memories(self) -> int:
        """清理过期记忆"""
        try:
            query = """
            DELETE FROM agent_memories
            WHERE expires_at IS NOT NULL AND expires_at <= CURRENT_TIMESTAMP;
            """
            result = await self.db.execute_command(query)
            logger.info(f"清理过期记忆完成: {result}")
            return result
        except Exception as e:
            logger.error(f"清理过期记忆失败: {e}")
            raise