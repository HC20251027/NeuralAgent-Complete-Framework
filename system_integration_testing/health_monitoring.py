"""
系统健康检查模块 - System Health Monitoring
===========================================

提供系统健康状态监控：
- 服务状态检查
- 资源使用监控
- 性能指标收集
- 告警机制

Author: HC20251027
Date: 2025-11-06
"""

import asyncio
import logging
import psutil
import time
import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import aiohttp
import socket

# 数据库连接
import psycopg2
import redis

# 配置管理
from agno_bmad_integration.framework import IntegrationFramework


@dataclass
class HealthCheckConfig:
    """健康检查配置类"""
    # 检查间隔
    check_interval: int = 30  # 秒
    timeout: int = 10  # 秒
    
    # 服务配置
    services: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    # 资源阈值
    cpu_threshold: float = 80.0  # %
    memory_threshold: float = 85.0  # %
    disk_threshold: float = 90.0  # %
    
    # 网络阈值
    network_latency_threshold: float = 1000.0  # ms
    connection_timeout_threshold: int = 5  # 秒
    
    # 数据库配置
    database_configs: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    # 告警配置
    alert_enabled: bool = True
    alert_thresholds: Dict[str, float] = field(default_factory=dict)
    
    # 日志配置
    log_level: str = "INFO"
    log_file: str = "/workspace/logs/health_monitor.log"


@dataclass
class HealthStatus:
    """健康状态类"""
    component: str
    status: str  # healthy, warning, critical, unknown
    last_check: datetime
    response_time: float
    error_message: Optional[str] = None
    metrics: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'component': self.component,
            'status': self.status,
            'last_check': self.last_check.isoformat(),
            'response_time': self.response_time,
            'error_message': self.error_message,
            'metrics': self.metrics,
            'metadata': self.metadata
        }


@dataclass
class AlertRule:
    """告警规则类"""
    rule_id: str
    name: str
    condition: str  # greater_than, less_than, equals
    threshold: float
    component: str
    severity: str  # info, warning, critical
    enabled: bool = True
    cooldown: int = 300  # 5分钟
    last_triggered: Optional[datetime] = None
    
    def should_trigger(self, value: float, current_time: datetime) -> bool:
        """检查是否应该触发告警"""
        if not self.enabled:
            return False
        
        # 检查冷却期
        if (self.last_triggered and 
            current_time - self.last_triggered < timedelta(seconds=self.cooldown)):
            return False
        
        # 检查条件
        if self.condition == "greater_than":
            return value > self.threshold
        elif self.condition == "less_than":
            return value < self.threshold
        elif self.condition == "equals":
            return abs(value - self.threshold) < 0.01
        
        return False


