"""
Agno多智能体框架 - 管道处理
提供数据处理管道功能
"""

import asyncio
from typing import Dict, List, Optional, Any, Callable, AsyncIterator
from datetime import datetime
import logging

from .workflow_engine import Workflow, WorkflowStep

logger = logging.getLogger(__name__)


class PipelineStage:
    """管道阶段"""
    
    def __init__(
        self,
        stage_id: str,
        name: str,
        processor: Callable,
        config: Optional[Dict[str, Any]] = None,
        input_schema: Optional[Dict[str, Any]] = None,
        output_schema: Optional[Dict[str, Any]] = None
    ):
        self.id = stage_id
        self.name = name
        self.processor = processor
        self.config = config or {}
        self.input_schema = input_schema or {}
        self.output_schema = output_schema or {}
        
        # 统计信息
        self.execution_count = 0
        self.success_count = 0
        self.error_count = 0
        self.total_execution_time = 0.0
    
    async def process(self, input_data: Any) -> Any:
        """处理数据"""
        start_time = datetime.now()
        self.execution_count += 1
        
        try:
            # 验证输入
            if self.input_schema:
                await self._validate_input(input_data)
            
            # 执行处理
            if asyncio.iscoroutinefunction(self.processor):
                result = await self.processor(input_data, self.config)
            else:
                result = self.processor(input_data, self.config)
            
            # 验证输出
            if self.output_schema:
                await self._validate_output(result)
            
            self.success_count += 1
            return result
            
        except Exception as e:
            self.error_count += 1
            logger.error(f"管道阶段处理失败: {self.name} - {e}")
            raise
        finally:
            execution_time = (datetime.now() - start_time).total_seconds()
            self.total_execution_time += execution_time
    
    async def _validate_input(self, data: Any) -> None:
        """验证输入数据"""
        # 简化的验证逻辑
        # 实际应用中应该使用更复杂的模式验证
        pass
    
    async def _validate_output(self, data: Any) -> None:
        """验证输出数据"""
        # 简化的验证逻辑
        # 实际应用中应该使用更复杂的模式验证
        pass
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        success_rate = 0.0
        if self.execution_count > 0:
            success_rate = self.success_count / self.execution_count
        
        avg_execution_time = 0.0
        if self.execution_count > 0:
            avg_execution_time = self.total_execution_time / self.execution_count
        
        return {
            "stage_id": self.id,
            "stage_name": self.name,
            "execution_count": self.execution_count,
            "success_count": self.success_count,
            "error_count": self.error_count,
            "success_rate": success_rate,
            "average_execution_time": avg_execution_time,
            "total_execution_time": self.total_execution_time
        }


class Pipeline:
    """数据处理管道"""
    
    def __init__(
        self,
        pipeline_id: str,
        name: str,
        description: str = "",
        stages: Optional[List[PipelineStage]] = None
    ):
        self.id = pipeline_id
        self.name = name
        self.description = description
        self.stages = stages or []
        
        # 管道状态
        self.is_running = False
        self.created_at = datetime.now()
        
        # 配置
        self.config = {
            "max_concurrent_stages": 3,
            "stage_timeout": 300,  # 5分钟
            "error_handling": "stop",  # stop, continue, retry
            "retry_count": 3,
            "retry_delay": 1.0  # 秒
        }
        
        # 统计信息
        self.stats = {
            "total_executions": 0,
            "successful_executions": 0,
            "failed_executions": 0,
            "total_processed_items": 0,
            "average_execution_time": 0.0
        }
    
    def add_stage(self, stage: PipelineStage) -> None:
        """添加阶段"""
        self.stages.append(stage)
    
    def insert_stage(self, index: int, stage: PipelineStage) -> None:
        """插入阶段"""
        self.stages.insert(index, stage)
    
    def remove_stage(self, stage_id: str) -> bool:
        """移除阶段"""
        for i, stage in enumerate(self.stages):
            if stage.id == stage_id:
                self.stages.pop(i)
                return True
        return False
    
    async def execute(self, input_data: Any) -> Any:
        """执行管道"""
        if not self.stages:
            return input_data
        
        self.is_running = True
        start_time = datetime.now()
        
        try:
            current_data = input_data
            
            for stage in self.stages:
                try:
                    current_data = await stage.process(current_data)
                except Exception as e:
                    if self.config["error_handling"] == "stop":
                        raise
                    elif self.config["error_handling"] == "retry":
                        current_data = await self._retry_stage(stage, current_data)
                    # continue 模式下忽略错误，继续执行
            
            # 更新统计
            execution_time = (datetime.now() - start_time).total_seconds()
            self.stats["total_executions"] += 1
            self.stats["successful_executions"] += 1
            self.stats["total_processed_items"] += 1
            
            # 更新平均执行时间
            total_executions = self.stats["total_executions"]
            current_avg = self.stats["average_execution_time"]
            self.stats["average_execution_time"] = (
                (current_avg * (total_executions - 1) + execution_time) / total_executions
            )
            
            return current_data
            
        except Exception as e:
            self.stats["total_executions"] += 1
            self.stats["failed_executions"] += 1
            
            logger.error(f"管道执行失败: {self.name} - {e}")
            raise
        finally:
            self.is_running = False
    
    async def execute_batch(self, input_data_list: List[Any]) -> List[Any]:
        """批量执行管道"""
        results = []
        
        for input_data in input_data_list:
            try:
                result = await self.execute(input_data)
                results.append(result)
            except Exception as e:
                logger.error(f"批量处理项目失败: {e}")
                if self.config["error_handling"] == "stop":
                    raise
                results.append(None)  # 错误处理策略
        
        return results
    
    async def execute_stream(self, input_stream: AsyncIterator[Any]) -> AsyncIterator[Any]:
        """流式执行管道"""
        async for input_data in input_stream:
            try:
                result = await self.execute(input_data)
                yield result
            except Exception as e:
                logger.error(f"流式处理失败: {e}")
                if self.config["error_handling"] == "stop":
                    raise
                # continue 模式下跳过该项目
    
    async def _retry_stage(self, stage: PipelineStage, input_data: Any) -> Any:
        """重试阶段"""
        for attempt in range(self.config["retry_count"]):
            try:
                return await stage.process(input_data)
            except Exception as e:
                if attempt == self.config["retry_count"] - 1:
                    raise
                await asyncio.sleep(self.config["retry_delay"] * (attempt + 1))
        
        raise Exception(f"阶段重试失败: {stage.name}")
    
    def get_stage(self, stage_id: str) -> Optional[PipelineStage]:
        """获取阶段"""
        for stage in self.stages:
            if stage.id == stage_id:
                return stage
        return None
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取管道统计信息"""
        success_rate = 0.0
        if self.stats["total_executions"] > 0:
            success_rate = self.stats["successful_executions"] / self.stats["total_executions"]
        
        stage_stats = [stage.get_statistics() for stage in self.stages]
        
        return {
            "pipeline_id": self.id,
            "pipeline_name": self.name,
            "description": self.description,
            "stage_count": len(self.stages),
            "is_running": self.is_running,
            "created_at": self.created_at.isoformat(),
            "statistics": self.stats,
            "stage_statistics": stage_stats,
            "config": self.config
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "stages": [
                {
                    "id": stage.id,
                    "name": stage.name,
                    "config": stage.config
                }
                for stage in self.stages
            ],
            "statistics": self.get_statistics()
        }


class PipelineManager:
    """管道管理器"""
    
    def __init__(self):
        self.pipelines: Dict[str, Pipeline] = {}
        self.pipeline_templates: Dict[str, Dict[str, Any]] = {}
        
        # 统计信息
        self.stats = {
            "total_pipelines": 0,
            "active_pipelines": 0,
            "total_executions": 0
        }
    
    def create_pipeline(
        self,
        name: str,
        description: str = "",
        stages: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """创建管道"""
        pipeline_id = f"pipeline_{len(self.pipelines)}"
        
        pipeline_stages = []
        if stages:
            for stage_config in stages:
                stage = PipelineStage(
                    stage_id=stage_config.get("id", f"stage_{len(pipeline_stages)}"),
                    name=stage_config.get("name", "Stage"),
                    processor=stage_config.get("processor", lambda x, c: x),
                    config=stage_config.get("config", {}),
                    input_schema=stage_config.get("input_schema"),
                    output_schema=stage_config.get("output_schema")
                )
                pipeline_stages.append(stage)
        
        pipeline = Pipeline(
            pipeline_id=pipeline_id,
            name=name,
            description=description,
            stages=pipeline_stages
        )
        
        self.pipelines[pipeline_id] = pipeline
        self.stats["total_pipelines"] += 1
        
        return pipeline_id
    
    def get_pipeline(self, pipeline_id: str) -> Optional[Pipeline]:
        """获取管道"""
        return self.pipelines.get(pipeline_id)
    
    def delete_pipeline(self, pipeline_id: str) -> bool:
        """删除管道"""
        if pipeline_id in self.pipelines:
            del self.pipelines[pipeline_id]
            return True
        return False
    
    async def execute_pipeline(self, pipeline_id: str, input_data: Any) -> Any:
        """执行管道"""
        pipeline = self.get_pipeline(pipeline_id)
        if not pipeline:
            raise ValueError(f"管道不存在: {pipeline_id}")
        
        return await pipeline.execute(input_data)
    
    async def execute_pipeline_batch(self, pipeline_id: str, input_data_list: List[Any]) -> List[Any]:
        """批量执行管道"""
        pipeline = self.get_pipeline(pipeline_id)
        if not pipeline:
            raise ValueError(f"管道不存在: {pipeline_id}")
        
        return await pipeline.execute_batch(input_data_list)
    
    async def execute_pipeline_stream(self, pipeline_id: str, input_stream: AsyncIterator[Any]) -> AsyncIterator[Any]:
        """流式执行管道"""
        pipeline = self.get_pipeline(pipeline_id)
        if not pipeline:
            raise ValueError(f"管道不存在: {pipeline_id}")
        
        return pipeline.execute_stream(input_stream)
    
    def register_pipeline_template(self, template_id: str, template: Dict[str, Any]) -> None:
        """注册管道模板"""
        self.pipeline_templates[template_id] = template
    
    def create_pipeline_from_template(self, template_id: str, name: str, 
                                    description: str = "", **kwargs) -> str:
        """从模板创建管道"""
        if template_id not in self.pipeline_templates:
            raise ValueError(f"模板不存在: {template_id}")
        
        template = self.pipeline_templates[template_id]
        
        # 应用模板参数
        stages = template.get("stages", [])
        for stage_config in stages:
            for key, value in kwargs.items():
                if f"{{{key}}}" in str(stage_config):
                    stage_config = {k: v.replace(f"{{{key}}}", str(value)) 
                                  for k, v in stage_config.items()}
        
        return self.create_pipeline(name, description, stages)
    
    def get_all_pipelines(self) -> List[Dict[str, Any]]:
        """获取所有管道"""
        return [pipeline.to_dict() for pipeline in self.pipelines.values()]
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取管理器统计信息"""
        active_count = sum(1 for pipeline in self.pipelines.values() if pipeline.is_running)
        
        return {
            "total_pipelines": self.stats["total_pipelines"],
            "active_pipelines": active_count,
            "total_executions": self.stats["total_executions"],
            "pipeline_templates": len(self.pipeline_templates)
        }


