"""
Built-in Web Search Plugin
"""

from ..base import Plugin, PluginManifest, PluginType, PluginPermission
from local_agent.tools.web_tools import WebTools

class WebSearchPlugin(Plugin):
    manifest = PluginManifest(
        name="web_search",
        version="1.0.0",
        description="Search the web for information",
        author="Local Agent Team",
        type=PluginType.TOOL,
        permissions=[PluginPermission.NETWORK]
    )
    
    def initialize(self, agent) -> bool:
        self.agent = agent
        self.web_tools = WebTools(agent)
        return True
    
    def get_tools(self):
        return {
            "web_search": self._web_search_wrapper
        }
    
    def _web_search_wrapper(self, query: str, token: str = None) -> str:
        """Wrapper for web search tool"""
        return self.web_tools.web_search(query, token)
    
    def on_load(self):
        print("Web Search plugin loaded")