class ServiceHealthChecker:
    """服务健康检查器"""
    
    def __init__(self, config: HealthCheckConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
    
    async def check_service_health(self, service_name: str, service_config: Dict[str, Any]) -> HealthStatus:
        """检查服务健康状态"""
        start_time = time.time()
        
        try:
            # 检查HTTP服务
            if 'url' in service_config:
                return await self._check_http_service(service_name, service_config)
            
            # 检查TCP端口
            elif 'port' in service_config:
                return await self._check_tcp_service(service_name, service_config)
            
            # 检查进程
            elif 'process' in service_config:
                return await self._check_process_health(service_name, service_config)
            
            else:
                return HealthStatus(
                    component=service_name,
                    status="unknown",
                    last_check=datetime.now(),
                    response_time=time.time() - start_time,
                    error_message="未知的检查类型"
                )
        
        except Exception as e:
            return HealthStatus(
                component=service_name,
                status="critical",
                last_check=datetime.now(),
                response_time=time.time() - start_time,
                error_message=str(e)
            )
    
    async def _check_http_service(self, service_name: str, service_config: Dict[str, Any]) -> HealthStatus:
        """检查HTTP服务"""
        start_time = time.time()
        url = service_config['url']
        
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.config.timeout)) as session:
                async with session.get(url) as response:
                    response_time = time.time() - start_time
                    
                    if response.status == 200:
                        status = "healthy"
                    elif response.status < 500:
                        status = "warning"
                    else:
                        status = "critical"
                    
                    # 尝试获取响应数据
                    try:
                        response_data = await response.json()
                    except:
                        response_data = await response.text()
                    
                    return HealthStatus(
                        component=service_name,
                        status=status,
                        last_check=datetime.now(),
                        response_time=response_time,
                        metrics={
                            'status_code': response.status,
                            'response_size': len(str(response_data))
                        },
                        metadata={'url': url}
                    )
        
        except asyncio.TimeoutError:
            return HealthStatus(
                component=service_name,
                status="critical",
                last_check=datetime.now(),
                response_time=self.config.timeout,
                error_message="请求超时"
            )
        except Exception as e:
            return HealthStatus(
                component=service_name,
                status="critical",
                last_check=datetime.now(),
                response_time=time.time() - start_time,
                error_message=str(e)
            )
    
    async def _check_tcp_service(self, service_name: str, service_config: Dict[str, Any]) -> HealthStatus:
        """检查TCP服务"""
        start_time = time.time()
        host = service_config.get('host', 'localhost')
        port = service_config['port']
        
        try:
            # 创建socket连接
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.config.timeout)
            
            result = sock.connect_ex((host, port))
            sock.close()
            
            response_time = time.time() - start_time
            
            if result == 0:
                status = "healthy"
                error_message = None
            else:
                status = "critical"
                error_message = f"无法连接到 {host}:{port}"
            
            return HealthStatus(
                component=service_name,
                status=status,
                last_check=datetime.now(),
                response_time=response_time,
                error_message=error_message,
                metadata={'host': host, 'port': port}
            )
        
        except Exception as e:
            return HealthStatus(
                component=service_name,
                status="critical",
                last_check=datetime.now(),
                response_time=time.time() - start_time,
                error_message=str(e)
            )
    
    async def _check_process_health(self, service_name: str, service_config: Dict[str, Any]) -> HealthStatus:
        """检查进程健康状态"""
        start_time = time.time()
        process_name = service_config['process']
        
        try:
            # 查找进程
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'status']):
                if process_name.lower() in proc.info['name'].lower():
                    processes.append(proc)
            
            if not processes:
                return HealthStatus(
                    component=service_name,
                    status="critical",
                    last_check=datetime.now(),
                    response_time=time.time() - start_time,
                    error_message=f"进程 {process_name} 未找到"
                )
            
            # 检查主进程状态
            main_process = processes[0]
            process_info = main_process.info
            
            # 获取进程指标
            cpu_percent = main_process.cpu_percent()
            memory_info = main_process.memory_info()
            
            status = "healthy"
            if cpu_percent > self.config.cpu_threshold:
                status = "warning"
            if memory_info.rss / 1024 / 1024 > self.config.memory_threshold * psutil.virtual_memory().total / 100:
                status = "warning"
            
            return HealthStatus(
                component=service_name,
                status=status,
                last_check=datetime.now(),
                response_time=time.time() - start_time,
                metrics={
                    'cpu_percent': cpu_percent,
                    'memory_mb': memory_info.rss / 1024 / 1024,
                    'pid': process_info['pid'],
                    'status': process_info['status']
                },
                metadata={'process_name': process_name}
            )
        
        except Exception as e:
            return HealthStatus(
                component=service_name,
                status="critical",
                last_check=datetime.now(),
                response_time=time.time() - start_time,
                error_message=str(e)
            )


