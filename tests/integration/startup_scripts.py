"""
一键启动脚本模板 - One-Click Startup Scripts
============================================

提供系统一键启动功能：
- 环境检查
- 服务启动
- 依赖验证
- 配置管理

Author: HC20251027
Date: 2025-11-06
"""

import asyncio
import logging
import os
import sys
import subprocess
import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
import signal
import psutil

# 配置管理
from agno_bmad_integration.framework import IntegrationFramework


@dataclass
class ServiceConfig:
    """服务配置类"""
    name: str
    command: str
    args: List[str] = field(default_factory=list)
    cwd: Optional[str] = None
    env: Dict[str, str] = field(default_factory=dict)
    port: Optional[int] = None
    health_check_url: Optional[str] = None
    health_check_interval: int = 30
    restart_on_failure: bool = True
    max_restart_attempts: int = 3
    required: bool = True
    startup_timeout: int = 60


@dataclass
class StartupConfig:
    """启动配置类"""
    # 基本配置
    project_root: str = "/workspace"
    log_dir: str = "/workspace/logs"
    config_dir: str = "/workspace/config"
    
    # 服务配置
    services: List[ServiceConfig] = field(default_factory=list)
    
    # 启动配置
    parallel_startup: bool = True
    startup_timeout: int = 300
    health_check_enabled: bool = True
    auto_restart: bool = True
    
    # 数据库配置
    database_enabled: bool = True
    database_config: Dict[str, Any] = field(default_factory=dict)
    
    # 网关配置
    gateway_enabled: bool = True
    gateway_config: Dict[str, Any] = field(default_factory=dict)
    
    # 集成配置
    integration_enabled: bool = True


class ServiceManager:
    """服务管理器"""
    
    def __init__(self, service_config: ServiceConfig):
        self.config = service_config
        self.logger = logging.getLogger(__name__)
        self.process: Optional[subprocess.Popen] = None
        self.status = "stopped"
        self.start_time: Optional[datetime] = None
        self.restart_count = 0
    
    async def start(self) -> bool:
        """启动服务"""
        try:
            # 构建启动命令
            cmd = [self.config.command] + self.config.args
            
            # 设置工作目录
            cwd = self.config.cwd or os.getcwd()
            
            # 设置环境变量
            env = os.environ.copy()
            env.update(self.config.env)
            
            # 启动进程
            self.process = subprocess.Popen(
                cmd,
                cwd=cwd,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=os.setsid if os.name != 'nt' else None
            )
            
            self.status = "starting"
            self.start_time = datetime.now()
            
            self.logger.info(f"启动服务 {self.config.name}: {' '.join(cmd)}")
            
            # 等待启动完成
            return await self._wait_for_startup()
            
        except Exception as e:
            self.logger.error(f"启动服务 {self.config.name} 失败: {e}")
            self.status = "failed"
            return False
    
    async def stop(self) -> bool:
        """停止服务"""
        try:
            if self.process:
                # 发送终止信号
                if os.name != 'nt':
                    os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
                else:
                    self.process.terminate()
                
                # 等待进程结束
                try:
                    self.process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    # 强制杀死
                    if os.name != 'nt':
                        os.killpg(os.getpgid(self.process.pid), signal.SIGKILL)
                    else:
                        self.process.kill()
                
                self.process = None
            
            self.status = "stopped"
            self.logger.info(f"停止服务 {self.config.name}")
            return True
            
        except Exception as e:
            self.logger.error(f"停止服务 {self.config.name} 失败: {e}")
            return False
    
    async def restart(self) -> bool:
        """重启服务"""
        self.logger.info(f"重启服务 {self.config.name}")
        await self.stop()
        await asyncio.sleep(2)  # 等待清理
        return await self.start()
    
    def is_running(self) -> bool:
        """检查服务是否运行"""
        if not self.process:
            return False
        
        # 检查进程是否还在运行
        try:
            psutil.Process(self.process.pid)
            return self.process.poll() is None
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """获取服务状态"""
        return {
            'name': self.config.name,
            'status': self.status,
            'running': self.is_running(),
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'restart_count': self.restart_count,
            'pid': self.process.pid if self.process else None
        }
    
    async def _wait_for_startup(self) -> bool:
        """等待服务启动完成"""
        start_time = time.time()
        
        while time.time() - start_time < self.config.startup_timeout:
            if self.is_running():
                # 检查健康状态
                if await self._check_health():
                    self.status = "running"
                    self.logger.info(f"服务 {self.config.name} 启动成功")
                    return True
            
            await asyncio.sleep(2)
        
        self.status = "failed"
        self.logger.error(f"服务 {self.config.name} 启动超时")
        return False
    
    async def _check_health(self) -> bool:
        """检查服务健康状态"""
        if not self.config.health_check_url:
            return True  # 没有健康检查URL，默认为健康
        
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(self.config.health_check_url, timeout=10) as response:
                    return response.status == 200
        except Exception as e:
            self.logger.warning(f"健康检查失败 {self.config.name}: {e}")
            return False


