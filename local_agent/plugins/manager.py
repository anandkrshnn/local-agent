"""
Plugin Manager - Loads, manages, and orchestrates plugins
"""

import importlib
import inspect
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field

from .base import Plugin, PluginManifest, PluginType, PluginPermission

@dataclass
class PluginInfo:
    """Information about loaded plugin"""
    manifest: PluginManifest
    instance: Plugin
    enabled: bool = True
    error: Optional[str] = None

class PluginManager:
    """
    Manages all plugins: discovery, loading, unloading, and tool registration
    """
    
    def __init__(self, plugins_dir: str = None):
        if plugins_dir is None:
            plugins_dir = os.path.expanduser("~/.local-agent-v4/plugins")
        self.plugins_dir = Path(plugins_dir)
        self.plugins: Dict[str, PluginInfo] = {}
        self.plugins_dir.mkdir(parents=True, exist_ok=True)
        
        # Create built-in plugins directory
        self.builtins_dir = Path(__file__).parent / "builtins"
        self.builtins_dir.mkdir(exist_ok=True)
    
    def initialize_plugins(self, agent):
        """Load and initialize all plugins"""
        self._load_builtin_plugins(agent)
        self.discover_plugins(agent)
    
    def _load_builtin_plugins(self, agent):
        """Load built-in plugins that ship with the agent"""
        try:
            from .builtins.web_search import WebSearchPlugin
            plugin = WebSearchPlugin()
            plugin.initialize(agent)
            self.register_plugin(plugin)
        except Exception as e:
            print(f"Failed to load builtin web_search: {e}")
            
        try:
            from .builtins.calculator import CalculatorPlugin
            plugin = CalculatorPlugin()
            plugin.initialize(agent)
            self.register_plugin(plugin)
        except Exception as e:
            print(f"Failed to load builtin calculator: {e}")
    
    def register_plugin(self, plugin: Plugin) -> bool:
        """Register a plugin instance"""
        manifest = getattr(plugin, 'manifest', None)
        if not manifest:
            if hasattr(plugin.__class__, 'manifest'):
                manifest = plugin.__class__.manifest
            else:
                return False
        
        self.plugins[manifest.name] = PluginInfo(
            manifest=manifest,
            instance=plugin
        )
        return True
    
    def discover_plugins(self, agent) -> List[str]:
        """Discover plugins from plugins directory"""
        discovered = []
        
        if not self.plugins_dir.exists():
            return discovered

        for plugin_dir in self.plugins_dir.iterdir():
            if plugin_dir.is_dir():
                manifest_file = plugin_dir / "manifest.json"
                if manifest_file.exists():
                    try:
                        with open(manifest_file) as f:
                            manifest_data = json.load(f)
                        
                        sys.path.insert(0, str(plugin_dir))
                        module_name = manifest_data['entry_point'].replace('.py', '')
                        module = importlib.import_module(module_name)
                        
                        for name, obj in inspect.getmembers(module):
                            if inspect.isclass(obj) and issubclass(obj, Plugin) and obj != Plugin:
                                plugin_instance = obj()
                                plugin_instance.initialize(agent)
                                self.register_plugin(plugin_instance)
                                discovered.append(manifest_data['name'])
                                break
                    except Exception as e:
                        print(f"Failed to load plugin {plugin_dir.name}: {e}")
        
        return discovered
    
    def get_all_tools(self) -> Dict[str, callable]:
        """Get all tools from all enabled plugins"""
        tools = {}
        for name, info in self.plugins.items():
            if info.enabled and not info.error:
                try:
                    plugin_tools = info.instance.get_tools()
                    tools.update(plugin_tools)
                except Exception as e:
                    info.error = str(e)
        return tools
    
    def get_status(self) -> Dict:
        """Get plugin system status"""
        return {
            "total_plugins": len(self.plugins),
            "enabled_plugins": sum(1 for p in self.plugins.values() if p.enabled),
            "plugins": [
                {
                    "name": info.manifest.name,
                    "version": info.manifest.version,
                    "description": info.manifest.description,
                    "enabled": info.enabled,
                    "error": info.error
                }
                for info in self.plugins.values()
            ]
        }
