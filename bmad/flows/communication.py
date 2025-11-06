"""
代理间通信接口 - 支持BMAD框架中不同角色智能体之间的协作和任务传递
Agent Communication Interface - Supports collaboration and task passing between different role agents in BMAD framework
"""

import asyncio
import logging
import json
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import asyncio
import aiohttp
from collections import defaultdict, deque
import weakref

from agno.agents.base_agent import BaseAgent
from agno.memory.memory_manager import MemoryManager


class MessageType(Enum):
    """消息类型"""
    TASK_ASSIGNMENT = "task_assignment"
    TASK_UPDATE = "task_update"
    TASK_COMPLETION = "task_completion"
    REQUEST_FOR_INFORMATION = "request_for_information"
    COLLABORATION_REQUEST = "collaboration_request"
    STATUS_UPDATE = "status_update"
    ERROR_NOTIFICATION = "error_notification"
    APPROVAL_REQUEST = "approval_request"
    FEEDBACK = "feedback"
    NOTIFICATION = "notification"


class MessagePriority(Enum):
    """消息优先级"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class CommunicationStatus(Enum):
    """通信状态"""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    PROCESSED = "processed"
    FAILED = "failed"


class AgentRole(Enum):
    """智能体角色"""
    ANALYST = "analyst"
    PM = "project_manager"
    ARCHITECT = "architect"
    DEVELOPER = "developer"
    QA = "qa"
    COORDINATOR = "coordinator"


@dataclass
class Message:
    """消息"""
    id: str
    sender_id: str
    receiver_id: str
    message_type: MessageType
    priority: MessagePriority
    subject: str
    content: Dict[str, Any]
    timestamp: datetime
    status: CommunicationStatus
    requires_response: bool = False
    response_deadline: Optional[datetime] = None
    attachments: List[str] = None
    correlation_id: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.attachments is None:
            self.attachments = []
        if self.metadata is None:
            self.metadata = {}


@dataclass
class TaskHandoff:
    """任务交接"""
    id: str
    task_id: str
    from_agent: str
    to_agent: str
    handoff_type: str  # "assignment", "escalation", "collaboration"
    context: Dict[str, Any]
    requirements: Dict[str, Any]
    handover_notes: str
    timestamp: datetime
    status: str  # "pending", "accepted", "rejected", "completed"
    acceptance_criteria: List[str] = None
    dependencies: List[str] = None
    
    def __post_init__(self):
        if self.acceptance_criteria is None:
            self.acceptance_criteria = []
        if self.dependencies is None:
            self.dependencies = []


@dataclass
class CollaborationSession:
    """协作会话"""
    id: str
    session_type: str  # "pair_programming", "code_review", "design_review", "planning"
    participants: List[str]
    initiator: str
    topic: str
    start_time: datetime
    end_time: Optional[datetime] = None
    status: str = "active"  # "active", "paused", "completed", "cancelled"
    agenda: List[str] = None
    decisions: List[Dict[str, Any]] = None
    action_items: List[Dict[str, Any]] = None
    notes: str = ""
    
    def __post_init__(self):
        if self.agenda is None:
            self.agenda = []
        if self.decisions is None:
            self.decisions = []
        if self.action_items is None:
            self.action_items = []


@dataclass
class CommunicationMetrics:
    """通信指标"""
    agent_id: str
    messages_sent: int = 0
    messages_received: int = 0
    average_response_time: float = 0.0
    collaboration_sessions: int = 0
    task_handoffs: int = 0
    success_rate: float = 0.0
    last_updated: datetime = None
    
    def __post_init__(self):
        if self.last_updated is None:
            self.last_updated = datetime.now()


class AgentCommunicationInterface(BaseAgent):
    """代理间通信接口 - 负责智能体间的消息传递和协作协调"""
    
    def __init__(self, 
                 agent_id: str,
                 name: str = "Agent Communication Interface",
                 memory_manager: Optional[MemoryManager] = None,
                 config: Optional[Dict] = None):
        super().__init__(agent_id, name, memory_manager, config)
        
        # 通信配置
        self.max_retries = 3
        self.message_timeout = 300  # 5分钟
        self.max_concurrent_sessions = 10
        
        # 消息队列
        self.message_queue = deque()
        self.pending_messages: Dict[str, Message] = {}
        self.message_history: List[Message] = []
        
        # 任务交接管理
        self.task_handoffs: Dict[str, TaskHandoff] = {}
        self.active_handoffs: Dict[str, TaskHandoff] = {}
        
        # 协作会话管理
        self.collaboration_sessions: Dict[str, CollaborationSession] = {}
        self.active_sessions: Dict[str, CollaborationSession] = {}
        
        # 智能体注册表
        self.registered_agents: Dict[str, Dict[str, Any]] = {}
        
        # 通信指标
        self.communication_metrics: Dict[str, CommunicationMetrics] = {}
        
        # 消息处理器
        self.message_handlers: Dict[MessageType, Callable] = {}
        
        # 角色协作规则
        self.collaboration_rules = {
            (AgentRole.ANALYST, AgentRole.PM): {
                "handoff_types": ["requirements_handoff", "stakeholder_feedback"],
                "communication_frequency": "daily",
                "escalation_triggers": ["requirements_change", "scope_modification"]
            },
            (AgentRole.PM, AgentRole.ARCHITECT): {
                "handoff_types": ["feature_specification", "technical_constraints"],
                "communication_frequency": "as_needed",
                "escalation_triggers": ["technical_blocker", "architecture_decision"]
            },
            (AgentRole.ARCHITECT, AgentRole.DEVELOPER): {
                "handoff_types": ["design_specification", "technical_requirements"],
                "communication_frequency": "weekly",
                "escalation_triggers": ["implementation_blocker", "design_clarification"]
            },
            (AgentRole.DEVELOPER, AgentRole.QA): {
                "handoff_types": ["code_handoff", "test_requirements"],
                "communication_frequency": "daily",
                "escalation_triggers": ["quality_issue", "test_blocker"]
            }
        }
        
        self.logger = logging.getLogger(__name__)
    
    async def register_agent(self, 
                           agent_id: str,
                           agent_role: AgentRole,
                           capabilities: List[str],
                           availability: Dict[str, Any]) -> Dict[str, Any]:
        """注册智能体"""
        try:
            self.logger.info(f"注册智能体: {agent_id} ({agent_role.value})")
            
            # 验证智能体信息
            await self._validate_agent_registration(agent_id, agent_role, capabilities, availability)
            
            # 注册智能体
            self.registered_agents[agent_id] = {
                "id": agent_id,
                "role": agent_role,
                "capabilities": capabilities,
                "availability": availability,
                "status": "active",
                "registered_date": datetime.now(),
                "last_seen": datetime.now()
            }
            
            # 初始化通信指标
            if agent_id not in self.communication_metrics:
                self.communication_metrics[agent_id] = CommunicationMetrics(agent_id=agent_id)
            
            # 保存到记忆
            await self.save_memory(f"agent_registration_{agent_id}", self.registered_agents[agent_id])
            
            return {
                "status": "success",
                "agent_id": agent_id,
                "role": agent_role.value,
                "registration_date": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"智能体注册失败: {str(e)}")
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def send_message(self, 
                         sender_id: str,
                         receiver_id: str,
                         message_type: MessageType,
                         subject: str,
                         content: Dict[str, Any],
                         priority: MessagePriority = MessagePriority.MEDIUM,
                         requires_response: bool = False,
                         response_deadline: Optional[datetime] = None) -> str:
        """发送消息"""
        try:
            # 验证发送者和接收者
            if sender_id not in self.registered_agents:
                raise ValueError(f"发送者 {sender_id} 未注册")
            if receiver_id not in self.registered_agents:
                raise ValueError(f"接收者 {receiver_id} 未注册")
            
            # 创建消息
            message_id = str(uuid.uuid4())
            message = Message(
                id=message_id,
                sender_id=sender_id,
                receiver_id=receiver_id,
                message_type=message_type,
                priority=priority,
                subject=subject,
                content=content,
                timestamp=datetime.now(),
                status=CommunicationStatus.PENDING,
                requires_response=requires_response,
                response_deadline=response_deadline
            )
            
            # 添加到队列
            self.message_queue.append(message)
            self.pending_messages[message_id] = message
            
            # 更新发送者指标
            if sender_id in self.communication_metrics:
                self.communication_metrics[sender_id].messages_sent += 1
                self.communication_metrics[sender_id].last_updated = datetime.now()
            
            # 异步处理消息
            asyncio.create_task(self._process_message(message))
            
            self.logger.info(f"消息已发送: {message_id} 从 {sender_id} 到 {receiver_id}")
            
            return message_id
            
        except Exception as e:
            self.logger.error(f"消息发送失败: {str(e)}")
            raise
    
    async def initiate_task_handoff(self, 
                                  task_id: str,
                                  from_agent: str,
                                  to_agent: str,
                                  handoff_type: str,
                                  context: Dict[str, Any],
                                  requirements: Dict[str, Any]) -> str:
        """启动任务交接"""
        try:
            self.logger.info(f"启动任务交接: {task_id} 从 {from_agent} 到 {to_agent}")
            
            # 验证智能体
            if from_agent not in self.registered_agents or to_agent not in self.registered_agents:
                raise ValueError("智能体未注册")
            
            # 创建交接记录
            handoff_id = str(uuid.uuid4())
            handoff = TaskHandoff(
                id=handoff_id,
                task_id=task_id,
                from_agent=from_agent,
                to_agent=to_agent,
                handoff_type=handoff_type,
                context=context,
                requirements=requirements,
                handover_notes=context.get("handover_notes", ""),
                timestamp=datetime.now(),
                status="pending"
            )
            
            # 保存交接记录
            self.task_handoffs[handoff_id] = handoff
            self.active_handoffs[handoff_id] = handoff
            
            # 发送交接通知消息
            await self.send_message(
                sender_id=from_agent,
                receiver_id=to_agent,
                message_type=MessageType.TASK_ASSIGNMENT,
                subject=f"任务交接: {task_id}",
                content={
                    "handoff_id": handoff_id,
                    "task_id": task_id,
                    "handoff_type": handoff_type,
                    "context": context,
                    "requirements": requirements,
                    "handover_notes": handoff.handover_notes
                },
                priority=MessagePriority.HIGH
            )
            
            # 更新指标
            if from_agent in self.communication_metrics:
                self.communication_metrics[from_agent].task_handoffs += 1
            
            return handoff_id
            
        except Exception as e:
            self.logger.error(f"任务交接启动失败: {str(e)}")
            raise
    
    async def accept_task_handoff(self, 
                                handoff_id: str,
                                acceptance_notes: str = "") -> Dict[str, Any]:
        """接受任务交接"""
        try:
            handoff = self.task_handoffs.get(handoff_id)
            if not handoff:
                raise ValueError(f"交接记录 {handoff_id} 不存在")
            
            # 更新交接状态
            handoff.status = "accepted"
            
            # 发送接受确认
            await self.send_message(
                sender_id=handoff.to_agent,
                receiver_id=handoff.from_agent,
                message_type=MessageType.TASK_UPDATE,
                subject=f"任务交接已接受: {handoff.task_id}",
                content={
                    "handoff_id": handoff_id,
                    "task_id": handoff.task_id,
                    "acceptance_notes": acceptance_notes,
                    "accepted_at": datetime.now().isoformat()
                }
            )
            
            # 从活跃交接中移除
            if handoff_id in self.active_handoffs:
                del self.active_handoffs[handoff_id]
            
            return {
                "status": "accepted",
                "handoff_id": handoff_id,
                "accepted_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"任务交接接受失败: {str(e)}")
            raise
    
    async def reject_task_handoff(self, 
                                handoff_id: str,
                                rejection_reason: str) -> Dict[str, Any]:
        """拒绝任务交接"""
        try:
            handoff = self.task_handoffs.get(handoff_id)
            if not handoff:
                raise ValueError(f"交接记录 {handoff_id} 不存在")
            
            # 更新交接状态
            handoff.status = "rejected"
            
            # 发送拒绝通知
            await self.send_message(
                sender_id=handoff.to_agent,
                receiver_id=handoff.from_agent,
                message_type=MessageType.ERROR_NOTIFICATION,
                subject=f"任务交接被拒绝: {handoff.task_id}",
                content={
                    "handoff_id": handoff_id,
                    "task_id": handoff.task_id,
                    "rejection_reason": rejection_reason,
                    "rejected_at": datetime.now().isoformat()
                }
            )
            
            # 从活跃交接中移除
            if handoff_id in self.active_handoffs:
                del self.active_handoffs[handoff_id]
            
            return {
                "status": "rejected",
                "handoff_id": handoff_id,
                "rejection_reason": rejection_reason,
                "rejected_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"任务交接拒绝失败: {str(e)}")
            raise
    
    async def start_collaboration_session(self, 
                                        session_type: str,
                                        participants: List[str],
                                        initiator: str,
                                        topic: str,
                                        agenda: List[str]) -> str:
        """启动协作会话"""
        try:
            # 验证参与者
            for participant in participants:
                if participant not in self.registered_agents:
                    raise ValueError(f"参与者 {participant} 未注册")
            
            # 检查并发限制
            if len(self.active_sessions) >= self.max_concurrent_sessions:
                raise ValueError("达到最大并发会话限制")
            
            # 创建协作会话
            session_id = str(uuid.uuid4())
            session = CollaborationSession(
                id=session_id,
                session_type=session_type,
                participants=participants,
                initiator=initiator,
                topic=topic,
                start_time=datetime.now(),
                agenda=agenda
            )
            
            # 保存会话
            self.collaboration_sessions[session_id] = session
            self.active_sessions[session_id] = session
            
            # 发送会话邀请
            for participant in participants:
                if participant != initiator:
                    await self.send_message(
                        sender_id=initiator,
                        receiver_id=participant,
                        message_type=MessageType.COLLABORATION_REQUEST,
                        subject=f"协作会话邀请: {topic}",
                        content={
                            "session_id": session_id,
                            "session_type": session_type,
                            "topic": topic,
                            "agenda": agenda,
                            "initiator": initiator,
                            "start_time": session.start_time.isoformat()
                        },
                        priority=MessagePriority.HIGH
                    )
            
            # 更新指标
            if initiator in self.communication_metrics:
                self.communication_metrics[initiator].collaboration_sessions += 1
            
            return session_id
            
        except Exception as e:
            self.logger.error(f"协作会话启动失败: {str(e)}")
            raise
    
    async def join_collaboration_session(self, 
                                       session_id: str,
                                       agent_id: str,
                                       response: str) -> Dict[str, Any]:
        """加入协作会话"""
        try:
            session = self.collaboration_sessions.get(session_id)
            if not session:
                raise ValueError(f"协作会话 {session_id} 不存在")
            
            if agent_id not in session.participants:
                session.participants.append(agent_id)
            
            # 发送加入确认
            await self.send_message(
                sender_id=agent_id,
                receiver_id=session.initiator,
                message_type=MessageType.STATUS_UPDATE,
                subject=f"加入协作会话: {session.topic}",
                content={
                    "session_id": session_id,
                    "agent_id": agent_id,
                    "response": response,
                    "joined_at": datetime.now().isoformat()
                }
            )
            
            return {
                "status": "joined",
                "session_id": session_id,
                "agent_id": agent_id,
                "joined_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"加入协作会话失败: {str(e)}")
            raise
    
    async def end_collaboration_session(self, 
                                      session_id: str,
                                      summary: str,
                                      decisions: List[Dict[str, Any]],
                                      action_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """结束协作会话"""
        try:
            session = self.collaboration_sessions.get(session_id)
            if not session:
                raise ValueError(f"协作会话 {session_id} 不存在")
            
            # 更新会话信息
            session.status = "completed"
            session.end_time = datetime.now()
            session.notes = summary
            session.decisions = decisions
            session.action_items = action_items
            
            # 发送会话结束通知
            for participant in session.participants:
                await self.send_message(
                    sender_id=session.initiator,
                    receiver_id=participant,
                    message_type=MessageType.NOTIFICATION,
                    subject=f"协作会话结束: {session.topic}",
                    content={
                        "session_id": session_id,
                        "summary": summary,
                        "decisions": decisions,
                        "action_items": action_items,
                        "ended_at": session.end_time.isoformat()
                    }
                )
            
            # 从活跃会话中移除
            if session_id in self.active_sessions:
                del self.active_sessions[session_id]
            
            return {
                "status": "completed",
                "session_id": session_id,
                "duration": (session.end_time - session.start_time).total_seconds() / 60,  # 分钟
                "participants": session.participants,
                "decisions_count": len(decisions),
                "action_items_count": len(action_items)
            }
            
        except Exception as e:
            self.logger.error(f"协作会话结束失败: {str(e)}")
            raise
    
    async def get_communication_status(self, agent_id: str) -> Dict[str, Any]:
        """获取通信状态"""
        try:
            if agent_id not in self.registered_agents:
                raise ValueError(f"智能体 {agent_id} 未注册")
            
            # 获取相关消息
            sent_messages = [msg for msg in self.message_history if msg.sender_id == agent_id]
            received_messages = [msg for msg in self.message_history if msg.receiver_id == agent_id]
            
            # 获取活跃交接
            active_handoffs = [h for h in self.active_handoffs.values() 
                             if h.from_agent == agent_id or h.to_agent == agent_id]
            
            # 获取活跃会话
            active_sessions = [s for s in self.active_sessions.values() 
                             if agent_id in s.participants]
            
            # 获取指标
            metrics = self.communication_metrics.get(agent_id, CommunicationMetrics(agent_id=agent_id))
            
            return {
                "agent_id": agent_id,
                "registration_info": self.registered_agents[agent_id],
                "communication_metrics": asdict(metrics),
                "message_summary": {
                    "sent_today": len([msg for msg in sent_messages 
                                     if msg.timestamp.date() == datetime.now().date()]),
                    "received_today": len([msg for msg in received_messages 
                                         if msg.timestamp.date() == datetime.now().date()]),
                    "pending_responses": len([msg for msg in received_messages 
                                            if msg.requires_response and msg.status != CommunicationStatus.PROCESSED])
                },
                "active_handoffs": len(active_handoffs),
                "active_sessions": len(active_sessions),
                "status": "active"
            }
            
        except Exception as e:
            self.logger.error(f"获取通信状态失败: {str(e)}")
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def get_collaboration_analytics(self, time_range: Dict[str, Any]) -> Dict[str, Any]:
        """获取协作分析数据"""
        try:
            start_date = datetime.fromisoformat(time_range["start"])
            end_date = datetime.fromisoformat(time_range["end"])
            
            # 收集数据
            messages_in_range = [msg for msg in self.message_history 
                               if start_date <= msg.timestamp <= end_date]
            
            handoffs_in_range = [h for h in self.task_handoffs.values() 
                               if start_date <= h.timestamp <= end_date]
            
            sessions_in_range = [s for s in self.collaboration_sessions.values() 
                               if start_date <= s.start_time <= end_date]
            
            # 计算指标
            total_messages = len(messages_in_range)
            total_handoffs = len(handoffs_in_range)
            total_sessions = len(sessions_in_range)
            
            # 消息类型分布
            message_type_distribution = defaultdict(int)
            for msg in messages_in_range:
                message_type_distribution[msg.message_type.value] += 1
            
            # 角色间通信频率
            role_communication = defaultdict(int)
            for msg in messages_in_range:
                sender_role = self.registered_agents[msg.sender_id]["role"]
                receiver_role = self.registered_agents[msg.receiver_id]["role"]
                role_pair = f"{sender_role.value} -> {receiver_role.value}"
                role_communication[role_pair] += 1
            
            # 平均响应时间
            response_times = []
            for msg in messages_in_range:
                if msg.requires_response:
                    # 这里应该计算实际响应时间，简化处理
                    response_times.append(30)  # 模拟30分钟响应时间
            
            avg_response_time = sum(response_times) / len(response_times) if response_times else 0
            
            return {
                "time_range": time_range,
                "summary": {
                    "total_messages": total_messages,
                    "total_handoffs": total_handoffs,
                    "total_sessions": total_sessions,
                    "average_response_time": avg_response_time
                },
                "message_distribution": dict(message_type_distribution),
                "role_communication": dict(role_communication),
                "collaboration_patterns": await self._analyze_collaboration_patterns(sessions_in_range),
                "bottlenecks": await self._identify_communication_bottlenecks(messages_in_range),
                "recommendations": await self._generate_collaboration_recommendations(
                    total_messages, total_handoffs, total_sessions, avg_response_time
                )
            }
            
        except Exception as e:
            self.logger.error(f"协作分析失败: {str(e)}")
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    # 私有方法实现
    
    async def _validate_agent_registration(self, agent_id: str, role: AgentRole, 
                                         capabilities: List[str], availability: Dict[str, Any]) -> None:
        """验证智能体注册信息"""
        if not agent_id:
            raise ValueError("智能体ID不能为空")
        
        if not capabilities:
            raise ValueError("智能体必须具备至少一项能力")
        
        if not availability.get("working_hours"):
            raise ValueError("必须指定工作时间")
    
    async def _process_message(self, message: Message) -> None:
        """处理消息"""
        try:
            # 模拟消息处理
            await asyncio.sleep(0.1)  # 模拟处理时间
            
            # 更新消息状态
            message.status = CommunicationStatus.DELIVERED
            
            # 更新接收者指标
            if message.receiver_id in self.communication_metrics:
                self.communication_metrics[message.receiver_id].messages_received += 1
                self.communication_metrics[message.receiver_id].last_updated = datetime.now()
            
            # 移动到历史记录
            self.message_history.append(message)
            if message.id in self.pending_messages:
                del self.pending_messages[message.id]
            
            self.logger.info(f"消息处理完成: {message.id}")
            
        except Exception as e:
            self.logger.error(f"消息处理失败: {message.id}, 错误: {str(e)}")
            message.status = CommunicationStatus.FAILED
    
    async def _analyze_collaboration_patterns(self, sessions: List[CollaborationSession]) -> Dict[str, Any]:
        """分析协作模式"""
        if not sessions:
            return {}
        
        # 会话类型分布
        session_types = defaultdict(int)
        for session in sessions:
            session_types[session.session_type] += 1
        
        # 平均会话时长
        durations = []
        for session in sessions:
            if session.end_time:
                duration = (session.end_time - session.start_time).total_seconds() / 60
                durations.append(duration)
        
        avg_duration = sum(durations) / len(durations) if durations else 0
        
        # 参与度分析
        participation_rates = []
        for session in sessions:
            if session.end_time:
                participation_rate = len(session.participants) / 5  # 假设最大5人
                participation_rates.append(participation_rate)
        
        avg_participation = sum(participation_rates) / len(participation_rates) if participation_rates else 0
        
        return {
            "session_type_distribution": dict(session_types),
            "average_duration_minutes": avg_duration,
            "average_participation_rate": avg_participation,
            "most_common_type": max(session_types.items(), key=lambda x: x[1])[0] if session_types else None
        }
    
    async def _identify_communication_bottlenecks(self, messages: List[Message]) -> List[Dict[str, Any]]:
        """识别通信瓶颈"""
        bottlenecks = []
        
        # 分析消息积压
        pending_messages = [msg for msg in messages if msg.status == CommunicationStatus.PENDING]
        if len(pending_messages) > 10:
            bottlenecks.append({
                "type": "消息积压",
                "severity": "high",
                "count": len(pending_messages),
                "description": "待处理消息过多"
            })
        
        # 分析响应延迟
        slow_responses = []
        for msg in messages:
            if msg.requires_response:
                # 模拟响应时间检查
                if (datetime.now() - msg.timestamp).total_seconds() > self.message_timeout:
                    slow_responses.append(msg)
        
        if len(slow_responses) > 5:
            bottlenecks.append({
                "type": "响应延迟",
                "severity": "medium",
                "count": len(slow_responses),
                "description": "响应时间过长"
            })
        
        return bottlenecks
    
    async def _generate_collaboration_recommendations(self, total_messages: int, 
                                                    total_handoffs: int, 
                                                    total_sessions: int, 
                                                    avg_response_time: float) -> List[str]:
        """生成协作建议"""
        recommendations = []
        
        if total_messages > 100:
            recommendations.append("消息量较大，建议优化通信流程，减少不必要的消息")
        
        if total_handoffs > 20:
            recommendations.append("任务交接频繁，建议改进任务分配机制")
        
        if total_sessions < 5:
            recommendations.append("协作会话较少，建议增加团队协作活动")
        
        if avg_response_time > 60:
            recommendations.append("响应时间较长，建议建立更快的响应机制")
        
        recommendations.append("定期回顾通信效率，持续优化协作流程")
        
        return recommendations
    
    async def cleanup_expired_messages(self) -> Dict[str, Any]:
        """清理过期消息"""
        try:
            current_time = datetime.now()
            expired_count = 0
            
            # 清理过期消息
            for message_id in list(self.pending_messages.keys()):
                message = self.pending_messages[message_id]
                if (current_time - message.timestamp).total_seconds() > self.message_timeout:
                    message.status = CommunicationStatus.FAILED
                    self.message_history.append(message)
                    del self.pending_messages[message_id]
                    expired_count += 1
            
            # 清理过期的协作会话
            for session_id in list(self.active_sessions.keys()):
                session = self.active_sessions[session_id]
                if (current_time - session.start_time).total_seconds() > 7200:  # 2小时超时
                    session.status = "cancelled"
                    self.collaboration_sessions[session_id] = session
                    del self.active_sessions[session_id]
            
            self.logger.info(f"清理完成，过期消息: {expired_count}")
            
            return {
                "status": "completed",
                "expired_messages": expired_count,
                "cleanup_time": current_time.isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"清理过期消息失败: {str(e)}")
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }