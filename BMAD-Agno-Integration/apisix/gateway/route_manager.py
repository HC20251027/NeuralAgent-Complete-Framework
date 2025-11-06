"""
APISIX网关 - 服务路由管理
负责服务注册、路由配置和流量管理
"""

import asyncio
import json
import uuid
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import logging

from ..config.config_loader import ConfigLoader

logger = logging.getLogger(__name__)


class ServiceInfo:
    """服务信息类"""
    
    def __init__(
        self,
        name: str,
        host: str,
        port: int,
        path_prefix: str = "/",
        health_check_path: str = "/health",
        weight: int = 100,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.id = str(uuid.uuid4())
        self.name = name
        self.host = host
        self.port = port
        self.path_prefix = path_prefix
        self.health_check_path = health_check_path
        self.weight = weight
        self.metadata = metadata or {}
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.status = "pending"  # pending, healthy, unhealthy, offline
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "id": self.id,
            "name": self.name,
            "host": self.host,
            "port": self.port,
            "path_prefix": self.path_prefix,
            "health_check_path": self.health_check_path,
            "weight": self.weight,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "status": self.status
        }


class RouteInfo:
    """路由信息类"""
    
    def __init__(
        self,
        name: str,
        service_name: str,
        uri_patterns: List[str],
        methods: Optional[List[str]] = None,
        priority: int = 1000,
        timeout: int = 30,
        retry_count: int = 3,
        plugins: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.id = str(uuid.uuid4())
        self.name = name
        self.service_name = service_name
        self.uri_patterns = uri_patterns
        self.methods = methods or ["GET", "POST", "PUT", "DELETE", "PATCH"]
        self.priority = priority
        self.timeout = timeout
        self.retry_count = retry_count
        self.plugins = plugins or {}
        self.metadata = metadata or {}
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.enabled = True
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "id": self.id,
            "name": self.name,
            "service_name": self.service_name,
            "uri": self.uri_patterns,
            "methods": self.methods,
            "priority": self.priority,
            "timeout": self.timeout,
            "retries": self.retry_count,
            "plugins": self.plugins,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "enabled": self.enabled
        }


