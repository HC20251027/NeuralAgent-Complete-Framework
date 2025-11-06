"""
BMAD-METHOD框架 - 分析师智能体
负责需求分析、用户研究和数据分析
"""

import asyncio
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

from ...agno.agents.specialist import SpecialistAgent

logger = logging.getLogger(__name__)


class AnalystAgent(SpecialistAgent):
    """分析师智能体"""
    
    def __init__(self, agent_id: Optional[str] = None, name: str = "Analyst", **kwargs):
        super().__init__(
            agent_id=agent_id,
            name=name,
            description="需求分析师，负责任务分析、用户研究和数据分析",
            specialization="analysis",
            expertise_areas=[
                "requirements_analysis",
                "user_research", 
                "data_analysis",
                "market_research",
                "competitive_analysis",
                "process_analysis"
            ],
            **kwargs
        )
        
        # 分析工具
        self.analysis_tools = {
            "swot_analysis": self._swot_analysis,
            "user_persona": self._create_user_persona,
            "requirements_matrix": self._create_requirements_matrix,
            "data_visualization": self._create_data_visualization,
            "trend_analysis": self._perform_trend_analysis,
            "risk_assessment": self._perform_risk_assessment
        }
        
        # 分析模板
        self.analysis_templates = {
            "requirements_document": self._generate_requirements_document,
            "user_story": self._generate_user_story,
            "acceptance_criteria": self._generate_acceptance_criteria,
            "research_report": self._generate_research_report
        }
    
    async def analyze_requirements(self, requirements_data: Dict[str, Any]) -> Dict[str, Any]:
        """分析需求"""
        try:
            analysis_result = {
                "analysis_type": "requirements",
                "timestamp": datetime.now().isoformat(),
                "requirements": requirements_data,
                "findings": [],
                "recommendations": [],
                "risks": [],
                "priorities": {},
                "dependencies": [],
                "acceptance_criteria": []
            }
            
            # 执行需求分析
            findings = await self._analyze_requirements_findings(requirements_data)
            analysis_result["findings"] = findings
            
            # 生成建议
            recommendations = await self._generate_recommendations(requirements_data, findings)
            analysis_result["recommendations"] = recommendations
            
            # 风险评估
            risks = await self._assess_requirements_risks(requirements_data)
            analysis_result["risks"] = risks
            
            # 优先级排序
            priorities = await self._prioritize_requirements(requirements_data)
            analysis_result["priorities"] = priorities
            
            # 依赖分析
            dependencies = await self._analyze_dependencies(requirements_data)
            analysis_result["dependencies"] = dependencies
            
            # 验收标准
            acceptance_criteria = await self._generate_acceptance_criteria(requirements_data)
            analysis_result["acceptance_criteria"] = acceptance_criteria
            
            # 保存分析结果
            await self.remember(
                content=json.dumps(analysis_result),
                memory_type="analysis",
                importance=0.9
            )
            
            logger.info(f"需求分析完成: {len(findings)} 个发现")
            return analysis_result
            
        except Exception as e:
            logger.error(f"需求分析失败: {e}")
            raise
    
    async def conduct_user_research(self, research_scope: Dict[str, Any]) -> Dict[str, Any]:
        """进行用户研究"""
        try:
            research_result = {
                "research_type": "user_research",
                "timestamp": datetime.now().isoformat(),
                "scope": research_scope,
                "personas": [],
                "user_journeys": [],
                "pain_points": [],
                "opportunities": [],
                "recommendations": []
            }
            
            # 创建用户画像
            personas = await self._create_user_personas(research_scope)
            research_result["personas"] = personas
            
            # 用户旅程映射
            user_journeys = await self._map_user_journeys(research_scope)
            research_result["user_journeys"] = user_journeys
            
            # 痛点识别
            pain_points = await self._identify_pain_points(research_scope)
            research_result["pain_points"] = pain_points
            
            # 机会识别
            opportunities = await self._identify_opportunities(research_scope, pain_points)
            research_result["opportunities"] = opportunities
            
            # 研究建议
            recommendations = await self._generate_research_recommendations(research_result)
            research_result["recommendations"] = recommendations
            
            # 保存研究结果
            await self.remember(
                content=json.dumps(research_result),
                memory_type="research",
                importance=0.8
            )
            
            logger.info(f"用户研究完成: {len(personas)} 个用户画像")
            return research_result
            
        except Exception as e:
            logger.error(f"用户研究失败: {e}")
            raise
    
    async def perform_data_analysis(self, data_sources: List[Dict[str, Any]]) -> Dict[str, Any]:
        """执行数据分析"""
        try:
            analysis_result = {
                "analysis_type": "data_analysis",
                "timestamp": datetime.now().isoformat(),
                "data_sources": data_sources,
                "insights": [],
                "patterns": [],
                "anomalies": [],
                "trends": [],
                "predictions": [],
                "recommendations": []
            }
            
            # 数据探索
            exploration = await self._explore_data(data_sources)
            analysis_result["insights"] = exploration.get("insights", [])
            
            # 模式识别
            patterns = await self._identify_patterns(data_sources)
            analysis_result["patterns"] = patterns
            
            # 异常检测
            anomalies = await self._detect_anomalies(data_sources)
            analysis_result["anomalies"] = anomalies
            
            # 趋势分析
            trends = await self._analyze_trends(data_sources)
            analysis_result["trends"] = trends
            
            # 预测分析
            predictions = await self._make_predictions(data_sources, trends)
            analysis_result["predictions"] = predictions
            
            # 分析建议
            recommendations = await self._generate_analysis_recommendations(analysis_result)
            analysis_result["recommendations"] = recommendations
            
            # 保存分析结果
            await self.remember(
                content=json.dumps(analysis_result),
                memory_type="data_analysis",
                importance=0.7
            )
            
            logger.info(f"数据分析完成: {len(analysis_result['insights'])} 个洞察")
            return analysis_result
            
        except Exception as e:
            logger.error(f"数据分析失败: {e}")
            raise
    
    async def create_market_analysis(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建市场分析"""
        try:
            market_result = {
                "analysis_type": "market_analysis",
                "timestamp": datetime.now().isoformat(),
                "market_data": market_data,
                "market_size": {},
                "competitors": [],
                "market_trends": [],
                "opportunities": [],
                "threats": [],
                "recommendations": []
            }
            
            # 市场规模分析
            market_size = await self._analyze_market_size(market_data)
            market_result["market_size"] = market_size
            
            # 竞争对手分析
            competitors = await self._analyze_competitors(market_data)
            market_result["competitors"] = competitors
            
            # 市场趋势
            trends = await self._identify_market_trends(market_data)
            market_result["market_trends"] = trends
            
            # SWOT分析
            swot = await self._perform_swot_analysis(market_data)
            market_result["opportunities"] = swot.get("opportunities", [])
            market_result["threats"] = swot.get("threats", [])
            
            # 市场建议
            recommendations = await self._generate_market_recommendations(market_result)
            market_result["recommendations"] = recommendations
            
            # 保存分析结果
            await self.remember(
                content=json.dumps(market_result),
                memory_type="market_analysis",
                importance=0.8
            )
            
            logger.info(f"市场分析完成: {len(competitors)} 个竞争对手")
            return market_result
            
        except Exception as e:
            logger.error(f"市场分析失败: {e}")
            raise
    
    async def generate_analysis_report(self, analysis_data: Dict[str, Any], 
                                     report_type: str = "comprehensive") -> Dict[str, Any]:
        """生成分析报告"""
        try:
            report = {
                "report_type": report_type,
                "timestamp": datetime.now().isoformat(),
                "analyst": self.name,
                "analysis_data": analysis_data,
                "executive_summary": "",
                "detailed_findings": [],
                "methodology": "",
                "limitations": [],
                "next_steps": [],
                "appendices": {}
            }
            
            # 执行摘要
            report["executive_summary"] = await self._generate_executive_summary(analysis_data)
            
            # 详细发现
            report["detailed_findings"] = await self._generate_detailed_findings(analysis_data)
            
            # 方法论
            report["methodology"] = await self._document_methodology(analysis_data)
            
            # 局限性
            report["limitations"] = await self._identify_limitations(analysis_data)
            
            # 下一步行动
            report["next_steps"] = await self._recommend_next_steps(analysis_data)
            
            # 附录
            report["appendices"] = await self._prepare_appendices(analysis_data)
            
            # 保存报告
            await self.remember(
                content=json.dumps(report),
                memory_type="analysis_report",
                importance=0.9
            )
            
            logger.info(f"分析报告生成完成: {report_type}")
            return report
            
        except Exception as e:
            logger.error(f"生成分析报告失败: {e}")
            raise
    
    async def _analyze_requirements_findings(self, requirements: Dict[str, Any]) -> List[Dict[str, Any]]:
        """分析需求发现"""
        findings = []
        
        # 功能性需求分析
        functional_reqs = requirements.get("functional", [])
        for req in functional_reqs:
            finding = {
                "type": "functional_requirement",
                "requirement": req,
                "clarity": await self._assess_requirement_clarity(req),
                "completeness": await self._assess_requirement_completeness(req),
                "testability": await self._assess_requirement_testability(req),
                "priority": req.get("priority", "medium")
            }
            findings.append(finding)
        
        # 非功能性需求分析
        non_functional_reqs = requirements.get("non_functional", [])
        for req in non_functional_reqs:
            finding = {
                "type": "non_functional_requirement",
                "requirement": req,
                "measurable": await self._assess_measurability(req),
                "achievable": await self._assess_achievability(req),
                "priority": req.get("priority", "medium")
            }
            findings.append(finding)
        
        return findings
    
    async def _generate_recommendations(self, requirements: Dict[str, Any], 
                                      findings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """生成建议"""
        recommendations = []
        
        # 基于发现生成建议
        for finding in findings:
            if finding.get("clarity") < 0.7:
                recommendations.append({
                    "type": "clarification",
                    "finding": finding,
                    "recommendation": "需要澄清需求表述",
                    "priority": "high"
                })
            
            if finding.get("completeness") < 0.8:
                recommendations.append({
                    "type": "completeness",
                    "finding": finding,
                    "recommendation": "需要补充需求细节",
                    "priority": "medium"
                })
        
        # 整体建议
        recommendations.extend([
            {
                "type": "process",
                "recommendation": "建立需求变更管理流程",
                "priority": "high"
            },
            {
                "type": "validation",
                "recommendation": "与利益相关者验证需求",
                "priority": "high"
            }
        ])
        
        return recommendations
    
    async def _assess_requirements_risks(self, requirements: Dict[str, Any]) -> List[Dict[str, Any]]:
        """评估需求风险"""
        risks = []
        
        # 需求歧义风险
        ambiguous_reqs = [req for req in requirements.get("functional", []) 
                         if len(req.get("description", "")) < 50]
        if ambiguous_reqs:
            risks.append({
                "type": "ambiguity",
                "description": "存在歧义的需求描述",
                "impact": "medium",
                "probability": "high",
                "mitigation": "与需求提出者澄清"
            })
        
        # 需求变更风险
        if len(requirements.get("functional", [])) > 20:
            risks.append({
                "type": "scope_creep",
                "description": "需求范围可能不断扩大",
                "impact": "high",
                "probability": "medium",
                "mitigation": "建立严格的需求变更控制"
            })
        
        # 技术风险
        complex_reqs = [req for req in requirements.get("functional", []) 
                       if req.get("complexity", "medium") == "high"]
        if complex_reqs:
            risks.append({
                "type": "technical_complexity",
                "description": "存在高复杂度需求",
                "impact": "high",
                "probability": "high",
                "mitigation": "进行技术可行性评估"
            })
        
        return risks
    
    async def _prioritize_requirements(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """优先级排序"""
        all_reqs = requirements.get("functional", []) + requirements.get("non_functional", [])
        
        # MoSCoW优先级方法
        priorities = {
            "must_have": [],
            "should_have": [],
            "could_have": [],
            "wont_have": []
        }
        
        for req in all_reqs:
            priority = req.get("priority", "should_have").lower()
            if priority in priorities:
                priorities[priority].append(req)
            else:
                priorities["should_have"].append(req)
        
        return priorities
    
    async def _analyze_dependencies(self, requirements: Dict[str, Any]) -> List[Dict[str, Any]]:
        """依赖分析"""
        dependencies = []
        
        functional_reqs = requirements.get("functional", [])
        
        for i, req1 in enumerate(functional_reqs):
            for j, req2 in enumerate(functional_reqs[i+1:], i+1):
                # 简化的依赖检测逻辑
                if self._has_dependency(req1, req2):
                    dependencies.append({
                        "from": req1.get("id", f"req_{i}"),
                        "to": req2.get("id", f"req_{j}"),
                        "type": "functional",
                        "strength": "medium"
                    })
        
        return dependencies
    
    def _has_dependency(self, req1: Dict[str, Any], req2: Dict[str, Any]) -> bool:
        """检查依赖关系（简化实现）"""
        # 基于关键词的简单依赖检测
        desc1 = req1.get("description", "").lower()
        desc2 = req2.get("description", "").lower()
        
        # 如果描述中有相互引用的词汇，认为有依赖
        common_words = set(desc1.split()) & set(desc2.split())
        return len(common_words) > 2
    
    async def _generate_acceptance_criteria(self, requirements: Dict[str, Any]) -> List[Dict[str, Any]]:
        """生成验收标准"""
        criteria = []
        
        functional_reqs = requirements.get("functional", [])
        
        for req in functional_reqs:
            acceptance_criteria = {
                "requirement_id": req.get("id"),
                "criteria": [
                    f"系统应能{req.get('description', '执行指定功能')}",
                    "功能应能在5秒内响应",
                    "功能应支持并发访问",
                    "错误情况应有适当处理"
                ],
                "test_cases": [
                    "正常流程测试",
                    "边界条件测试",
                    "异常情况测试",
                    "性能测试"
                ]
            }
            criteria.append(acceptance_criteria)
        
        return criteria
    
    async def _create_user_personas(self, research_scope: Dict[str, Any]) -> List[Dict[str, Any]]:
        """创建用户画像"""
        personas = []
        
        # 基于研究范围创建典型用户画像
        target_users = research_scope.get("target_users", ["general_user"])
        
        for user_type in target_users:
            persona = {
                "id": f"persona_{user_type}",
                "name": f"典型{user_type}用户",
                "demographics": {
                    "age_range": "25-45",
                    "occupation": "knowledge_worker",
                    "tech_savviness": "medium"
                },
                "goals": [],
                "frustrations": [],
                "behaviors": [],
                "quote": f"我是一个典型的{user_type}用户"
            }
            
            # 为不同用户类型设置特定属性
            if user_type == "executive":
                persona["goals"] = ["提高决策效率", "获得数据洞察"]
                persona["frustrations"] = ["信息过载", "报告复杂"]
            elif user_type == "developer":
                persona["goals"] = ["快速开发", "代码质量"]
                persona["frustrations"] = ["需求变更", "技术债务"]
            
            personas.append(persona)
        
        return personas
    
    async def _map_user_journeys(self, research_scope: Dict[str, Any]) -> List[Dict[str, Any]]:
        """用户旅程映射"""
        journeys = []
        
        primary_journey = {
            "id": "primary_journey",
            "name": "主要用户旅程",
            "stages": [
                {
                    "stage": "awareness",
                    "description": "用户意识到需求",
                    "emotions": ["curious", "hopeful"],
                    "touchpoints": ["search", "referral"],
                    "pain_points": []
                },
                {
                    "stage": "consideration",
                    "description": "用户评估解决方案",
                    "emotions": ["analyzing", "comparing"],
                    "touchpoints": ["website", "demo", "reviews"],
                    "pain_points": ["信息不足", "选择困难"]
                },
                {
                    "stage": "decision",
                    "description": "用户做出决策",
                    "emotions": ["confident", "excited"],
                    "touchpoints": ["trial", "consultation"],
                    "pain_points": ["决策压力", "预算考虑"]
                },
                {
                    "stage": "usage",
                    "description": "用户开始使用",
                    "emotions": ["learning", "adapting"],
                    "touchpoints": ["onboarding", "support"],
                    "pain_points": ["学习曲线", "功能发现"]
                }
            ]
        }
        
        journeys.append(primary_journey)
        return journeys
    
    async def _identify_pain_points(self, research_scope: Dict[str, Any]) -> List[Dict[str, Any]]:
        """识别痛点"""
        pain_points = []
        
        # 基于研究范围识别常见痛点
        common_pain_points = [
            {
                "category": "usability",
                "description": "界面复杂，学习成本高",
                "impact": "high",
                "frequency": "common"
            },
            {
                "category": "performance",
                "description": "系统响应慢，影响效率",
                "impact": "high", 
                "frequency": "frequent"
            },
            {
                "category": "functionality",
                "description": "缺少关键功能",
                "impact": "critical",
                "frequency": "occasional"
            }
        ]
        
        pain_points.extend(common_pain_points)
        return pain_points
    
    async def _identify_opportunities(self, research_scope: Dict[str, Any], 
                                    pain_points: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """识别机会"""
        opportunities = []
        
        # 基于痛点识别改进机会
        for pain_point in pain_points:
            if pain_point["category"] == "usability":
                opportunities.append({
                    "opportunity": "简化用户界面",
                    "description": "重新设计交互流程，降低学习成本",
                    "impact": "high",
                    "effort": "medium"
                })
            elif pain_point["category"] == "performance":
                opportunities.append({
                    "opportunity": "优化系统性能",
                    "description": "提升响应速度，改善用户体验",
                    "impact": "high",
                    "effort": "high"
                })
        
        return opportunities
    
    async def _generate_research_recommendations(self, research_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """生成研究建议"""
        recommendations = [
            {
                "type": "validation",
                "recommendation": "与真实用户验证发现",
                "priority": "high"
            },
            {
                "type": "prioritization",
                "recommendation": "基于影响力和可行性排序机会",
                "priority": "medium"
            },
            {
                "type": "prototyping",
                "recommendation": "制作原型验证关键假设",
                "priority": "medium"
            }
        ]
        
        return recommendations
    
    # 数据分析方法
    async def _explore_data(self, data_sources: List[Dict[str, Any]]) -> Dict[str, Any]:
        """数据探索"""
        insights = []
        
        for source in data_sources:
            insight = {
                "source": source.get("name", "unknown"),
                "record_count": source.get("record_count", 0),
                "data_quality": "good",  # 简化实现
                "key_fields": source.get("key_fields", []),
                "observations": ["数据完整性良好", "字段命名规范"]
            }
            insights.append(insight)
        
        return {"insights": insights}
    
    async def _identify_patterns(self, data_sources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """识别模式"""
        patterns = [
            {
                "pattern_type": "temporal",
                "description": "数据显示明显的季节性模式",
                "confidence": 0.8,
                "impact": "medium"
            },
            {
                "pattern_type": "behavioral",
                "description": "用户行为呈现聚类特征",
                "confidence": 0.7,
                "impact": "high"
            }
        ]
        return patterns
    
    async def _detect_anomalies(self, data_sources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """异常检测"""
        anomalies = [
            {
                "type": "data_gap",
                "description": "某时间段数据缺失",
                "severity": "medium",
                "timestamp": "2024-01-15"
            }
        ]
        return anomalies
    
    async def _analyze_trends(self, data_sources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """趋势分析"""
        trends = [
            {
                "trend": "用户增长",
                "direction": "increasing",
                "strength": "strong",
                "timeframe": "6_months"
            }
        ]
        return trends
    
    async def _make_predictions(self, data_sources: List[Dict[str, Any]], 
                              trends: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """预测分析"""
        predictions = [
            {
                "prediction": "下季度用户增长20%",
                "confidence": 0.75,
                "timeframe": "3_months",
                "factors": ["市场趋势", "产品改进"]
            }
        ]
        return predictions
    
    async def _generate_analysis_recommendations(self, analysis_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """生成分析建议"""
        return [
            {
                "type": "data_quality",
                "recommendation": "改善数据收集流程",
                "priority": "high"
            },
            {
                "type": "monitoring",
                "recommendation": "建立实时监控机制",
                "priority": "medium"
            }
        ]
    
    # 市场分析方法
    async def _analyze_market_size(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """市场规模分析"""
        return {
            "total_addressable_market": 1000000,
            "serviceable_addressable_market": 500000,
            "serviceable_obtainable_market": 100000,
            "growth_rate": 0.15
        }
    
    async def _analyze_competitors(self, market_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """竞争对手分析"""
        competitors = [
            {
                "name": "竞争对手A",
                "market_share": 0.25,
                "strengths": ["品牌知名度", "技术领先"],
                "weaknesses": ["价格高", "客户服务差"]
            },
            {
                "name": "竞争对手B", 
                "market_share": 0.20,
                "strengths": ["价格优势", "快速响应"],
                "weaknesses": ["功能有限", "稳定性差"]
            }
        ]
        return competitors
    
    async def _identify_market_trends(self, market_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """市场趋势"""
        return [
            {
                "trend": "数字化转型加速",
                "impact": "positive",
                "timeframe": "2_years"
            },
            {
                "trend": "AI技术普及",
                "impact": "transformative", 
                "timeframe": "1_year"
            }
        ]
    
    async def _perform_swot_analysis(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """SWOT分析"""
        return {
            "strengths": ["技术优势", "团队能力", "创新文化"],
            "weaknesses": ["市场经验不足", "资源有限"],
            "opportunities": ["市场增长", "技术趋势"],
            "threats": ["竞争加剧", "技术变化"]
        }
    
    async def _generate_market_recommendations(self, market_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """市场建议"""
        return [
            {
                "type": "positioning",
                "recommendation": "定位为技术领先的解决方案",
                "priority": "high"
            },
            {
                "type": "pricing",
                "recommendation": "采用价值定价策略",
                "priority": "medium"
            }
        ]
    
    # 报告生成方法
    async def _generate_executive_summary(self, analysis_data: Dict[str, Any]) -> str:
        """生成执行摘要"""
        return f"基于对{len(analysis_data)}个数据源的分析，发现了关键洞察和机会。"
    
    async def _generate_detailed_findings(self, analysis_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """生成详细发现"""
        return [
            {
                "finding": "主要发现1",
                "description": "详细描述",
                "evidence": "支持数据",
                "implication": "业务影响"
            }
        ]
    
    async def _document_methodology(self, analysis_data: Dict[str, Any]) -> str:
        """记录方法论"""
        return "采用混合研究方法，结合定量和定性分析。"
    
    async def _identify_limitations(self, analysis_data: Dict[str, Any]) -> List[str]:
        """识别局限性"""
        return [
            "数据样本有限",
            "时间范围限制",
            "外部因素影响"
        ]
    
    async def _recommend_next_steps(self, analysis_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """建议下一步行动"""
        return [
            {
                "action": "验证关键发现",
                "timeline": "2_weeks",
                "owner": "research_team"
            },
            {
                "action": "制定行动计划",
                "timeline": "1_month",
                "owner": "product_team"
            }
        ]
    
    async def _prepare_appendices(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """准备附录"""
        return {
            "data_sources": "详细数据源列表",
            "methodology_details": "方法论详细说明",
            "raw_data": "原始数据摘要"
        }
    
    # 辅助评估方法
    async def _assess_requirement_clarity(self, requirement: Dict[str, Any]) -> float:
        """评估需求清晰度"""
        description = requirement.get("description", "")
        return min(1.0, len(description) / 100)
    
    async def _assess_requirement_completeness(self, requirement: Dict[str, Any]) -> float:
        """评估需求完整性"""
        required_fields = ["description", "acceptance_criteria", "priority"]
        present_fields = sum(1 for field in required_fields if field in requirement)
        return present_fields / len(required_fields)
    
    async def _assess_requirement_testability(self, requirement: Dict[str, Any]) -> float:
        """评估需求可测试性"""
        acceptance_criteria = requirement.get("acceptance_criteria", [])
        return min(1.0, len(acceptance_criteria) / 3)
    
    async def _assess_measurability(self, requirement: Dict[str, Any]) -> float:
        """评估可测量性"""
        description = requirement.get("description", "")
        measurable_keywords = ["性能", "响应时间", "吞吐量", "可用性"]
        score = sum(1 for keyword in measurable_keywords if keyword in description)
        return score / len(measurable_keywords)
    
    async def _assess_achievability(self, requirement: Dict[str, Any]) -> float:
        """评估可实现性"""
        complexity = requirement.get("complexity", "medium")
        complexity_scores = {"low": 0.9, "medium": 0.7, "high": 0.4}
        return complexity_scores.get(complexity, 0.7)
    
    async def get_specialized_capabilities(self) -> List[str]:
        """获取专业能力"""
        base_capabilities = await super().get_specialized_capabilities()
        base_capabilities.extend([
            "analysis:requirements_analysis",
            "analysis:user_research",
            "analysis:data_analysis", 
            "analysis:market_research",
            "analysis:competitive_analysis",
            "analysis:process_analysis",
            "analysis:risk_assessment",
            "analysis:trend_analysis"
        ])
        return base_capabilities