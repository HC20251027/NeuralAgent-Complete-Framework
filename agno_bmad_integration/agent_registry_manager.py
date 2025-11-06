"""
代理注册管理接口 - 统一管理Agno和BMAD智能体的注册、发现和生命周期管理
Agent Registry Management Interface - Unified management of Agno and BMAD agent registration, discovery, and lifecycle
"""

import asyncio
import logging
import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Union, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
from collections import defaultdict, deque
import psutil
import weakref

from agno.agents.base_agent import BaseAgent
from agno.agents.coordinator import CoordinatorAgent
from agno.agents.specialist import SpecialistAgent

from bmad.roles.analyst import AnalystAgent
from bmad.roles.pm import PMAgent
from bmad.roles.architect import ArchitectAgent
from bmad.roles.dev import DeveloperAgent
from bmad.roles.qa import QAAgent


class AgentType(Enum):
    """智能体类型"""
    AGNO_COORDINATOR = "agno_coordinator"
    AGNO_SPECIALIST = "agno_specialist"
    BMAD_ANALYST = "bmad_analyst"
    BMAD_PROJECT_MANAGER = "bmad_project_manager"
    BMAD_ARCHITECT = "bmad_architect"
    BMAD_DEVELOPER = "bmad_developer"
    BMAD_QA = "bmad_qa"


class AgentStatus(Enum):
    """智能体状态"""
    REGISTERING = "registering"
    ACTIVE = "active"
    BUSY = "busy"
    IDLE = "idle"
    PAUSED = "paused"
    ERROR = "error"
    SHUTTING_DOWN = "shutting_down"
    OFFLINE = "offline"


class CapabilityType(Enum):
    """能力类型"""
    TASK_EXECUTION = "task_execution"
    COORDINATION = "coordination"
    ANALYSIS = "analysis"
    DEVELOPMENT = "development"
    TESTING = "testing"
    ARCHITECTURE = "architecture"
    PROJECT_MANAGEMENT = "project_management"
    COMMUNICATION = "communication"
    LEARNING = "learning"
    REASONING = "reasoning"


@dataclass
class AgentCapability:
    """智能体能力"""
    name: str
    type: CapabilityType
    level: float  # 0.0 - 1.0
    description: str
    dependencies: List[str] = None
    performance_metrics: Dict[str, float] = None
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []
        if self.performance_metrics is None:
            self.performance_metrics = {}


@dataclass
class AgentResource:
    """智能体资源"""
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    disk_usage: float = 0.0
    network_usage: float = 0.0
    active_connections: int = 0
    queued_tasks: int = 0
    processing_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    last_updated: datetime = None
    
    def __post_init__(self):
        if self.last_updated is None:
            self.last_updated = datetime.now()


@dataclass
class RegisteredAgent:
    """已注册智能体"""
    id: str
    name: str
    agent_type: AgentType
    status: AgentStatus
    capabilities: List[AgentCapability]
    configuration: Dict[str, Any]
    resource_requirements: Dict[str, Any]
    registration_time: datetime
    last_heartbeat: Optional[datetime] = None
    lifecycle_state: str = "initialized"
    metadata: Dict[str, Any] = None
    health_metrics: Dict[str, float] = None
    performance_history: List[Dict[str, Any]] = None
    current_tasks: List[str] = None
    resource_usage: AgentResource = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.health_metrics is None:
            self.health_metrics = {}
        if self.performance_history is None:
            self.performance_history = []
        if self.current_tasks is None:
            self.current_tasks = []
        if self.resource_usage is None:
            self.resource_usage = AgentResource()


@dataclass
class AgentDiscoveryQuery:
    """智能体发现查询"""
    query_id: str
    capabilities_required: List[CapabilityType]
    agent_types: List[AgentType]
    status_filter: List[AgentStatus]
    performance_threshold: float = 0.0
    resource_requirements: Dict[str, Any] = None
    max_results: int = 10
    timeout: int = 30
    
    def __post_init__(self):
        if self.resource_requirements is None:
            self.resource_requirements = {}


@dataclass
class AgentDiscoveryResult:
    """智能体发现结果"""
    query_id: str
    matched_agents: List[RegisteredAgent]
    search_time: float
    total_candidates: int
    match_score: Dict[str, float]  # agent_id -> score
    recommendations: List[str] = None
    
    def __post_init__(self):
        if self.recommendations is None:
            self.recommendations = []


@dataclass
class RegistryMetrics:
    """注册表指标"""
    total_registered_agents: int = 0
    active_agents: int = 0
    busy_agents: int = 0
    idle_agents: int = 0
    error_agents: int = 0
    average_response_time: float = 0.0
    total_tasks_processed: int = 0
    successful_tasks: int = 0
    failed_tasks: int = 0
    registry_health_score: float = 0.0
    last_updated: datetime = None
    
    def __post_init__(self):
        if self.last_updated is None:
            self.last_updated = datetime.now()


