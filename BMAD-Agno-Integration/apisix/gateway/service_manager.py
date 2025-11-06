"""
APISIX网关 - 服务管理器
负责服务发现、负载均衡和健康检查
"""

import asyncio
import json
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
import aiohttp
import logging

from .route_manager import ServiceInfo, RouteManager

logger = logging.getLogger(__name__)


class ServiceHealthChecker:
    """服务健康检查器"""
    
    def __init__(self, timeout: int = 5, retry_count: int = 3):
        self.timeout = timeout
        self.retry_count = retry_count
        self.check_interval = 30  # 检查间隔（秒）
        self._running = False
        self._tasks: Dict[str, asyncio.Task] = {}
    
    async def start_checking(self, route_manager: RouteManager) -> None:
        """开始健康检查"""
        self._running = True
        
        while self._running:
            try:
                await self._check_all_services(route_manager)
                await asyncio.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"健康检查循环错误: {e}")
                await asyncio.sleep(5)
    
    async def stop_checking(self) -> None:
        """停止健康检查"""
        self._running = False
        
        # 取消所有检查任务
        for task in self._tasks.values():
            task.cancel()
        
        self._tasks.clear()
    
    async def _check_all_services(self, route_manager: RouteManager) -> None:
        """检查所有服务"""
        services = route_manager.services
        
        for service_name, service in services.items():
            if service_name not in self._tasks or self._tasks[service_name].done():
                # 启动新的检查任务
                task = asyncio.create_task(
                    self._check_service_health(service_name, service, route_manager)
                )
                self._tasks[service_name] = task
    
    async def _check_service_health(
        self, 
        service_name: str, 
        service: ServiceInfo, 
        route_manager: RouteManager
    ) -> None:
        """检查单个服务健康状态"""
        try:
            url = f"http://{service.host}:{service.port}{service.health_check_path}"
            
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            ) as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        healthy = True
                        logger.debug(f"服务健康检查通过: {service_name}")
                    else:
                        healthy = False
                        logger.warning(f"服务健康检查失败: {service_name} - 状态码: {response.status}")
            
            # 更新服务状态
            await route_manager.update_service_health(service_name, healthy)
            
        except asyncio.TimeoutError:
            logger.warning(f"服务健康检查超时: {service_name}")
            await route_manager.update_service_health(service_name, False)
            
        except Exception as e:
            logger.error(f"服务健康检查异常: {service_name} - {e}")
            await route_manager.update_service_health(service_name, False)


class LoadBalancer:
    """负载均衡器"""
    
    def __init__(self):
        self.strategies = {
            "roundrobin": self._round_robin,
            "random": self._random,
            "least_connections": self._least_connections,
            "weighted_roundrobin": self._weighted_roundrobin
        }
        self._connection_counts: Dict[str, int] = {}
        self._round_robin_index: Dict[str, int] = {}
    
    def select_upstream(
        self, 
        service_name: str, 
        upstreams: Dict[str, int],
        strategy: str = "roundrobin"
    ) -> Optional[str]:
        """选择上游节点"""
        if not upstreams:
            return None
        
        if strategy in self.strategies:
            return self.strategies[strategy](service_name, upstreams)
        else:
            logger.warning(f"未知的负载均衡策略: {strategy}，使用轮询")
            return self._round_robin(service_name, upstreams)
    
    def _round_robin(self, service_name: str, upstreams: Dict[str, int]) -> str:
        """轮询策略"""
        if service_name not in self._round_robin_index:
            self._round_robin_index[service_name] = 0
        
        upstream_list = list(upstreams.keys())
        index = self._round_robin_index[service_name] % len(upstream_list)
        selected = upstream_list[index]
        
        self._round_robin_index[service_name] += 1
        return selected
    
    def _random(self, service_name: str, upstreams: Dict[str, int]) -> str:
        """随机策略"""
        import random
        return random.choice(list(upstreams.keys()))
    
    def _least_connections(self, service_name: str, upstreams: Dict[str, int]) -> str:
        """最少连接策略"""
        min_connections = float('inf')
        selected = None
        
        for upstream in upstreams.keys():
            connections = self._connection_counts.get(upstream, 0)
            if connections < min_connections:
                min_connections = connections
                selected = upstream
        
        return selected or list(upstreams.keys())[0]
    
    def _weighted_roundrobin(self, service_name: str, upstreams: Dict[str, int]) -> str:
        """加权轮询策略"""
        # 简化实现，实际应该根据权重进行更复杂的调度
        return self._round_robin(service_name, upstreams)
    
    def increment_connection(self, upstream: str) -> None:
        """增加连接计数"""
        self._connection_counts[upstream] = self._connection_counts.get(upstream, 0) + 1
    
    def decrement_connection(self, upstream: str) -> None:
        """减少连接计数"""
        if upstream in self._connection_counts:
            self._connection_counts[upstream] = max(0, self._connection_counts[upstream] - 1)