class RouteManager:
    """路由管理器"""
    
    def __init__(self, config_loader: Optional[ConfigLoader] = None):
        self.config_loader = config_loader or ConfigLoader()
        self.services: Dict[str, ServiceInfo] = {}
        self.routes: Dict[str, RouteInfo] = {}
        self._lock = asyncio.Lock()
    
    async def register_service(self, service: ServiceInfo) -> bool:
        """注册服务"""
        async with self._lock:
            try:
                # 检查服务是否已存在
                if service.name in self.services:
                    logger.warning(f"服务已存在，更新配置: {service.name}")
                    service.id = self.services[service.name].id
                
                self.services[service.name] = service
                service.updated_at = datetime.now()
                
                # 生成APISIX服务配置
                apisix_service = await self._generate_apisix_service(service)
                
                # 保存到配置文件
                await self.config_loader.save_service_config(service.name, apisix_service)
                
                logger.info(f"服务注册成功: {service.name} ({service.host}:{service.port})")
                return True
                
            except Exception as e:
                logger.error(f"服务注册失败: {service.name} - {e}")
                return False
    
    async def unregister_service(self, service_name: str) -> bool:
        """注销服务"""
        async with self._lock:
            try:
                if service_name not in self.services:
                    logger.warning(f"服务不存在: {service_name}")
                    return False
                
                # 删除相关路由
                routes_to_remove = [
                    route_id for route_id, route in self.routes.items()
                    if route.service_name == service_name
                ]
                
                for route_id in routes_to_remove:
                    await self.unregister_route(route_id)
                
                # 删除服务配置
                del self.services[service_name]
                await self.config_loader.remove_service_config(service_name)
                
                logger.info(f"服务注销成功: {service_name}")
                return True
                
            except Exception as e:
                logger.error(f"服务注销失败: {service_name} - {e}")
                return False
    
    async def register_route(self, route: RouteInfo) -> bool:
        """注册路由"""
        async with self._lock:
            try:
                # 检查服务是否存在
                if route.service_name not in self.services:
                    logger.error(f"服务不存在: {route.service_name}")
                    return False
                
                # 检查路由是否已存在
                if route.name in [r.name for r in self.routes.values()]:
                    logger.warning(f"路由已存在，更新配置: {route.name}")
                    route.id = next(
                        r.id for r in self.routes.values() if r.name == route.name
                    )
                
                self.routes[route.id] = route
                route.updated_at = datetime.now()
                
                # 生成APISIX路由配置
                apisix_route = await self._generate_apisix_route(route)
                
                # 保存到配置文件
                await self.config_loader.save_route_config(route.id, apisix_route)
                
                logger.info(f"路由注册成功: {route.name} -> {route.service_name}")
                return True
                
            except Exception as e:
                logger.error(f"路由注册失败: {route.name} - {e}")
                return False
    
    async def unregister_route(self, route_id: str) -> bool:
        """注销路由"""
        async with self._lock:
            try:
                if route_id not in self.routes:
                    logger.warning(f"路由不存在: {route_id}")
                    return False
                
                route_name = self.routes[route_id].name
                del self.routes[route_id]
                await self.config_loader.remove_route_config(route_id)
                
                logger.info(f"路由注销成功: {route_name}")
                return True
                
            except Exception as e:
                logger.error(f"路由注销失败: {route_id} - {e}")
                return False
    
    async def update_service_health(self, service_name: str, healthy: bool) -> None:
        """更新服务健康状态"""
        async with self._lock:
            if service_name in self.services:
                service = self.services[service_name]
                service.status = "healthy" if healthy else "unhealthy"
                service.updated_at = datetime.now()
                
                logger.info(f"服务健康状态更新: {service_name} -> {service.status}")
    
    async def get_service_status(self, service_name: str) -> Optional[Dict[str, Any]]:
        """获取服务状态"""
        if service_name in self.services:
            service = self.services[service_name]
            return {
                "name": service.name,
                "status": service.status,
                "host": service.host,
                "port": service.port,
                "last_updated": service.updated_at.isoformat(),
                "routes_count": len([
                    r for r in self.routes.values() 
                    if r.service_name == service_name
                ])
            }
        return None
    
    async def get_all_services(self) -> List[Dict[str, Any]]:
        """获取所有服务状态"""
        return [
            await self.get_service_status(name) 
            for name in self.services.keys()
        ]
    
    async def _generate_apisix_service(self, service: ServiceInfo) -> Dict[str, Any]:
        """生成APISIX服务配置"""
        return {
            "id": service.id,
            "name": service.name,
            "plugins": {
                "traffic-protections": {
                    "allow_methods": ["GET", "POST", "PUT", "DELETE", "PATCH"]
                }
            },
            "upstream": {
                "type": "roundrobin",
                "nodes": {
                    f"{service.host}:{service.port}": service.weight
                },
                "checks": {
                    "active": {
                        "http_path": service.health_check_path,
                        "timeout": 5,
                        "concurrency": 10,
                        "healthy": {
                            "interval": 5,
                            "http_statuses": [200, 302]
                        },
                        "unhealthy": {
                            "interval": 5,
                            "http_statuses": [429, 500, 502, 503, 504]
                        }
                    }
                }
            },
            "metadata": service.metadata
        }
    
    async def _generate_apisix_route(self, route: RouteInfo) -> Dict[str, Any]:
        """生成APISIX路由配置"""
        return {
            "id": route.id,
            "name": route.name,
            "uri": route.uri_patterns,
            "methods": route.methods,
            "priority": route.priority,
            "timeout": {
                "connect": route.timeout,
                "read": route.timeout,
                "send": route.timeout
            },
            "plugins": route.plugins,
            "upstream": {
                "type": "roundrobin",
                "retry_count": route.retry_count
            },
            "metadata": route.metadata
        }
    
    async def load_existing_configs(self) -> None:
        """加载现有配置"""
        try:
            # 加载服务配置
            services = await self.config_loader.load_all_services()
            for service_name, service_config in services.items():
                service = ServiceInfo(
                    name=service_name,
                    host=service_config["upstream"]["nodes"].keys()[0].split(":")[0],
                    port=int(service_config["upstream"]["nodes"].keys()[0].split(":")[1]),
                    metadata=service_config.get("metadata", {})
                )
                service.id = service_config["id"]
                service.status = "healthy"  # 假设现有服务都是健康的
                self.services[service_name] = service
            
            # 加载路由配置
            routes = await self.config_loader.load_all_routes()
            for route_id, route_config in routes.items():
                route = RouteInfo(
                    name=route_config["name"],
                    service_name="",  # 需要从服务配置中推断
                    uri_patterns=route_config["uri"],
                    methods=route_config.get("methods", ["GET", "POST"]),
                    plugins=route_config.get("plugins", {}),
                    metadata=route_config.get("metadata", {})
                )
                route.id = route_config["id"]
                route.enabled = True
                self.routes[route_id] = route
            
            logger.info(f"加载了 {len(self.services)} 个服务和 {len(self.routes)} 个路由")
            
        except Exception as e:
            logger.error(f"加载现有配置失败: {e}")
    
    async def export_config(self) -> Dict[str, Any]:
        """导出完整配置"""
        return {
            "services": {name: service.to_dict() for name, service in self.services.items()},
            "routes": {route_id: route.to_dict() for route_id, route in self.routes.items()},
            "exported_at": datetime.now().isoformat()
        }