class AgentRegistryManager(BaseAgent):
    """代理注册管理接口 - 统一管理智能体注册、发现和生命周期"""
    
    def __init__(self, 
                 agent_id: str,
                 name: str = "Agent Registry Manager",
                 memory_manager: Optional[MemoryManager] = None,
                 config: Optional[Dict] = None):
        super().__init__(agent_id, name, memory_manager, config)
        
        # 注册表配置
        self.registry_config = {
            "heartbeat_interval": 30,  # 秒
            "health_check_interval": 60,  # 秒
            "cleanup_interval": 300,  # 5分钟
            "max_registry_size": 1000,
            "discovery_timeout": 30,
            "performance_history_size": 100
        }
        
        # 核心存储
        self.registered_agents: Dict[str, RegisteredAgent] = {}
        self.agent_instances: Dict[str, BaseAgent] = {}  # 智能体实例引用
        self.agent_index: Dict[CapabilityType, List[str]] = defaultdict(list)  # 能力索引
        self.agent_type_index: Dict[AgentType, List[str]] = defaultdict(list)  # 类型索引
        self.status_index: Dict[AgentStatus, List[str]] = defaultdict(list)  # 状态索引
        
        # 任务管理
        self.task_queue: Dict[str, List[str]] = defaultdict(list)  # agent_id -> task_ids
        self.active_tasks: Dict[str, Dict[str, Any]] = {}  # task_id -> task_info
        
        # 生命周期管理
        self.lifecycle_hooks: Dict[str, List[Callable]] = defaultdict(list)
        self.health_monitors: Dict[str, Callable] = {}
        
        # 性能监控
        self.performance_metrics: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self.resource_monitors: Dict[str, Any] = {}
        
        # 发现缓存
        self.discovery_cache: Dict[str, AgentDiscoveryResult] = {}
        self.cache_ttl = 300  # 5分钟
        
        # 指标统计
        self.registry_metrics = RegistryMetrics()
        
        # 后台服务
        self.background_services = []
        
        self.logger = logging.getLogger(__name__)
    
    async def register_agent(self, 
                           agent_config: Dict[str, Any]) -> Dict[str, Any]:
        """注册智能体"""
        try:
            self.logger.info(f"注册智能体: {agent_config.get('name', 'Unknown')}")
            
            # 1. 验证配置
            await self._validate_agent_config(agent_config)
            
            # 2. 创建智能体实例
            agent_instance = await self._create_agent_instance(agent_config)
            
            # 3. 创建注册记录
            agent_id = str(uuid.uuid4())
            registered_agent = RegisteredAgent(
                id=agent_id,
                name=agent_config["name"],
                agent_type=AgentType(agent_config["agent_type"]),
                status=AgentStatus.REGISTERING,
                capabilities=await self._parse_capabilities(agent_config.get("capabilities", [])),
                configuration=agent_config.get("configuration", {}),
                resource_requirements=agent_config.get("resource_requirements", {}),
                registration_time=datetime.now(),
                metadata=agent_config.get("metadata", {})
            )
            
            # 4. 更新索引
            await self._update_agent_indexes(registered_agent)
            
            # 5. 存储智能体和实例
            self.registered_agents[agent_id] = registered_agent
            self.agent_instances[agent_id] = agent_instance
            
            # 6. 执行注册后处理
            await self._post_registration_processing(registered_agent)
            
            # 7. 更新指标
            self.registry_metrics.total_registered_agents += 1
            self.registry_metrics.active_agents += 1
            
            # 保存到记忆
            await self.save_memory(f"agent_registration_{agent_id}", asdict(registered_agent))
            
            return {
                "status": "registered",
                "agent_id": agent_id,
                "agent_info": asdict(registered_agent),
                "registration_time": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"智能体注册失败: {str(e)}")
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def discover_agents(self, 
                            discovery_query: Dict[str, Any]) -> AgentDiscoveryResult:
        """发现智能体"""
        try:
            self.logger.info(f"发现智能体: {discovery_query}")
            
            # 1. 解析查询
            query = AgentDiscoveryQuery(
                query_id=str(uuid.uuid4()),
                capabilities_required=[CapabilityType(c) for c in discovery_query.get("capabilities_required", [])],
                agent_types=[AgentType(t) for t in discovery_query.get("agent_types", [])],
                status_filter=[AgentStatus(s) for s in discovery_query.get("status_filter", [AgentStatus.ACTIVE])],
                performance_threshold=discovery_query.get("performance_threshold", 0.0),
                resource_requirements=discovery_query.get("resource_requirements", {}),
                max_results=discovery_query.get("max_results", 10),
                timeout=discovery_query.get("timeout", 30)
            )
            
            # 2. 检查缓存
            cache_key = self._generate_cache_key(query)
            if cache_key in self.discovery_cache:
                cached_result = self.discovery_cache[cache_key]
                if (datetime.now() - cached_result.search_time).total_seconds() < self.cache_ttl:
                    return cached_result
            
            # 3. 执行发现
            start_time = datetime.now()
            matched_agents = await self._perform_agent_discovery(query)
            search_time = (datetime.now() - start_time).total_seconds()
            
            # 4. 计算匹配分数
            match_scores = await self._calculate_match_scores(matched_agents, query)
            
            # 5. 排序和限制结果
            sorted_agents = sorted(
                matched_agents,
                key=lambda agent: match_scores.get(agent.id, 0.0),
                reverse=True
            )[:query.max_results]
            
            # 6. 生成结果
            result = AgentDiscoveryResult(
                query_id=query.query_id,
                matched_agents=sorted_agents,
                search_time=search_time,
                total_candidates=len(matched_agents),
                match_score=match_scores,
                recommendations=await self._generate_discovery_recommendations(sorted_agents, query)
            )
            
            # 7. 缓存结果
            self.discovery_cache[cache_key] = result
            
            return result
            
        except Exception as e:
            self.logger.error(f"智能体发现失败: {str(e)}")
            raise
    
    async def assign_task_to_agent(self, 
                                 task_config: Dict[str, Any],
                                 agent_selection_strategy: str = "best_fit") -> Dict[str, Any]:
        """分配任务给智能体"""
        try:
            self.logger.info(f"分配任务: {task_config.get('name', 'Unknown')}")
            
            # 1. 验证任务配置
            await self._validate_task_config(task_config)
            
            # 2. 发现合适的智能体
            discovery_query = {
                "capabilities_required": task_config.get("required_capabilities", []),
                "agent_types": task_config.get("preferred_agent_types", []),
                "status_filter": [AgentStatus.ACTIVE.value, AgentStatus.IDLE.value],
                "performance_threshold": task_config.get("performance_threshold", 0.5),
                "resource_requirements": task_config.get("resource_requirements", {}),
                "max_results": 5
            }
            
            discovery_result = await self.discover_agents(discovery_query)
            
            if not discovery_result.matched_agents:
                return {
                    "status": "no_suitable_agent",
                    "error": "没有找到合适的智能体"
                }
            
            # 3. 根据策略选择智能体
            selected_agent = await self._select_agent_by_strategy(
                discovery_result.matched_agents, 
                discovery_result.match_score,
                agent_selection_strategy,
                task_config
            )
            
            # 4. 创建任务记录
            task_id = str(uuid.uuid4())
            task_info = {
                "id": task_id,
                "name": task_config["name"],
                "description": task_config.get("description", ""),
                "assigned_agent": selected_agent.id,
                "status": "assigned",
                "created_time": datetime.now(),
                "config": task_config,
                "priority": task_config.get("priority", "medium")
            }
            
            # 5. 更新智能体状态
            await self._update_agent_status(selected_agent.id, AgentStatus.BUSY)
            
            # 6. 存储任务信息
            self.active_tasks[task_id] = task_info
            self.task_queue[selected_agent.id].append(task_id)
            selected_agent.current_tasks.append(task_id)
            
            # 7. 启动任务执行监控
            asyncio.create_task(self._monitor_task_execution(task_id, selected_agent.id))
            
            # 8. 更新指标
            self.registry_metrics.total_tasks_processed += 1
            
            return {
                "status": "assigned",
                "task_id": task_id,
                "assigned_agent": {
                    "id": selected_agent.id,
                    "name": selected_agent.name,
                    "type": selected_agent.agent_type.value
                },
                "assignment_time": datetime.now().isoformat(),
                "estimated_completion": task_config.get("estimated_duration", 3600)
            }
            
        except Exception as e:
            self.logger.error(f"任务分配失败: {str(e)}")
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def update_agent_status(self, 
                                agent_id: str,
                                new_status: AgentStatus,
                                metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """更新智能体状态"""
        try:
            if agent_id not in self.registered_agents:
                raise ValueError(f"智能体 {agent_id} 未注册")
            
            agent = self.registered_agents[agent_id]
            old_status = agent.status
            
            # 更新状态
            agent.status = new_status
            agent.last_heartbeat = datetime.now()
            
            # 更新索引
            await self._update_status_index(agent_id, old_status, new_status)
            
            # 更新指标
            await self._update_status_metrics(old_status, new_status)
            
            # 执行状态变更钩子
            await self._execute_status_change_hooks(agent_id, old_status, new_status)
            
            # 记录状态变更
            if metadata:
                agent.metadata.update(metadata)
            
            return {
                "status": "updated",
                "agent_id": agent_id,
                "old_status": old_status.value,
                "new_status": new_status.value,
                "update_time": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"智能体状态更新失败: {str(e)}")
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def deregister_agent(self, agent_id: str, reason: str = "") -> Dict[str, Any]:
        """注销智能体"""
        try:
            if agent_id not in self.registered_agents:
                raise ValueError(f"智能体 {agent_id} 未注册")
            
            agent = self.registered_agents[agent_id]
            
            # 1. 检查是否有活跃任务
            active_task_count = len(agent.current_tasks)
            if active_task_count > 0:
                return {
                    "status": "cannot_deregister",
                    "reason": f"智能体仍有 {active_task_count} 个活跃任务",
                    "active_tasks": agent.current_tasks
                }
            
            # 2. 更新状态
            await self._update_agent_status(agent_id, AgentStatus.SHUTTING_DOWN)
            
            # 3. 执行注销前处理
            await self._pre_deregistration_processing(agent_id)
            
            # 4. 清理索引
            await self._remove_from_indexes(agent_id)
            
            # 5. 清理缓存
            await self._cleanup_agent_cache(agent_id)
            
            # 6. 关闭智能体实例
            agent_instance = self.agent_instances.get(agent_id)
            if agent_instance and hasattr(agent_instance, 'shutdown'):
                await agent_instance.shutdown()
            
            # 7. 更新指标
            self.registry_metrics.total_registered_agents -= 1
            if agent.status == AgentStatus.ACTIVE:
                self.registry_metrics.active_agents -= 1
            
            # 8. 移除记录
            del self.registered_agents[agent_id]
            if agent_id in self.agent_instances:
                del self.agent_instances[agent_id]
            
            # 保存注销记录
            await self.save_memory(f"agent_deregistration_{agent_id}", {
                "agent_id": agent_id,
                "deregistration_time": datetime.now().isoformat(),
                "reason": reason,
                "lifecycle_duration": (datetime.now() - agent.registration_time).total_seconds()
            })
            
            return {
                "status": "deregistered",
                "agent_id": agent_id,
                "deregistration_time": datetime.now().isoformat(),
                "reason": reason
            }
            
        except Exception as e:
            self.logger.error(f"智能体注销失败: {str(e)}")
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def get_registry_status(self) -> Dict[str, Any]:
        """获取注册表状态"""
        try:
            # 收集各类型智能体统计
            agent_type_stats = defaultdict(int)
            agent_status_stats = defaultdict(int)
            
            for agent in self.registered_agents.values():
                agent_type_stats[agent.agent_type.value] += 1
                agent_status_stats[agent.status.value] += 1
            
            # 计算健康度
            health_score = self._calculate_registry_health()
            
            # 获取性能统计
            performance_stats = await self._get_performance_statistics()
            
            # 获取资源使用统计
            resource_stats = await self._get_resource_statistics()
            
            return {
                "registry_id": self.agent_id,
                "status": "active",
                "health_score": health_score,
                "metrics": asdict(self.registry_metrics),
                "statistics": {
                    "total_agents": len(self.registered_agents),
                    "by_type": dict(agent_type_stats),
                    "by_status": dict(agent_status_stats),
                    "active_tasks": len(self.active_tasks),
                    "queued_tasks": sum(len(queue) for queue in self.task_queue.values())
                },
                "performance": performance_stats,
                "resources": resource_stats,
                "cache_stats": {
                    "discovery_cache_size": len(self.discovery_cache),
                    "cache_hit_rate": await self._calculate_cache_hit_rate()
                },
                "last_updated": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"获取注册表状态失败: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def get_agent_details(self, agent_id: str) -> Dict[str, Any]:
        """获取智能体详细信息"""
        try:
            if agent_id not in self.registered_agents:
                raise ValueError(f"智能体 {agent_id} 未注册")
            
            agent = self.registered_agents[agent_id]
            
            # 获取性能历史
            performance_history = self.performance_metrics.get(agent_id, [])
            
            # 获取当前任务详情
            current_task_details = []
            for task_id in agent.current_tasks:
                if task_id in self.active_tasks:
                    current_task_details.append(self.active_tasks[task_id])
            
            # 获取资源使用详情
            resource_details = asdict(agent.resource_usage)
            
            return {
                "agent_info": asdict(agent),
                "performance_history": performance_history[-10:],  # 最近10条记录
                "current_tasks": current_task_details,
                "resource_usage": resource_details,
                "health_status": await self._get_agent_health_status(agent_id),
                "capability_details": [asdict(cap) for cap in agent.capabilities],
                "last_heartbeat": agent.last_heartbeat.isoformat() if agent.last_heartbeat else None
            }
            
        except Exception as e:
            self.logger.error(f"获取智能体详情失败: {str(e)}")
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def start_background_services(self) -> None:
        """启动后台服务"""
        # 启动心跳监控服务
        asyncio.create_task(self._heartbeat_monitor_service())
        
        # 启动健康检查服务
        asyncio.create_task(self._health_check_service())
        
        # 启动清理服务
        asyncio.create_task(self._cleanup_service())
        
        # 启动性能监控服务
        asyncio.create_task(self._performance_monitoring_service())
        
        self.logger.info("后台服务已启动")
    
    # 私有方法实现
    
    async def _validate_agent_config(self, config: Dict[str, Any]) -> None:
        """验证智能体配置"""
        required_fields = ["name", "agent_type"]
        for field in required_fields:
            if field not in config:
                raise ValueError(f"缺少必需字段: {field}")
        
        # 验证智能体类型
        try:
            AgentType(config["agent_type"])
        except ValueError:
            raise ValueError(f"不支持的智能体类型: {config['agent_type']}")
    
    async def _create_agent_instance(self, config: Dict[str, Any]) -> BaseAgent:
        """创建智能体实例"""
        agent_type = AgentType(config["agent_type"])
        agent_id = config.get("id", str(uuid.uuid4()))
        
        if agent_type == AgentType.AGNO_COORDINATOR:
            return CoordinatorAgent(
                agent_id=agent_id,
                name=config["name"],
                memory_manager=self.memory_manager,
                config=config.get("configuration", {})
            )
        elif agent_type == AgentType.AGNO_SPECIALIST:
            return SpecialistAgent(
                agent_id=agent_id,
                name=config["name"],
                memory_manager=self.memory_manager,
                config=config.get("configuration", {})
            )
        elif agent_type == AgentType.BMAD_ANALYST:
            return AnalystAgent(
                agent_id=agent_id,
                name=config["name"],
                memory_manager=self.memory_manager,
                config=config.get("configuration", {})
            )
        elif agent_type == AgentType.BMAD_PROJECT_MANAGER:
            return PMAgent(
                agent_id=agent_id,
                name=config["name"],
                memory_manager=self.memory_manager,
                config=config.get("configuration", {})
            )
        elif agent_type == AgentType.BMAD_ARCHITECT:
            return ArchitectAgent(
                agent_id=agent_id,
                name=config["name"],
                memory_manager=self.memory_manager,
                config=config.get("configuration", {})
            )
        elif agent_type == AgentType.BMAD_DEVELOPER:
            return DeveloperAgent(
                agent_id=agent_id,
                name=config["name"],
                memory_manager=self.memory_manager,
                config=config.get("configuration", {})
            )
        elif agent_type == AgentType.BMAD_QA:
            return QAAgent(
                agent_id=agent_id,
                name=config["name"],
                memory_manager=self.memory_manager,
                config=config.get("configuration", {})
            )
        else:
            raise ValueError(f"未实现的智能体类型: {agent_type}")
    
    async def _parse_capabilities(self, capabilities_config: List[Dict[str, Any]]) -> List[AgentCapability]:
        """解析能力配置"""
        capabilities = []
        
        for cap_config in capabilities_config:
            capability = AgentCapability(
                name=cap_config["name"],
                type=CapabilityType(cap_config["type"]),
                level=cap_config.get("level", 1.0),
                description=cap_config.get("description", ""),
                dependencies=cap_config.get("dependencies", []),
                performance_metrics=cap_config.get("performance_metrics", {})
            )
            capabilities.append(capability)
        
        return capabilities
    
    async def _update_agent_indexes(self, agent: RegisteredAgent) -> None:
        """更新智能体索引"""
        # 能力索引
        for capability in agent.capabilities:
            self.agent_index[capability.type].append(agent.id)
        
        # 类型索引
        self.agent_type_index[agent.agent_type].append(agent.id)
        
        # 状态索引
        self.status_index[agent.status].append(agent.id)
    
    async def _remove_from_indexes(self, agent_id: str) -> None:
        """从索引中移除智能体"""
        agent = self.registered_agents.get(agent_id)
        if not agent:
            return
        
        # 从能力索引中移除
        for capability in agent.capabilities:
            if agent_id in self.agent_index[capability.type]:
                self.agent_index[capability.type].remove(agent_id)
        
        # 从类型索引中移除
        if agent_id in self.agent_type_index[agent.agent_type]:
            self.agent_type_index[agent.agent_type].remove(agent_id)
        
        # 从状态索引中移除
        if agent_id in self.status_index[agent.status]:
            self.status_index[agent.status].remove(agent_id)
    
    async def _post_registration_processing(self, agent: RegisteredAgent) -> None:
        """注册后处理"""
        # 初始化健康指标
        agent.health_metrics = {
            "availability": 1.0,
            "performance": 1.0,
            "reliability": 1.0,
            "responsiveness": 1.0
        }
        
        # 执行注册后钩子
        for hook in self.lifecycle_hooks.get("post_registration", []):
            try:
                await hook(agent)
            except Exception as e:
                self.logger.error(f"注册后处理钩子执行失败: {str(e)}")
    
    async def _perform_agent_discovery(self, query: AgentDiscoveryQuery) -> List[RegisteredAgent]:
        """执行智能体发现"""
        candidates = []
        
        # 根据能力过滤
        capability_candidates = set()
        for capability_type in query.capabilities_required:
            capability_candidates.update(self.agent_index.get(capability_type, []))
        
        # 根据类型过滤
        type_candidates = set()
        for agent_type in query.agent_types:
            type_candidates.update(self.agent_type_index.get(agent_type, []))
        
        # 根据状态过滤
        status_candidates = set()
        for status in query.status_filter:
            status_candidates.update(self.status_index.get(status, []))
        
        # 取交集
        if capability_candidates:
            candidates = list(capability_candidates)
        elif type_candidates:
            candidates = list(type_candidates)
        elif status_candidates:
            candidates = list(status_candidates)
        else:
            candidates = list(self.registered_agents.keys())
        
        # 过滤实际存在的智能体
        valid_candidates = []
        for agent_id in candidates:
            if agent_id in self.registered_agents:
                agent = self.registered_agents[agent_id]
                
                # 检查性能阈值
                if query.performance_threshold > 0:
                    agent_performance = agent.health_metrics.get("performance", 0.0)
                    if agent_performance < query.performance_threshold:
                        continue
                
                # 检查资源要求
                if query.resource_requirements:
                    if not await self._check_resource_requirements(agent, query.resource_requirements):
                        continue
                
                valid_candidates.append(agent)
        
        return valid_candidates
    
    async def _calculate_match_scores(self, agents: List[RegisteredAgent], query: AgentDiscoveryQuery) -> Dict[str, float]:
        """计算匹配分数"""
        scores = {}
        
        for agent in agents:
            score = 0.0
            
            # 能力匹配分数
            capability_score = 0.0
            for required_capability in query.capabilities_required:
                agent_capability = next(
                    (cap for cap in agent.capabilities if cap.type == required_capability),
                    None
                )
                if agent_capability:
                    capability_score += agent_capability.level
            
            if query.capabilities_required:
                capability_score /= len(query.capabilities_required)
            
            score += capability_score * 0.4
            
            # 类型匹配分数
            type_score = 0.0
            if query.agent_types and agent.agent_type in query.agent_types:
                type_score = 1.0
            score += type_score * 0.3
            
            # 状态分数
            status_score = 0.0
            if agent.status in [AgentStatus.ACTIVE, AgentStatus.IDLE]:
                status_score = 1.0
            elif agent.status == AgentStatus.BUSY:
                status_score = 0.5
            score += status_score * 0.2
            
            # 性能分数
            performance_score = agent.health_metrics.get("performance", 0.0)
            score += performance_score * 0.1
            
            scores[agent.id] = score
        
        return scores
    
    def _generate_cache_key(self, query: AgentDiscoveryQuery) -> str:
        """生成缓存键"""
        key_parts = [
            str(sorted(query.capabilities_required)),
            str(sorted(query.agent_types)),
            str(sorted(query.status_filter)),
            str(query.performance_threshold),
            str(query.max_results)
        ]
        return hashlib.md5("|".join(key_parts).encode()).hexdigest()
    
    async def _generate_discovery_recommendations(self, agents: List[RegisteredAgent], query: AgentDiscoveryQuery) -> List[str]:
        """生成发现建议"""
        recommendations = []
        
        if len(agents) == 0:
            recommendations.append("没有找到匹配的智能体，考虑放宽搜索条件")
        elif len(agents) < query.max_results:
            recommendations.append("匹配的智能体较少，考虑扩展搜索范围")
        
        # 检查能力覆盖
        covered_capabilities = set()
        for agent in agents:
            for capability in agent.capabilities:
                covered_capabilities.add(capability.type)
        
        missing_capabilities = set(query.capabilities_required) - covered_capabilities
        if missing_capabilities:
            recommendations.append(f"缺少能力: {', '.join([c.value for c in missing_capabilities])}")
        
        return recommendations
    
    async def _select_agent_by_strategy(self, 
                                      agents: List[RegisteredAgent], 
                                      scores: Dict[str, float],
                                      strategy: str, 
                                      task_config: Dict[str, Any]) -> RegisteredAgent:
        """根据策略选择智能体"""
        if strategy == "best_fit":
            # 选择分数最高的智能体
            best_agent = max(agents, key=lambda agent: scores.get(agent.id, 0.0))
        elif strategy == "load_balancing":
            # 选择负载最低的智能体
            best_agent = min(agents, key=lambda agent: agent.resource_usage.processing_tasks)
        elif strategy == "random":
            # 随机选择
            import random
            best_agent = random.choice(agents)
        else:
            # 默认选择分数最高的
            best_agent = max(agents, key=lambda agent: scores.get(agent.id, 0.0))
        
        return best_agent
    
    async def _validate_task_config(self, config: Dict[str, Any]) -> None:
        """验证任务配置"""
        required_fields = ["name"]
        for field in required_fields:
            if field not in config:
                raise ValueError(f"缺少必需字段: {field}")
    
    async def _monitor_task_execution(self, task_id: str, agent_id: str) -> None:
        """监控任务执行"""
        try:
            # 模拟任务执行监控
            task_info = self.active_tasks.get(task_id)
            if not task_info:
                return
            
            # 更新任务状态为执行中
            task_info["status"] = "running"
            task_info["start_time"] = datetime.now()
            
            # 模拟执行时间
            await asyncio.sleep(5)  # 模拟5秒执行时间
            
            # 完成任务
            task_info["status"] = "completed"
            task_info["completion_time"] = datetime.now()
            
            # 更新智能体状态
            await self._update_agent_status(agent_id, AgentStatus.IDLE)
            
            # 更新指标
            self.registry_metrics.successful_tasks += 1
            
            # 清理任务
            if task_id in self.active_tasks:
                del self.active_tasks[task_id]
            
            # 从智能体当前任务中移除
            if agent_id in self.registered_agents:
                agent = self.registered_agents[agent_id]
                if task_id in agent.current_tasks:
                    agent.current_tasks.remove(task_id)
            
        except Exception as e:
            self.logger.error(f"任务监控失败: {str(e)}")
            
            # 标记任务失败
            if task_id in self.active_tasks:
                self.active_tasks[task_id]["status"] = "failed"
                self.active_tasks[task_id]["error"] = str(e)
            
            # 更新智能体状态
            await self._update_agent_status(agent_id, AgentStatus.IDLE)
            
            # 更新指标
            self.registry_metrics.failed_tasks += 1
    
    async def _update_status_index(self, agent_id: str, old_status: AgentStatus, new_status: AgentStatus) -> None:
        """更新状态索引"""
        # 从旧状态索引中移除
        if agent_id in self.status_index[old_status]:
            self.status_index[old_status].remove(agent_id)
        
        # 添加到新状态索引
        self.status_index[new_status].append(agent_id)
    
    async def _update_status_metrics(self, old_status: AgentStatus, new_status: AgentStatus) -> None:
        """更新状态指标"""
        # 更新各种状态计数
        if old_status == AgentStatus.ACTIVE:
            self.registry_metrics.active_agents -= 1
        elif old_status == AgentStatus.BUSY:
            self.registry_metrics.busy_agents -= 1
        elif old_status == AgentStatus.IDLE:
            self.registry_metrics.idle_agents -= 1
        elif old_status == AgentStatus.ERROR:
            self.registry_metrics.error_agents -= 1
        
        if new_status == AgentStatus.ACTIVE:
            self.registry_metrics.active_agents += 1
        elif new_status == AgentStatus.BUSY:
            self.registry_metrics.busy_agents += 1
        elif new_status == AgentStatus.IDLE:
            self.registry_metrics.idle_agents += 1
        elif new_status == AgentStatus.ERROR:
            self.registry_metrics.error_agents += 1
    
    async def _execute_status_change_hooks(self, agent_id: str, old_status: AgentStatus, new_status: AgentStatus) -> None:
        """执行状态变更钩子"""
        hooks = self.lifecycle_hooks.get("status_change", [])
        for hook in hooks:
            try:
                await hook(agent_id, old_status, new_status)
            except Exception as e:
                self.logger.error(f"状态变更钩子执行失败: {str(e)}")
    
    async def _pre_deregistration_processing(self, agent_id: str) -> None:
        """注销前处理"""
        hooks = self.lifecycle_hooks.get("pre_deregistration", [])
        for hook in hooks:
            try:
                await hook(agent_id)
            except Exception as e:
                self.logger.error(f"注销前处理钩子执行失败: {str(e)}")
    
    async def _cleanup_agent_cache(self, agent_id: str) -> None:
        """清理智能体缓存"""
        # 清理发现缓存中包含该智能体的条目
        keys_to_remove = []
        for cache_key, result in self.discovery_cache.items():
            if any(agent.id == agent_id for agent in result.matched_agents):
                keys_to_remove.append(cache_key)
        
        for key in keys_to_remove:
            del self.discovery_cache[key]
    
    def _calculate_registry_health(self) -> float:
        """计算注册表健康度"""
        if self.registry_metrics.total_registered_agents == 0:
            return 0.0
        
        # 基于错误率和响应时间计算健康度
        error_rate = self.registry_metrics.failed_tasks / max(self.registry_metrics.total_tasks_processed, 1)
        health_score = (1.0 - error_rate) * 100
        
        return min(100.0, health_score)
    
    async def _get_performance_statistics(self) -> Dict[str, Any]:
        """获取性能统计"""
        return {
            "average_response_time": self.registry_metrics.average_response_time,
            "task_success_rate": (self.registry_metrics.successful_tasks / max(self.registry_metrics.total_tasks_processed, 1)) * 100,
            "throughput": self.registry_metrics.total_tasks_processed / 3600  # 每小时任务数
        }
    
    async def _get_resource_statistics(self) -> Dict[str, Any]:
        """获取资源统计"""
        total_cpu = sum(agent.resource_usage.cpu_usage for agent in self.registered_agents.values())
        total_memory = sum(agent.resource_usage.memory_usage for agent in self.registered_agents.values())
        
        return {
            "total_cpu_usage": total_cpu,
            "total_memory_usage": total_memory,
            "average_cpu_per_agent": total_cpu / max(len(self.registered_agents), 1),
            "average_memory_per_agent": total_memory / max(len(self.registered_agents), 1)
        }
    
    async def _calculate_cache_hit_rate(self) -> float:
        """计算缓存命中率"""
        # 简化实现，返回模拟值
        return 75.0
    
    async def _check_resource_requirements(self, agent: RegisteredAgent, requirements: Dict[str, Any]) -> bool:
        """检查资源要求"""
        # 简化实现
        return True
    
    async def _get_agent_health_status(self, agent_id: str) -> Dict[str, Any]:
        """获取智能体健康状态"""
        agent = self.registered_agents.get(agent_id)
        if not agent:
            return {"status": "not_found"}
        
        # 计算健康度
        health_score = sum(agent.health_metrics.values()) / len(agent.health_metrics)
        
        return {
            "overall_health": health_score,
            "last_heartbeat": agent.last_heartbeat.isoformat() if agent.last_heartbeat else None,
            "uptime": (datetime.now() - agent.registration_time).total_seconds(),
            "status": agent.status.value
        }
    
    # 后台服务方法
    
    async def _heartbeat_monitor_service(self) -> None:
        """心跳监控服务"""
        while True:
            try:
                current_time = datetime.now()
                timeout_threshold = current_time - timedelta(seconds=self.registry_config["heartbeat_interval"] * 2)
                
                # 检查心跳超时的智能体
                for agent_id, agent in self.registered_agents.items():
                    if agent.last_heartbeat and agent.last_heartbeat < timeout_threshold:
                        if agent.status == AgentStatus.ACTIVE:
                            await self._update_agent_status(agent_id, AgentStatus.OFFLINE)
                
                await asyncio.sleep(self.registry_config["heartbeat_interval"])
                
            except Exception as e:
                self.logger.error(f"心跳监控服务错误: {str(e)}")
                await asyncio.sleep(60)
    
    async def _health_check_service(self) -> None:
        """健康检查服务"""
        while True:
            try:
                for agent_id, agent in self.registered_agents.items():
                    # 执行健康检查
                    health_status = await self._perform_health_check(agent)
                    
                    # 更新健康指标
                    agent.health_metrics.update(health_status)
                    
                    # 检查是否需要状态变更
                    if health_status.get("availability", 1.0) < 0.5 and agent.status == AgentStatus.ACTIVE:
                        await self._update_agent_status(agent_id, AgentStatus.ERROR)
                
                await asyncio.sleep(self.registry_config["health_check_interval"])
                
            except Exception as e:
                self.logger.error(f"健康检查服务错误: {str(e)}")
                await asyncio.sleep(60)
    
    async def _perform_health_check(self, agent: RegisteredAgent) -> Dict[str, float]:
        """执行健康检查"""
        # 简化实现，返回模拟健康指标
        return {
            "availability": 0.95,
            "performance": 0.90,
            "reliability": 0.88,
            "responsiveness": 0.92
        }
    
    async def _cleanup_service(self) -> None:
        """清理服务"""
        while True:
            try:
                # 清理过期的发现缓存
                current_time = datetime.now()
                expired_cache_keys = [
                    key for key, result in self.discovery_cache.items()
                    if (current_time - result.search_time).total_seconds() > self.cache_ttl
                ]
                
                for key in expired_cache_keys:
                    del self.discovery_cache[key]
                
                # 清理过期的性能历史
                for agent_id, history in self.performance_metrics.items():
                    if len(history) > self.registry_config["performance_history_size"]:
                        self.performance_metrics[agent_id] = history[-self.registry_config["performance_history_size"]:]
                
                await asyncio.sleep(self.registry_config["cleanup_interval"])
                
            except Exception as e:
                self.logger.error(f"清理服务错误: {str(e)}")
                await asyncio.sleep(300)
    
    async def _performance_monitoring_service(self) -> None:
        """性能监控服务"""
        while True:
            try:
                # 收集性能指标
                for agent_id, agent in self.registered_agents.items():
                    performance_data = {
                        "timestamp": datetime.now().isoformat(),
                        "cpu_usage": agent.resource_usage.cpu_usage,
                        "memory_usage": agent.resource_usage.memory_usage,
                        "task_queue_size": len(self.task_queue.get(agent_id, [])),
                        "active_tasks": agent.resource_usage.processing_tasks
                    }
                    
                    self.performance_metrics[agent_id].append(performance_data)
                
                await asyncio.sleep(30)  # 每30秒收集一次
                
            except Exception as e:
                self.logger.error(f"性能监控服务错误: {str(e)}")
                await asyncio.sleep(60)