"""Tool registry for agent capabilities"""

from typing import Dict, Any, Callable
from dataclasses import dataclass, field
from enum import Enum

class ToolRisk(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class ToolDefinition:
    name: str
    description: str
    handler: Callable
    risk: ToolRisk
    requires_confirmation: bool = False
    parameters: Dict[str, Any] = field(default_factory=dict)

class ToolRegistry:
    """Registry for all agent tools"""
    
    def __init__(self, agent):
        self.agent = agent
        self.tools: Dict[str, ToolDefinition] = {}
        self._register_default_tools()
    
    def _register_default_tools(self):
        """Register all available tools"""
        from .file_ops import FileTools
        from .web_tools import WebTools
        from .comms import CommsTools
        from .system import SystemTools
        
        file_tools = FileTools(self.agent)
        web_tools = WebTools(self.agent)
        comms_tools = CommsTools(self.agent)
        system_tools = SystemTools(self.agent)
        
        # File operations
        self.register(ToolDefinition(
            name="read_file",
            description="Read contents of a file",
            handler=file_tools.read_file,
            risk=ToolRisk.LOW,
            requires_confirmation=False,
            parameters={"path": "string"}
        ))
        
        self.register(ToolDefinition(
            name="write_file",
            description="Write content to a file",
            handler=file_tools.write_file,
            risk=ToolRisk.MEDIUM,
            requires_confirmation=True,
            parameters={"path": "string", "content": "string"}
        ))
        
        # Web tools
        self.register(ToolDefinition(
            name="web_search",
            description="Search the web for information",
            handler=web_tools.web_search,
            risk=ToolRisk.LOW,
            requires_confirmation=False,
            parameters={"query": "string"}
        ))
        
        self.register(ToolDefinition(
            name="http_request",
            description="Make HTTP requests to APIs",
            handler=web_tools.http_request,
            risk=ToolRisk.MEDIUM,
            requires_confirmation=True,
            parameters={"method": "string", "url": "string", "body": "string (optional)"}
        ))
        
        # Communication
        self.register(ToolDefinition(
            name="send_email",
            description="Send an email",
            handler=comms_tools.send_email,
            risk=ToolRisk.HIGH,
            requires_confirmation=True,
            parameters={"to": "string", "subject": "string", "body": "string"}
        ))
        
        # System (safe only)
        self.register(ToolDefinition(
            name="run_command",
            description="Run a safe system command (whitelisted)",
            handler=system_tools.run_command_safe,
            risk=ToolRisk.HIGH,
            requires_confirmation=True,
            parameters={"command": "string"}
        ))
    
    def register(self, tool: ToolDefinition):
        """Register a new tool"""
        self.tools[tool.name] = tool
    
    def get(self, name: str) -> ToolDefinition:
        """Get tool by name"""
        return self.tools.get(name)
    
    def list_tools(self) -> Dict[str, str]:
        """List all tools with descriptions"""
        return {name: tool.description for name, tool in self.tools.items()}
