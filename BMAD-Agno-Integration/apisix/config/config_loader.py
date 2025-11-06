"""
APISIX网关配置加载器
负责加载和管理配置文件
"""

import json
import yaml
from typing import Dict, List, Any, Optional
from pathlib import Path
import logging
import aiofiles
import asyncio

logger = logging.getLogger(__name__)


class ConfigLoader:
    """配置加载器"""
    
    def __init__(self, config_dir: str = "configs/apisix"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self._config_cache: Dict[str, Any] = {}
        self._watchers: Dict[str, List[callable]] = {}
    
    async def load_config(self, config_file: str) -> Optional[Dict[str, Any]]:
        """加载配置文件"""
        config_path = self.config_dir / config_file
        
        if not config_path.exists():
            logger.warning(f"配置文件不存在: {config_path}")
            return None
        
        try:
            async with aiofiles.open(config_path, 'r', encoding='utf-8') as f:
                content = await f.read()
            
            if config_file.endswith('.yaml') or config_file.endswith('.yml'):
                config = yaml.safe_load(content)
            elif config_file.endswith('.json'):
                config = json.loads(content)
            else:
                logger.error(f"不支持的配置文件格式: {config_file}")
                return None
            
            # 缓存配置
            self._config_cache[config_file] = config
            
            logger.debug(f"配置文件加载成功: {config_file}")
            return config
            
        except Exception as e:
            logger.error(f"加载配置文件失败: {config_file} - {e}")
            return None
    
    async def save_config(self, config: Dict[str, Any], config_file: str) -> bool:
        """保存配置文件"""
        config_path = self.config_dir / config_file
        
        try:
            # 创建目录
            config_path.parent.mkdir(parents=True, exist_ok=True)
            
            async with aiofiles.open(config_path, 'w', encoding='utf-8') as f:
                if config_file.endswith('.yaml') or config_file.endswith('.yml'):
                    content = yaml.dump(config, default_flow_style=False, allow_unicode=True)
                elif config_file.endswith('.json'):
                    content = json.dumps(config, indent=2, ensure_ascii=False)
                else:
                    logger.error(f"不支持的配置文件格式: {config_file}")
                    return False
                
                await f.write(content)
            
            # 更新缓存
            self._config_cache[config_file] = config
            
            # 通知观察者
            await self._notify_watchers(config_file, config)
            
            logger.info(f"配置文件保存成功: {config_file}")
            return True
            
        except Exception as e:
            logger.error(f"保存配置文件失败: {config_file} - {e}")
            return False
    
    async def remove_config(self, config_file: str) -> bool:
        """删除配置文件"""
        config_path = self.config_dir / config_file
        
        try:
            if config_path.exists():
                config_path.unlink()
            
            # 从缓存中移除
            if config_file in self._config_cache:
                del self._config_cache[config_file]
            
            # 通知观察者
            await self._notify_watchers(config_file, None)
            
            logger.info(f"配置文件删除成功: {config_file}")
            return True
            
        except Exception as e:
            logger.error(f"删除配置文件失败: {config_file} - {e}")
            return False
    
    async def load_all_configs(self) -> Dict[str, Any]:
        """加载所有配置文件"""
        configs = {}
        
        for config_file in self.config_dir.glob("*.yaml"):
            if config_file.name != "apisix.yaml":
                config = await self.load_config(config_file.name)
                if config:
                    configs[config_file.stem] = config
        
        return configs
    
    async def load_service_config(self, service_name: str) -> Optional[Dict[str, Any]]:
        """加载服务配置"""
        config_file = f"service_{service_name}.yaml"
        return await self.load_config(config_file)
    
    async def save_service_config(self, service_name: str, service_config: Dict[str, Any]) -> bool:
        """保存服务配置"""
        config_file = f"service_{service_name}.yaml"
        return await self.save_config(service_config, config_file)
    
    async def remove_service_config(self, service_name: str) -> bool:
        """删除服务配置"""
        config_file = f"service_{service_name}.yaml"
        return await self.remove_config(config_file)
    
    async def load_all_services(self) -> Dict[str, Dict[str, Any]]:
        """加载所有服务配置"""
        services = {}
        
        for config_file in self.config_dir.glob("service_*.yaml"):
            service_name = config_file.stem.replace("service_", "")
            config = await self.load_config(config_file.name)
            if config:
                services[service_name] = config
        
        return services
    
    async def load_route_config(self, route_id: str) -> Optional[Dict[str, Any]]:
        """加载路由配置"""
        config_file = f"route_{route_id}.yaml"
        return await self.load_config(config_file)
    
    async def save_route_config(self, route_id: str, route_config: Dict[str, Any]) -> bool:
        """保存路由配置"""
        config_file = f"route_{route_id}.yaml"
        return await self.save_config(route_config, config_file)
    
    async def remove_route_config(self, route_id: str) -> bool:
        """删除路由配置"""
        config_file = f"route_{route_id}.yaml"
        return await self.remove_config(config_file)
    
    async def load_all_routes(self) -> Dict[str, Dict[str, Any]]:
        """加载所有路由配置"""
        routes = {}
        
        for config_file in self.config_dir.glob("route_*.yaml"):
            route_id = config_file.stem.replace("route_", "")
            config = await self.load_config(config_file.name)
            if config:
                routes[route_id] = config
        
        return routes
    
    async def load_plugin_config(self, plugin_name: str) -> Optional[Dict[str, Any]]:
        """加载插件配置"""
        config_file = f"plugin_{plugin_name}.yaml"
        return await self.load_config(config_file)
    
    async def save_plugin_config(self, plugin_name: str, plugin_config: Dict[str, Any]) -> bool:
        """保存插件配置"""
        config_file = f"plugin_{plugin_name}.yaml"
        return await self.save_config(plugin_config, config_file)
    
    async def load_all_plugins(self) -> Dict[str, Dict[str, Any]]:
        """加载所有插件配置"""
        plugins = {}
        
        for config_file in self.config_dir.glob("plugin_*.yaml"):
            plugin_name = config_file.stem.replace("plugin_", "")
            config = await self.load_config(config_file.name)
            if config:
                plugins[plugin_name] = config
        
        return plugins
    
    def register_watcher(self, config_file: str, callback: callable) -> None:
        """注册配置变更观察者"""
        if config_file not in self._watchers:
            self._watchers[config_file] = []
        
        self._watchers[config_file].append(callback)
    
    def unregister_watcher(self, config_file: str, callback: callable) -> None:
        """取消注册配置变更观察者"""
        if config_file in self._watchers:
            try:
                self._watchers[config_file].remove(callback)
            except ValueError:
                pass
    
    async def _notify_watchers(self, config_file: str, config: Optional[Dict[str, Any]]) -> None:
        """通知配置变更观察者"""
        if config_file in self._watchers:
            for callback in self._watchers[config_file]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(config_file, config)
                    else:
                        callback(config_file, config)
                except Exception as e:
                    logger.error(f"配置变更通知失败: {e}")
    
    def get_cached_config(self, config_file: str) -> Optional[Dict[str, Any]]:
        """获取缓存的配置"""
        return self._config_cache.get(config_file)
    
    def clear_cache(self, config_file: Optional[str] = None) -> None:
        """清除配置缓存"""
        if config_file:
            if config_file in self._config_cache:
                del self._config_cache[config_file]
        else:
            self._config_cache.clear()
    
    async def backup_config(self, config_file: str) -> bool:
        """备份配置文件"""
        config_path = self.config_dir / config_file
        backup_path = self.config_dir / f"{config_file}.backup"
        
        try:
            if config_path.exists():
                import shutil
                shutil.copy2(config_path, backup_path)
                logger.info(f"配置文件备份成功: {config_file}")
                return True
            return False
        except Exception as e:
            logger.error(f"配置文件备份失败: {config_file} - {e}")
            return False
    
    async def restore_config(self, config_file: str) -> bool:
        """恢复配置文件"""
        config_path = self.config_dir / config_file
        backup_path = self.config_dir / f"{config_file}.backup"
        
        try:
            if backup_path.exists():
                import shutil
                shutil.copy2(backup_path, config_path)
                logger.info(f"配置文件恢复成功: {config_file}")
                return True
            return False
        except Exception as e:
            logger.error(f"配置文件恢复失败: {config_file} - {e}")
            return False
    
    async def validate_config_file(self, config_file: str) -> Dict[str, Any]:
        """验证配置文件"""
        result = {
            "valid": True,
            "errors": [],
            "warnings": []
        }
        
        config_path = self.config_dir / config_file
        
        if not config_path.exists():
            result["valid"] = False
            result["errors"].append("配置文件不存在")
            return result
        
        try:
            async with aiofiles.open(config_path, 'r', encoding='utf-8') as f:
                content = await f.read()
            
            if config_file.endswith('.yaml') or config_file.endswith('.yml'):
                config = yaml.safe_load(content)
            elif config_file.endswith('.json'):
                config = json.loads(content)
            else:
                result["valid"] = False
                result["errors"].append("不支持的配置文件格式")
                return result
            
            if config is None:
                result["valid"] = False
                result["errors"].append("配置文件为空或格式错误")
                return result
            
            # 基本验证
            if not isinstance(config, dict):
                result["valid"] = False
                result["errors"].append("配置文件必须是对象格式")
                return result
            
        except yaml.YAMLError as e:
            result["valid"] = False
            result["errors"].append(f"YAML格式错误: {e}")
        except json.JSONDecodeError as e:
            result["valid"] = False
            result["errors"].append(f"JSON格式错误: {e}")
        except Exception as e:
            result["valid"] = False
            result["errors"].append(f"文件读取错误: {e}")
        
        return result
    
    def get_config_files(self, pattern: str = "*") -> List[str]:
        """获取配置文件列表"""
        files = []
        for config_file in self.config_dir.glob(pattern):
            if config_file.is_file():
                files.append(config_file.name)
        return sorted(files)