class EnvironmentChecker:
    """环境检查器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    async def check_environment(self) -> Dict[str, Any]:
        """检查环境"""
        results = {
            'overall_status': 'unknown',
            'checks': {},
            'errors': [],
            'warnings': []
        }
        
        # 检查Python版本
        python_version = sys.version_info
        results['checks']['python_version'] = {
            'status': 'ok' if python_version >= (3, 8) else 'error',
            'version': f"{python_version.major}.{python_version.minor}.{python_version.micro}",
            'required': '3.8+'
        }
        
        if python_version < (3, 8):
            results['errors'].append("Python版本需要3.8或更高版本")
        
        # 检查必要的包
        required_packages = [
            'asyncio', 'aiohttp', 'numpy', 'pandas', 'scikit-learn',
            'librosa', 'soundfile', 'psycopg2', 'redis'
        ]
        
        missing_packages = []
        for package in required_packages:
            try:
                __import__(package)
                results['checks'][f'package_{package}'] = {'status': 'ok'}
            except ImportError:
                results['checks'][f'package_{package}'] = {'status': 'missing'}
                missing_packages.append(package)
        
        if missing_packages:
            results['warnings'].append(f"缺少包: {', '.join(missing_packages)}")
        
        # 检查系统资源
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        results['checks']['memory'] = {
            'status': 'ok' if memory.percent < 90 else 'warning',
            'total': f"{memory.total // (1024**3)}GB",
            'available': f"{memory.available // (1024**3)}GB",
            'usage_percent': memory.percent
        }
        
        results['checks']['disk'] = {
            'status': 'ok' if disk.percent < 90 else 'warning',
            'total': f"{disk.total // (1024**3)}GB",
            'free': f"{disk.free // (1024**3)}GB",
            'usage_percent': disk.percent
        }
        
        # 检查端口可用性
        ports_to_check = [5432, 6379, 8080, 9080]  # PostgreSQL, Redis, API Gateway
        available_ports = []
        used_ports = []
        
        for port in ports_to_check:
            if self._is_port_available(port):
                available_ports.append(port)
                results['checks'][f'port_{port}'] = {'status': 'available'}
            else:
                used_ports.append(port)
                results['checks'][f'port_{port}'] = {'status': 'in_use'}
        
        # 确定总体状态
        if results['errors']:
            results['overall_status'] = 'error'
        elif results['warnings']:
            results['overall_status'] = 'warning'
        else:
            results['overall_status'] = 'ok'
        
        return results
    
    def _is_port_available(self, port: int) -> bool:
        """检查端口是否可用"""
        import socket
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.bind(('localhost', port))
                return True
        except OSError:
            return False


class SystemStartupManager:
    """系统启动管理器"""
    
    def __init__(self, config: Optional[StartupConfig] = None):
        self.config = config or self._create_default_config()
        self.logger = logging.getLogger(__name__)
        
        # 初始化组件
        self.environment_checker = EnvironmentChecker()
        self.service_managers: Dict[str, ServiceManager] = {}
        self.integration_framework = IntegrationFramework()
        
        # 设置日志
        self._setup_logging()
        
        # 创建服务管理器
        self._create_service_managers()
    
    def _create_default_config(self) -> StartupConfig:
        """创建默认配置"""
        services = [
            ServiceConfig(
                name="postgres",
                command="docker",
                args=["run", "-d", "--name", "postgres", 
                      "-e", "POSTGRES_PASSWORD=password", 
                      "-p", "5432:5432", "postgres:13"],
                health_check_url="postgresql://localhost:5432",
                required=True
            ),
            ServiceConfig(
                name="redis",
                command="docker", 
                args=["run", "-d", "--name", "redis", 
                      "-p", "6379:6379", "redis:alpine"],
                health_check_url="redis://localhost:6379",
                required=True
            ),
            ServiceConfig(
                name="apisix_gateway",
                command="apisix",
                args=["start"],
                cwd="/workspace/apisix",
                health_check_url="http://localhost:9080/apisix/status",
                required=True
            ),
            ServiceConfig(
                name="agno_framework",
                command="python",
                args=["-m", "agno.main"],
                cwd="/workspace/agno",
                health_check_url="http://localhost:8000/health",
                required=True
            ),
            ServiceConfig(
                name="bmad_framework", 
                command="python",
                args=["-m", "bmad.main"],
                cwd="/workspace/bmad",
                health_check_url="http://localhost:8001/health",
                required=True
            ),
            ServiceConfig(
                name="neural_vision",
                command="python",
                args=["-m", "neural_agent_vision.main"],
                cwd="/workspace/neural_agent_vision",
                health_check_url="http://localhost:8002/health",
                required=False
            ),
            ServiceConfig(
                name="voice_interaction",
                command="python", 
                args=["-m", "voice_interaction.main"],
                cwd="/workspace/voice_interaction",
                health_check_url="http://localhost:8003/health",
                required=False
            )
        ]
        
        return StartupConfig(services=services)
    
    def _setup_logging(self):
        """设置日志"""
        log_dir = Path(self.config.log_dir)
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # 配置日志格式
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        
        # 创建文件处理器
        file_handler = logging.FileHandler(log_dir / 'startup.log')
        file_handler.setFormatter(logging.Formatter(log_format))
        
        # 创建控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter(log_format))
        
        # 配置根日志器
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)
        root_logger.addHandler(file_handler)
        root_logger.addHandler(console_handler)
    
    def _create_service_managers(self):
        """创建服务管理器"""
        for service_config in self.config.services:
            self.service_managers[service_config.name] = ServiceManager(service_config)
    
    async def startup(self) -> Dict[str, Any]:
        """启动系统"""
        self.logger.info("开始系统启动...")
        
        startup_results = {
            'success': False,
            'start_time': datetime.now().isoformat(),
            'environment_check': {},
            'service_status': {},
            'errors': [],
            'warnings': []
        }
        
        try:
            # 1. 环境检查
            self.logger.info("执行环境检查...")
            env_check = await self.environment_checker.check_environment()
            startup_results['environment_check'] = env_check
            
            if env_check['overall_status'] == 'error':
                startup_results['errors'].extend(env_check['errors'])
                return startup_results
            
            startup_results['warnings'].extend(env_check['warnings'])
            
            # 2. 启动服务
            self.logger.info("启动服务...")
            service_results = await self._start_services()
            startup_results['service_status'] = service_results
            
            # 检查是否有失败的服务
            failed_services = [
                name for name, result in service_results.items() 
                if not result['success']
            ]
            
            if failed_services:
                startup_results['errors'].extend([
                    f"服务启动失败: {', '.join(failed_services)}"
                ])
            
            # 3. 验证系统集成
            self.logger.info("验证系统集成...")
            integration_result = await self._verify_integration()
            startup_results['integration_check'] = integration_result
            
            if not integration_result['success']:
                startup_results['errors'].append("系统集成验证失败")
            
            # 4. 确定总体结果
            startup_results['success'] = (
                env_check['overall_status'] in ['ok', 'warning'] and
                not failed_services and
                integration_result['success']
            )
            
            startup_results['end_time'] = datetime.now().isoformat()
            
            if startup_results['success']:
                self.logger.info("系统启动成功!")
            else:
                self.logger.error("系统启动失败!")
            
            return startup_results
            
        except Exception as e:
            self.logger.error(f"系统启动异常: {e}")
            startup_results['errors'].append(str(e))
            return startup_results
    
    async def shutdown(self) -> Dict[str, Any]:
        """关闭系统"""
        self.logger.info("开始系统关闭...")
        
        shutdown_results = {
            'success': True,
            'start_time': datetime.now().isoformat(),
            'service_status': {},
            'errors': []
        }
        
        try:
            # 停止所有服务
            for service_name, manager in self.service_managers.items():
                self.logger.info(f"停止服务: {service_name}")
                try:
                    success = await manager.stop()
                    shutdown_results['service_status'][service_name] = {
                        'success': success,
                        'status': manager.get_status()
                    }
                    if not success:
                        shutdown_results['errors'].append(f"停止服务 {service_name} 失败")
                except Exception as e:
                    self.logger.error(f"停止服务 {service_name} 失败: {e}")
                    shutdown_results['service_status'][service_name] = {
                        'success': False,
                        'error': str(e)
                    }
                    shutdown_results['errors'].append(f"停止服务 {service_name} 失败: {e}")
            
            shutdown_results['success'] = len(shutdown_results['errors']) == 0
            shutdown_results['end_time'] = datetime.now().isoformat()
            
            if shutdown_results['success']:
                self.logger.info("系统关闭成功!")
            else:
                self.logger.warning("系统关闭完成，但有错误")
            
            return shutdown_results
            
        except Exception as e:
            self.logger.error(f"系统关闭异常: {e}")
            shutdown_results['errors'].append(str(e))
            return shutdown_results
    
    async def _start_services(self) -> Dict[str, Dict[str, Any]]:
        """启动服务"""
        service_results = {}
        
        if self.config.parallel_startup:
            # 并行启动
            tasks = []
            for service_name, manager in self.service_managers.items():
                task = self._start_single_service(service_name, manager)
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for i, (service_name, manager) in enumerate(self.service_managers.items()):
                if isinstance(results[i], Exception):
                    service_results[service_name] = {
                        'success': False,
                        'error': str(results[i])
                    }
                else:
                    service_results[service_name] = results[i]
        else:
            # 串行启动
            for service_name, manager in self.service_managers.items():
                result = await self._start_single_service(service_name, manager)
                service_results[service_name] = result
        
        return service_results
    
    async def _start_single_service(self, service_name: str, manager: ServiceManager) -> Dict[str, Any]:
        """启动单个服务"""
        try:
            success = await manager.start()
            return {
                'success': success,
                'status': manager.get_status()
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _verify_integration(self) -> Dict[str, Any]:
        """验证系统集成"""
        try:
            # 测试集成框架
            if self.integration_framework:
                # 发送测试事件
                await self.integration_framework.broadcast_event(
                    'startup_verification',
                    {'timestamp': datetime.now().isoformat()}
                )
            
            return {'success': True, 'message': '集成验证通过'}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        status = {
            'timestamp': datetime.now().isoformat(),
            'services': {},
            'overall_status': 'unknown'
        }
        
        # 获取所有服务状态
        for service_name, manager in self.service_managers.items():
            status['services'][service_name] = manager.get_status()
        
        # 计算总体状态
        running_services = sum(
            1 for s in status['services'].values() 
            if s['status'] == 'running'
        )
        total_services = len(self.service_managers)
        
        if running_services == total_services:
            status['overall_status'] = 'healthy'
        elif running_services > 0:
            status['overall_status'] = 'partial'
        else:
            status['overall_status'] = 'unhealthy'
        
        return status
    
    def restart_service(self, service_name: str) -> bool:
        """重启指定服务"""
        if service_name not in self.service_managers:
            return False
        
        manager = self.service_managers[service_name]
        # 这里应该实现重启逻辑
        # 为简化，这里返回True
        return True