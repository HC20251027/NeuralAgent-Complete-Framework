"""
BMAD-METHOD框架 - 项目经理智能体
负责任务管理、资源调度和项目协调
"""

import asyncio
import json
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import logging

from ...agno.agents.specialist import SpecialistAgent

logger = logging.getLogger(__name__)


class ProjectStatus:
    """项目状态枚举"""
    PLANNING = "planning"
    ACTIVE = "active"
    ON_HOLD = "on_hold"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ARCHIVED = "archived"


class TaskPriority:
    """任务优先级"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


class ProjectManagerAgent(SpecialistAgent):
    """项目经理智能体"""
    
    def __init__(self, agent_id: Optional[str] = None, name: str = "ProjectManager", **kwargs):
        super().__init__(
            agent_id=agent_id,
            name=name,
            description="项目经理，负责任务管理、资源调度和项目协调",
            specialization="project_management",
            expertise_areas=[
                "project_planning",
                "resource_management",
                "risk_management",
                "stakeholder_management",
                "budget_management",
                "timeline_management",
                "quality_assurance"
            ],
            **kwargs
        )
        
        # 项目管理工具
        self.management_tools = {
            "create_project": self._create_project,
            "plan_sprint": self._plan_sprint,
            "allocate_resources": self._allocate_resources,
            "track_progress": self._track_progress,
            "manage_risks": self._manage_risks,
            "generate_report": self._generate_project_report
        }
        
        # 项目模板
        self.project_templates = {
            "agile_software": self._create_agile_software_project,
            "research_project": self._create_research_project,
            "infrastructure": self._create_infrastructure_project
        }
        
        # 项目数据存储
        self.projects: Dict[str, Dict[str, Any]] = {}
        self.active_sprints: Dict[str, Dict[str, Any]] = {}
        self.resource_pool: Dict[str, Dict[str, Any]] = {}
    
    async def create_project(self, project_config: Dict[str, Any]) -> str:
        """创建项目"""
        try:
            project_id = f"project_{len(self.projects)}"
            
            project = {
                "id": project_id,
                "name": project_config.get("name", "新项目"),
                "description": project_config.get("description", ""),
                "status": ProjectStatus.PLANNING,
                "created_at": datetime.now(),
                "start_date": project_config.get("start_date"),
                "end_date": project_config.get("end_date"),
                "budget": project_config.get("budget", 0),
                "team": project_config.get("team", []),
                "stakeholders": project_config.get("stakeholders", []),
                "objectives": project_config.get("objectives", []),
                "deliverables": project_config.get("deliverables", []),
                "milestones": [],
                "tasks": [],
                "risks": [],
                "issues": [],
                "progress": 0.0,
                "metrics": {
                    "tasks_completed": 0,
                    "tasks_total": 0,
                    "budget_spent": 0,
                    "schedule_variance": 0.0,
                    "quality_score": 0.0
                }
            }
            
            self.projects[project_id] = project
            
            # 保存项目记忆
            await self.remember(
                content=json.dumps(project, default=str),
                memory_type="project",
                importance=0.9
            )
            
            logger.info(f"项目已创建: {project['name']} ({project_id})")
            return project_id
            
        except Exception as e:
            logger.error(f"创建项目失败: {e}")
            raise
    
    async def plan_sprint(self, project_id: str, sprint_config: Dict[str, Any]) -> str:
        """规划冲刺"""
        try:
            if project_id not in self.projects:
                raise ValueError(f"项目不存在: {project_id}")
            
            sprint_id = f"sprint_{len(self.active_sprints)}"
            
            sprint = {
                "id": sprint_id,
                "project_id": project_id,
                "name": sprint_config.get("name", f"冲刺 {sprint_id}"),
                "goal": sprint_config.get("goal", ""),
                "duration": sprint_config.get("duration", 14),  # 天
                "start_date": sprint_config.get("start_date", datetime.now()),
                "end_date": sprint_config.get("start_date", datetime.now()) + timedelta(days=sprint_config.get("duration", 14)),
                "tasks": sprint_config.get("tasks", []),
                "capacity": sprint_config.get("capacity", 100),  # 故事点
                "velocity": 0.0,
                "burndown_data": [],
                "status": "planned"
            }
            
            self.active_sprints[sprint_id] = sprint
            
            # 更新项目状态
            project = self.projects[project_id]
            project["status"] = ProjectStatus.ACTIVE
            
            logger.info(f"冲刺已规划: {sprint['name']} ({sprint_id})")
            return sprint_id
            
        except Exception as e:
            logger.error(f"规划冲刺失败: {e}")
            raise
    
    async def assign_task(self, project_id: str, task_config: Dict[str, Any]) -> str:
        """分配任务"""
        try:
            if project_id not in self.projects:
                raise ValueError(f"项目不存在: {project_id}")
            
            task_id = f"task_{len(self.projects[project_id]['tasks'])}"
            
            task = {
                "id": task_id,
                "project_id": project_id,
                "title": task_config.get("title", "新任务"),
                "description": task_config.get("description", ""),
                "assignee": task_config.get("assignee"),
                "priority": task_config.get("priority", TaskPriority.MEDIUM),
                "story_points": task_config.get("story_points", 1),
                "status": "todo",
                "created_at": datetime.now(),
                "start_date": task_config.get("start_date"),
                "due_date": task_config.get("due_date"),
                "dependencies": task_config.get("dependencies", []),
                "acceptance_criteria": task_config.get("acceptance_criteria", []),
                "estimated_hours": task_config.get("estimated_hours", 0),
                "actual_hours": 0,
                "comments": []
            }
            
            self.projects[project_id]["tasks"].append(task)
            
            # 更新项目指标
            await self._update_project_metrics(project_id)
            
            logger.info(f"任务已分配: {task['title']} -> {task.get('assignee', '未分配')}")
            return task_id
            
        except Exception as e:
            logger.error(f"分配任务失败: {e}")
            raise
    
    async def update_task_status(self, project_id: str, task_id: str, 
                               status: str, hours_spent: float = 0) -> bool:
        """更新任务状态"""
        try:
            if project_id not in self.projects:
                return False
            
            project = self.projects[project_id]
            task = next((t for t in project["tasks"] if t["id"] == task_id), None)
            
            if not task:
                return False
            
            # 更新任务状态
            old_status = task["status"]
            task["status"] = status
            task["actual_hours"] += hours_spent
            
            # 记录状态变更
            status_change = {
                "timestamp": datetime.now(),
                "from_status": old_status,
                "to_status": status,
                "hours_spent": hours_spent
            }
            task["comments"].append(status_change)
            
            # 更新项目指标
            await self._update_project_metrics(project_id)
            
            # 检查是否完成冲刺
            await self._check_sprint_completion(project_id)
            
            logger.info(f"任务状态已更新: {task_id} {old_status} -> {status}")
            return True
            
        except Exception as e:
            logger.error(f"更新任务状态失败: {e}")
            return False
    
    async def manage_project_risks(self, project_id: str, risk_config: Dict[str, Any]) -> str:
        """管理项目风险"""
        try:
            if project_id not in self.projects:
                raise ValueError(f"项目不存在: {project_id}")
            
            risk_id = f"risk_{len(self.projects[project_id]['risks'])}"
            
            risk = {
                "id": risk_id,
                "project_id": project_id,
                "title": risk_config.get("title", "新风险"),
                "description": risk_config.get("description", ""),
                "category": risk_config.get("category", "technical"),
                "probability": risk_config.get("probability", 0.5),  # 0-1
                "impact": risk_config.get("impact", 0.5),  # 0-1
                "risk_score": 0.0,  # probability * impact
                "status": "identified",
                "owner": risk_config.get("owner"),
                "mitigation_plan": risk_config.get("mitigation_plan", ""),
                "contingency_plan": risk_config.get("contingency_plan", ""),
                "created_at": datetime.now(),
                "last_reviewed": datetime.now()
            }
            
            # 计算风险评分
            risk["risk_score"] = risk["probability"] * risk["impact"]
            
            self.projects[project_id]["risks"].append(risk)
            
            logger.info(f"风险已记录: {risk['title']} (评分: {risk['risk_score']:.2f})")
            return risk_id
            
        except Exception as e:
            logger.error(f"管理项目风险失败: {e}")
            raise
    
    async def generate_project_report(self, project_id: str, report_type: str = "status") -> Dict[str, Any]:
        """生成项目报告"""
        try:
            if project_id not in self.projects:
                raise ValueError(f"项目不存在: {project_id}")
            
            project = self.projects[project_id]
            
            if report_type == "status":
                return await self._generate_status_report(project)
            elif report_type == "progress":
                return await self._generate_progress_report(project)
            elif report_type == "risks":
                return await self._generate_risk_report(project)
            elif report_type == "resources":
                return await self._generate_resource_report(project)
            else:
                return await self._generate_comprehensive_report(project)
            
        except Exception as e:
            logger.error(f"生成项目报告失败: {e}")
            raise
    
    async def track_project_progress(self, project_id: str) -> Dict[str, Any]:
        """跟踪项目进度"""
        try:
            if project_id not in self.projects:
                raise ValueError(f"项目不存在: {project_id}")
            
            project = self.projects[project_id]
            
            # 计算进度指标
            total_tasks = len(project["tasks"])
            completed_tasks = len([t for t in project["tasks"] if t["status"] == "done"])
            in_progress_tasks = len([t for t in project["tasks"] if t["status"] == "in_progress"])
            
            # 计算完成百分比
            progress_percentage = (completed_tasks / max(1, total_tasks)) * 100
            
            # 计算预算使用情况
            total_budget = project["budget"]
            budget_spent = sum(task["actual_hours"] * 50 for task in project["tasks"])  # 假设每小时50元
            budget_utilization = (budget_spent / max(1, total_budget)) * 100
            
            # 计算时间进度
            start_date = project["start_date"]
            end_date = project["end_date"]
            current_date = datetime.now()
            
            if start_date and end_date:
                total_duration = (end_date - start_date).days
                elapsed_duration = (current_date - start_date).days
                time_progress = (elapsed_duration / max(1, total_duration)) * 100
            else:
                time_progress = 0
            
            # 更新项目指标
            project["progress"] = progress_percentage
            project["metrics"]["tasks_completed"] = completed_tasks
            project["metrics"]["tasks_total"] = total_tasks
            project["metrics"]["budget_spent"] = budget_spent
            project["metrics"]["schedule_variance"] = time_progress - progress_percentage
            
            progress_report = {
                "project_id": project_id,
                "timestamp": datetime.now().isoformat(),
                "overall_progress": progress_percentage,
                "task_progress": {
                    "total": total_tasks,
                    "completed": completed_tasks,
                    "in_progress": in_progress_tasks,
                    "todo": total_tasks - completed_tasks - in_progress_tasks
                },
                "budget_progress": {
                    "total_budget": total_budget,
                    "budget_spent": budget_spent,
                    "budget_utilization": budget_utilization,
                    "remaining_budget": total_budget - budget_spent
                },
                "schedule_progress": {
                    "time_progress": time_progress,
                    "schedule_variance": time_progress - progress_percentage,
                    "is_on_schedule": abs(time_progress - progress_percentage) < 10
                },
                "milestones": await self._check_milestone_progress(project),
                "risks_status": await self._assess_risk_status(project)
            }
            
            logger.info(f"项目进度跟踪完成: {project['name']} - {progress_percentage:.1f}%")
            return progress_report
            
        except Exception as e:
            logger.error(f"跟踪项目进度失败: {e}")
            raise
    
    async def allocate_resources(self, project_id: str, allocation_config: Dict[str, Any]) -> bool:
        """分配资源"""
        try:
            if project_id not in self.projects:
                return False
            
            project = self.projects[project_id]
            
            # 资源分配逻辑
            resource_allocations = allocation_config.get("allocations", [])
            
            for allocation in resource_allocations:
                resource_id = allocation.get("resource_id")
                task_id = allocation.get("task_id")
                allocation_percentage = allocation.get("percentage", 100)
                
                # 查找任务
                task = next((t for t in project["tasks"] if t["id"] == task_id), None)
                if task:
                    task["resource_allocation"] = {
                        "resource_id": resource_id,
                        "percentage": allocation_percentage,
                        "allocated_at": datetime.now()
                    }
            
            logger.info(f"资源分配完成: {len(resource_allocations)} 个分配")
            return True
            
        except Exception as e:
            logger.error(f"分配资源失败: {e}")
            return False
    
    async def get_project_dashboard(self, project_id: str) -> Dict[str, Any]:
        """获取项目仪表板"""
        try:
            if project_id not in self.projects:
                raise ValueError(f"项目不存在: {project_id}")
            
            project = self.projects[project_id]
            
            # 获取当前冲刺
            current_sprint = None
            for sprint in self.active_sprints.values():
                if sprint["project_id"] == project_id and sprint["status"] == "active":
                    current_sprint = sprint
                    break
            
            dashboard = {
                "project_info": {
                    "id": project_id,
                    "name": project["name"],
                    "status": project["status"],
                    "progress": project["progress"]
                },
                "key_metrics": project["metrics"],
                "current_sprint": current_sprint.to_dict() if current_sprint else None,
                "recent_activities": await self._get_recent_activities(project),
                "upcoming_milestones": await self._get_upcoming_milestones(project),
                "top_risks": await self._get_top_risks(project),
                "team_performance": await self._calculate_team_performance(project)
            }
            
            return dashboard
            
        except Exception as e:
            logger.error(f"获取项目仪表板失败: {e}")
            raise
    
    # 内部辅助方法
    async def _update_project_metrics(self, project_id: str) -> None:
        """更新项目指标"""
        project = self.projects[project_id]
        
        tasks = project["tasks"]
        total_tasks = len(tasks)
        completed_tasks = len([t for t in tasks if t["status"] == "done"])
        
        # 计算质量评分（基于任务完成质量和及时性）
        quality_score = 0.0
        if completed_tasks > 0:
            on_time_completion = len([t for t in tasks if t["status"] == "done" and 
                                    t.get("due_date") and t.get("completed_at", datetime.now()) <= t["due_date"]])
            quality_score = (on_time_completion / completed_tasks) * 100
        
        project["metrics"]["quality_score"] = quality_score
    
    async def _check_sprint_completion(self, project_id: str) -> None:
        """检查冲刺完成"""
        for sprint_id, sprint in self.active_sprints.items():
            if sprint["project_id"] != project_id:
                continue
            
            # 检查所有任务是否完成
            project = self.projects[project_id]
            sprint_tasks = [t for t in project["tasks"] if sprint_id in t.get("sprint_id", "")]
            
            if sprint_tasks and all(t["status"] == "done" for t in sprint_tasks):
                sprint["status"] = "completed"
                sprint["completed_at"] = datetime.now()
                
                # 计算冲刺速度
                total_story_points = sum(t.get("story_points", 0) for t in sprint_tasks)
                sprint["velocity"] = total_story_points
                
                logger.info(f"冲刺已完成: {sprint['name']} (速度: {total_story_points})")
    
    async def _generate_status_report(self, project: Dict[str, Any]) -> Dict[str, Any]:
        """生成状态报告"""
        return {
            "report_type": "status",
            "timestamp": datetime.now().isoformat(),
            "project_name": project["name"],
            "status": project["status"],
            "progress": project["progress"],
            "summary": f"项目进度: {project['progress']:.1f}%",
            "next_milestones": await self._get_upcoming_milestones(project)
        }
    
    async def _generate_progress_report(self, project: Dict[str, Any]) -> Dict[str, Any]:
        """生成进度报告"""
        tasks = project["tasks"]
        
        return {
            "report_type": "progress",
            "timestamp": datetime.now().isoformat(),
            "project_name": project["name"],
            "task_summary": {
                "total": len(tasks),
                "completed": len([t for t in tasks if t["status"] == "done"]),
                "in_progress": len([t for t in tasks if t["status"] == "in_progress"]),
                "blocked": len([t for t in tasks if t["status"] == "blocked"])
            },
            "burndown_data": await self._calculate_burndown_data(project),
            "velocity_trend": await self._calculate_velocity_trend(project)
        }
    
    async def _generate_risk_report(self, project: Dict[str, Any]) -> Dict[str, Any]:
        """生成风险报告"""
        risks = project["risks"]
        
        high_risks = [r for r in risks if r["risk_score"] > 0.7]
        medium_risks = [r for r in risks if 0.3 < r["risk_score"] <= 0.7]
        low_risks = [r for r in risks if r["risk_score"] <= 0.3]
        
        return {
            "report_type": "risks",
            "timestamp": datetime.now().isoformat(),
            "project_name": project["name"],
            "risk_summary": {
                "total": len(risks),
                "high": len(high_risks),
                "medium": len(medium_risks),
                "low": len(low_risks)
            },
            "top_risks": high_risks[:5],
            "risk_trends": await self._analyze_risk_trends(risks)
        }
    
    async def _generate_resource_report(self, project: Dict[str, Any]) -> Dict[str, Any]:
        """生成资源报告"""
        return {
            "report_type": "resources",
            "timestamp": datetime.now().isoformat(),
            "project_name": project["name"],
            "budget_status": {
                "allocated": project["budget"],
                "spent": project["metrics"]["budget_spent"],
                "remaining": project["budget"] - project["metrics"]["budget_spent"]
            },
            "resource_utilization": await self._calculate_resource_utilization(project)
        }
    
    async def _generate_comprehensive_report(self, project: Dict[str, Any]) -> Dict[str, Any]:
        """生成综合报告"""
        return {
            "report_type": "comprehensive",
            "timestamp": datetime.now().isoformat(),
            "project_name": project["name"],
            "status": await self._generate_status_report(project),
            "progress": await self._generate_progress_report(project),
            "risks": await self._generate_risk_report(project),
            "resources": await self._generate_resource_report(project)
        }
    
    async def _check_milestone_progress(self, project: Dict[str, Any]) -> List[Dict[str, Any]]:
        """检查里程碑进度"""
        milestones = project.get("milestones", [])
        current_date = datetime.now()
        
        milestone_status = []
        for milestone in milestones:
            status = {
                "name": milestone.get("name", ""),
                "due_date": milestone.get("due_date"),
                "status": "upcoming"
            }
            
            if milestone.get("due_date"):
                if current_date > milestone["due_date"]:
                    status["status"] = "overdue"
                elif current_date.date() == milestone["due_date"].date():
                    status["status"] = "due_today"
                else:
                    days_until = (milestone["due_date"] - current_date).days
                    if days_until <= 7:
                        status["status"] = "due_soon"
            
            milestone_status.append(status)
        
        return milestone_status
    
    async def _assess_risk_status(self, project: Dict[str, Any]) -> Dict[str, Any]:
        """评估风险状态"""
        risks = project["risks"]
        
        if not risks:
            return {"status": "no_risks", "score": 0}
        
        avg_risk_score = sum(r["risk_score"] for r in risks) / len(risks)
        
        if avg_risk_score > 0.7:
            status = "high_risk"
        elif avg_risk_score > 0.4:
            status = "medium_risk"
        else:
            status = "low_risk"
        
        return {
            "status": status,
            "score": avg_risk_score,
            "total_risks": len(risks)
        }
    
    async def _get_recent_activities(self, project: Dict[str, Any]) -> List[Dict[str, Any]]:
        """获取最近活动"""
        # 简化的活动记录
        recent_tasks = [t for t in project["tasks"] if t.get("status_change_history")]
        
        activities = []
        for task in recent_tasks[-10:]:  # 最近10个任务
            activities.append({
                "type": "task_update",
                "description": f"任务 '{task['title']}' 状态更新",
                "timestamp": task.get("last_updated", datetime.now()),
                "user": task.get("assignee")
            })
        
        return activities
    
    async def _get_upcoming_milestones(self, project: Dict[str, Any]) -> List[Dict[str, Any]]:
        """获取即将到来的里程碑"""
        current_date = datetime.now()
        upcoming = []
        
        for milestone in project.get("milestones", []):
            if milestone.get("due_date") and milestone["due_date"] > current_date:
                days_until = (milestone["due_date"] - current_date).days
                if days_until <= 30:  # 30天内
                    upcoming.append({
                        "name": milestone.get("name", ""),
                        "due_date": milestone["due_date"].isoformat(),
                        "days_until": days_until
                    })
        
        return sorted(upcoming, key=lambda x: x["days_until"])
    
    async def _get_top_risks(self, project: Dict[str, Any]) -> List[Dict[str, Any]]:
        """获取主要风险"""
        risks = sorted(project["risks"], key=lambda x: x["risk_score"], reverse=True)
        return risks[:5]
    
    async def _calculate_team_performance(self, project: Dict[str, Any]) -> Dict[str, Any]:
        """计算团队绩效"""
        tasks = project["tasks"]
        team_members = {}
        
        for task in tasks:
            assignee = task.get("assignee")
            if assignee:
                if assignee not in team_members:
                    team_members[assignee] = {
                        "tasks_assigned": 0,
                        "tasks_completed": 0,
                        "total_hours": 0,
                        "velocity": 0.0
                    }
                
                team_members[assignee]["tasks_assigned"] += 1
                if task["status"] == "done":
                    team_members[assignee]["tasks_completed"] += 1
                team_members[assignee]["total_hours"] += task.get("actual_hours", 0)
        
        # 计算速度
        for member in team_members.values():
            if member["tasks_assigned"] > 0:
                member["velocity"] = member["tasks_completed"] / member["tasks_assigned"]
        
        return team_members
    
    async def _calculate_burndown_data(self, project: Dict[str, Any]) -> List[Dict[str, Any]]:
        """计算燃尽图数据"""
        # 简化的燃尽图计算
        tasks = project["tasks"]
        total_story_points = sum(t.get("story_points", 0) for t in tasks)
        
        # 生成每日燃尽数据
        burndown_data = []
        for i in range(14):  # 假设14天冲刺
            date = datetime.now() - timedelta(days=13-i)
            remaining_points = max(0, total_story_points - (i * total_story_points / 14))
            burndown_data.append({
                "date": date.date().isoformat(),
                "remaining_points": remaining_points,
                "ideal_remaining": total_story_points - (i * total_story_points / 14)
            })
        
        return burndown_data
    
    async def _calculate_velocity_trend(self, project: Dict[str, Any]) -> List[Dict[str, Any]]:
        """计算速度趋势"""
        # 简化的速度趋势
        return [
            {"sprint": 1, "velocity": 45},
            {"sprint": 2, "velocity": 52},
            {"sprint": 3, "velocity": 48}
        ]
    
    async def _analyze_risk_trends(self, risks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析风险趋势"""
        return {
            "trend": "stable",
            "new_risks_this_period": 2,
            "mitigated_risks": 1,
            "escalated_risks": 0
        }
    
    async def _calculate_resource_utilization(self, project: Dict[str, Any]) -> Dict[str, Any]:
        """计算资源利用率"""
        return {
            "overall_utilization": 85.0,
            "team_utilization": {
                "developer_1": 90,
                "developer_2": 80,
                "designer": 85
            }
        }
    
    # 项目模板方法
    async def _create_agile_software_project(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """创建敏捷软件开发项目"""
        return {
            "type": "agile_software",
            "methodology": "scrum",
            "sprint_duration": 14,
            "roles": ["product_owner", "scrum_master", "development_team"],
            "ceremonies": ["daily_standup", "sprint_planning", "sprint_review", "retrospective"]
        }
    
    async def _create_research_project(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """创建研究项目"""
        return {
            "type": "research",
            "phases": ["literature_review", "methodology_design", "data_collection", "analysis", "reporting"],
            "deliverables": ["research_proposal", "interim_report", "final_report", "presentations"]
        }
    
    async def _create_infrastructure_project(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """创建基础设施项目"""
        return {
            "type": "infrastructure",
            "phases": ["planning", "design", "implementation", "testing", "deployment"],
            "compliance_requirements": ["security", "performance", "scalability"]
        }
    
    async def get_specialized_capabilities(self) -> List[str]:
        """获取专业能力"""
        base_capabilities = await super().get_specialized_capabilities()
        base_capabilities.extend([
            "pm:project_planning",
            "pm:resource_management",
            "pm:risk_management",
            "pm:stakeholder_management",
            "pm:budget_management",
            "pm:timeline_management",
            "pm:sprint_management",
            "pm:progress_tracking"
        ])
        return base_capabilities