"""
Base classes for plugin development
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from enum import Enum

class PluginType(Enum):
    TOOL = "tool"           # Adds new tool capabilities
    MODEL = "model"         # Adds new model provider
    HOOK = "hook"           # Adds lifecycle hooks
    UI = "ui"               # Adds UI components

class PluginPermission(Enum):
    READ = "read"
    WRITE = "write"
    NETWORK = "network"
    SYSTEM = "system"

@dataclass
class PluginManifest:
    """Plugin metadata"""
    name: str
    version: str
    description: str
    author: str
    type: PluginType
    permissions: List[PluginPermission]
    dependencies: List[str] = field(default_factory=list)
    min_agent_version: str = "4.0.0"
    entry_point: str = "main.py"
    
class Plugin(ABC):
    """Base class for all plugins"""
    
    @abstractmethod
    def initialize(self, agent) -> bool:
        """Initialize plugin with agent instance"""
        pass
    
    @abstractmethod
    def get_tools(self) -> Dict[str, callable]:
        """Return dictionary of tools provided by plugin"""
        pass
    
    def on_load(self):
        """Called when plugin is loaded"""
        pass
    
    def on_unload(self):
        """Called when plugin is unloaded"""
        pass
    
    def get_ui_components(self) -> Dict[str, str]:
        """Return UI components (React components)"""
        return {}
    
    def get_settings_schema(self) -> Dict:
        """Return settings schema for UI configuration"""
        return {}