# 预定义的管道模板
PIPELINE_TEMPLATES = {
    "data_processing": {
        "name": "数据处理管道",
        "description": "通用的数据处理管道",
        "stages": [
            {
                "id": "validation",
                "name": "数据验证",
                "processor": "validate_data",
                "config": {"schema": "input_schema"}
            },
            {
                "id": "transformation",
                "name": "数据转换",
                "processor": "transform_data",
                "config": {"rules": "transformation_rules"}
            },
            {
                "id": "enrichment",
                "name": "数据丰富",
                "processor": "enrich_data",
                "config": {"sources": "enrichment_sources"}
            },
            {
                "id": "output",
                "name": "输出格式化",
                "processor": "format_output",
                "config": {"format": "output_format"}
            }
        ]
    },
    
    "ml_pipeline": {
        "name": "机器学习管道",
        "description": "机器学习模型处理管道",
        "stages": [
            {
                "id": "preprocessing",
                "name": "数据预处理",
                "processor": "preprocess_data",
                "config": {"steps": "preprocessing_steps"}
            },
            {
                "id": "feature_engineering",
                "name": "特征工程",
                "processor": "engineer_features",
                "config": {"methods": "feature_methods"}
            },
            {
                "id": "model_inference",
                "name": "模型推理",
                "processor": "model_predict",
                "config": {"model": "model_config"}
            },
            {
                "id": "postprocessing",
                "name": "结果后处理",
                "processor": "postprocess_results",
                "config": {"rules": "postprocessing_rules"}
            }
        ]
    }
}