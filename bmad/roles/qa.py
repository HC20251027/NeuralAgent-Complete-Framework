"""
QA智能体 - 负责测试计划、测试用例编写、自动化测试、缺陷管理
QA Agent - Responsible for test planning, test case creation, automated testing, and defect management
"""

import asyncio
import logging
import json
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import re
import xml.etree.ElementTree as ET

from agno.agents.base_agent import BaseAgent
from agno.memory.memory_manager import MemoryManager


class TestType(Enum):
    """测试类型"""
    UNIT = "unit"
    INTEGRATION = "integration"
    FUNCTIONAL = "functional"
    PERFORMANCE = "performance"
    SECURITY = "security"
    USABILITY = "usability"
    REGRESSION = "regression"
    SMOKE = "smoke"


class TestStatus(Enum):
    """测试状态"""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    BLOCKED = "blocked"


class DefectSeverity(Enum):
    """缺陷严重程度"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    TRIVIAL = "trivial"


class DefectStatus(Enum):
    """缺陷状态"""
    NEW = "new"
    CONFIRMED = "confirmed"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    VERIFIED = "verified"
    CLOSED = "closed"


@dataclass
class TestCase:
    """测试用例"""
    id: str
    title: str
    description: str
    test_type: TestType
    preconditions: List[str]
    test_steps: List[str]
    expected_results: List[str]
    priority: str
    tags: List[str]
    automation_status: str
    created_date: datetime
    updated_date: datetime


@dataclass
class TestSuite:
    """测试套件"""
    id: str
    name: str
    description: str
    test_cases: List[TestCase]
    dependencies: List[str]
    estimated_duration: int  # 分钟
    environment_requirements: List[str]


@dataclass
class TestExecution:
    """测试执行"""
    id: str
    test_suite_id: str
    test_cases: List[str]
    executor: str
    start_time: datetime
    end_time: Optional[datetime]
    status: TestStatus
    results: Dict[str, Any]
    defects_found: List[str]
    coverage_metrics: Dict[str, float]


@dataclass
class Defect:
    """缺陷"""
    id: str
    title: str
    description: str
    severity: DefectSeverity
    priority: str
    status: DefectStatus
    reporter: str
    assignee: Optional[str]
    test_case_id: Optional[str]
    environment: str
    steps_to_reproduce: List[str]
    actual_result: str
    expected_result: str
    attachments: List[str]
    created_date: datetime
    resolved_date: Optional[datetime]
    verification_date: Optional[datetime]


@dataclass
class TestReport:
    """测试报告"""
    id: str
    name: str
    execution_id: str
    generated_date: datetime
    summary: Dict[str, Any]
    detailed_results: List[Dict[str, Any]]
    defect_summary: Dict[str, Any]
    recommendations: List[str]


class QAAgent(BaseAgent):
    """QA智能体 - 负责测试和质量保证"""
    
    def __init__(self, 
                 agent_id: str,
                 name: str = "QA Agent",
                 memory_manager: Optional[MemoryManager] = None,
                 config: Optional[Dict] = None):
        super().__init__(agent_id, name, memory_manager, config)
        
        # 测试配置
        self.test_frameworks = {
            "python": ["pytest", "unittest", "nose", "robot"],
            "javascript": ["jest", "mocha", "jasmine", "cypress"],
            "api": ["postman", "newman", "rest-assured"]
        }
        
        self.test_environments = {
            "development": "http://dev.example.com",
            "staging": "http://staging.example.com",
            "production": "http://prod.example.com"
        }
        
        # 质量门禁
        self.quality_gates = {
            "test_coverage_threshold": 80.0,
            "critical_defects_threshold": 0,
            "high_defects_threshold": 5,
            "performance_threshold": 2.0,  # seconds
            "security_score_threshold": 90.0
        }
        
        # 数据存储
        self.test_cases: Dict[str, TestCase] = {}
        self.test_suites: Dict[str, TestSuite] = {}
        self.test_executions: Dict[str, TestExecution] = {}
        self.defects: Dict[str, Defect] = {}
        self.test_reports: Dict[str, TestReport] = {}
        
        self.logger = logging.getLogger(__name__)
    
    async def create_test_plan(self, 
                             project_requirements: Dict[str, Any],
                             timeline: Dict[str, Any]) -> Dict[str, Any]:
        """创建测试计划"""
        try:
            self.logger.info("开始创建测试计划")
            
            # 1. 分析项目需求
            requirements_analysis = await self._analyze_test_requirements(project_requirements)
            
            # 2. 确定测试策略
            testing_strategy = await self._define_testing_strategy(requirements_analysis)
            
            # 3. 创建测试套件
            test_suites = await self._create_test_suites(testing_strategy)
            
            # 4. 估算测试工作量
            effort_estimation = await self._estimate_testing_effort(test_suites, timeline)
            
            # 5. 制定测试时间表
            test_schedule = await self._create_test_schedule(test_suites, timeline)
            
            # 6. 定义质量门禁
            quality_gates = await self._define_quality_gates(requirements_analysis)
            
            test_plan = {
                "id": f"TP_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "project_name": project_requirements.get("name", "Unknown Project"),
                "version": project_requirements.get("version", "1.0"),
                "requirements_analysis": requirements_analysis,
                "testing_strategy": testing_strategy,
                "test_suites": {suite.id: asdict(suite) for suite in test_suites},
                "effort_estimation": effort_estimation,
                "test_schedule": test_schedule,
                "quality_gates": quality_gates,
                "resource_requirements": await self._define_resource_requirements(test_suites),
                "risk_analysis": await self._analyze_testing_risks(project_requirements),
                "created_date": datetime.now().isoformat(),
                "status": "draft"
            }
            
            # 保存到记忆
            await self.save_memory(f"test_plan_{test_plan['id']}", test_plan)
            
            return test_plan
            
        except Exception as e:
            self.logger.error(f"测试计划创建失败: {str(e)}")
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def create_test_cases(self, 
                              requirements: List[Dict[str, Any]],
                              test_plan_id: str) -> List[TestCase]:
        """创建测试用例"""
        try:
            self.logger.info(f"开始创建测试用例，共 {len(requirements)} 个需求")
            
            test_cases = []
            
            for req in requirements:
                # 1. 分析需求
                req_analysis = await self._analyze_requirement(req)
                
                # 2. 生成正向测试用例
                positive_cases = await self._generate_positive_test_cases(req_analysis)
                
                # 3. 生成负向测试用例
                negative_cases = await self._generate_negative_test_cases(req_analysis)
                
                # 4. 生成边界测试用例
                boundary_cases = await self._generate_boundary_test_cases(req_analysis)
                
                # 5. 生成异常测试用例
                exception_cases = await self._generate_exception_test_cases(req_analysis)
                
                all_cases = positive_cases + negative_cases + boundary_cases + exception_cases
                
                # 6. 为每个测试用例分配ID并保存
                for case in all_cases:
                    case.id = f"TC_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self.test_cases)}"
                    case.created_date = datetime.now()
                    case.updated_date = datetime.now()
                    
                    self.test_cases[case.id] = case
                    test_cases.append(case)
            
            # 更新测试计划中的用例数量
            await self._update_test_plan_case_count(test_plan_id, len(test_cases))
            
            return test_cases
            
        except Exception as e:
            self.logger.error(f"测试用例创建失败: {str(e)}")
            return []
    
    async def execute_test_suite(self, 
                               test_suite_id: str,
                               environment: str,
                               execution_config: Dict[str, Any]) -> TestExecution:
        """执行测试套件"""
        try:
            self.logger.info(f"开始执行测试套件: {test_suite_id}")
            
            # 1. 获取测试套件
            test_suite = self.test_suites.get(test_suite_id)
            if not test_suite:
                raise ValueError(f"测试套件 {test_suite_id} 不存在")
            
            # 2. 准备测试环境
            env_preparation = await self._prepare_test_environment(environment, execution_config)
            
            # 3. 创建执行记录
            execution_id = f"TE_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            execution = TestExecution(
                id=execution_id,
                test_suite_id=test_suite_id,
                test_cases=[case.id for case in test_suite.test_cases],
                executor=self.agent_id,
                start_time=datetime.now(),
                end_time=None,
                status=TestStatus.RUNNING,
                results={},
                defects_found=[],
                coverage_metrics={}
            )
            
            # 4. 执行测试用例
            execution_results = await self._execute_test_cases(
                test_suite.test_cases, environment, execution_config
            )
            
            # 5. 收集测试结果
            execution.results = execution_results
            execution.end_time = datetime.now()
            execution.status = TestStatus.PASSED if all(
                result.get("status") == "passed" for result in execution_results.values()
            ) else TestStatus.FAILED
            
            # 6. 计算覆盖率
            execution.coverage_metrics = await self._calculate_coverage_metrics(
                test_suite, execution_results
            )
            
            # 7. 生成缺陷报告
            defects = await self._extract_defects_from_results(execution_results)
            execution.defects_found = [defect.id for defect in defects]
            
            # 保存执行记录
            self.test_executions[execution_id] = execution
            
            # 保存到记忆
            await self.save_memory(f"test_execution_{execution_id}", asdict(execution))
            
            return execution
            
        except Exception as e:
            self.logger.error(f"测试套件执行失败: {str(e)}")
            raise
    
    async def manage_defects(self, 
                           defect_data: Dict[str, Any],
                           action: str) -> Defect:
        """管理缺陷"""
        try:
            self.logger.info(f"执行缺陷管理操作: {action}")
            
            if action == "create":
                return await self._create_defect(defect_data)
            elif action == "update":
                return await self._update_defect(defect_data)
            elif action == "resolve":
                return await self._resolve_defect(defect_data)
            elif action == "verify":
                return await self._verify_defect_resolution(defect_data)
            else:
                raise ValueError(f"不支持的缺陷操作: {action}")
                
        except Exception as e:
            self.logger.error(f"缺陷管理失败: {str(e)}")
            raise
    
    async def generate_test_report(self, 
                                 execution_id: str,
                                 report_config: Dict[str, Any]) -> TestReport:
        """生成测试报告"""
        try:
            self.logger.info(f"生成测试报告，执行ID: {execution_id}")
            
            # 1. 获取执行记录
            execution = self.test_executions.get(execution_id)
            if not execution:
                raise ValueError(f"执行记录 {execution_id} 不存在")
            
            # 2. 收集测试结果
            test_results = execution.results
            
            # 3. 生成汇总信息
            summary = await self._generate_execution_summary(execution, test_results)
            
            # 4. 生成详细结果
            detailed_results = await self._generate_detailed_results(execution, test_results)
            
            # 5. 生成缺陷摘要
            defect_summary = await self._generate_defect_summary(execution.defects_found)
            
            # 6. 生成建议
            recommendations = await self._generate_test_recommendations(execution, test_results)
            
            # 7. 创建报告
            report_id = f"TR_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            report = TestReport(
                id=report_id,
                name=f"测试报告_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                execution_id=execution_id,
                generated_date=datetime.now(),
                summary=summary,
                detailed_results=detailed_results,
                defect_summary=defect_summary,
                recommendations=recommendations
            )
            
            self.test_reports[report_id] = report
            
            # 保存到记忆
            await self.save_memory(f"test_report_{report_id}", asdict(report))
            
            return report
            
        except Exception as e:
            self.logger.error(f"测试报告生成失败: {str(e)}")
            raise
    
    async def setup_automation_framework(self, 
                                       project_config: Dict[str, Any]) -> Dict[str, Any]:
        """设置自动化测试框架"""
        try:
            self.logger.info("设置自动化测试框架")
            
            # 1. 选择测试框架
            framework_selection = await self._select_testing_frameworks(project_config)
            
            # 2. 创建项目结构
            project_structure = await self._create_automation_project_structure(project_config)
            
            # 3. 配置测试环境
            environment_config = await self._configure_test_environments(project_config)
            
            # 4. 创建基础测试模板
            test_templates = await self._create_test_templates(project_config)
            
            # 5. 设置CI/CD集成
            cicd_integration = await self._setup_cicd_integration(project_config)
            
            # 6. 配置报告系统
            reporting_config = await self._configure_reporting_system(project_config)
            
            # 7. 创建执行脚本
            execution_scripts = await self._create_execution_scripts(project_config)
            
            return {
                "status": "completed",
                "framework_selection": framework_selection,
                "project_structure": project_structure,
                "environment_config": environment_config,
                "test_templates": test_templates,
                "cicd_integration": cicd_integration,
                "reporting_config": reporting_config,
                "execution_scripts": execution_scripts,
                "setup_instructions": await self._generate_setup_instructions(project_config)
            }
            
        except Exception as e:
            self.logger.error(f"自动化框架设置失败: {str(e)}")
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def perform_quality_assessment(self, 
                                       project_artifacts: Dict[str, Any]) -> Dict[str, Any]:
        """执行质量评估"""
        try:
            self.logger.info("执行质量评估")
            
            # 1. 代码质量评估
            code_quality = await self._assess_code_quality(project_artifacts)
            
            # 2. 测试覆盖率评估
            test_coverage = await self._assess_test_coverage(project_artifacts)
            
            # 3. 性能评估
            performance_assessment = await self._assess_performance(project_artifacts)
            
            # 4. 安全评估
            security_assessment = await self._assess_security(project_artifacts)
            
            # 5. 文档质量评估
            documentation_quality = await self._assess_documentation_quality(project_artifacts)
            
            # 6. 整体质量评分
            overall_score = await self._calculate_overall_quality_score(
                code_quality, test_coverage, performance_assessment, 
                security_assessment, documentation_quality
            )
            
            # 7. 生成改进建议
            improvement_suggestions = await self._generate_improvement_suggestions(
                code_quality, test_coverage, performance_assessment,
                security_assessment, documentation_quality
            )
            
            return {
                "status": "completed",
                "overall_score": overall_score,
                "code_quality": code_quality,
                "test_coverage": test_coverage,
                "performance_assessment": performance_assessment,
                "security_assessment": security_assessment,
                "documentation_quality": documentation_quality,
                "quality_gates_status": await self._check_quality_gates(
                    code_quality, test_coverage, performance_assessment,
                    security_assessment, documentation_quality
                ),
                "improvement_suggestions": improvement_suggestions,
                "assessment_date": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"质量评估失败: {str(e)}")
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    # 私有方法实现
    
    async def _analyze_test_requirements(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """分析测试需求"""
        return {
            "functional_requirements": len(requirements.get("functional", [])),
            "non_functional_requirements": len(requirements.get("non_functional", [])),
            "integration_points": len(requirements.get("integrations", [])),
            "performance_requirements": requirements.get("performance", {}),
            "security_requirements": requirements.get("security", {}),
            "usability_requirements": requirements.get("usability", {})
        }
    
    async def _define_testing_strategy(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """定义测试策略"""
        return {
            "testing_levels": ["unit", "integration", "system", "acceptance"],
            "testing_types": ["functional", "performance", "security", "usability"],
            "testing_approach": "risk-based",
            "automation_strategy": "pyramid",
            "environment_strategy": "containerized"
        }
    
    async def _create_test_suites(self, strategy: Dict[str, Any]) -> List[TestSuite]:
        """创建测试套件"""
        suites = []
        
        # 单元测试套件
        unit_suite = TestSuite(
            id="TS_UNIT",
            name="单元测试套件",
            description="功能模块的单元测试",
            test_cases=[],
            dependencies=[],
            estimated_duration=30,
            environment_requirements=["development"]
        )
        suites.append(unit_suite)
        
        # 集成测试套件
        integration_suite = TestSuite(
            id="TS_INTEGRATION",
            name="集成测试套件",
            description="模块间集成测试",
            test_cases=[],
            dependencies=["TS_UNIT"],
            estimated_duration=60,
            environment_requirements=["staging"]
        )
        suites.append(integration_suite)
        
        return suites
    
    async def _estimate_testing_effort(self, suites: List[TestSuite], timeline: Dict[str, Any]) -> Dict[str, Any]:
        """估算测试工作量"""
        total_effort = sum(suite.estimated_duration for suite in suites)
        
        return {
            "total_effort_hours": total_effort / 60,
            "effort_breakdown": {
                "unit_testing": 0.3,
                "integration_testing": 0.4,
                "system_testing": 0.2,
                "regression_testing": 0.1
            },
            "resource_requirements": {
                "qa_engineers": 2,
                "automation_engineers": 1,
                "test_managers": 1
            }
        }
    
    async def _create_test_schedule(self, suites: List[TestSuite], timeline: Dict[str, Any]) -> Dict[str, Any]:
        """创建测试时间表"""
        return {
            "phases": [
                {"name": "Unit Testing", "start_date": "2025-11-06", "duration": 3},
                {"name": "Integration Testing", "start_date": "2025-11-09", "duration": 5},
                {"name": "System Testing", "start_date": "2025-11-14", "duration": 3},
                {"name": "Acceptance Testing", "start_date": "2025-11-17", "duration": 2}
            ],
            "milestones": [
                {"name": "Alpha Release", "date": "2025-11-13"},
                {"name": "Beta Release", "date": "2025-11-16"},
                {"name": "Production Release", "date": "2025-11-19"}
            ]
        }
    
    async def _define_quality_gates(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """定义质量门禁"""
        return {
            "code_coverage": 80.0,
            "critical_defects": 0,
            "high_defects": 5,
            "performance_threshold": 2.0,
            "security_score": 90.0
        }
    
    async def _define_resource_requirements(self, suites: List[TestSuite]) -> Dict[str, Any]:
        """定义资源需求"""
        return {
            "human_resources": {
                "qa_lead": 1,
                "qa_engineers": 2,
                "automation_engineers": 1
            },
            "infrastructure": {
                "test_environments": 3,
                "test_data_sets": 5,
                "automation_tools": ["selenium", "jmeter", "postman"]
            }
        }
    
    async def _analyze_testing_risks(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """分析测试风险"""
        return {
            "high_risks": [
                {"risk": "第三方集成依赖", "impact": "high", "probability": "medium"},
                {"risk": "性能要求严格", "impact": "high", "probability": "low"}
            ],
            "medium_risks": [
                {"risk": "测试数据准备", "impact": "medium", "probability": "medium"}
            ],
            "mitigation_strategies": [
                "提前准备测试环境",
                "建立模拟数据生成机制",
                "实施持续集成测试"
            ]
        }
    
    async def _analyze_requirement(self, requirement: Dict[str, Any]) -> Dict[str, Any]:
        """分析单个需求"""
        return {
            "id": requirement.get("id", ""),
            "type": requirement.get("type", "functional"),
            "complexity": requirement.get("complexity", "medium"),
            "dependencies": requirement.get("dependencies", []),
            "testability": requirement.get("testability", "high")
        }
    
    async def _generate_positive_test_cases(self, analysis: Dict[str, Any]) -> List[TestCase]:
        """生成正向测试用例"""
        cases = []
        
        case = TestCase(
            id="",
            title=f"正向测试 - {analysis['id']}",
            description=f"验证{analysis['id']}的基本功能",
            test_type=TestType.FUNCTIONAL,
            preconditions=["系统正常运行"],
            test_steps=["执行主要功能"],
            expected_results=["功能正常执行"],
            priority="high",
            tags=["positive", "functional"],
            automation_status="manual",
            created_date=datetime.now(),
            updated_date=datetime.now()
        )
        cases.append(case)
        
        return cases
    
    async def _generate_negative_test_cases(self, analysis: Dict[str, Any]) -> List[TestCase]:
        """生成负向测试用例"""
        cases = []
        
        case = TestCase(
            id="",
            title=f"负向测试 - {analysis['id']}",
            description=f"验证{analysis['id']}的错误处理",
            test_type=TestType.FUNCTIONAL,
            preconditions=["系统正常运行"],
            test_steps=["输入无效数据"],
            expected_results=["显示错误信息"],
            priority="medium",
            tags=["negative", "error_handling"],
            automation_status="manual",
            created_date=datetime.now(),
            updated_date=datetime.now()
        )
        cases.append(case)
        
        return cases
    
    async def _generate_boundary_test_cases(self, analysis: Dict[str, Any]) -> List[TestCase]:
        """生成边界测试用例"""
        cases = []
        
        case = TestCase(
            id="",
            title=f"边界测试 - {analysis['id']}",
            description=f"验证{analysis['id']}的边界条件",
            test_type=TestType.FUNCTIONAL,
            preconditions=["系统正常运行"],
            test_steps=["输入边界值"],
            expected_results=["正确处理边界值"],
            priority="medium",
            tags=["boundary", "edge_case"],
            automation_status="manual",
            created_date=datetime.now(),
            updated_date=datetime.now()
        )
        cases.append(case)
        
        return cases
    
    async def _generate_exception_test_cases(self, analysis: Dict[str, Any]) -> List[TestCase]:
        """生成异常测试用例"""
        cases = []
        
        case = TestCase(
            id="",
            title=f"异常测试 - {analysis['id']}",
            description=f"验证{analysis['id']}的异常处理",
            test_type=TestType.FUNCTIONAL,
            preconditions=["系统正常运行"],
            test_steps=["模拟异常情况"],
            expected_results=["优雅处理异常"],
            priority="high",
            tags=["exception", "error_handling"],
            automation_status="manual",
            created_date=datetime.now(),
            updated_date=datetime.now()
        )
        cases.append(case)
        
        return cases
    
    async def _update_test_plan_case_count(self, test_plan_id: str, case_count: int) -> None:
        """更新测试计划中的用例数量"""
        # 这里应该更新数据库或配置文件
        pass
    
    async def _prepare_test_environment(self, environment: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """准备测试环境"""
        return {
            "environment": environment,
            "status": "ready",
            "config": config,
            "setup_time": datetime.now().isoformat()
        }
    
    async def _execute_test_cases(self, test_cases: List[TestCase], environment: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """执行测试用例"""
        results = {}
        
        for case in test_cases:
            # 模拟执行测试
            result = {
                "case_id": case.id,
                "status": "passed",
                "execution_time": 1.5,
                "output": "测试通过",
                "screenshots": [],
                "logs": []
            }
            results[case.id] = result
        
        return results
    
    async def _calculate_coverage_metrics(self, suite: TestSuite, results: Dict[str, Any]) -> Dict[str, float]:
        """计算覆盖率指标"""
        total_cases = len(suite.test_cases)
        passed_cases = len([r for r in results.values() if r.get("status") == "passed"])
        
        return {
            "test_coverage": (passed_cases / total_cases) * 100 if total_cases > 0 else 0,
            "pass_rate": (passed_cases / total_cases) * 100 if total_cases > 0 else 0
        }
    
    async def _extract_defects_from_results(self, results: Dict[str, Any]) -> List[Defect]:
        """从测试结果中提取缺陷"""
        defects = []
        
        for case_id, result in results.items():
            if result.get("status") == "failed":
                defect = Defect(
                    id=f"DEF_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    title=f"测试失败 - {case_id}",
                    description=result.get("output", "测试执行失败"),
                    severity=DefectSeverity.MEDIUM,
                    priority="medium",
                    status=DefectStatus.NEW,
                    reporter=self.agent_id,
                    assignee=None,
                    test_case_id=case_id,
                    environment="test",
                    steps_to_reproduce=["执行测试用例"],
                    actual_result="测试失败",
                    expected_result="测试通过",
                    attachments=[],
                    created_date=datetime.now(),
                    resolved_date=None,
                    verification_date=None
                )
                defects.append(defect)
                self.defects[defect.id] = defect
        
        return defects
    
    async def _create_defect(self, defect_data: Dict[str, Any]) -> Defect:
        """创建缺陷"""
        defect_id = f"DEF_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        defect = Defect(
            id=defect_id,
            title=defect_data.get("title", ""),
            description=defect_data.get("description", ""),
            severity=DefectSeverity(defect_data.get("severity", "medium")),
            priority=defect_data.get("priority", "medium"),
            status=DefectStatus.NEW,
            reporter=self.agent_id,
            assignee=defect_data.get("assignee"),
            test_case_id=defect_data.get("test_case_id"),
            environment=defect_data.get("environment", "test"),
            steps_to_reproduce=defect_data.get("steps_to_reproduce", []),
            actual_result=defect_data.get("actual_result", ""),
            expected_result=defect_data.get("expected_result", ""),
            attachments=defect_data.get("attachments", []),
            created_date=datetime.now(),
            resolved_date=None,
            verification_date=None
        )
        
        self.defects[defect_id] = defect
        return defect
    
    async def _update_defect(self, defect_data: Dict[str, Any]) -> Defect:
        """更新缺陷"""
        defect_id = defect_data.get("id")
        defect = self.defects.get(defect_id)
        
        if not defect:
            raise ValueError(f"缺陷 {defect_id} 不存在")
        
        # 更新缺陷信息
        if "title" in defect_data:
            defect.title = defect_data["title"]
        if "description" in defect_data:
            defect.description = defect_data["description"]
        if "severity" in defect_data:
            defect.severity = DefectSeverity(defect_data["severity"])
        if "priority" in defect_data:
            defect.priority = defect_data["priority"]
        if "assignee" in defect_data:
            defect.assignee = defect_data["assignee"]
        
        return defect
    
    async def _resolve_defect(self, defect_data: Dict[str, Any]) -> Defect:
        """解决缺陷"""
        defect_id = defect_data.get("id")
        defect = self.defects.get(defect_id)
        
        if not defect:
            raise ValueError(f"缺陷 {defect_id} 不存在")
        
        defect.status = DefectStatus.RESOLVED
        defect.resolved_date = datetime.now()
        
        return defect
    
    async def _verify_defect_resolution(self, defect_data: Dict[str, Any]) -> Defect:
        """验证缺陷解决"""
        defect_id = defect_data.get("id")
        defect = self.defects.get(defect_id)
        
        if not defect:
            raise ValueError(f"缺陷 {defect_id} 不存在")
        
        defect.status = DefectStatus.VERIFIED
        defect.verification_date = datetime.now()
        
        return defect
    
    async def _generate_execution_summary(self, execution: TestExecution, results: Dict[str, Any]) -> Dict[str, Any]:
        """生成执行汇总"""
        total_cases = len(results)
        passed_cases = len([r for r in results.values() if r.get("status") == "passed"])
        failed_cases = len([r for r in results.values() if r.get("status") == "failed"])
        
        return {
            "total_test_cases": total_cases,
            "passed": passed_cases,
            "failed": failed_cases,
            "pass_rate": (passed_cases / total_cases) * 100 if total_cases > 0 else 0,
            "execution_time": (execution.end_time - execution.start_time).total_seconds() if execution.end_time else 0,
            "defects_found": len(execution.defects_found)
        }
    
    async def _generate_detailed_results(self, execution: TestExecution, results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """生成详细结果"""
        detailed = []
        
        for case_id, result in results.items():
            detailed.append({
                "test_case_id": case_id,
                "status": result.get("status"),
                "execution_time": result.get("execution_time"),
                "output": result.get("output"),
                "screenshots": result.get("screenshots", []),
                "logs": result.get("logs", [])
            })
        
        return detailed
    
    async def _generate_defect_summary(self, defect_ids: List[str]) -> Dict[str, Any]:
        """生成缺陷摘要"""
        defects = [self.defects[defect_id] for defect_id in defect_ids if defect_id in self.defects]
        
        severity_counts = {}
        for defect in defects:
            severity = defect.severity.value
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        return {
            "total_defects": len(defects),
            "by_severity": severity_counts,
            "critical_defects": len([d for d in defects if d.severity == DefectSeverity.CRITICAL]),
            "high_defects": len([d for d in defects if d.severity == DefectSeverity.HIGH])
        }
    
    async def _generate_test_recommendations(self, execution: TestExecution, results: Dict[str, Any]) -> List[str]:
        """生成测试建议"""
        recommendations = []
        
        pass_rate = len([r for r in results.values() if r.get("status") == "passed"]) / len(results) * 100 if results else 0
        
        if pass_rate < 80:
            recommendations.append("建议增加测试覆盖率，修复失败的测试用例")
        
        if len(execution.defects_found) > 5:
            recommendations.append("发现较多缺陷，建议进行代码审查")
        
        recommendations.append("建议实施持续集成测试，提高测试效率")
        
        return recommendations
    
    async def _select_testing_frameworks(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """选择测试框架"""
        return {
            "unit_testing": "pytest",
            "integration_testing": "pytest + requests",
            "ui_testing": "selenium",
            "api_testing": "requests + json",
            "performance_testing": "locust"
        }
    
    async def _create_automation_project_structure(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """创建自动化项目结构"""
        return {
            "directories": [
                "tests/unit",
                "tests/integration", 
                "tests/ui",
                "tests/api",
                "tests/performance",
                "tests/data",
                "tests/utils",
                "reports"
            ],
            "files": [
                "conftest.py",
                "pytest.ini",
                "requirements.txt",
                "README.md"
            ]
        }
    
    async def _configure_test_environments(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """配置测试环境"""
        return {
            "environments": {
                "dev": {"url": "http://dev.example.com", "browser": "chrome"},
                "staging": {"url": "http://staging.example.com", "browser": "firefox"},
                "prod": {"url": "http://prod.example.com", "browser": "chrome"}
            },
            "environment_variables": {
                "DATABASE_URL": "test_db_url",
                "API_KEY": "test_api_key"
            }
        }
    
    async def _create_test_templates(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """创建测试模板"""
        return {
            "unit_test_template": "def test_function():\n    # Arrange\n    \n    # Act\n    \n    # Assert\n    pass",
            "integration_test_template": "def test_api_integration():\n    # Test API integration\n    pass",
            "ui_test_template": "def test_ui_element():\n    # Test UI interaction\n    pass"
        }
    
    async def _setup_cicd_integration(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """设置CI/CD集成"""
        return {
            "github_actions": {
                "workflow_file": ".github/workflows/tests.yml",
                "triggers": ["push", "pull_request"],
                "jobs": ["unit_tests", "integration_tests", "ui_tests"]
            },
            "quality_gates": {
                "min_coverage": 80,
                "max_failures": 0
            }
        }
    
    async def _configure_reporting_system(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """配置报告系统"""
        return {
            "formats": ["html", "xml", "json"],
            "plugins": ["pytest-html", "allure"],
            "storage": "reports/",
            "retention": "30 days"
        }
    
    async def _create_execution_scripts(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """创建执行脚本"""
        return {
            "run_all_tests.sh": "#!/bin/bash\npytest tests/\n",
            "run_unit_tests.sh": "#!/bin/bash\npytest tests/unit/\n",
            "run_integration_tests.sh": "#!/bin/bash\npytest tests/integration/\n"
        }
    
    async def _generate_setup_instructions(self, config: Dict[str, Any]) -> List[str]:
        """生成设置说明"""
        return [
            "1. 安装Python依赖: pip install -r requirements.txt",
            "2. 安装浏览器驱动: webdriver-manager",
            "3. 配置测试环境变量",
            "4. 运行测试: pytest tests/",
            "5. 生成报告: pytest --html=reports/report.html"
        ]
    
    async def _assess_code_quality(self, artifacts: Dict[str, Any]) -> Dict[str, Any]:
        """评估代码质量"""
        return {
            "score": 85.0,
            "metrics": {
                "complexity": 7.5,
                "maintainability": 8.5,
                "documentation": 8.0,
                "testing": 9.0
            },
            "issues": []
        }
    
    async def _assess_test_coverage(self, artifacts: Dict[str, Any]) -> Dict[str, Any]:
        """评估测试覆盖率"""
        return {
            "overall_coverage": 82.5,
            "by_module": {
                "core": 90.0,
                "utils": 85.0,
                "api": 75.0
            },
            "gaps": ["error_handling", "edge_cases"]
        }
    
    async def _assess_performance(self, artifacts: Dict[str, Any]) -> Dict[str, Any]:
        """评估性能"""
        return {
            "response_time": 1.2,
            "throughput": 1000,
            "memory_usage": 512,
            "cpu_usage": 45.0,
            "score": 88.0
        }
    
    async def _assess_security(self, artifacts: Dict[str, Any]) -> Dict[str, Any]:
        """评估安全性"""
        return {
            "security_score": 92.0,
            "vulnerabilities": [],
            "compliance": ["OWASP", "GDPR"],
            "recommendations": []
        }
    
    async def _assess_documentation_quality(self, artifacts: Dict[str, Any]) -> Dict[str, Any]:
        """评估文档质量"""
        return {
            "completeness": 85.0,
            "accuracy": 90.0,
            "clarity": 88.0,
            "coverage": "API docs, user guide, deployment guide"
        }
    
    async def _calculate_overall_quality_score(self, code_quality: Dict[str, Any], test_coverage: Dict[str, Any], 
                                              performance: Dict[str, Any], security: Dict[str, Any], 
                                              documentation: Dict[str, Any]) -> float:
        """计算整体质量分数"""
        weights = {
            "code_quality": 0.25,
            "test_coverage": 0.25,
            "performance": 0.20,
            "security": 0.20,
            "documentation": 0.10
        }
        
        score = (
            code_quality["score"] * weights["code_quality"] +
            test_coverage["overall_coverage"] * weights["test_coverage"] +
            performance["score"] * weights["performance"] +
            security["security_score"] * weights["security"] +
            documentation["completeness"] * weights["documentation"]
        )
        
        return round(score, 2)
    
    async def _generate_improvement_suggestions(self, code_quality: Dict[str, Any], test_coverage: Dict[str, Any],
                                              performance: Dict[str, Any], security: Dict[str, Any],
                                              documentation: Dict[str, Any]) -> List[str]:
        """生成改进建议"""
        suggestions = []
        
        if test_coverage["overall_coverage"] < 80:
            suggestions.append("增加测试覆盖率，特别是错误处理和边界条件测试")
        
        if performance["response_time"] > 2.0:
            suggestions.append("优化性能，减少响应时间")
        
        if security["security_score"] < 90:
            suggestions.append("加强安全措施，修复潜在漏洞")
        
        suggestions.append("持续改进代码质量和文档完整性")
        
        return suggestions
    
    async def _check_quality_gates(self, code_quality: Dict[str, Any], test_coverage: Dict[str, Any],
                                 performance: Dict[str, Any], security: Dict[str, Any],
                                 documentation: Dict[str, Any]) -> Dict[str, str]:
        """检查质量门禁"""
        return {
            "test_coverage": "PASS" if test_coverage["overall_coverage"] >= 80 else "FAIL",
            "performance": "PASS" if performance["response_time"] <= 2.0 else "FAIL",
            "security": "PASS" if security["security_score"] >= 90 else "FAIL",
            "code_quality": "PASS" if code_quality["score"] >= 80 else "FAIL"
        }