class ServiceManager:
    """服务管理器"""
    
    def __init__(self, route_manager: RouteManager):
        self.route_manager = route_manager
        self.health_checker = ServiceHealthChecker()
        self.load_balancer = LoadBalancer()
        self._service_callbacks: Dict[str, List[Callable]] = {}
        self._running = False
    
    async def start(self) -> None:
        """启动服务管理器"""
        self._running = True
        await self.health_checker.start_checking(self.route_manager)
        logger.info("服务管理器已启动")
    
    async def stop(self) -> None:
        """停止服务管理器"""
        self._running = False
        await self.health_checker.stop_checking()
        logger.info("服务管理器已停止")
    
    async def discover_service(self, service_name: str) -> Optional[ServiceInfo]:
        """服务发现"""
        return self.route_manager.services.get(service_name)
    
    async def get_healthy_services(self) -> List[ServiceInfo]:
        """获取健康的服务列表"""
        return [
            service for service in self.route_manager.services.values()
            if service.status == "healthy"
        ]
    
    async def register_service_callback(
        self, 
        service_name: str, 
        callback: Callable[[ServiceInfo, bool], None]
    ) -> None:
        """注册服务状态变化回调"""
        if service_name not in self._service_callbacks:
            self._service_callbacks[service_name] = []
        
        self._service_callbacks[service_name].append(callback)
    
    async def _notify_service_callbacks(self, service: ServiceInfo, healthy: bool) -> None:
        """通知服务状态变化回调"""
        callbacks = self._service_callbacks.get(service.name, [])
        for callback in callbacks:
            try:
                await callback(service, healthy)
            except Exception as e:
                logger.error(f"服务回调执行失败: {e}")
    
    async def get_service_metrics(self, service_name: str) -> Optional[Dict[str, Any]]:
        """获取服务指标"""
        service = self.route_manager.services.get(service_name)
        if not service:
            return None
        
        # 计算路由数量
        routes_count = len([
            route for route in self.route_manager.routes.values()
            if route.service_name == service_name
        ])
        
        # 计算连接数
        connections = sum(
            self.load_balancer._connection_counts.get(upstream, 0)
            for upstream in [f"{service.host}:{service.port}"]
        )
        
        return {
            "service_name": service_name,
            "status": service.status,
            "host": service.host,
            "port": service.port,
            "routes_count": routes_count,
            "active_connections": connections,
            "last_updated": service.updated_at.isoformat(),
            "uptime": (datetime.now() - service.created_at).total_seconds()
        }
    
    async def get_all_service_metrics(self) -> List[Dict[str, Any]]:
        """获取所有服务指标"""
        metrics = []
        for service_name in self.route_manager.services.keys():
            metric = await self.get_service_metrics(service_name)
            if metric:
                metrics.append(metric)
        return metrics
    
    async def scale_service(
        self, 
        service_name: str, 
        target_instances: int
    ) -> bool:
        """服务扩缩容（模拟）"""
        try:
            service = self.route_manager.services.get(service_name)
            if not service:
                logger.error(f"服务不存在: {service_name}")
                return False
            
            # 这里是模拟实现，实际应该调用容器编排平台
            logger.info(f"服务扩缩容: {service_name} -> {target_instances} 实例")
            
            # 更新服务权重（模拟负载）
            service.weight = target_instances * 100
            
            return True
            
        except Exception as e:
            logger.error(f"服务扩缩容失败: {service_name} - {e}")
            return False
    
    async def get_service_topology(self) -> Dict[str, Any]:
        """获取服务拓扑"""
        topology = {
            "services": {},
            "routes": {},
            "relationships": []
        }
        
        # 服务信息
        for service_name, service in self.route_manager.services.items():
            topology["services"][service_name] = {
                "id": service.id,
                "host": service.host,
                "port": service.port,
                "status": service.status,
                "weight": service.weight
            }
        
        # 路由信息
        for route_id, route in self.route_manager.routes.items():
            topology["routes"][route_id] = {
                "name": route.name,
                "service_name": route.service_name,
                "uri_patterns": route.uri_patterns,
                "methods": route.methods,
                "enabled": route.enabled
            }
            
            # 服务关系
            topology["relationships"].append({
                "from": route_id,
                "to": route.service_name,
                "type": "route_to_service"
            })
        
        return topology