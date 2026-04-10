"""
Plugin System for Local Agent v4.0
Allows community-contributed tools with auto-discovery
"""

from .base import Plugin, PluginManifest, PluginType, PluginPermission
from .manager import PluginManager

__all__ = ['Plugin', 'PluginManifest', 'PluginType', 'PluginPermission', 'PluginManager']
