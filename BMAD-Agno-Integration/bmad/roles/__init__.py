"""
BMAD-METHOD框架 - 角色模块
包含5个核心开发角色代理
"""

from .analyst import AnalystAgent
from .pm import ProjectManagerAgent
from .architect import ArchitectAgent
from .developer import DeveloperAgent
from .qa import QAAgent

__all__ = ['AnalystAgent', 'ProjectManagerAgent', 'ArchitectAgent', 'DeveloperAgent', 'QAAgent']