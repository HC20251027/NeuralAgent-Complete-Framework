"""
APISIX网关 - 插件管理器
负责网关插件的配置和管理
"""

import json
import uuid
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class PluginConfig:
    """插件配置类"""
    
    def __init__(
        self,
        name: str,
        plugin_type: str,
        config: Dict[str, Any],
        enabled: bool = True,
        priority: int = 1000,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.id = str(uuid.uuid4())
        self.name = name
        self.plugin_type = plugin_type
        self.config = config
        self.enabled = enabled
        self.priority = priority
        self.metadata = metadata or {}
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "id": self.id,
            "name": self.name,
            "plugin_type": self.plugin_type,
            "config": self.config,
            "enabled": self.enabled,
            "priority": self.priority,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }


class PluginManager:
    """插件管理器"""
    
    def __init__(self):
        self.plugins: Dict[str, PluginConfig] = {}
        self.plugin_templates = self._load_plugin_templates()
        self._lock = asyncio.Lock()
    
    def _load_plugin_templates(self) -> Dict[str, Dict[str, Any]]:
        """加载插件模板"""
        return {
            # 认证插件
            "jwt-auth": {
                "name": "jwt-auth",
                "schema": {
                    "header": {"type": "string"},
                    "secret": {"type": "string"},
                    "算法": {"type": "string", "enum": ["HS256", "RS256"]},
                    "exp": {"type": "integer"}
                },
                "default_config": {
                    "header": "Authorization",
                    "算法": "HS256"
                }
            },
            
            # 限流插件
            "rate-limit": {
                "name": "rate-limit",
                "schema": {
                    "rate": {"type": "number"},
                    "window": {"type": "integer"},
                    "key_type": {"type": "string", "enum": ["var", "var_combination", "constant"]},
                    "key": {"type": "string"}
                },
                "default_config": {
                    "rate": 100,
                    "window": 60,
                    "key_type": "var",
                    "key": "remote_addr"
                }
            },
            
            # 请求重写插件
            "rewrite": {
                "name": "rewrite",
                "schema": {
                    "uri": {"type": "string"},
                    "uri_args": {"type": "object"},
                    "headers": {"type": "object"},
                    "vars": {"type": "array"}
                },
                "default_config": {}
            },
            
            # 响应转换插件
            "response-rewrite": {
                "name": "response-rewrite",
                "schema": {
                    "status_code": {"type": "integer"},
                    "body": {"type": "string"},
                    "headers": {"type": "object"}
                },
                "default_config": {}
            },
            
            # 请求验证插件
            "request-validation": {
                "name": "request-validation",
                "schema": {
                    "body_schema": {"type": "object"},
                    "header_schema": {"type": "object"},
                    "query_schema": {"type": "object"}
                },
                "default_config": {}
            },
            
            # 缓存插件
            "proxy-cache": {
                "name": "proxy-cache",
                "schema": {
                    "cache_zone": {"type": "string"},
                    "cache_key": {"type": "array"},
                    "cache_ttl": {"type": "integer"},
                    "cache_http_status": {"type": "array"}
                },
                "default_config": {
                    "cache_zone": "default",
                    "cache_ttl": 300
                }
            },
            
            # 日志插件
            "http-logger": {
                "name": "http-logger",
                "schema": {
                    "uri": {"type": "string"},
                    "method": {"type": "string"},
                    "headers": {"type": "object"},
                    "batch_max_size": {"type": "integer"},
                    "inactive_timeout": {"type": "integer"}
                },
                "default_config": {
                    "method": "POST",
                    "batch_max_size": 100,
                    "inactive_timeout": 5
                }
            },
            
            # 跨域插件
            "cors": {
                "name": "cors",
                "schema": {
                    "allow_origins": {"type": "string"},
                    "allow_methods": {"type": "string"},
                    "allow_headers": {"type": "string"},
                    "allow_credentials": {"type": "boolean"},
                    "max_age": {"type": "integer"}
                },
                "default_config": {
                    "allow_methods": "GET,POST,PUT,DELETE,PATCH,OPTIONS",
                    "allow_headers": "*",
                    "allow_credentials": True,
                    "max_age": 86400
                }
            },
            
            # IP白名单/黑名单插件
            "ip-restriction": {
                "name": "ip-restriction",
                "schema": {
                    "whitelist": {"type": "array"},
                    "blacklist": {"type": "array"}
                },
                "default_config": {}
            },
            
            # 压缩插件
            "gzip": {
                "name": "gzip",
                "schema": {
                    "types": {"type": "array"},
                    "min_length": {"type": "integer"},
                    "comp_level": {"type": "integer"}
                },
                "default_config": {
                    "types": ["text/plain", "text/css", "text/xml", "text/javascript", 
                             "application/javascript", "application/xml+rss", 
                             "application/json"],
                    "min_length": 1024,
                    "comp_level": 5
                }
            }
        }
    
    async def register_plugin(self, plugin: PluginConfig) -> bool:
        """注册插件"""
        async with self._lock:
            try:
                # 验证插件配置
                if not await self._validate_plugin_config(plugin):
                    logger.error(f"插件配置验证失败: {plugin.name}")
                    return False
                
                # 检查插件是否已存在
                if plugin.name in self.plugins:
                    logger.warning(f"插件已存在，更新配置: {plugin.name}")
                    plugin.id = self.plugins[plugin.name].id
                
                self.plugins[plugin.name] = plugin
                plugin.updated_at = datetime.now()
                
                logger.info(f"插件注册成功: {plugin.name} ({plugin.plugin_type})")
                return True
                
            except Exception as e:
                logger.error(f"插件注册失败: {plugin.name} - {e}")
                return False
    
    async def unregister_plugin(self, plugin_name: str) -> bool:
        """注销插件"""
        async with self._lock:
            try:
                if plugin_name not in self.plugins:
                    logger.warning(f"插件不存在: {plugin_name}")
                    return False
                
                del self.plugins[plugin_name]
                logger.info(f"插件注销成功: {plugin_name}")
                return True
                
            except Exception as e:
                logger.error(f"插件注销失败: {plugin_name} - {e}")
                return False
    
    async def enable_plugin(self, plugin_name: str) -> bool:
        """启用插件"""
        async with self._lock:
            if plugin_name in self.plugins:
                self.plugins[plugin_name].enabled = True
                self.plugins[plugin_name].updated_at = datetime.now()
                logger.info(f"插件已启用: {plugin_name}")
                return True
            return False
    
    async def disable_plugin(self, plugin_name: str) -> bool:
        """禁用插件"""
        async with self._lock:
            if plugin_name in self.plugins:
                self.plugins[plugin_name].enabled = False
                self.plugins[plugin_name].updated_at = datetime.now()
                logger.info(f"插件已禁用: {plugin_name}")
                return True
            return False
    
    async def update_plugin_config(
        self, 
        plugin_name: str, 
        config: Dict[str, Any]
    ) -> bool:
        """更新插件配置"""
        async with self._lock:
            if plugin_name in self.plugins:
                self.plugins[plugin_name].config.update(config)
                self.plugins[plugin_name].updated_at = datetime.now()
                logger.info(f"插件配置已更新: {plugin_name}")
                return True
            return False
    
    async def get_plugin(self, plugin_name: str) -> Optional[PluginConfig]:
        """获取插件配置"""
        return self.plugins.get(plugin_name)
    
    async def get_all_plugins(self) -> List[PluginConfig]:
        """获取所有插件"""
        return list(self.plugins.values())
    
    async def get_enabled_plugins(self) -> List[PluginConfig]:
        """获取启用的插件"""
        return [plugin for plugin in self.plugins.values() if plugin.enabled]
    
    async def get_plugins_by_type(self, plugin_type: str) -> List[PluginConfig]:
        """根据类型获取插件"""
        return [
            plugin for plugin in self.plugins.values() 
            if plugin.plugin_type == plugin_type
        ]
    
    async def _validate_plugin_config(self, plugin: PluginConfig) -> bool:
        """验证插件配置"""
        if plugin.plugin_type not in self.plugin_templates:
            logger.error(f"不支持的插件类型: {plugin.plugin_type}")
            return False
        
        template = self.plugin_templates[plugin.plugin_type]
        
        # 检查必需的配置项
        required_fields = template["schema"].keys()
        for field in required_fields:
            if field not in plugin.config:
                logger.error(f"插件配置缺少必需字段: {field}")
                return False
        
        return True
    
    async def create_plugin_from_template(
        self,
        plugin_type: str,
        name: str,
        custom_config: Optional[Dict[str, Any]] = None
    ) -> Optional[PluginConfig]:
        """从模板创建插件"""
        if plugin_type not in self.plugin_templates:
            logger.error(f"插件模板不存在: {plugin_type}")
            return None
        
        template = self.plugin_templates[plugin_type]
        
        # 合并默认配置和自定义配置
        config = template["default_config"].copy()
        if custom_config:
            config.update(custom_config)
        
        plugin = PluginConfig(
            name=name,
            plugin_type=plugin_type,
            config=config
        )
        
        return plugin
    
    async def export_plugin_configs(self) -> Dict[str, Any]:
        """导出插件配置"""
        return {
            plugin_name: plugin.to_dict()
            for plugin_name, plugin in self.plugins.items()
        }
    
    async def import_plugin_configs(self, configs: Dict[str, Any]) -> int:
        """导入插件配置"""
        imported_count = 0
        
        for plugin_name, config_data in configs.items():
            try:
                plugin = PluginConfig(
                    name=config_data["name"],
                    plugin_type=config_data["plugin_type"],
                    config=config_data["config"],
                    enabled=config_data.get("enabled", True),
                    priority=config_data.get("priority", 1000),
                    metadata=config_data.get("metadata", {})
                )
                plugin.id = config_data["id"]
                
                if await self.register_plugin(plugin):
                    imported_count += 1
                    
            except Exception as e:
                logger.error(f"导入插件配置失败: {plugin_name} - {e}")
        
        logger.info(f"成功导入 {imported_count} 个插件配置")
        return imported_count
    
    async def get_plugin_templates(self) -> Dict[str, Dict[str, Any]]:
        """获取插件模板"""
        return self.plugin_templates
    
    async def validate_all_plugins(self) -> Dict[str, List[str]]:
        """验证所有插件配置"""
        validation_results = {}
        
        for plugin_name, plugin in self.plugins.items():
            errors = []
            
            if plugin.plugin_type not in self.plugin_templates:
                errors.append(f"不支持的插件类型: {plugin.plugin_type}")
            else:
                template = self.plugin_templates[plugin.plugin_type]
                
                # 检查必需字段
                for field, field_config in template["schema"].items():
                    if field not in plugin.config:
                        errors.append(f"缺少必需字段: {field}")
            
            if errors:
                validation_results[plugin_name] = errors
        
        return validation_results