"""
Plugin Marketplace - Discovery and Installation
Fetches plugins from official registry or local catalog
"""

import os
import json
import requests
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path

from local_agent.core.db import db_manager

# Configuration
MARKETPLACE_URL = os.getenv("MARKETPLACE_URL", "https://registry.local-agent.com/plugins.json")
USE_REMOTE_REGISTRY = os.getenv("USE_REMOTE_REGISTRY", "false").lower() == "true"

logger = logging.getLogger(__name__)

class PluginMarketplace:
    """Manages plugin discovery, installation, and updates using unified DB"""
    
    def fetch_available_plugins(self) -> List[Dict]:
        """Fetch list of available plugins from registry"""
        if USE_REMOTE_REGISTRY:
            try:
                response = requests.get(MARKETPLACE_URL, timeout=10)
                if response.status_code == 200:
                    return response.json()
            except Exception as e:
                logger.warning(f"Failed to fetch remote registry: {e}")
        
        # Fallback to local catalog
        return self._get_local_catalog()
    
    def _get_local_catalog(self) -> List[Dict]:
        """Get local plugin catalog (built-in + discovered)"""
        plugins = []
        
        # Built-in plugins
        builtins = [
            {
                "plugin_id": "calculator",
                "name": "Calculator",
                "version": "1.0.0",
                "author": "Local Agent Team",
                "description": "Perform mathematical calculations",
                "repository_url": "builtin",
                "category": "utility"
            },
            {
                "plugin_id": "web_search",
                "name": "Web Search",
                "version": "1.0.0",
                "author": "Local Agent Team",
                "description": "Search the web for information",
                "repository_url": "builtin",
                "category": "web"
            }
        ]
        
        plugins.extend(builtins)
        
        # Discovered plugins from plugins directory
        plugins_dir = Path(__file__).parent
        for plugin_dir in plugins_dir.iterdir():
            if plugin_dir.is_dir() and plugin_dir.name not in ['builtins', '__pycache__']:
                manifest_file = plugin_dir / "manifest.json"
                if manifest_file.exists():
                    try:
                        with open(manifest_file) as f:
                            manifest = json.load(f)
                            manifest['plugin_id'] = plugin_dir.name
                            plugins.append(manifest)
                    except:
                        pass
        
        return plugins
    
    def install_plugin(self, user_id: int, plugin_id: str) -> bool:
        """Install a plugin for a user using unified connection pool"""
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            # Check if already installed
            cursor.execute("SELECT 1 FROM user_plugins WHERE user_id = ? AND plugin_id = ?", 
                           (user_id, plugin_id))
            if cursor.fetchone():
                return False
            
            # Install
            cursor.execute("""
                INSERT INTO user_plugins (user_id, plugin_id, installed_at, is_active)
                VALUES (?, ?, ?, ?)
            """, (user_id, plugin_id, datetime.utcnow().timestamp(), 1))
            
            # Update registry download count
            cursor.execute("""
                UPDATE plugin_registry SET downloads = downloads + 1 WHERE plugin_id = ?
            """, (plugin_id,))
            
            conn.commit()
        
        # Actually download/install plugin code
        return self._download_plugin(plugin_id)
    
    def _download_plugin(self, plugin_id: str) -> bool:
        """Download plugin code from repository"""
        # Get plugin info
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT repository_url FROM plugin_registry WHERE plugin_id = ?", (plugin_id,))
            row = cursor.fetchone()
        
        if not row or not row['repository_url'] or row['repository_url'] == 'builtin':
            return True  # Built-in plugins already available
        
        # Clone/pull from git repository
        import subprocess
        plugins_dir = Path(__file__).parent / plugin_id
        
        if plugins_dir.exists():
            # Update existing
            subprocess.run(["git", "-C", str(plugins_dir), "pull"], capture_output=True)
        else:
            # Clone new
            subprocess.run(["git", "clone", row['repository_url'], str(plugins_dir)], capture_output=True)
        
        return True
    
    def uninstall_plugin(self, user_id: int, plugin_id: str) -> bool:
        """Uninstall a plugin for a user"""
        db_manager.execute(
            "DELETE FROM user_plugins WHERE user_id = ? AND plugin_id = ?",
            (user_id, plugin_id)
        )
        return True
    
    def get_user_plugins(self, user_id: int) -> List[Dict]:
        """Get installed plugins for a user from unified DB"""
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT p.*, up.installed_at, up.is_active, up.settings
                FROM user_plugins up
                JOIN plugin_registry p ON up.plugin_id = p.plugin_id
                WHERE up.user_id = ?
            """, (user_id,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def toggle_plugin(self, user_id: int, plugin_id: str, active: bool) -> bool:
        """Enable or disable a plugin"""
        db_manager.execute(
            "UPDATE user_plugins SET is_active = ? WHERE user_id = ? AND plugin_id = ?",
            (1 if active else 0, user_id, plugin_id)
        )
        return True

plugin_marketplace = PluginMarketplace()
