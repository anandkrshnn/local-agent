"""Local Agent v4.0 - Main Orchestrator"""

import os
import uuid
import time
import json
import re
from typing import Dict, Any, Optional, List

from .broker import LocalPermissionBroker
from .memory import VectorMemory
from .sandbox import SandboxPath
from .trace import TraceLogger
from .orchestrator import AgentOrchestrator
from .semantic_router import semantic_router, IntentType
from ..plugins.manager import PluginManager
from ..models.router import ModelRouter
from ..tools.registry import ToolRegistry, ToolRisk

class LocalAgent:
    """Production-ready local agent v4.0 with multi-model and expanded tools"""
    
    def __init__(self, 
                 model: str = "phi3:mini",
                 sandbox_root: str = None,
                 verbose: bool = True):
        
        self.trace = TraceLogger(verbose)
        self.broker = LocalPermissionBroker(learning_enabled=True)
        self.memory = VectorMemory()
        self.sandbox = SandboxPath(sandbox_root)
        self.model_router = ModelRouter()
        self.tool_registry = ToolRegistry(self)
        self.orchestrator = AgentOrchestrator(self)
        self.semantic_router = semantic_router
        self.use_semantic_routing = True
        
        # Plugin System (Sprint 3)
        self.plugin_manager = PluginManager()
        self.plugin_manager.initialize_plugins(self)
        
        self.trace.thinking(f"Agent v4.0 initialized. Router and Plugins ready.")
    
    def chat(self, user_input: str) -> str:
        """Process user input with rule-based routing and model fallback"""
        
        # 1. Record the interaction
        self.memory.store("user_input", {"text": user_input})
        
        # 2. Check for simple conversations (direct routing)
        simple_patterns = ["hello", "hi", "greeting", "who are you", "what can you do", "help"]
        input_lower = user_input.lower().strip()
        
        if any(input_lower == p for p in simple_patterns) or \
           any(input_lower.startswith(p + " ") for p in simple_patterns):
            self.trace.thinking("Simple conversation detected (Direct Route)")
            response = self.model_router.route(user_input)
            return response.content
            
        # 3. Semantic Routing (Sprint 2)
        if self.use_semantic_routing:
            self.trace.thinking("Routing intent via Semantic Router...")
            intent_result = self.semantic_router.route(user_input)
            
            if intent_result.intent != IntentType.CHAT and intent_result.intent != IntentType.UNKNOWN:
                self.trace.thinking(f"Detected Intent: {intent_result.intent.value} ({intent_result.method})")
                return self._dispatch_intent(intent_result)

        # 4. Default: Model Router
        self.trace.thinking("No specific tool intent. Consulting Model Router.")
        response = self.model_router.route(user_input)
        return response.content

    def _dispatch_intent(self, result) -> str:
        """Dispatch intent to appropriate tool handler"""
        intent = result.intent
        params = result.extracted_params
        
        if intent == IntentType.READ_FILE:
            return self._handle_direct_tool("read_file", params.get("path", params.get("raw", "")))
        elif intent == IntentType.WRITE_FILE:
            return self._handle_direct_tool("write_file", f"write '{params.get('content', '')}' to {params.get('path', '')}")
        elif intent == IntentType.SEARCH_MEMORY:
            return self._handle_direct_tool("search_memory", params.get("query", params.get("raw", "")))
        elif intent == IntentType.WEB_SEARCH:
            return self._handle_direct_tool("web_search", params.get("query", params.get("raw", "")))
        elif intent == IntentType.HELP:
            return self._handle_help_intent()
            
        return self.chat(result.raw_input) # Fallback

    def _handle_help_intent(self) -> str:
        return """I can help you with:
- Reading files: "read test.txt"
- Writing files: "write 'content' to file.txt"
- Searching memory: "search memory for history"
- Web search: "search web for news"
- Multi-step tasks: "Build a data pipeline" (orchestrator)"""

    def _handle_direct_tool(self, tool_name: str, user_input: str) -> str:
        """Helper to handle common tool requests via rules or plugins"""
        # First check plugin tools (Sprint 3)
        plugin_tools = self.plugin_manager.get_all_tools()
        if tool_name in plugin_tools:
            self.trace.thinking(f"Executing Plugin Tool: {tool_name}")
            return plugin_tools[tool_name](user_input)

        # Fallback to Registry Tools (Legacy)
        tool = self.tool_registry.get(tool_name)
        if not tool:
            return f"Error: Tool '{tool_name}' not found."
            
        # Extract resource based on tool
        resource = ""
        args = {}
        
        if tool_name == "read_file":
            match = re.search(r'(?:read\s+)?([\w-]+\.(?:txt|md|json|log))', user_input.lower())
            resource = match.group(1) if match else "unknown"
            args = {"path": resource}
            
        elif tool_name == "write_file":
            match = re.search(r'(?:write|create)\s+[\'"]?([^\'"]+)[\'"]?\s+(?:to\s+)?[\'"]?([^\'"]+)[\'"]?', user_input)
            if match:
                args = {"content": match.group(1), "path": match.group(2)}
                resource = args["path"]
            else:
                return "Usage: write 'content' to 'file.txt'"
                
        elif tool_name == "web_search":
            match = re.search(r'(?:search\s+web\s+for\s+)?[\'"]?([^\'"]+)[\'"]?', user_input.lower())
            resource = match.group(1) if match else "unknown"
            args = {"query": resource}
            
        elif tool_name == "search_memory":
            match = re.search(r'(?:search\s+memory\s+for\s+)?[\'"]?([^\'"]+)[\'"]?', user_input.lower())
            resource = match.group(1) if match else "unknown"
            # Actual implementation might use keyword search
            return self._handle_memory_search(resource)

        # Permission check
        perm_request = {
            "request_id": str(uuid.uuid4()),
            "intent": tool_name,
            "resource": resource,
            "context": {"args": args}
        }
        
        perm_response = self.broker.request_permission(perm_request)
        
        if not perm_response["granted"]:
            if perm_response.get("requires_confirmation"):
                return f"⚠️ Action '{tool_name}' requires confirmation.\nRequest ID: {perm_response.get('request_id')}\nType '/confirm {perm_response.get('request_id')}' to approve."
            return f"❌ Permission denied: {perm_response.get('reason')}"
            
        # Execute tool
        try:
            # Pass the token as required by tool handlers
            args["token"] = perm_response["token"]
            result = tool.handler(**args)
            return result
        except Exception as e:
            return f"❌ Tool execution failed: {e}"

    def _handle_memory_search(self, term: str) -> str:
        """Legacy search handler ported to tool architecture"""
        results = self.memory.search_keyword(term, limit=5)
        if not results:
            return f"No results found for '{term}'"
        
        output = [f"🔍 Found {len(results)} results in memory:"]
        for r in results:
            output.append(f"  • [{r['type']}] {str(r['data'])[:100]}")
        return "\n".join(output)

    def confirm_action(self, request_id: str, approved: bool) -> str:
        """Confirm a pending action"""
        result = self.broker.confirm_permission(request_id, approved)
        if result.get("confirmed"):
            return "✅ Action confirmed. Please repeat your request."
        return f"❌ {result.get('reason', 'Action rejected')}"

    async def execute_goal(self, goal: str, max_tasks: int = 10) -> Dict[str, Any]:
        """
        Execute a complex goal using multi-step planning
        """
        # Plan
        plan = await self.orchestrator.plan(goal, max_tasks)
        
        # Execute
        results = await self.orchestrator.execute(plan)
        
        return results
    
    def execute_goal_sync(self, goal: str, max_tasks: int = 10) -> Dict[str, Any]:
        """Synchronous wrapper for execute_goal"""
        import asyncio
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
        
        if loop and loop.is_running():
            # Already in async context, handle nest_asyncio if needed
            # For simplicity in this environment, we use a separate thread or similar
            # but usually, we just call the async version in an async app.
            return asyncio.run_coroutine_threadsafe(
                self.execute_goal(goal, max_tasks), 
                loop
            ).result()
        else:
            return asyncio.run(self.execute_goal(goal, max_tasks))

    def get_stats(self) -> Dict:
        return {
            "memory": self.memory.get_stats(),
            "audit": self.broker.get_audit_summary(),
            "model_router": self.model_router.get_status(),
            "sandbox_files": len(self.sandbox.list_sandbox())
        }

def cli_main():
    """Simple CLI for Local Agent v4.0"""
    agent = LocalAgent()
    print("🤖 Local Agent v4.0 CLI")
    print("Type '/exit' to quit, '/stats' for system info.")
    
    while True:
        try:
            user_input = input("\n👤 > ").strip()
            if not user_input: continue
            if user_input.lower() == '/exit': break
            if user_input.lower() == '/stats':
                print(json.dumps(agent.get_stats(), indent=2))
                continue
                
            if user_input.startswith('/confirm'):
                parts = user_input.split()
                if len(parts) > 1:
                    print(agent.confirm_action(parts[1], True))
                continue
                
            response = agent.chat(user_input)
            print(f"\n🤖 {response}")
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    cli_main()
