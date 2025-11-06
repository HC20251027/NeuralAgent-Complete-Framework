"""
APISIX网关配置生成器
负责生成和验证APISIX配置文件
"""

import json
import yaml
from typing import Dict, List, Any, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class ConfigGenerator:
    """配置生成器"""
    
    def __init__(self, output_dir: str = "configs/apisix"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_main_config(self) -> Dict[str, Any]:
        """生成主配置文件"""
        return {
            "apisix": {
                "node_listen": 9080,
                "enable_admin_cors": True,
                "enable_dev_mode": False,
                "enable_reuseport": True,
                "enable_ipv6": False,
                "config_center": "yaml",
                "proxy_cache": {
                    "cache_ttl": 10,
                    "zones": [
                        {
                            "name": "disk_cache_one",
                            "memory_size": 50,
                            "disk_size": 1,
                            "disk_path": "/tmp/disk_cache_one",
                            "cache_levels": "1:2"
                        }
                    ]
                },
                "router": {
                    "http": {
                        "radixtree_host_uri": True
                    }
                },
                "stream_proxy": {
                    "tcp": [
                        {
                            "addr": 9100,
                            "proxy_protocol": True,
                            "upstream": {
                                "nodes": {
                                    "127.0.0.1:80": 1
                                },
                                "type": "roundrobin"
                            }
                        }
                    ],
                    "udp": [
                        {
                            "addr": 9200,
                            "proxy_protocol": True,
                            "upstream": {
                                "nodes": {
                                    "127.0.0.1:1194": 1
                                },
                                "type": "roundrobin"
                            }
                        }
                    ]
                },
                "dns_resolver": [
                    {
                        "address": "127.0.0.1:53",
                        "addrs": ["127.0.0.1"],
                        "port": 53
                    }
                ],
                "nginx_config": {
                    "error_log": "/tmp/error.log",
                    "error_log_level": "warn",
                    "worker_processes": "auto",
                    "enable_reuseport": True,
                    "max_core_dumps_unlimited": True,
                    "enable_cpu_affinity": True
                }
            },
            "nginx_config": {
                "error_log": "/tmp/error.log",
                "error_log_level": "warn",
                "worker_processes": "auto",
                "enable_reuseport": True,
                "max_core_dumps_unlimited": True,
                "enable_cpu_affinity": True,
                "worker_rlimit_nofile": 20480,
                "event": {
                    "worker_connections": 10620
                },
                "http": {
                    "access_log": "/tmp/access.log",
                    "keepalive_timeout": 60,
                    "client_header_timeout": 60,
                    "client_body_timeout": 60,
                    "send_timeout": 10,
                    "underscores_in_headers": "on",
                    "real_ip_header": "X-Real-IP",
                    "real_ip_from": [
                        "127.0.0.1",
                        "unix:/"
                    ]
                }
            }
        }
    
    def generate_admin_config(self) -> Dict[str, Any]:
        """生成Admin API配置"""
        return {
            "admin": {
                "enable_admin_cors": True,
                "allow_admin": [
                    "127.0.0.0/24",
                    "1.2.3.4/32"
                ],
                "admin_key": [
                    {
                        "name": "admin",
                        "key": "edd1c9f034335f136f87ad84b625c8f1",
                        "role": "admin"
                    },
                    {
                        "name": "viewer",
                        "key": "4054f7cf07e344346f3dc3b8dac6901f",
                        "role": "viewer"
                    }
                ],
                "secret": "secret-key",
                "encrypt_key": "orderinsider",
                "token_expire": 7200
            }
        }
    
    def generate_apisix_config(self) -> Dict[str, Any]:
        """生成完整的APISIX配置"""
        config = self.generate_main_config()
        config.update(self.generate_admin_config())
        return config
    
    def save_config(self, config: Dict[str, Any], filename: str) -> None:
        """保存配置到文件"""
        filepath = self.output_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            if filename.endswith('.yaml') or filename.endswith('.yml'):
                yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
            else:
                json.dump(config, f, indent=2, ensure_ascii=False)
        
        logger.info(f"配置已保存: {filepath}")
    
    def generate_service_config(self, service_config: Dict[str, Any]) -> Dict[str, Any]:
        """生成服务配置"""
        return {
            "id": service_config.get("id"),
            "name": service_config.get("name"),
            "plugins": service_config.get("plugins", {}),
            "upstream": service_config.get("upstream", {}),
            "metadata": service_config.get("metadata", {})
        }
    
    def generate_route_config(self, route_config: Dict[str, Any]) -> Dict[str, Any]:
        """生成路由配置"""
        return {
            "id": route_config.get("id"),
            "name": route_config.get("name"),
            "uri": route_config.get("uri", []),
            "methods": route_config.get("methods", ["GET", "POST"]),
            "priority": route_config.get("priority", 0),
            "timeout": route_config.get("timeout", {}),
            "plugins": route_config.get("plugins", {}),
            "upstream": route_config.get("upstream", {}),
            "metadata": route_config.get("metadata", {})
        }
    
    def generate_upstream_config(
        self,
        upstream_id: str,
        nodes: Dict[str, int],
        upstream_type: str = "roundrobin",
        health_checker: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """生成上游配置"""
        config = {
            "id": upstream_id,
            "type": upstream_type,
            "nodes": nodes
        }
        
        if health_checker:
            config["checks"] = health_checker
        
        return config
    
    def generate_plugin_config(
        self,
        plugin_name: str,
        plugin_config: Dict[str, Any],
        plugin_type: str = "global"
    ) -> Dict[str, Any]:
        """生成插件配置"""
        return {
            "name": plugin_name,
            "config": plugin_config,
            "type": plugin_type
        }
    
    def generate_ssl_config(
        self,
        ssl_id: str,
        cert: str,
        key: str,
        sni: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """生成SSL配置"""
        config = {
            "id": ssl_id,
            "cert": cert,
            "key": key
        }
        
        if sni:
            config["sni"] = sni
        
        return config
    
    def generate_consumer_config(
        self,
        consumer_id: str,
        username: str,
        plugins: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """生成消费者配置"""
        config = {
            "id": consumer_id,
            "username": username
        }
        
        if plugins:
            config["plugins"] = plugins
        
        return config
    
    def generate_consumer_group_config(
        self,
        group_id: str,
        group_name: str,
        consumers: List[str]
    ) -> Dict[str, Any]:
        """生成消费者组配置"""
        return {
            "id": group_id,
            "group_name": group_name,
            "consumers": consumers
        }
    
    def generate_plugin_metadata_config(
        self,
        plugin_name: str,
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """生成插件元数据配置"""
        return {
            "plugin": plugin_name,
            "metadata": metadata
        }
    
    def validate_config(self, config: Dict[str, Any], config_type: str) -> List[str]:
        """验证配置"""
        errors = []
        
        if config_type == "service":
            errors.extend(self._validate_service_config(config))
        elif config_type == "route":
            errors.extend(self._validate_route_config(config))
        elif config_type == "upstream":
            errors.extend(self._validate_upstream_config(config))
        elif config_type == "plugin":
            errors.extend(self._validate_plugin_config(config))
        elif config_type == "ssl":
            errors.extend(self._validate_ssl_config(config))
        elif config_type == "consumer":
            errors.extend(self._validate_consumer_config(config))
        
        return errors
    
    def _validate_service_config(self, config: Dict[str, Any]) -> List[str]:
        """验证服务配置"""
        errors = []
        
        if "name" not in config:
            errors.append("服务配置缺少 'name' 字段")
        
        if "upstream" not in config:
            errors.append("服务配置缺少 'upstream' 字段")
        else:
            upstream = config["upstream"]
            if "nodes" not in upstream:
                errors.append("上游配置缺少 'nodes' 字段")
        
        return errors
    
    def _validate_route_config(self, config: Dict[str, Any]) -> List[str]:
        """验证路由配置"""
        errors = []
        
        if "name" not in config:
            errors.append("路由配置缺少 'name' 字段")
        
        if "uri" not in config:
            errors.append("路由配置缺少 'uri' 字段")
        
        if "service_id" not in config and "upstream" not in config:
            errors.append("路由配置必须包含 'service_id' 或 'upstream'")
        
        return errors
    
    def _validate_upstream_config(self, config: Dict[str, Any]) -> List[str]:
        """验证上游配置"""
        errors = []
        
        if "nodes" not in config:
            errors.append("上游配置缺少 'nodes' 字段")
        elif not config["nodes"]:
            errors.append("上游节点列表不能为空")
        
        return errors
    
    def _validate_plugin_config(self, config: Dict[str, Any]) -> List[str]:
        """验证插件配置"""
        errors = []
        
        if "name" not in config:
            errors.append("插件配置缺少 'name' 字段")
        
        if "config" not in config:
            errors.append("插件配置缺少 'config' 字段")
        
        return errors
    
    def _validate_ssl_config(self, config: Dict[str, Any]) -> List[str]:
        """验证SSL配置"""
        errors = []
        
        if "cert" not in config:
            errors.append("SSL配置缺少 'cert' 字段")
        
        if "key" not in config:
            errors.append("SSL配置缺少 'key' 字段")
        
        return errors
    
    def _validate_consumer_config(self, config: Dict[str, Any]) -> List[str]:
        """验证消费者配置"""
        errors = []
        
        if "username" not in config:
            errors.append("消费者配置缺少 'username' 字段")
        
        return errors
    
    def export_all_configs(self) -> Dict[str, Any]:
        """导出所有配置"""
        configs = {}
        
        # 导出主配置
        configs["apisix.yaml"] = self.generate_apisix_config()
        
        # 导出各类型配置
        for config_file in self.output_dir.glob("*.yaml"):
            if config_file.name != "apisix.yaml":
                try:
                    with open(config_file, 'r', encoding='utf-8') as f:
                        configs[config_file.name] = yaml.safe_load(f)
                except Exception as e:
                    logger.warning(f"读取配置文件失败: {config_file} - {e}")
        
        return configs