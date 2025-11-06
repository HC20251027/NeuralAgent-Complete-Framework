"""
数据库连接管理模块
负责PostgreSQL + PgVector数据库的连接和配置管理
"""

import os
import asyncpg
from typing import Optional, Dict, Any, List
from contextlib import asynccontextmanager
import logging

logger = logging.getLogger(__name__)


class DatabaseConnection:
    """数据库连接管理器"""
    
    def __init__(self):
        self._connection_pool: Optional[asyncpg.Pool] = None
        self._config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """加载数据库配置"""
        return {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': int(os.getenv('DB_PORT', '5432')),
            'database': os.getenv('DB_NAME', 'ai_agents'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', ''),
            'min_size': int(os.getenv('DB_MIN_CONNECTIONS', '5')),
            'max_size': int(os.getenv('DB_MAX_CONNECTIONS', '20')),
            'command_timeout': int(os.getenv('DB_COMMAND_TIMEOUT', '60'))
        }
    
    async def initialize(self) -> None:
        """初始化数据库连接池"""
        try:
            self._connection_pool = await asyncpg.create_pool(
                host=self._config['host'],
                port=self._config['port'],
                database=self._config['database'],
                user=self._config['user'],
                password=self._config['password'],
                min_size=self._config['min_size'],
                max_size=self._config['max_size'],
                command_timeout=self._config['command_timeout']
            )
            logger.info("数据库连接池初始化成功")
        except Exception as e:
            logger.error(f"数据库连接池初始化失败: {e}")
            raise
    
    async def close(self) -> None:
        """关闭数据库连接池"""
        if self._connection_pool:
            await self._connection_pool.close()
            logger.info("数据库连接池已关闭")
    
    @asynccontextmanager
    async def get_connection(self):
        """获取数据库连接的上下文管理器"""
        if not self._connection_pool:
            await self.initialize()
        
        async with self._connection_pool.acquire() as connection:
            try:
                yield connection
            except Exception as e:
                logger.error(f"数据库操作错误: {e}")
                raise
    
    async def execute_query(self, query: str, *args) -> List[Dict[str, Any]]:
        """执行查询SQL"""
        async with self.get_connection() as conn:
            try:
                rows = await conn.fetch(query, *args)
                return [dict(row) for row in rows]
            except Exception as e:
                logger.error(f"查询执行失败: {e}")
                raise
    
    async def execute_command(self, command: str, *args) -> str:
        """执行非查询SQL命令"""
        async with self.get_connection() as conn:
            try:
                result = await conn.execute(command, *args)
                return result
            except Exception as e:
                logger.error(f"命令执行失败: {e}")
                raise
    
    async def execute_transaction(self, queries: List[tuple]) -> List[Any]:
        """执行事务"""
        async with self.get_connection() as conn:
            async with conn.transaction():
                results = []
                for query, args in queries:
                    result = await conn.fetch(query, *args)
                    results.append(result)
                return results
    
    def get_config(self) -> Dict[str, Any]:
        """获取数据库配置"""
        return self._config.copy()
    
    async def test_connection(self) -> bool:
        """测试数据库连接"""
        try:
            async with self.get_connection() as conn:
                await conn.fetchval('SELECT 1')
            return True
        except Exception as e:
            logger.error(f"数据库连接测试失败: {e}")
            return False


# 全局数据库连接实例
db_connection = DatabaseConnection()