"""
系统集成与测试框架 - System Integration and Testing Framework
==============================================================

提供完整的系统集成和测试解决方案：
- 一键启动脚本
- 集成测试框架
- 系统健康检查
- 模拟数据测试接口

Author: HC20251027
Date: 2025-11-06
"""

from .startup_scripts import SystemStartupManager
from .integration_testing import IntegrationTestFramework
from .health_monitoring import SystemHealthMonitor
from .mock_data_interface import MockDataInterface

__all__ = [
    'SystemStartupManager',
    'IntegrationTestFramework', 
    'SystemHealthMonitor',
    'MockDataInterface'
]

__version__ = '1.0.0'
__author__ = 'HC20251027'