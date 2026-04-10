"""Tool Registry and Execution Framework for localagent"""

from typing import Dict, Any, Callable, List
from enum import Enum
from dataclasses import dataclass

class ToolRisk(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

@dataclass
class ToolDefinition:
    name: str
    description: str
    handler: Callable
    risk_level: ToolRisk
    parameters: Dict[str, str]

class ToolRegistry:
    """Central registry for all agent tools"""
    
    def __init__(self):
        self.tools: Dict[str, ToolDefinition] = {}
    
    def register(self, tool: ToolDefinition):
        """Register a new tool"""
        self.tools[tool.name] = tool
    
    def get(self, name: str) -> ToolDefinition:
        """Get tool by name"""
        return self.tools.get(name)
    
    def list_tools(self) -> Dict[str, str]:
        """List all tools with descriptions"""
        return {name: tool.description for name, tool in self.tools.items()}

# Common Tool Handlers (Safe Implementation)

def read_file_handler(path: str, token: str = None) -> str:
    from ..sandbox import SandboxPath
    # Token validation happens in the agent before calling this
    try:
        sandbox = SandboxPath()
        return sandbox.secure_read(path)
    except Exception as e:
        return f"Error reading file: {e}"

def write_file_handler(path: str, content: str, token: str = None) -> str:
    from ..sandbox import SandboxPath
    try:
        sandbox = SandboxPath()
        sandbox.secure_write(path, content)
        return f"Successfully wrote {len(content)} characters to {path}"
    except Exception as e:
        return f"Error writing file: {e}"

# Global registry and default setup
registry = ToolRegistry()
registry.register(ToolDefinition(
    name="read_file",
    description="Read content from a safely sandboxed file.",
    handler=read_file_handler,
    risk_level=ToolRisk.LOW,
    parameters={"path": "string"}
))
registry.register(ToolDefinition(
    name="write_file",
    description="Write content to a file in the sandbox.",
    handler=write_file_handler,
    risk_level=ToolRisk.MEDIUM,
    parameters={"path": "string", "content": "string"}
))
