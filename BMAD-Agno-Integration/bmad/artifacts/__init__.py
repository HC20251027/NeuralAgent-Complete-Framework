"""
BMAD-METHOD框架 - 产物模块
包含各种开发产物和文档模板
"""

from .prd_template import PRDTemplate
from .design_template import DesignTemplate
from .code_template import CodeTemplate
from .test_template import TestTemplate

__all__ = ['PRDTemplate', 'DesignTemplate', 'CodeTemplate', 'TestTemplate']