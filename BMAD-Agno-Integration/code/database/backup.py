"""
数据库备份和恢复模块
提供数据库备份、恢复和维护功能
"""

import os
import shutil
import subprocess
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import logging
import json

from .connection import db_connection

logger = logging.getLogger(__name__)


class DatabaseBackup:
    """数据库备份管理器"""
    
    def __init__(self, backup_dir: str = "backups"):
        self.db = db_connection
        self.backup_dir = backup_dir
        self.max_backup_age_days = 30  # 备份保留天数
    
    async def initialize_backup_system(self) -> None:
        """初始化备份系统"""
        try:
            # 确保备份目录存在
            os.makedirs(self.backup_dir, exist_ok=True)
            
            # 创建备份记录表
            await self.db.execute_command("""
            CREATE TABLE IF NOT EXISTS backup_records (
                id SERIAL PRIMARY KEY,
                backup_type VARCHAR(50) NOT NULL,
                file_path TEXT NOT NULL,
                file_size BIGINT,
                checksum VARCHAR(64),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                description TEXT
            );
            """)
            
            logger.info("数据库备份系统初始化成功")
        except Exception as e:
            logger.error(f"数据库备份系统初始化失败: {e}")
            raise
    
    def _get_backup_filename(self, backup_type: str = "full") -> str:
        """生成备份文件名"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return f"backup_{backup_type}_{timestamp}.sql"
    
    def _calculate_file_checksum(self, filepath: str) -> str:
        """计算文件校验和"""
        import hashlib
        hash_md5 = hashlib.md5()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    async def create_full_backup(self, description: str = "完整备份") -> str:
        """创建完整数据库备份"""
        try:
            await self.initialize_backup_system()
            
            filename = self._get_backup_filename("full")
            filepath = os.path.join(self.backup_dir, filename)
            
            # 获取数据库连接信息
            config = self.db.get_config()
            
            # 使用pg_dump创建备份
            cmd = [
                'pg_dump',
                '-h', config['host'],
                '-p', str(config['port']),
                '-U', config['user'],
                '-d', config['database'],
                '-f', filepath,
                '--verbose',
                '--no-password'
            ]
            
            # 设置密码环境变量
            env = os.environ.copy()
            env['PGPASSWORD'] = config['password']
            
            # 执行备份命令
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)
            
            if result.returncode != 0:
                raise Exception(f"pg_dump失败: {result.stderr}")
            
            # 计算文件大小和校验和
            file_size = os.path.getsize(filepath)
            checksum = self._calculate_file_checksum(filepath)
            
            # 记录备份信息
            await self.db.execute_command("""
            INSERT INTO backup_records (backup_type, file_path, file_size, checksum, description)
            VALUES ($1, $2, $3, $4, $5);
            """, "full", filepath, file_size, checksum, description)
            
            logger.info(f"完整备份创建成功: {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"创建完整备份失败: {e}")
            raise
    
    async def create_vector_backup(self, description: str = "向量数据备份") -> str:
        """创建向量数据专用备份"""
        try:
            filename = self._get_backup_filename("vector")
            filepath = os.path.join(self.backup_dir, filename)
            
            # 只备份向量相关表
            vector_tables = [
                'text_embeddings',
                'image_embeddings', 
                'audio_embeddings',
                'multimodal_embeddings',
                'agent_memories'
            ]
            
            config = self.db.get_config()
            
            # 构建pg_dump命令
            table_args = []
            for table in vector_tables:
                table_args.extend(['-t', table])
            
            cmd = [
                'pg_dump',
                '-h', config['host'],
                '-p', str(config['port']),
                '-U', config['user'],
                '-d', config['database'],
                '-f', filepath,
                '--verbose',
                '--no-password'
            ] + table_args
            
            # 设置密码环境变量
            env = os.environ.copy()
            env['PGPASSWORD'] = config['password']
            
            # 执行备份命令
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)
            
            if result.returncode != 0:
                raise Exception(f"pg_dump向量数据失败: {result.stderr}")
            
            # 计算文件大小和校验和
            file_size = os.path.getsize(filepath)
            checksum = self._calculate_file_checksum(filepath)
            
            # 记录备份信息
            await self.db.execute_command("""
            INSERT INTO backup_records (backup_type, file_path, file_size, checksum, description)
            VALUES ($1, $2, $3, $4, $5);
            """, "vector", filepath, file_size, checksum, description)
            
            logger.info(f"向量数据备份创建成功: {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"创建向量数据备份失败: {e}")
            raise
    
    async def restore_backup(self, backup_file: str, restore_type: str = "full") -> bool:
        """从备份文件恢复数据库"""
        try:
            if not os.path.exists(backup_file):
                raise FileNotFoundError(f"备份文件不存在: {backup_file}")
            
            config = self.db.get_config()
            
            # 验证备份文件校验和
            expected_checksum = await self._get_backup_checksum(backup_file)
            if expected_checksum:
                actual_checksum = self._calculate_file_checksum(backup_file)
                if actual_checksum != expected_checksum:
                    raise Exception(f"备份文件校验和不匹配")
            
            # 使用psql恢复数据
            cmd = [
                'psql',
                '-h', config['host'],
                '-p', str(config['port']),
                '-U', config['user'],
                '-d', config['database'],
                '-f', backup_file,
                '--quiet',
                '--no-password'
            ]
            
            # 设置密码环境变量
            env = os.environ.copy()
            env['PGPASSWORD'] = config['password']
            
            # 执行恢复命令
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)
            
            if result.returncode != 0:
                raise Exception(f"psql恢复失败: {result.stderr}")
            
            logger.info(f"数据库恢复成功: {backup_file}")
            return True
        except Exception as e:
            logger.error(f"数据库恢复失败: {e}")
            raise
    
    async def _get_backup_checksum(self, backup_file: str) -> Optional[str]:
        """获取备份文件的校验和"""
        try:
            query = """
            SELECT checksum FROM backup_records 
            WHERE file_path = $1 
            ORDER BY created_at DESC 
            LIMIT 1;
            """
            result = await self.db.execute_query(query, backup_file)
            return result[0]['checksum'] if result else None
        except Exception:
            return None
    
    async def list_backups(self, backup_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """列出所有备份"""
        try:
            if backup_type:
                query = """
                SELECT * FROM backup_records 
                WHERE backup_type = $1 
                ORDER BY created_at DESC;
                """
                results = await self.db.execute_query(query, backup_type)
            else:
                query = """
                SELECT * FROM backup_records 
                ORDER BY created_at DESC;
                """
                results = await self.db.execute_query(query)
            
            return results
        except Exception as e:
            logger.error(f"获取备份列表失败: {e}")
            raise
    
    async def cleanup_old_backups(self) -> int:
        """清理过期备份"""
        try:
            cutoff_date = datetime.now() - timedelta(days=self.max_backup_age_days)
            
            # 获取过期备份列表
            query = """
            SELECT file_path FROM backup_records 
            WHERE created_at < $1;
            """
            old_backups = await self.db.execute_query(query, cutoff_date)
            
            deleted_count = 0
            for backup in old_backups:
                try:
                    # 删除物理文件
                    if os.path.exists(backup['file_path']):
                        os.remove(backup['file_path'])
                    
                    # 删除数据库记录
                    await self.db.execute_command(
                        "DELETE FROM backup_records WHERE file_path = $1;",
                        backup['file_path']
                    )
                    
                    deleted_count += 1
                    logger.info(f"删除过期备份: {backup['file_path']}")
                except Exception as e:
                    logger.warning(f"删除备份文件失败: {backup['file_path']} - {e}")
            
            logger.info(f"清理过期备份完成，删除了 {deleted_count} 个备份")
            return deleted_count
        except Exception as e:
            logger.error(f"清理过期备份失败: {e}")
            raise
    
    async def get_backup_info(self, backup_file: str) -> Optional[Dict[str, Any]]:
        """获取备份文件详细信息"""
        try:
            query = """
            SELECT * FROM backup_records 
            WHERE file_path = $1 
            ORDER BY created_at DESC 
            LIMIT 1;
            """
            result = await self.db.execute_query(query, backup_file)
            return result[0] if result else None
        except Exception as e:
            logger.error(f"获取备份信息失败: {e}")
            return None
    
    async def verify_backup(self, backup_file: str) -> Dict[str, Any]:
        """验证备份文件完整性"""
        try:
            backup_info = await self.get_backup_info(backup_file)
            if not backup_info:
                return {'valid': False, 'error': '备份记录不存在'}
            
            # 检查文件是否存在
            if not os.path.exists(backup_file):
                return {'valid': False, 'error': '备份文件不存在'}
            
            # 验证文件大小
            actual_size = os.path.getsize(backup_file)
            if actual_size != backup_info['file_size']:
                return {'valid': False, 'error': '文件大小不匹配'}
            
            # 验证校验和
            actual_checksum = self._calculate_file_checksum(backup_file)
            if actual_checksum != backup_info['checksum']:
                return {'valid': False, 'error': '文件校验和不匹配'}
            
            return {
                'valid': True,
                'file_size': actual_size,
                'checksum': actual_checksum,
                'created_at': backup_info['created_at'],
                'backup_type': backup_info['backup_type']
            }
        except Exception as e:
            logger.error(f"验证备份文件失败: {e}")
            return {'valid': False, 'error': str(e)}