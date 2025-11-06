"""
数据库迁移管理模块
负责数据库结构的版本管理和迁移
"""

import os
import re
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from .connection import db_connection

logger = logging.getLogger(__name__)


class DatabaseMigration:
    """数据库迁移管理器"""
    
    def __init__(self, migrations_dir: str = "migrations"):
        self.db = db_connection
        self.migrations_dir = migrations_dir
        self.migration_table = "schema_migrations"
    
    async def initialize_migration_system(self) -> None:
        """初始化迁移系统"""
        try:
            # 创建迁移记录表
            await self.db.execute_command(f"""
            CREATE TABLE IF NOT EXISTS {self.migration_table} (
                id SERIAL PRIMARY KEY,
                version VARCHAR(255) UNIQUE NOT NULL,
                name VARCHAR(255) NOT NULL,
                executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                checksum VARCHAR(64)
            );
            """)
            
            logger.info("数据库迁移系统初始化成功")
        except Exception as e:
            logger.error(f"数据库迁移系统初始化失败: {e}")
            raise
    
    def _get_migration_files(self) -> List[Dict[str, Any]]:
        """获取所有迁移文件"""
        if not os.path.exists(self.migrations_dir):
            return []
        
        migration_files = []
        for filename in os.listdir(self.migrations_dir):
            if filename.endswith('.sql') and re.match(r'^\d{4}_\d{2}_\d{2}_\d{6}_.*\.sql$', filename):
                filepath = os.path.join(self.migrations_dir, filename)
                version = filename.split('_')[0:3]  # YYYY_MM_DD
                version_str = '_'.join(version)
                timestamp = datetime.strptime(version_str, '%Y_%m_%d')
                
                migration_files.append({
                    'filename': filename,
                    'filepath': filepath,
                    'version': version_str,
                    'timestamp': timestamp,
                    'name': filename.replace('.sql', '').split('_', 3)[-1]
                })
        
        return sorted(migration_files, key=lambda x: x['timestamp'])
    
    async def create_migration(self, name: str) -> str:
        """创建新的迁移文件"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{timestamp}_{name}.sql"
            filepath = os.path.join(self.migrations_dir, filename)
            
            # 确保迁移目录存在
            os.makedirs(self.migrations_dir, exist_ok=True)
            
            # 创建迁移文件模板
            template = f"""-- Migration: {name}
-- Created: {datetime.now().isoformat()}

-- 在这里添加您的SQL迁移语句
-- 例如:
-- CREATE TABLE example_table (
--     id SERIAL PRIMARY KEY,
--     name VARCHAR(255) NOT NULL
-- );

"""
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(template)
            
            logger.info(f"创建迁移文件: {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"创建迁移文件失败: {e}")
            raise
    
    async def get_executed_migrations(self) -> List[str]:
        """获取已执行的迁移版本"""
        try:
            query = f"SELECT version FROM {self.migration_table} ORDER BY version;"
            results = await self.db.execute_query(query)
            return [row['version'] for row in results]
        except Exception as e:
            logger.error(f"获取已执行迁移失败: {e}")
            return []
    
    def _calculate_checksum(self, content: str) -> str:
        """计算文件校验和"""
        import hashlib
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    async def execute_migration(self, migration: Dict[str, Any]) -> bool:
        """执行单个迁移"""
        try:
            # 检查迁移是否已执行
            executed_migrations = await self.get_executed_migrations()
            if migration['version'] in executed_migrations:
                logger.info(f"迁移已执行，跳过: {migration['version']}")
                return True
            
            # 读取迁移文件内容
            with open(migration['filepath'], 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 计算校验和
            checksum = self._calculate_checksum(content)
            
            # 执行迁移SQL（分割多个语句）
            sql_statements = [stmt.strip() for stmt in content.split(';') if stmt.strip()]
            
            for statement in sql_statements:
                if statement and not statement.startswith('--'):
                    await self.db.execute_command(statement)
            
            # 记录迁移执行
            await self.db.execute_command(f"""
            INSERT INTO {self.migration_table} (version, name, checksum)
            VALUES ($1, $2, $3);
            """, migration['version'], migration['name'], checksum)
            
            logger.info(f"迁移执行成功: {migration['version']}")
            return True
        except Exception as e:
            logger.error(f"迁移执行失败: {migration['version']} - {e}")
            raise
    
    async def migrate(self, target_version: Optional[str] = None) -> int:
        """执行数据库迁移"""
        try:
            await self.initialize_migration_system()
            
            migration_files = self._get_migration_files()
            executed_migrations = await self.get_executed_migrations()
            
            executed_count = 0
            
            for migration in migration_files:
                # 如果指定了目标版本，只执行到该版本
                if target_version and migration['version'] > target_version:
                    break
                
                # 执行未执行的迁移
                if migration['version'] not in executed_migrations:
                    await self.execute_migration(migration)
                    executed_count += 1
            
            logger.info(f"数据库迁移完成，执行了 {executed_count} 个迁移")
            return executed_count
        except Exception as e:
            logger.error(f"数据库迁移失败: {e}")
            raise
    
    async def rollback_migration(self, version: str) -> bool:
        """回滚指定版本的迁移"""
        try:
            # 查找回滚文件
            rollback_file = os.path.join(self.migrations_dir, f"{version}_rollback.sql")
            
            if not os.path.exists(rollback_file):
                logger.warning(f"未找到回滚文件: {rollback_file}")
                return False
            
            # 执行回滚SQL
            with open(rollback_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            sql_statements = [stmt.strip() for stmt in content.split(';') if stmt.strip()]
            
            for statement in sql_statements:
                if statement and not statement.startswith('--'):
                    await self.db.execute_command(statement)
            
            # 删除迁移记录
            await self.db.execute_command(
                f"DELETE FROM {self.migration_table} WHERE version = $1;",
                version
            )
            
            logger.info(f"迁移回滚成功: {version}")
            return True
        except Exception as e:
            logger.error(f"迁移回滚失败: {version} - {e}")
            raise
    
    async def get_migration_status(self) -> Dict[str, Any]:
        """获取迁移状态"""
        try:
            migration_files = self._get_migration_files()
            executed_migrations = await self.get_executed_migrations()
            
            pending_migrations = []
            executed_list = []
            
            for migration in migration_files:
                if migration['version'] in executed_migrations:
                    executed_list.append(migration)
                else:
                    pending_migrations.append(migration)
            
            return {
                'total_migrations': len(migration_files),
                'executed_count': len(executed_list),
                'pending_count': len(pending_migrations),
                'executed_migrations': executed_list,
                'pending_migrations': pending_migrations,
                'latest_version': migration_files[-1]['version'] if migration_files else None
            }
        except Exception as e:
            logger.error(f"获取迁移状态失败: {e}")
            raise