class DatabaseHealthChecker:
    """数据库健康检查器"""
    
    def __init__(self, config: HealthCheckConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
    
    async def check_database_health(self, db_name: str, db_config: Dict[str, Any]) -> HealthStatus:
        """检查数据库健康状态"""
        start_time = time.time()
        
        try:
            db_type = db_config.get('type', 'postgresql')
            
            if db_type == 'postgresql':
                return await self._check_postgresql_health(db_name, db_config)
            elif db_type == 'redis':
                return await self._check_redis_health(db_name, db_config)
            else:
                return HealthStatus(
                    component=f"database_{db_name}",
                    status="unknown",
                    last_check=datetime.now(),
                    response_time=time.time() - start_time,
                    error_message=f"不支持的数据库类型: {db_type}"
                )
        
        except Exception as e:
            return HealthStatus(
                component=f"database_{db_name}",
                status="critical",
                last_check=datetime.now(),
                response_time=time.time() - start_time,
                error_message=str(e)
            )
    
    async def _check_postgresql_health(self, db_name: str, db_config: Dict[str, Any]) -> HealthStatus:
        """检查PostgreSQL健康状态"""
        start_time = time.time()
        
        try:
            connection = psycopg2.connect(
                host=db_config.get('host', 'localhost'),
                port=db_config.get('port', 5432),
                database=db_config.get('database', 'postgres'),
                user=db_config.get('user', 'postgres'),
                password=db_config.get('password', 'password'),
                connect_timeout=self.config.timeout
            )
            
            cursor = connection.cursor()
            
            # 执行健康检查查询
            cursor.execute("SELECT 1")
            cursor.fetchone()
            
            # 获取数据库统计信息
            cursor.execute("""
                SELECT 
                    datname,
                    numbackends,
                    xact_commit,
                    xact_rollback,
                    blks_read,
                    blks_hit,
                    tup_returned,
                    tup_fetched,
                    tup_inserted,
                    tup_updated,
                    tup_deleted
                FROM pg_stat_database 
                WHERE datname = %s
            """, (db_config.get('database', 'postgres'),))
            
            stats = cursor.fetchone()
            
            cursor.close()
            connection.close()
            
            response_time = time.time() - start_time
            
            return HealthStatus(
                component=f"database_{db_name}",
                status="healthy",
                last_check=datetime.now(),
                response_time=response_time,
                metrics={
                    'datname': stats[0] if stats else 'unknown',
                    'numbackends': stats[1] if stats else 0,
                    'xact_commit': stats[2] if stats else 0,
                    'xact_rollback': stats[3] if stats else 0,
                    'blks_read': stats[4] if stats else 0,
                    'blks_hit': stats[5] if stats else 0
                },
                metadata={'connection_string': f"postgresql://{db_config.get('host', 'localhost')}:{db_config.get('port', 5432)}"}
            )
        
        except psycopg2.Error as e:
            return HealthStatus(
                component=f"database_{db_name}",
                status="critical",
                last_check=datetime.now(),
                response_time=time.time() - start_time,
                error_message=f"PostgreSQL错误: {str(e)}"
            )
        except Exception as e:
            return HealthStatus(
                component=f"database_{db_name}",
                status="critical",
                last_check=datetime.now(),
                response_time=time.time() - start_time,
                error_message=str(e)
            )
    
    async def _check_redis_health(self, db_name: str, db_config: Dict[str, Any]) -> HealthStatus:
        """检查Redis健康状态"""
        start_time = time.time()
        
        try:
            r = redis.Redis(
                host=db_config.get('host', 'localhost'),
                port=db_config.get('port', 6379),
                password=db_config.get('password'),
                socket_timeout=self.config.timeout,
                socket_connect_timeout=self.config.timeout
            )
            
            # 执行PING命令
            ping_result = r.ping()
            
            # 获取Redis信息
            info = r.info()
            
            response_time = time.time() - start_time
            
            r.close()
            
            if ping_result:
                status = "healthy"
                error_message = None
            else:
                status = "critical"
                error_message = "Redis PING失败"
            
            return HealthStatus(
                component=f"database_{db_name}",
                status=status,
                last_check=datetime.now(),
                response_time=response_time,
                error_message=error_message,
                metrics={
                    'redis_version': info.get('redis_version', 'unknown'),
                    'used_memory': info.get('used_memory', 0),
                    'connected_clients': info.get('connected_clients', 0),
                    'total_commands_processed': info.get('total_commands_processed', 0)
                },
                metadata={'connection_string': f"redis://{db_config.get('host', 'localhost')}:{db_config.get('port', 6379)}"}
            )
        
        except redis.RedisError as e:
            return HealthStatus(
                component=f"database_{db_name}",
                status="critical",
                last_check=datetime.now(),
                response_time=time.time() - start_time,
                error_message=f"Redis错误: {str(e)}"
            )
        except Exception as e:
            return HealthStatus(
                component=f"database_{db_name}",
                status="critical",
                last_check=datetime.now(),
                response_time=time.time() - start_time,
                error_message=str(e)
            )


class SystemResourceMonitor:
    """系统资源监控器"""
    
    def __init__(self, config: HealthCheckConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
    
    async def check_system_resources(self) -> List[HealthStatus]:
        """检查系统资源"""
        results = []
        
        # CPU使用率
        cpu_status = await self._check_cpu_usage()
        results.append(cpu_status)
        
        # 内存使用率
        memory_status = await self._check_memory_usage()
        results.append(memory_status)
        
        # 磁盘使用率
        disk_status = await self._check_disk_usage()
        results.append(disk_status)
        
        # 网络状态
        network_status = await self._check_network_status()
        results.append(network_status)
        
        return results
    
    async def _check_cpu_usage(self) -> HealthStatus:
        """检查CPU使用率"""
        start_time = time.time()
        
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            
            if cpu_percent < self.config.cpu_threshold:
                status = "healthy"
            elif cpu_percent < self.config.cpu_threshold * 1.2:
                status = "warning"
            else:
                status = "critical"
            
            return HealthStatus(
                component="system_cpu",
                status=status,
                last_check=datetime.now(),
                response_time=time.time() - start_time,
                metrics={
                    'cpu_percent': cpu_percent,
                    'cpu_count': psutil.cpu_count(),
                    'load_average': psutil.getloadavg() if hasattr(psutil, 'getloadavg') else None
                }
            )
        
        except Exception as e:
            return HealthStatus(
                component="system_cpu",
                status="critical",
                last_check=datetime.now(),
                response_time=time.time() - start_time,
                error_message=str(e)
            )
    
    async def _check_memory_usage(self) -> HealthStatus:
        """检查内存使用率"""
        start_time = time.time()
        
        try:
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            if memory_percent < self.config.memory_threshold:
                status = "healthy"
            elif memory_percent < self.config.memory_threshold * 1.1:
                status = "warning"
            else:
                status = "critical"
            
            return HealthStatus(
                component="system_memory",
                status=status,
                last_check=datetime.now(),
                response_time=time.time() - start_time,
                metrics={
                    'memory_percent': memory_percent,
                    'total_gb': memory.total / (1024**3),
                    'available_gb': memory.available / (1024**3),
                    'used_gb': memory.used / (1024**3)
                }
            )
        
        except Exception as e:
            return HealthStatus(
                component="system_memory",
                status="critical",
                last_check=datetime.now(),
                response_time=time.time() - start_time,
                error_message=str(e)
            )
    
    async def _check_disk_usage(self) -> HealthStatus:
        """检查磁盘使用率"""
        start_time = time.time()
        
        try:
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            
            if disk_percent < self.config.disk_threshold:
                status = "healthy"
            elif disk_percent < self.config.disk_threshold * 1.05:
                status = "warning"
            else:
                status = "critical"
            
            return HealthStatus(
                component="system_disk",
                status=status,
                last_check=datetime.now(),
                response_time=time.time() - start_time,
                metrics={
                    'disk_percent': disk_percent,
                    'total_gb': disk.total / (1024**3),
                    'free_gb': disk.free / (1024**3),
                    'used_gb': disk.used / (1024**3)
                }
            )
        
        except Exception as e:
            return HealthStatus(
                component="system_disk",
                status="critical",
                last_check=datetime.now(),
                response_time=time.time() - start_time,
                error_message=str(e)
            )
    
    async def _check_network_status(self) -> HealthStatus:
        """检查网络状态"""
        start_time = time.time()
        
        try:
            # 检查网络接口
            network_io = psutil.net_io_counters()
            
            # 计算网络延迟 (简单的ping测试)
            latency = await self._measure_network_latency()
            
            if latency < self.config.network_latency_threshold:
                status = "healthy"
            elif latency < self.config.network_latency_threshold * 1.5:
                status = "warning"
            else:
                status = "critical"
            
            return HealthStatus(
                component="system_network",
                status=status,
                last_check=datetime.now(),
                response_time=time.time() - start_time,
                metrics={
                    'latency_ms': latency,
                    'bytes_sent': network_io.bytes_sent,
                    'bytes_recv': network_io.bytes_recv,
                    'packets_sent': network_io.packets_sent,
                    'packets_recv': network_io.packets_recv
                }
            )
        
        except Exception as e:
            return HealthStatus(
                component="system_network",
                status="critical",
                last_check=datetime.now(),
                response_time=time.time() - start_time,
                error_message=str(e)
            )
    
    async def _measure_network_latency(self) -> float:
        """测量网络延迟"""
        try:
            # 简单的延迟测量
            start_time = time.time()
            
            # 连接到本地网关 (假设是192.168.1.1)
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            
            try:
                sock.connect(('192.168.1.1', 80))
                latency = (time.time() - start_time) * 1000  # 转换为毫秒
                return latency
            except:
                # 如果连接失败，返回一个较大的值
                return self.config.network_latency_threshold * 2
            finally:
                sock.close()
        
        except Exception:
            return self.config.network_latency_threshold * 2


class AlertManager:
    """告警管理器"""
    
    def __init__(self, config: HealthCheckConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.alert_rules: List[AlertRule] = []
        self.alert_history: List[Dict[str, Any]] = []
    
    def add_alert_rule(self, rule: AlertRule):
        """添加告警规则"""
        self.alert_rules.append(rule)
    
    async def check_alerts(self, health_statuses: List[HealthStatus]) -> List[Dict[str, Any]]:
        """检查告警"""
        if not self.config.alert_enabled:
            return []
        
        triggered_alerts = []
        current_time = datetime.now()
        
        for status in health_statuses:
            for rule in self.alert_rules:
                if rule.component == status.component and rule.should_trigger(
                    self._extract_metric_value(status, rule), current_time
                ):
                    alert = {
                        'rule_id': rule.rule_id,
                        'rule_name': rule.name,
                        'component': status.component,
                        'severity': rule.severity,
                        'status': status.status,
                        'value': self._extract_metric_value(status, rule),
                        'threshold': rule.threshold,
                        'timestamp': current_time.isoformat(),
                        'error_message': status.error_message
                    }
                    
                    triggered_alerts.append(alert)
                    rule.last_triggered = current_time
                    
                    # 记录告警历史
                    self.alert_history.append(alert)
                    
                    self.logger.warning(f"告警触发: {rule.name} - {status.component}")
        
        return triggered_alerts
    
    def _extract_metric_value(self, status: HealthStatus, rule: AlertRule) -> float:
        """从健康状态中提取指标值"""
        # 这里可以根据规则类型提取相应的指标值
        # 简化实现，返回CPU使用率或内存使用率
        if 'cpu_percent' in status.metrics:
            return status.metrics['cpu_percent']
        elif 'memory_percent' in status.metrics:
            return status.metrics['memory_percent']
        elif 'disk_percent' in status.metrics:
            return status.metrics['disk_percent']
        else:
            return 0.0
    
    def get_alert_summary(self) -> Dict[str, Any]:
        """获取告警摘要"""
        recent_alerts = [
            alert for alert in self.alert_history
            if datetime.now() - datetime.fromisoformat(alert['timestamp']) < timedelta(hours=1)
        ]
        
        return {
            'total_alerts': len(self.alert_history),
            'recent_alerts': len(recent_alerts),
            'alert_by_severity': {
                'critical': len([a for a in recent_alerts if a['severity'] == 'critical']),
                'warning': len([a for a in recent_alerts if a['severity'] == 'warning']),
                'info': len([a for a in recent_alerts if a['severity'] == 'info'])
            }
        }


class SystemHealthMonitor:
    """系统健康监控器主类"""
    
    def __init__(self, config: Optional[HealthCheckConfig] = None):
        self.config = config or self._create_default_config()
        self.logger = logging.getLogger(__name__)
        
        # 初始化组件
        self.service_checker = ServiceHealthChecker(self.config)
        self.database_checker = DatabaseHealthChecker(self.config)
        self.resource_monitor = SystemResourceMonitor(self.config)
        self.alert_manager = AlertManager(self.config)
        
        # 状态存储
        self.current_statuses: List[HealthStatus] = []
        self.monitoring_task: Optional[asyncio.Task] = None
        self.is_monitoring = False
        
        # 集成框架
        self.integration_framework = IntegrationFramework()
        
        # 设置默认告警规则
        self._setup_default_alert_rules()
        
        # 设置日志
        self._setup_logging()
    
    def _create_default_config(self) -> HealthCheckConfig:
        """创建默认配置"""
        services = {
            'apisix_gateway': {
                'url': 'http://localhost:9080/apisix/status',
                'type': 'http'
            },
            'agno_framework': {
                'url': 'http://localhost:8000/health',
                'type': 'http'
            },
            'bmad_framework': {
                'url': 'http://localhost:8001/health',
                'type': 'http'
            },
            'neural_vision': {
                'url': 'http://localhost:8002/health',
                'type': 'http'
            },
            'voice_interaction': {
                'url': 'http://localhost:8003/health',
                'type': 'http'
            },
            'postgres': {
                'host': 'localhost',
                'port': 5432,
                'type': 'tcp'
            },
            'redis': {
                'host': 'localhost',
                'port': 6379,
                'type': 'tcp'
            }
        }
        
        database_configs = {
            'postgresql': {
                'type': 'postgresql',
                'host': 'localhost',
                'port': 5432,
                'database': 'postgres',
                'user': 'postgres',
                'password': 'password'
            },
            'redis': {
                'type': 'redis',
                'host': 'localhost',
                'port': 6379
            }
        }
        
        return HealthCheckConfig(
            services=services,
            database_configs=database_configs,
            alert_thresholds={
                'cpu': 80.0,
                'memory': 85.0,
                'disk': 90.0
            }
        )
    
    def _setup_default_alert_rules(self):
        """设置默认告警规则"""
        rules = [
            AlertRule(
                rule_id="cpu_high",
                name="CPU使用率过高",
                condition="greater_than",
                threshold=self.config.cpu_threshold,
                component="system_cpu",
                severity="warning"
            ),
            AlertRule(
                rule_id="memory_high",
                name="内存使用率过高",
                condition="greater_than",
                threshold=self.config.memory_threshold,
                component="system_memory",
                severity="warning"
            ),
            AlertRule(
                rule_id="disk_high",
                name="磁盘使用率过高",
                condition="greater_than",
                threshold=self.config.disk_threshold,
                component="system_disk",
                severity="warning"
            )
        ]
        
        for rule in rules:
            self.alert_manager.add_alert_rule(rule)
    
    def _setup_logging(self):
        """设置日志"""
        log_file = Path(self.config.log_file)
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        logging.basicConfig(
            level=getattr(logging, self.config.log_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
    
    async def start_monitoring(self):
        """开始监控"""
        if self.is_monitoring:
            return
        
        self.is_monitoring = True
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
        self.logger.info("系统健康监控已启动")
    
    async def stop_monitoring(self):
        """停止监控"""
        self.is_monitoring = False
        
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        
        self.logger.info("系统健康监控已停止")
    
    async def _monitoring_loop(self):
        """监控循环"""
        while self.is_monitoring:
            try:
                await self.perform_health_check()
                await asyncio.sleep(self.config.check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"监控循环异常: {e}")
                await asyncio.sleep(self.config.check_interval)
    
    async def perform_health_check(self) -> Dict[str, Any]:
        """执行健康检查"""
        self.logger.info("开始执行系统健康检查...")
        
        all_statuses = []
        
        try:
            # 1. 检查服务健康状态
            for service_name, service_config in self.config.services.items():
                status = await self.service_checker.check_service_health(service_name, service_config)
                all_statuses.append(status)
            
            # 2. 检查数据库健康状态
            for db_name, db_config in self.config.database_configs.items():
                status = await self.database_checker.check_database_health(db_name, db_config)
                all_statuses.append(status)
            
            # 3. 检查系统资源
            resource_statuses = await self.resource_monitor.check_system_resources()
            all_statuses.extend(resource_statuses)
            
            # 4. 检查告警
            alerts = await self.alert_manager.check_alerts(all_statuses)
            
            # 更新当前状态
            self.current_statuses = all_statuses
            
            # 集成到框架
            if self.integration_framework:
                await self._integrate_health_status(all_statuses, alerts)
            
            # 生成检查结果
            result = {
                'timestamp': datetime.now().isoformat(),
                'overall_status': self._calculate_overall_status(all_statuses),
                'statuses': [status.to_dict() for status in all_statuses],
                'alerts': alerts,
                'alert_summary': self.alert_manager.get_alert_summary(),
                'summary': self._generate_summary(all_statuses)
            }
            
            self.logger.info(f"健康检查完成: 总体状态 {result['overall_status']}")
            
            return result
        
        except Exception as e:
            self.logger.error(f"健康检查失败: {e}")
            return {
                'timestamp': datetime.now().isoformat(),
                'overall_status': 'error',
                'error': str(e)
            }
    
    def _calculate_overall_status(self, statuses: List[HealthStatus]) -> str:
        """计算总体状态"""
        if not statuses:
            return 'unknown'
        
        status_counts = {'healthy': 0, 'warning': 0, 'critical': 0, 'unknown': 0}
        
        for status in statuses:
            status_counts[status.status] += 1
        
        total = len(statuses)
        
        if status_counts['critical'] > 0:
            return 'critical'
        elif status_counts['warning'] > total * 0.3:  # 超过30%为warning
            return 'warning'
        elif status_counts['healthy'] == total:
            return 'healthy'
        else:
            return 'degraded'
    
    def _generate_summary(self, statuses: List[HealthStatus]) -> Dict[str, Any]:
        """生成摘要"""
        summary = {
            'total_components': len(statuses),
            'healthy_count': len([s for s in statuses if s.status == 'healthy']),
            'warning_count': len([s for s in statuses if s.status == 'warning']),
            'critical_count': len([s for s in statuses if s.status == 'critical']),
            'unknown_count': len([s for s in statuses if s.status == 'unknown']),
            'average_response_time': 0.0
        }
        
        if statuses:
            response_times = [s.response_time for s in statuses if s.response_time > 0]
            if response_times:
                summary['average_response_time'] = sum(response_times) / len(response_times)
        
        return summary
    
    async def _integrate_health_status(self, statuses: List[HealthStatus], alerts: List[Dict[str, Any]]):
        """集成健康状态到框架"""
        try:
            if self.integration_framework:
                await self.integration_framework.broadcast_event(
                    'health_check_completed',
                    {
                        'statuses': [status.to_dict() for status in statuses],
                        'alerts': alerts,
                        'timestamp': datetime.now().isoformat()
                    }
                )
        except Exception as e:
            self.logger.error(f"健康状态集成失败: {e}")
    
    def get_current_status(self) -> List[Dict[str, Any]]:
        """获取当前状态"""
        return [status.to_dict() for status in self.current_statuses]
    
    def get_health_report(self) -> Dict[str, Any]:
        """获取健康报告"""
        if not self.current_statuses:
            return {'error': '暂无健康状态数据'}
        
        return {
            'timestamp': datetime.now().isoformat(),
            'overall_status': self._calculate_overall_status(self.current_statuses),
            'current_statuses': self.get_current_status(),
            'alert_summary': self.alert_manager.get_alert_summary(),
            'summary': self._generate_summary(self.current_statuses)
        }
    
    def add_custom_service_check(self, service_name: str, check_function: Callable):
        """添加自定义服务检查"""
        # 这里可以实现自定义检查函数的注册
        # 简化实现
        pass
    
    def export_health_data(self, output_path: str) -> str:
        """导出健康数据"""
        report_data = {
            'export_time': datetime.now().isoformat(),
            'health_report': self.get_health_report(),
            'alert_history': self.alert_manager.alert_history
        }
        
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        
        return str(output_file)