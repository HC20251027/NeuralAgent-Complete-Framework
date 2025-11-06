"""
Agno多智能体框架 - 专业智能体
针对特定领域或任务类型的专业智能体
"""

import asyncio
import json
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
import logging

from .base_agent import BaseAgent, AgentStatus

logger = logging.getLogger(__name__)


class SpecialistAgent(BaseAgent):
    """专业智能体"""
    
    def __init__(
        self,
        agent_id: Optional[str] = None,
        name: str = "Specialist",
        description: str = "专业智能体",
        specialization: str = "general",
        expertise_areas: Optional[List[str]] = None,
        **kwargs
    ):
        super().__init__(
            agent_id=agent_id,
            name=name,
            description=description,
            **kwargs
        )
        
        self.specialization = specialization
        self.expertise_areas = expertise_areas or []
        
        # 专业技能
        self.skills: Dict[str, float] = {}  # 技能名称 -> 熟练度 (0-1)
        self.learning_progress: Dict[str, float] = {}
        
        # 工作历史
        self.task_history: List[Dict[str, Any]] = []
        self.success_patterns: List[Dict[str, Any]] = []
        self.failure_patterns: List[Dict[str, Any]] = []
        
        # 自适应学习
        self.adaptive_learning = True
        self.performance_feedback_loop = True
    
    async def initialize(self) -> None:
        """初始化专业智能体"""
        await super().initialize()
        
        # 初始化专业技能
        await self._initialize_skills()
        
        # 加载历史学习数据
        await self._load_learning_data()
        
        # 注册专业工具
        await self._register_specialist_tools()
        
        logger.info(f"专业智能体初始化完成: {self.name} ({self.specialization})")
    
    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """执行任务（专业版本）"""
        start_time = datetime.now()
        
        try:
            self.status = AgentStatus.BUSY
            self.current_task = task.get("task_id", f"task_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}")
            
            # 验证任务
            if not self._validate_task(task):
                raise ValueError("任务格式无效")
            
            # 检查专业匹配度
            match_score = await self._calculate_task_match(task)
            if match_score < 0.3:  # 最低匹配度阈值
                raise ValueError(f"任务与专业领域匹配度过低: {match_score:.2f}")
            
            # 执行任务
            result = await self._execute_specialized_task(task)
            
            # 更新学习数据
            await self._update_learning_data(task, result)
            
            # 更新统计
            execution_time = (datetime.now() - start_time).total_seconds()
            self.tasks_completed += 1
            self.total_execution_time += execution_time
            
            # 保存任务记录
            await self._save_task_record(task, result, execution_time, match_score)
            
            self.status = AgentStatus.IDLE
            self.current_task = None
            
            logger.info(f"专业任务执行完成: {self.name} - {task.get('type', 'unknown')}")
            return result
            
        except Exception as e:
            self.tasks_failed += 1
            self.status = AgentStatus.ERROR
            self.current_task = None
            
            # 记录失败模式
            await self._record_failure_pattern(task, str(e))
            
            error_result = {
                "task_id": task.get("task_id"),
                "status": "failed",
                "error": str(e),
                "agent_id": self.agent_id,
                "execution_time": (datetime.now() - start_time).total_seconds(),
                "specialization": self.specialization
            }
            
            logger.error(f"专业任务执行失败: {self.name} - {e}")
            return error_result
    
    async def learn_from_feedback(self, task_id: str, feedback: Dict[str, Any]) -> bool:
        """从反馈中学习"""
        try:
            # 查找对应的任务记录
            for record in self.task_history:
                if record["task_id"] == task_id:
                    # 更新学习进度
                    if "skill_improvement" in feedback:
                        for skill, improvement in feedback["skill_improvement"].items():
                            if skill in self.skills:
                                self.skills[skill] = min(1.0, self.skills[skill] + improvement)
                                self.learning_progress[skill] = self.learning_progress.get(skill, 0) + improvement
                    
                    # 记录学习事件
                    learning_event = {
                        "timestamp": datetime.now().isoformat(),
                        "task_id": task_id,
                        "feedback": feedback,
                        "skill_updates": feedback.get("skill_improvement", {})
                    }
                    
                    await self.remember(
                        content=json.dumps(learning_event),
                        memory_type="learning",
                        importance=0.7
                    )
                    
                    logger.info(f"学习完成: {self.name} - {task_id}")
                    return True
            
            logger.warning(f"未找到任务记录: {task_id}")
            return False
            
        except Exception as e:
            logger.error(f"学习失败: {e}")
            return False
    
    async def get_expertise_profile(self) -> Dict[str, Any]:
        """获取专业档案"""
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "specialization": self.specialization,
            "expertise_areas": self.expertise_areas,
            "skills": self.skills,
            "learning_progress": self.learning_progress,
            "task_history_count": len(self.task_history),
            "success_patterns_count": len(self.success_patterns),
            "failure_patterns_count": len(self.failure_patterns),
            "adaptive_learning": self.adaptive_learning,
            "performance_feedback_loop": self.performance_feedback_loop,
            "average_match_score": self._calculate_average_match_score(),
            "specialization_confidence": self._calculate_specialization_confidence()
        }
    
    async def recommend_task_approach(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """推荐任务执行方法"""
        try:
            # 分析任务特征
            task_features = await self._extract_task_features(task)
            
            # 基于历史模式推荐方法
            approach = await self._recommend_approach_from_patterns(task_features)
            
            # 评估执行风险
            risk_assessment = await self._assess_execution_risk(task, task_features)
            
            # 估算执行时间
            time_estimate = await self._estimate_execution_time(task, task_features)
            
            return {
                "recommended_approach": approach,
                "risk_assessment": risk_assessment,
                "time_estimate": time_estimate,
                "confidence_score": await self._calculate_task_confidence(task),
                "skill_requirements": self._identify_required_skills(task),
                "potential_challenges": await self._identify_potential_challenges(task),
                "success_factors": await self._identify_success_factors(task)
            }
            
        except Exception as e:
            logger.error(f"任务方法推荐失败: {e}")
            return {"error": str(e)}
    
    async def _execute_specialized_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """执行专业任务的具体实现"""
        task_type = task.get("type", "")
        
        # 根据专业化领域分发处理
        if self.specialization == "analysis":
            return await self._handle_analysis_task(task)
        elif self.specialization == "development":
            return await self._handle_development_task(task)
        elif self.specialization == "research":
            return await self._handle_research_task(task)
        elif self.specialization == "communication":
            return await self._handle_communication_task(task)
        else:
            # 默认处理
            return await self._handle_general_task(task)
    
    async def _handle_analysis_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """处理分析任务"""
        content = task.get("content", {})
        
        # 分析任务
        analysis_result = {
            "analysis_type": content.get("analysis_type", "general"),
            "findings": [],
            "insights": [],
            "recommendations": []
        }
        
        # 这里可以实现具体的分析逻辑
        # 例如：数据分析、文本分析、模式识别等
        
        return {
            "task_id": task.get("task_id"),
            "status": "completed",
            "result": analysis_result,
            "agent_id": self.agent_id,
            "timestamp": datetime.now().isoformat()
        }
    
    async def _handle_development_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """处理开发任务"""
        content = task.get("content", {})
        
        # 开发任务
        development_result = {
            "development_type": content.get("development_type", "general"),
            "code": "",
            "documentation": "",
            "tests": []
        }
        
        # 这里可以实现具体的开发逻辑
        # 例如：代码生成、架构设计、测试编写等
        
        return {
            "task_id": task.get("task_id"),
            "status": "completed",
            "result": development_result,
            "agent_id": self.agent_id,
            "timestamp": datetime.now().isoformat()
        }
    
    async def _handle_research_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """处理研究任务"""
        content = task.get("content", {})
        
        # 研究任务
        research_result = {
            "research_topic": content.get("research_topic", ""),
            "sources": [],
            "findings": [],
            "conclusions": []
        }
        
        # 这里可以实现具体的研究逻辑
        # 例如：文献调研、数据收集、趋势分析等
        
        return {
            "task_id": task.get("task_id"),
            "status": "completed",
            "result": research_result,
            "agent_id": self.agent_id,
            "timestamp": datetime.now().isoformat()
        }
    
    async def _handle_communication_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """处理通信任务"""
        content = task.get("content", {})
        
        # 通信任务
        communication_result = {
            "communication_type": content.get("communication_type", "general"),
            "message": "",
            "recipients": [],
            "response_expected": content.get("response_expected", False)
        }
        
        # 这里可以实现具体的通信逻辑
        # 例如：邮件写作、报告生成、会议组织等
        
        return {
            "task_id": task.get("task_id"),
            "status": "completed",
            "result": communication_result,
            "agent_id": self.agent_id,
            "timestamp": datetime.now().isoformat()
        }
    
    async def _handle_general_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """处理通用任务"""
        # 默认实现
        return {
            "task_id": task.get("task_id"),
            "status": "completed",
            "result": f"专业智能体 {self.name} 已处理任务类型: {task.get('type')}",
            "agent_id": self.agent_id,
            "specialization": self.specialization,
            "timestamp": datetime.now().isoformat()
        }
    
    async def _calculate_task_match(self, task: Dict[str, Any]) -> float:
        """计算任务匹配度"""
        match_score = 0.0
        
        # 任务类型匹配
        task_type = task.get("type", "")
        if task_type in self.expertise_areas:
            match_score += 0.4
        
        # 内容关键词匹配
        content = task.get("content", {})
        if isinstance(content, dict):
            for area in self.expertise_areas:
                if area in str(content):
                    match_score += 0.1
        
        # 技能匹配
        required_skills = content.get("required_skills", [])
        for skill in required_skills:
            if skill in self.skills:
                match_score += self.skills[skill] * 0.2
        
        return min(1.0, match_score)
    
    async def _initialize_skills(self) -> None:
        """初始化专业技能"""
        # 根据专业化领域设置默认技能
        if self.specialization == "analysis":
            self.skills = {
                "data_analysis": 0.8,
                "pattern_recognition": 0.7,
                "statistical_analysis": 0.8,
                "visualization": 0.6
            }
        elif self.specialization == "development":
            self.skills = {
                "coding": 0.9,
                "architecture_design": 0.7,
                "testing": 0.8,
                "debugging": 0.8
            }
        elif self.specialization == "research":
            self.skills = {
                "literature_review": 0.8,
                "data_collection": 0.7,
                "critical_thinking": 0.9,
                "writing": 0.8
            }
        elif self.specialization == "communication":
            self.skills = {
                "writing": 0.9,
                "presentation": 0.8,
                "negotiation": 0.7,
                "documentation": 0.8
            }
        else:
            self.skills = {
                "general": 0.6
            }
    
    async def _load_learning_data(self) -> None:
        """加载学习数据"""
        try:
            memories = await self.memory_manager.get_agent_memories(
                agent_id=self.agent_id,
                memory_type="learning",
                limit=50
            )
            
            for memory in memories:
                learning_data = json.loads(memory["content"])
                if "skill_updates" in learning_data:
                    for skill, progress in learning_data["skill_updates"].items():
                        self.learning_progress[skill] = self.learning_progress.get(skill, 0) + progress
            
            logger.info(f"已加载学习数据: {self.name}")
            
        except Exception as e:
            logger.warning(f"加载学习数据失败: {e}")
    
    async def _update_learning_data(self, task: Dict[str, Any], result: Dict[str, Any]) -> None:
        """更新学习数据"""
        if not self.adaptive_learning:
            return
        
        # 记录成功模式
        if result.get("status") == "completed":
            success_pattern = {
                "task_type": task.get("type"),
                "approach": "successful",
                "timestamp": datetime.now().isoformat(),
                "execution_time": result.get("execution_time", 0)
            }
            self.success_patterns.append(success_pattern)
            
            # 保持最近50个成功模式
            if len(self.success_patterns) > 50:
                self.success_patterns.pop(0)
        
        # 记录失败模式
        else:
            failure_pattern = {
                "task_type": task.get("type"),
                "error": result.get("error"),
                "timestamp": datetime.now().isoformat()
            }
            self.failure_patterns.append(failure_pattern)
            
            # 保持最近30个失败模式
            if len(self.failure_patterns) > 30:
                self.failure_patterns.pop(0)
    
    async def _save_task_record(self, task: Dict[str, Any], result: Dict[str, Any], 
                               execution_time: float, match_score: float) -> None:
        """保存任务记录"""
        record = {
            "task_id": task.get("task_id"),
            "task_type": task.get("type"),
            "content": task.get("content"),
            "result": result,
            "execution_time": execution_time,
            "match_score": match_score,
            "timestamp": datetime.now().isoformat()
        }
        
        self.task_history.append(record)
        
        # 保持最近100个任务记录
        if len(self.task_history) > 100:
            self.task_history.pop(0)
    
    async def _record_failure_pattern(self, task: Dict[str, Any], error: str) -> None:
        """记录失败模式"""
        failure_record = {
            "task_id": task.get("task_id"),
            "task_type": task.get("type"),
            "error": error,
            "timestamp": datetime.now().isoformat()
        }
        
        await self.remember(
            content=json.dumps(failure_record),
            memory_type="failure",
            importance=0.6
        )
    
    def _calculate_average_match_score(self) -> float:
        """计算平均匹配度"""
        if not self.task_history:
            return 0.0
        
        total_score = sum(record.get("match_score", 0) for record in self.task_history)
        return total_score / len(self.task_history)
    
    def _calculate_specialization_confidence(self) -> float:
        """计算专业化置信度"""
        if not self.skills:
            return 0.0
        
        # 基于技能熟练度计算置信度
        skill_confidence = sum(self.skills.values()) / len(self.skills)
        
        # 基于历史成功率调整
        total_tasks = self.tasks_completed + self.tasks_failed
        if total_tasks > 0:
            success_rate = self.tasks_completed / total_tasks
        else:
            success_rate = 0.5
        
        return (skill_confidence + success_rate) / 2
    
    async def _extract_task_features(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """提取任务特征"""
        return {
            "type": task.get("type"),
            "complexity": task.get("complexity", "medium"),
            "priority": task.get("priority", "normal"),
            "deadline": task.get("deadline"),
            "required_skills": task.get("content", {}).get("required_skills", []),
            "estimated_duration": task.get("estimated_duration")
        }
    
    async def _recommend_approach_from_patterns(self, task_features: Dict[str, Any]) -> str:
        """基于历史模式推荐方法"""
        # 简化的推荐逻辑
        task_type = task_features.get("type")
        
        # 查找相似的成功模式
        for pattern in reversed(self.success_patterns):
            if pattern.get("task_type") == task_type:
                return "基于历史成功经验的方法"
        
        return "标准处理方法"
    
    async def _assess_execution_risk(self, task: Dict[str, Any], 
                                   task_features: Dict[str, Any]) -> Dict[str, Any]:
        """评估执行风险"""
        risk_factors = []
        risk_level = "low"
        
        # 检查失败历史
        task_type = task_features.get("type")
        failure_count = sum(1 for pattern in self.failure_patterns 
                          if pattern.get("task_type") == task_type)
        
        if failure_count > 3:
            risk_factors.append("该任务类型历史失败率较高")
            risk_level = "high"
        elif failure_count > 1:
            risk_factors.append("该任务类型有一定失败率")
            risk_level = "medium"
        
        return {
            "risk_level": risk_level,
            "risk_factors": risk_factors,
            "mitigation_suggestions": ["充分准备", "分步执行", "及时反馈"]
        }
    
    async def _estimate_execution_time(self, task: Dict[str, Any], 
                                     task_features: Dict[str, Any]) -> Dict[str, Any]:
        """估算执行时间"""
        # 基于历史数据估算
        task_type = task_features.get("type")
        similar_tasks = [record for record in self.task_history 
                        if record.get("task_type") == task_type]
        
        if similar_tasks:
            avg_time = sum(record.get("execution_time", 0) for record in similar_tasks) / len(similar_tasks)
            min_time = min(record.get("execution_time", 0) for record in similar_tasks)
            max_time = max(record.get("execution_time", 0) for record in similar_tasks)
        else:
            avg_time = min_time = max_time = 300  # 默认5分钟
        
        return {
            "estimated_time": avg_time,
            "min_time": min_time,
            "max_time": max_time,
            "confidence": 0.7 if similar_tasks else 0.3
        }
    
    async def _calculate_task_confidence(self, task: Dict[str, Any]) -> float:
        """计算任务执行置信度"""
        match_score = await self._calculate_task_match(task)
        specialization_confidence = self._calculate_specialization_confidence()
        
        return (match_score + specialization_confidence) / 2
    
    def _identify_required_skills(self, task: Dict[str, Any]) -> List[str]:
        """识别所需技能"""
        required_skills = task.get("content", {}).get("required_skills", [])
        
        # 基于任务类型推断技能需求
        task_type = task.get("type")
        inferred_skills = []
        
        if task_type == "analysis":
            inferred_skills = ["data_analysis", "pattern_recognition"]
        elif task_type == "development":
            inferred_skills = ["coding", "architecture_design"]
        elif task_type == "research":
            inferred_skills = ["literature_review", "critical_thinking"]
        
        return list(set(required_skills + inferred_skills))
    
    async def _identify_potential_challenges(self, task: Dict[str, Any]) -> List[str]:
        """识别潜在挑战"""
        challenges = []
        
        # 基于失败历史识别挑战
        task_type = task.get("type")
        for pattern in self.failure_patterns:
            if pattern.get("task_type") == task_type:
                challenges.append(f"历史失败原因: {pattern.get('error', '未知错误')}")
        
        # 基于任务复杂度识别挑战
        complexity = task.get("complexity", "medium")
        if complexity == "high":
            challenges.append("任务复杂度较高")
        
        return challenges[:3]  # 最多返回3个挑战
    
    async def _identify_success_factors(self, task: Dict[str, Any]) -> List[str]:
        """识别成功因素"""
        factors = []
        
        # 基于成功模式识别因素
        task_type = task.get("type")
        for pattern in self.success_patterns:
            if pattern.get("task_type") == task_type:
                factors.append("遵循历史成功经验")
                break
        
        # 基于技能匹配度
        match_score = asyncio.create_task(self._calculate_task_match(task))
        if match_score.result() > 0.8:
            factors.append("任务与专业领域高度匹配")
        
        return factors[:3]  # 最多返回3个成功因素
    
    async def _register_specialist_tools(self) -> None:
        """注册专业工具"""
        await self.register_tool("get_expertise_profile", self.get_expertise_profile, "获取专业档案")
        await self.register_tool("recommend_approach", self.recommend_task_approach, "推荐任务方法")
        await self.register_tool("learn_from_feedback", self.learn_from_feedback, "从反馈学习")
    
    async def get_specialized_capabilities(self) -> List[str]:
        """获取专业能力"""
        base_capabilities = self.capabilities.copy()
        base_capabilities.extend([
            f"specialization:{self.specialization}",
            f"expertise:{area}" for area in self.expertise_areas
        ])
        return base_capabilities