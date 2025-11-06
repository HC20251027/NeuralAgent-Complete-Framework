"""
APISIX网关配置验证器
负责验证配置文件的正确性
"""

from typing import Dict, List, Any, Optional, Set, Tuple
import re
import logging

logger = logging.getLogger(__name__)


class ConfigValidator:
    """配置验证器"""
    
    def __init__(self):
        self.validation_rules = self._load_validation_rules()
        self.supported_plugins = self._get_supported_plugins()
        self.supported_methods = {"GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"}
    
    def _load_validation_rules(self) -> Dict[str, Dict[str, Any]]:
        """加载验证规则"""
        return {
            "service": {
                "required_fields": ["name", "upstream"],
                "field_types": {
                    "name": str,
                    "upstream": dict,
                    "plugins": dict,
                    "metadata": dict
                },
                "nested_validations": {
                    "upstream": {
                        "required_fields": ["nodes"],
                        "field_types": {
                            "nodes": dict,
                            "type": str,
                            "checks": dict
                        }
                    }
                }
            },
            "route": {
                "required_fields": ["name", "uri"],
                "field_types": {
                    "name": str,
                    "uri": list,
                    "methods": list,
                    "priority": int,
                    "timeout": dict,
                    "plugins": dict,
                    "upstream": dict,
                    "service_id": str,
                    "metadata": dict
                },
                "nested_validations": {
                    "timeout": {
                        "optional_fields": ["connect", "read", "send"],
                        "field_types": {"connect": int, "read": int, "send": int}
                    }
                }
            },
            "upstream": {
                "required_fields": ["nodes"],
                "field_types": {
                    "nodes": dict,
                    "type": str,
                    "checks": dict,
                    "retries": int,
                    "retry_timeout": int,
                    "desc": str,
                    "checks": dict,
                    "hash_on": str,
                    "key": str
                }
            },
            "plugin": {
                "required_fields": ["name", "config"],
                "field_types": {
                    "name": str,
                    "config": dict,
                    "type": str,
                    "priority": int
                }
            },
            "ssl": {
                "required_fields": ["cert", "key"],
                "field_types": {
                    "cert": str,
                    "key": str,
                    "sni": list,
                    "snis": list
                }
            },
            "consumer": {
                "required_fields": ["username"],
                "field_types": {
                    "username": str,
                    "plugins": dict,
                    "consumer_id": str
                }
            }
        }
    
    def _get_supported_plugins(self) -> Set[str]:
        """获取支持的插件列表"""
        return {
            "jwt-auth", "key-auth", "basic-auth", "api-breaker", "authz-keycloak",
            "authz-casbin", "authz-casdoor", "authz-ldap", "authz-oauth2",
            "rate-limit", "limit-conn", "limit-count", "limit-req",
            "proxy-rewrite", "rewrite", "server-info", "server-status",
            "response-rewrite", "proxy-mirror", "proxy-cache", "proxy-control",
            "request-validation", "response-validation", "batch-requests",
            "http-logger", "file-logger", "loggly", "skywalking-logger",
            "slack-logger", "splunk-logging", "syslog", "tcp-logger", "udp-logger",
            "cors", "ip-restriction", "referer-restriction", "uri-blocker",
            "request-validation", "openid-connect", "cas-auth", "authz-casdoor",
            "traffic-protections", "traffic-protection", "zipkin", "skywalking",
            "node-status", "prometheus", "datadog", "node-reporter",
            "traffic-protections", "traffic-protection", "api-breaker",
            "fault-injection", "mocking", "traffic-protections", "traffic-protection",
            "traffic-protections", "traffic-protection", "traffic-protections"
        }
    
    def validate_config(self, config: Dict[str, Any], config_type: str) -> Dict[str, Any]:
        """验证配置"""
        result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "suggestions": []
        }
        
        try:
            if config_type not in self.validation_rules:
                result["valid"] = False
                result["errors"].append(f"不支持的配置类型: {config_type}")
                return result
            
            rules = self.validation_rules[config_type]
            
            # 验证必需字段
            missing_fields = self._check_required_fields(config, rules.get("required_fields", []))
            if missing_fields:
                result["valid"] = False
                result["errors"].extend([f"缺少必需字段: {field}" for field in missing_fields])
            
            # 验证字段类型
            type_errors = self._check_field_types(config, rules.get("field_types", {}))
            result["errors"].extend(type_errors)
            
            # 验证嵌套结构
            nested_errors = self._check_nested_structures(config, rules.get("nested_validations", {}))
            result["errors"].extend(nested_errors)
            
            # 特定类型的验证
            type_specific_errors = self._validate_type_specific(config, config_type)
            result["errors"].extend(type_specific_errors)
            
            # 生成建议
            suggestions = self._generate_suggestions(config, config_type)
            result["suggestions"].extend(suggestions)
            
            if result["errors"]:
                result["valid"] = False
            
        except Exception as e:
            result["valid"] = False
            result["errors"].append(f"验证过程出错: {e}")
        
        return result
    
    def _check_required_fields(self, config: Dict[str, Any], required_fields: List[str]) -> List[str]:
        """检查必需字段"""
        missing = []
        for field in required_fields:
            if field not in config:
                missing.append(field)
        return missing
    
    def _check_field_types(self, config: Dict[str, Any], field_types: Dict[str, type]) -> List[str]:
        """检查字段类型"""
        errors = []
        for field, expected_type in field_types.items():
            if field in config:
                if not isinstance(config[field], expected_type):
                    errors.append(f"字段 '{field}' 类型错误，期望: {expected_type.__name__}, 实际: {type(config[field]).__name__}")
        return errors
    
    def _check_nested_structures(self, config: Dict[str, Any], nested_validations: Dict[str, Dict[str, Any]]) -> List[str]:
        """检查嵌套结构"""
        errors = []
        for field, validation_rules in nested_validations.items():
            if field in config and isinstance(config[field], dict):
                nested_config = config[field]
                
                # 检查嵌套结构的必需字段
                required_fields = validation_rules.get("required_fields", [])
                missing = self._check_required_fields(nested_config, required_fields)
                errors.extend([f"{field}.{m}" for m in missing])
                
                # 检查嵌套结构的字段类型
                field_types = validation_rules.get("field_types", {})
                type_errors = self._check_field_types(nested_config, field_types)
                errors.extend([f"{field}.{e}" for e in type_errors])
        
        return errors
    
    def _validate_type_specific(self, config: Dict[str, Any], config_type: str) -> List[str]:
        """特定类型的验证"""
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
        
        # 验证上游配置
        if "upstream" in config:
            upstream = config["upstream"]
            if "nodes" in upstream:
                nodes = upstream["nodes"]
                if not isinstance(nodes, dict) or not nodes:
                    errors.append("上游节点配置无效")
                else:
                    # 验证节点格式
                    for node, weight in nodes.items():
                        if not isinstance(node, str) or ":" not in node:
                            errors.append(f"节点格式错误: {node}")
                        elif not isinstance(weight, (int, float)) or weight < 0:
                            errors.append(f"节点权重无效: {node} -> {weight}")
        
        return errors
    
    def _validate_route_config(self, config: Dict[str, Any]) -> List[str]:
        """验证路由配置"""
        errors = []
        
        # 验证URI模式
        if "uri" in config:
            uris = config["uri"]
            if not isinstance(uris, list) or not uris:
                errors.append("URI配置无效")
            else:
                for uri in uris:
                    if not isinstance(uri, str):
                        errors.append(f"URI必须是字符串: {uri}")
        
        # 验证HTTP方法
        if "methods" in config:
            methods = config["methods"]
            if not isinstance(methods, list):
                errors.append("HTTP方法必须是列表")
            else:
                for method in methods:
                    if method not in self.supported_methods:
                        errors.append(f"不支持的HTTP方法: {method}")
        
        # 验证优先级
        if "priority" in config:
            priority = config["priority"]
            if not isinstance(priority, int):
                errors.append("优先级必须是整数")
        
        # 验证服务关联
        has_service = "service_id" in config
        has_upstream = "upstream" in config
        
        if not has_service and not has_upstream:
            errors.append("路由必须关联服务或上游")
        elif has_service and has_upstream:
            errors.append("路由不能同时关联服务和上游")
        
        return errors
    
    def _validate_upstream_config(self, config: Dict[str, Any]) -> List[str]:
        """验证上游配置"""
        errors = []
        
        # 验证节点配置
        if "nodes" in config:
            nodes = config["nodes"]
            if not isinstance(nodes, dict) or not nodes:
                errors.append("上游节点配置无效")
            else:
                for node, weight in nodes.items():
                    if not isinstance(node, str) or ":" not in node:
                        errors.append(f"节点格式错误: {node}")
                    elif not isinstance(weight, (int, float)) or weight < 0:
                        errors.append(f"节点权重无效: {node} -> {weight}")
        
        # 验证负载均衡类型
        if "type" in config:
            lb_type = config["type"]
            supported_types = {"roundrobin", "chash", "ewma", "least_connections", "user-defined"}
            if lb_type not in supported_types:
                errors.append(f"不支持的负载均衡类型: {lb_type}")
        
        # 验证重试配置
        if "retries" in config:
            retries = config["retries"]
            if not isinstance(retries, int) or retries < 0:
                errors.append("重试次数必须是非负整数")
        
        return errors
    
    def _validate_plugin_config(self, config: Dict[str, Any]) -> List[str]:
        """验证插件配置"""
        errors = []
        
        # 验证插件名称
        if "name" in config:
            plugin_name = config["name"]
            if plugin_name not in self.supported_plugins:
                errors.append(f"不支持的插件: {plugin_name}")
        
        # 验证插件配置
        if "config" in config:
            plugin_config = config["config"]
            if not isinstance(plugin_config, dict):
                errors.append("插件配置必须是对象")
        
        # 验证优先级
        if "priority" in config:
            priority = config["priority"]
            if not isinstance(priority, int):
                errors.append("插件优先级必须是整数")
        
        return errors
    
    def _validate_ssl_config(self, config: Dict[str, Any]) -> List[str]:
        """验证SSL配置"""
        errors = []
        
        # 验证证书和私钥
        if "cert" in config:
            cert = config["cert"]
            if not cert.strip():
                errors.append("SSL证书不能为空")
        
        if "key" in config:
            key = config["key"]
            if not key.strip():
                errors.append("SSL私钥不能为空")
        
        # 验证SNI配置
        if "sni" in config:
            sni = config["sni"]
            if not isinstance(sni, list):
                errors.append("SNI必须是列表")
            else:
                for sni_item in sni:
                    if not isinstance(sni_item, str):
                        errors.append(f"SNI项必须是字符串: {sni_item}")
        
        return errors
    
    def _validate_consumer_config(self, config: Dict[str, Any]) -> List[str]:
        """验证消费者配置"""
        errors = []
        
        # 验证用户名
        if "username" in config:
            username = config["username"]
            if not username.strip():
                errors.append("用户名不能为空")
            elif not re.match(r'^[a-zA-Z0-9_-]+$', username):
                errors.append("用户名只能包含字母、数字、下划线和连字符")
        
        return errors
    
    def _generate_suggestions(self, config: Dict[str, Any], config_type: str) -> List[str]:
        """生成建议"""
        suggestions = []
        
        if config_type == "route":
            # 建议添加健康检查
            if "upstream" in config and "checks" not in config["upstream"]:
                suggestions.append("建议为上游配置健康检查以提高可用性")
            
            # 建议设置合理的超时时间
            if "timeout" not in config:
                suggestions.append("建议设置合理的超时时间以避免请求长时间等待")
        
        elif config_type == "service":
            # 建议启用负载均衡
            if "upstream" in config and "type" not in config["upstream"]:
                suggestions.append("建议明确指定负载均衡类型")
        
        elif config_type == "plugin":
            # 建议设置插件优先级
            if "priority" not in config:
                suggestions.append("建议为插件设置优先级以控制执行顺序")
        
        return suggestions
    
    def validate_multiple_configs(self, configs: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """验证多个配置"""
        results = {}
        
        for config_name, config in configs.items():
            results[config_name] = self.validate_config(config, self._detect_config_type(config))
        
        return results
    
    def _detect_config_type(self, config: Dict[str, Any]) -> str:
        """自动检测配置类型"""
        if "upstream" in config and "uri" not in config:
            return "service"
        elif "uri" in config:
            return "route"
        elif "nodes" in config:
            return "upstream"
        elif "name" in config and "config" in config:
            return "plugin"
        elif "cert" in config:
            return "ssl"
        elif "username" in config:
            return "consumer"
        else:
            return "unknown"