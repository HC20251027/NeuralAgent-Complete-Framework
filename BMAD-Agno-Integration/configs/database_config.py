"""
数据库配置管理模块
统一管理数据库配置和连接参数
"""

import os
import json
import yaml
from typing import Dict, Any, Optional, List
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class DatabaseConfig:
    """数据库配置管理器"""
    
    def __init__(self, config_file: Optional[str] = None):
        self.config_file = config_file or "configs/database.yaml"
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        config_path = Path(self.config_file)
        
        if not config_path.exists():
            logger.warning(f"配置文件不存在，使用默认配置: {config_path}")
            return self._get_default_config()
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                if config_path.suffix.lower() == '.yaml' or config_path.suffix.lower() == '.yml':
                    return yaml.safe_load(f)
                elif config_path.suffix.lower() == '.json':
                    return json.load(f)
                else:
                    raise ValueError(f"不支持的配置文件格式: {config_path.suffix}")
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            'database': {
                'host': os.getenv('DB_HOST', 'localhost'),
                'port': int(os.getenv('DB_PORT', '5432')),
                'database': os.getenv('DB_NAME', 'ai_agents'),
                'user': os.getenv('DB_USER', 'postgres'),
                'password': os.getenv('DB_PASSWORD', ''),
                'min_connections': int(os.getenv('DB_MIN_CONNECTIONS', '5')),
                'max_connections': int(os.getenv('DB_MAX_CONNECTIONS', '20')),
                'command_timeout': int(os.getenv('DB_COMMAND_TIMEOUT', '60')),
                'connection_retry': int(os.getenv('DB_CONNECTION_RETRY', '3')),
                'connection_retry_delay': int(os.getenv('DB_CONNECTION_RETRY_DELAY', '5'))
            },
            'vector': {
                'dimensions': {
                    'text': 1536,
                    'image': 512,
                    'audio': 128,
                    'multimodal': 2048
                },
                'index_type': 'ivfflat',
                'index_params': {
                    'lists': 100
                },
                'similarity_threshold': 0.7,
                'max_results': 10
            },
            'backup': {
                'backup_dir': os.getenv('BACKUP_DIR', 'backups'),
                'max_backup_age_days': int(os.getenv('MAX_BACKUP_AGE_DAYS', '30')),
                'auto_backup': os.getenv('AUTO_BACKUP', 'true').lower() == 'true',
                'backup_schedule': os.getenv('BACKUP_SCHEDULE', 'daily')
            },
            'migration': {
                'migrations_dir': os.getenv('MIGRATIONS_DIR', 'migrations'),
                'backup_before_migration': True
            },
            'monitoring': {
                'enable_metrics': True,
                'log_slow_queries': True,
                'slow_query_threshold': 1000,  # 毫秒
                'connection_pool_monitoring': True
            }
        }
    
    def get_database_config(self) -> Dict[str, Any]:
        """获取数据库连接配置"""
        return self.config.get('database', {})
    
    def get_vector_config(self) -> Dict[str, Any]:
        """获取向量数据库配置"""
        return self.config.get('vector', {})
    
    def get_backup_config(self) -> Dict[str, Any]:
        """获取备份配置"""
        return self.config.get('backup', {})
    
    def get_migration_config(self) -> Dict[str, Any]:
        """获取迁移配置"""
        return self.config.get('migration', {})
    
    def get_monitoring_config(self) -> Dict[str, Any]:
        """获取监控配置"""
        return self.config.get('monitoring', {})
    
    def update_config(self, key_path: str, value: Any) -> None:
        """更新配置项"""
        keys = key_path.split('.')
        config = self.config
        
        # 导航到父级
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        
        # 设置值
        config[keys[-1]] = value
        
        # 保存到文件
        self.save_config()
    
    def save_config(self) -> None:
        """保存配置到文件"""
        config_path = Path(self.config_file)
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                if config_path.suffix.lower() == '.yaml' or config_path.suffix.lower() == '.yml':
                    yaml.dump(self.config, f, default_flow_style=False, allow_unicode=True)
                elif config_path.suffix.lower() == '.json':
                    json.dump(self.config, f, indent=2, ensure_ascii=False)
                else:
                    raise ValueError(f"不支持的配置文件格式: {config_path.suffix}")
            
            logger.info(f"配置已保存到: {config_path}")
        except Exception as e:
            logger.error(f"保存配置失败: {e}")
            raise
    
    def validate_config(self) -> List[str]:
        """验证配置有效性"""
        errors = []
        
        # 验证数据库配置
        db_config = self.get_database_config()
        required_db_fields = ['host', 'port', 'database', 'user']
        
        for field in required_db_fields:
            if field not in db_config or not db_config[field]:
                errors.append(f"数据库配置缺少必需字段: {field}")
        
        # 验证端口号
        if 'port' in db_config:
            try:
                port = int(db_config['port'])
                if port < 1 or port > 65535:
                    errors.append(f"端口号无效: {port}")
            except (ValueError, TypeError):
                errors.append(f"端口号格式错误: {db_config['port']}")
        
        # 验证连接数
        for field in ['min_connections', 'max_connections']:
            if field in db_config:
                try:
                    value = int(db_config[field])
                    if value < 1:
                        errors.append(f"{field} 必须大于0")
                except (ValueError, TypeError):
                    errors.append(f"{field} 格式错误")
        
        # 验证向量配置
        vector_config = self.get_vector_config()
        if 'similarity_threshold' in vector_config:
            threshold = vector_config['similarity_threshold']
            try:
                if not (0 <= threshold <= 1):
                    errors.append(f"相似度阈值必须在0-1之间: {threshold}")
            except (ValueError, TypeError):
                errors.append(f"相似度阈值格式错误: {threshold}")
        
        return errors
    
    def get_connection_string(self) -> str:
        """生成数据库连接字符串"""
        config = self.get_database_config()
        
        password_part = f":{config['password']}@" if config.get('password') else "@"
        
        return (
            f"postgresql://{config['user']}{password_part}"
            f"{config['host']}:{config['port']}/{config['database']}"
        )
    
    def get_environment_variables(self) -> Dict[str, str]:
        """生成环境变量字典"""
        config = self.get_database_config()
        
        return {
            'DB_HOST': str(config['host']),
            'DB_PORT': str(config['port']),
            'DB_NAME': str(config['database']),
            'DB_USER': str(config['user']),
            'DB_PASSWORD': str(config.get('password', '')),
            'DB_MIN_CONNECTIONS': str(config.get('min_connections', 5)),
            'DB_MAX_CONNECTIONS': str(config.get('max_connections', 20)),
            'DB_COMMAND_TIMEOUT': str(config.get('command_timeout', 60))
        }
    
    @classmethod
    def create_config_template(cls, config_file: str) -> None:
        """创建配置模板文件"""
        config_path = Path(config_file)
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        template_config = cls()._get_default_config()
        
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                if config_path.suffix.lower() == '.yaml' or config_path.suffix.lower() == '.yml':
                    yaml.dump(template_config, f, default_flow_style=False, allow_unicode=True)
                elif config_path.suffix.lower() == '.json':
                    json.dump(template_config, f, indent=2, ensure_ascii=False)
            
            logger.info(f"配置模板已创建: {config_path}")
        except Exception as e:
            logger.error(f"创建配置模板失败: {e}")
            raise


# 全局配置实例
db_config = DatabaseConfig()