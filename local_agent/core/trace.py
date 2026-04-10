"""Trace Logging for Agent Decisions"""

import time
from typing import Dict, Any, List, Optional
from enum import Enum

class AgentState(Enum):
    THINKING = "thinking"
    REQUESTING_PERMISSION = "requesting_permission"
    EXECUTING_TOOL = "executing_tool"
    RESPONDING = "responding"
    AWAITING_CONFIRMATION = "awaiting_confirmation"

class TraceLogger:
    """Provides visibility into agent's decision process"""
    
    COLORS = {
        "thinking": "\033[94m",
        "tool": "\033[92m",
        "permission": "\033[93m",
        "error": "\033[91m",
        "result": "\033[96m",
        "reset": "\033[0m"
    }
    
    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self.trace_log = []
    
    def log(self, state: AgentState, message: str, data: Any = None):
        if not self.verbose:
            return
        
        color = self.COLORS.get(state.value, self.COLORS["reset"])
        print(f"{color}[{state.value.upper()}]{self.COLORS['reset']} {message}")
        
        if data:
            print(f"   └─ {str(data)[:200]}")
        
        self.trace_log.append({
            "timestamp": time.time(),
            "state": state.value,
            "message": message,
            "data": data
        })
    
    def thinking(self, message: str):
        self.log(AgentState.THINKING, f"🤔 {message}")
    
    def tool_call(self, tool: str, args: Dict):
        self.log(AgentState.EXECUTING_TOOL, f"🔧 Calling {tool}", args)
    
    def permission_check(self, intent: str, resource: str, granted: bool):
        status = "✅ GRANTED" if granted else "❌ DENIED"
        self.log(AgentState.REQUESTING_PERMISSION, f"🔐 {status}: {intent} on {resource}")
    
    def result(self, message: str, data: Any = None):
        self.log(AgentState.RESPONDING, f"📝 {message}", data)
    
    def error(self, message: str):
        self.log(AgentState.THINKING, f"⚠️ {message}")
    
    def get_trace(self) -> List[Dict]:
        return self.trace_log
