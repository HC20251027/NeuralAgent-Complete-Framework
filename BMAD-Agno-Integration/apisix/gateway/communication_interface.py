"""
APISIX网关通信接口
提供与APISIX网关的REST API通信和管理接口
"""

import asyncio
import json
import aiohttp
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import logging
from urllib.parse import urljoin

from ..gateway.route_manager import RouteManager, ServiceInfo, RouteInfo
from ..gateway.service_manager import ServiceManager
from ..gateway.plugin_manager import PluginManager
from ..config.config_loader import ConfigLoader
from ..config.config_validator import ConfigValidator

logger = logging.getLogger(__name__)


class APISIXClient:
    """APISIX REST API客户端"""
    
    def __init__(
        self,
        base_url: str = "http://127.0.0.1:9180",
        admin_key: str = "edd1c9f034335f136f87ad84b625c8f1"
    ):
        self.base_url = base_url.rstrip('/')
        self.admin_key = admin_key
        self.session: Optional[aiohttp.ClientSession] = None
        self._headers = {
            "Content-Type": "application/json",
            "X-API-KEY": admin_key
        }
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            headers=self._headers,
            timeout=aiohttp.ClientTimeout(total=30)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """发送HTTP请求"""
        if not self.session:
            raise RuntimeError("Client not initialized. Use async context manager.")
        
        url = urljoin(self.base_url + "/apisix/admin", endpoint)
        
        try:
            async with self.session.request(
                method=method,
                url=url,
                json=data,
                params=params
            ) as response:
                response_data = await response.json()
                
                if response.status >= 400:
                    error_msg = response_data.get("message", "Unknown error")
                    logger.error(f"APISIX API错误: {response.status} - {error_msg}")
                    raise Exception(f"API请求失败: {response.status} - {error_msg}")
                
                return response_data
                
        except aiohttp.ClientError as e:
            logger.error(f"HTTP请求失败: {e}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {e}")
            raise
    
    # 服务管理API
    async def create_service(self, service_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建服务"""
        return await self._request("POST", "/services", data=service_data)
    
    async def get_service(self, service_id: str) -> Dict[str, Any]:
        """获取服务"""
        return await self._request("GET", f"/services/{service_id}")
    
    async def update_service(self, service_id: str, service_data: Dict[str, Any]) -> Dict[str, Any]:
        """更新服务"""
        return await self._request("PUT", f"/services/{service_id}", data=service_data)
    
    async def delete_service(self, service_id: str) -> Dict[str, Any]:
        """删除服务"""
        return await self._request("DELETE", f"/services/{service_id}")
    
    async def list_services(self) -> List[Dict[str, Any]]:
        """列出所有服务"""
        response = await self._request("GET", "/services")
        return response.get("list", [])
    
    # 路由管理API
    async def create_route(self, route_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建路由"""
        return await self._request("POST", "/routes", data=route_data)
    
    async def get_route(self, route_id: str) -> Dict[str, Any]:
        """获取路由"""
        return await self._request("GET", f"/routes/{route_id}")
    
    async def update_route(self, route_id: str, route_data: Dict[str, Any]) -> Dict[str, Any]:
        """更新路由"""
        return await self._request("PUT", f"/routes/{route_id}", data=route_data)
    
    async def delete_route(self, route_id: str) -> Dict[str, Any]:
        """删除路由"""
        return await self._request("DELETE", f"/routes/{route_id}")
    
    async def list_routes(self) -> List[Dict[str, Any]]:
        """列出所有路由"""
        response = await self._request("GET", "/routes")
        return response.get("list", [])
    
    # 上游管理API
    async def create_upstream(self, upstream_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建上游"""
        return await self._request("POST", "/upstreams", data=upstream_data)
    
    async def get_upstream(self, upstream_id: str) -> Dict[str, Any]:
        """获取上游"""
        return await self._request("GET", f"/upstreams/{upstream_id}")
    
    async def update_upstream(self, upstream_id: str, upstream_data: Dict[str, Any]) -> Dict[str, Any]:
        """更新上游"""
        return await self._request("PUT", f"/upstreams/{upstream_id}", data=upstream_data)
    
    async def delete_upstream(self, upstream_id: str) -> Dict[str, Any]:
        """删除上游"""
        return await self._request("DELETE", f"/upstreams/{upstream_id}")
    
    async def list_upstreams(self) -> List[Dict[str, Any]]:
        """列出所有上游"""
        response = await self._request("GET", "/upstreams")
        return response.get("list", [])
    
    # 插件管理API
    async def create_plugin(self, plugin_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建插件"""
        return await self._request("POST", "/plugins", data=plugin_data)
    
    async def get_plugin(self, plugin_name: str) -> Dict[str, Any]:
        """获取插件"""
        return await self._request("GET", f"/plugins/{plugin_name}")
    
    async def update_plugin(self, plugin_name: str, plugin_data: Dict[str, Any]) -> Dict[str, Any]:
        """更新插件"""
        return await self._request("PUT", f"/plugins/{plugin_name}", data=plugin_data)
    
    async def delete_plugin(self, plugin_name: str) -> Dict[str, Any]:
        """删除插件"""
        return await self._request("DELETE", f"/plugins/{plugin_name}")
    
    async def list_plugins(self) -> List[Dict[str, Any]]:
        """列出所有插件"""
        response = await self._request("GET", "/plugins")
        return response.get("list", [])
    
    # SSL证书管理API
    async def create_ssl(self, ssl_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建SSL证书"""
        return await self._request("POST", "/ssl", data=ssl_data)
    
    async def get_ssl(self, ssl_id: str) -> Dict[str, Any]:
        """获取SSL证书"""
        return await self._request("GET", f"/ssl/{ssl_id}")
    
    async def update_ssl(self, ssl_id: str, ssl_data: Dict[str, Any]) -> Dict[str, Any]:
        """更新SSL证书"""
        return await self._request("PUT", f"/ssl/{ssl_id}", data=ssl_data)
    
    async def delete_ssl(self, ssl_id: str) -> Dict[str, Any]:
        """删除SSL证书"""
        return await self._request("DELETE", f"/ssl/{ssl_id}")
    
    async def list_ssl(self) -> List[Dict[str, Any]]:
        """列出所有SSL证书"""
        response = await self._request("GET", "/ssl")
        return response.get("list", [])
    
    # 消费者管理API
    async def create_consumer(self, consumer_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建消费者"""
        return await self._request("POST", "/consumers", data=consumer_data)
    
    async def get_consumer(self, consumer_id: str) -> Dict[str, Any]:
        """获取消费者"""
        return await self._request("GET", f"/consumers/{consumer_id}")
    
    async def update_consumer(self, consumer_id: str, consumer_data: Dict[str, Any]) -> Dict[str, Any]:
        """更新消费者"""
        return await self._request("PUT", f"/consumers/{consumer_id}", data=consumer_data)
    
    async def delete_consumer(self, consumer_id: str) -> Dict[str, Any]:
        """删除消费者"""
        return await self._request("DELETE", f"/consumers/{consumer_id}")
    
    async def list_consumers(self) -> List[Dict[str, Any]]:
        """列出所有消费者"""
        response = await self._request("GET", "/consumers")
        return response.get("list", [])
    
    # 系统状态API
    async def get_server_info(self) -> Dict[str, Any]:
        """获取服务器信息"""
        return await self._request("GET", "/server_info")
    
    async def get_node_status(self) -> Dict[str, Any]:
        """获取节点状态"""
        return await self._request("GET", "/status")
    
    async def get_grafana_dashboards(self) -> Dict[str, Any]:
        """获取Grafana仪表板"""
        return await self._request("GET", "/grafana/dashboards")


class GatewayCommunicationInterface:
    """网关通信接口"""
    
    def __init__(
        self,
        apisix_url: str = "http://127.0.0.1:9180",
        admin_key: str = "edd1c9f034335f136f87ad84b625c8f1",
        route_manager: Optional[RouteManager] = None,
        service_manager: Optional[ServiceManager] = None,
        plugin_manager: Optional[PluginManager] = None,
        config_loader: Optional[ConfigLoader] = None
    ):
        self.apisix_url = apisix_url
        self.admin_key = admin_key
        self.route_manager = route_manager or RouteManager()
        self.service_manager = service_manager or ServiceManager(self.route_manager)
        self.plugin_manager = plugin_manager or PluginManager()
        self.config_loader = config_loader or ConfigLoader()
        self.config_validator = ConfigValidator()
        self.client: Optional[APISIXClient] = None
    
    async def initialize(self) -> None:
        """初始化通信接口"""
        try:
            # 初始化APISIX客户端
            self.client = APISIXClient(self.apisix_url, self.admin_key)
            
            # 加载现有配置
            await self.route_manager.load_existing_configs()
            
            logger.info("网关通信接口初始化成功")
        except Exception as e:
            logger.error(f"网关通信接口初始化失败: {e}")
            raise
    
    async def sync_configuration_to_apisix(self) -> Dict[str, Any]:
        """同步配置到APISIX"""
        results = {
            "services": {"created": 0, "updated": 0, "failed": 0},
            "routes": {"created": 0, "updated": 0, "failed": 0},
            "plugins": {"created": 0, "updated": 0, "failed": 0},
            "errors": []
        }
        
        async with self.client:
            try:
                # 同步服务配置
                await self._sync_services(results)
                
                # 同步路由配置
                await self._sync_routes(results)
                
                # 同步插件配置
                await self._sync_plugins(results)
                
                logger.info(f"配置同步完成: {results}")
                return results
                
            except Exception as e:
                error_msg = f"配置同步失败: {e}"
                logger.error(error_msg)
                results["errors"].append(error_msg)
                return results
    
    async def _sync_services(self, results: Dict[str, Any]) -> None:
        """同步服务配置"""
        for service_name, service in self.route_manager.services.items():
            try:
                service_config = await self._generate_apisix_service_config(service)
                
                # 验证配置
                validation_result = self.config_validator.validate_config(service_config, "service")
                if not validation_result["valid"]:
                    results["services"]["failed"] += 1
                    results["errors"].extend([f"服务 {service_name}: {error}" for error in validation_result["errors"]])
                    continue
                
                # 创建或更新服务
                async with self.client:
                    try:
                        await self.client.create_service(service_config)
                        results["services"]["created"] += 1
                        logger.info(f"服务创建成功: {service_name}")
                    except Exception:
                        # 如果创建失败，尝试更新
                        await self.client.update_service(service.id, service_config)
                        results["services"]["updated"] += 1
                        logger.info(f"服务更新成功: {service_name}")
                        
            except Exception as e:
                results["services"]["failed"] += 1
                results["errors"].append(f"服务 {service_name}: {e}")
    
    async def _sync_routes(self, results: Dict[str, Any]) -> None:
        """同步路由配置"""
        for route_id, route in self.route_manager.routes.items():
            try:
                route_config = await self._generate_apisix_route_config(route)
                
                # 验证配置
                validation_result = self.config_validator.validate_config(route_config, "route")
                if not validation_result["valid"]:
                    results["routes"]["failed"] += 1
                    results["errors"].extend([f"路由 {route.name}: {error}" for error in validation_result["errors"]])
                    continue
                
                # 创建或更新路由
                async with self.client:
                    try:
                        await self.client.create_route(route_config)
                        results["routes"]["created"] += 1
                        logger.info(f"路由创建成功: {route.name}")
                    except Exception:
                        # 如果创建失败，尝试更新
                        await self.client.update_route(route.id, route_config)
                        results["routes"]["updated"] += 1
                        logger.info(f"路由更新成功: {route.name}")
                        
            except Exception as e:
                results["routes"]["failed"] += 1
                results["errors"].append(f"路由 {route.name}: {e}")
    
    async def _sync_plugins(self, results: Dict[str, Any]) -> None:
        """同步插件配置"""
        for plugin_name, plugin in self.plugin_manager.plugins.items():
            try:
                if not plugin.enabled:
                    continue
                
                plugin_config = {
                    "name": plugin.plugin_type,
                    "config": plugin.config
                }
                
                # 验证配置
                validation_result = self.config_validator.validate_config(plugin_config, "plugin")
                if not validation_result["valid"]:
                    results["plugins"]["failed"] += 1
                    results["errors"].extend([f"插件 {plugin_name}: {error}" for error in validation_result["errors"]])
                    continue
                
                # 创建或更新插件
                async with self.client:
                    try:
                        await self.client.create_plugin(plugin_config)
                        results["plugins"]["created"] += 1
                        logger.info(f"插件创建成功: {plugin_name}")
                    except Exception:
                        # 如果创建失败，尝试更新
                        await self.client.update_plugin(plugin.plugin_type, plugin_config)
                        results["plugins"]["updated"] += 1
                        logger.info(f"插件更新成功: {plugin_name}")
                        
            except Exception as e:
                results["plugins"]["failed"] += 1
                results["errors"].append(f"插件 {plugin_name}: {e}")
    
    async def _generate_apisix_service_config(self, service: ServiceInfo) -> Dict[str, Any]:
        """生成APISIX服务配置"""
        return {
            "id": service.id,
            "name": service.name,
            "plugins": {},
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
    
    async def _generate_apisix_route_config(self, route: RouteInfo) -> Dict[str, Any]:
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
    
    async def get_gateway_status(self) -> Dict[str, Any]:
        """获取网关状态"""
        try:
            async with self.client:
                server_info = await self.client.get_server_info()
                node_status = await self.client.get_node_status()
                
                return {
                    "server_info": server_info,
                    "node_status": node_status,
                    "services_count": len(self.route_manager.services),
                    "routes_count": len(self.route_manager.routes),
                    "plugins_count": len(self.plugin_manager.plugins),
                    "timestamp": datetime.now().isoformat()
                }
        except Exception as e:
            logger.error(f"获取网关状态失败: {e}")
            return {"error": str(e)}
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        try:
            async with self.client:
                # 检查APISIX连接
                await self.client.get_server_info()
                
                # 检查本地服务状态
                healthy_services = await self.service_manager.get_healthy_services()
                
                return {
                    "status": "healthy",
                    "apisix_connection": True,
                    "healthy_services": len(healthy_services),
                    "total_services": len(self.route_manager.services),
                    "timestamp": datetime.now().isoformat()
                }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def reload_configuration(self) -> bool:
        """重新加载配置"""
        try:
            # 重新加载本地配置
            await self.route_manager.load_existing_configs()
            
            # 同步到APISIX
            sync_result = await self.sync_configuration_to_apisix()
            
            return len(sync_result["errors"]) == 0
        except Exception as e:
            logger.error(f"重新加载配置失败: {e}")
            return False