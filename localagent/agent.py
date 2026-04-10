import os
import json
import time
import re
import requests
from pathlib import Path
from typing import Dict, List, Any, Optional

from .broker import LocalPermissionBroker
from .sandbox import SandboxPath
from .memory import MemoryEngine
from .config import Config

class LocalAgent:
    """The central orchestrator for secure, local tool-use and semantic memory recall."""

    VALID_TOOLS = ["read_file", "write_file", "append_to_file", "list_directory", "query_memory", "search_memory"]

    def __init__(self, model: str = None, config: Config = None):
        self.config = config or Config.default()
        self.model = model or self.config.default_model
        
        # Core subsystems
        self.sandbox = SandboxPath(self.config.sandbox_root)
        self.broker = LocalPermissionBroker(db_path=str(self.config.audit_db))
        self.memory = MemoryEngine(db_path=str(self.config.memory_db))

        # ReAct loop settings
        self.max_iterations = self.config.max_iterations

    def chat(self, user_input: str) -> str:
        """Main entry point: Handle user prompt using ReAct loop and semantic context."""
        # 1. Semantic Recall (Augment prompt with relevant memories)
        memories = self.memory.recall_similar(user_input, top_k=3)
        context = ""
        if memories and "error" not in memories[0]:
            context = "\nRELEVANT MEMORIES:\n" + "\n".join([f"- {m['payload']}" for m in memories])

        # 2. System Prompt
        system_prompt = f"""You are 'localagent', a secure AI assistant.
You have access to a local sandbox and a semantic memory.
Available Tools: {', '.join(self.VALID_TOOLS)}

Use the following format:
Thought: your reasoning
Action: tool_name({{"param": "value"}})
Observation: the tool output
... (repeat if needed)
Final Answer: your final response to the user

{context}
"""
        
        # 3. Execution Loop (ReAct)
        current_prompt = f"{system_prompt}\nUser: {user_input}\n"
        
        for i in range(self.max_iterations):
            response = self._call_llm(current_prompt)
            print(f"[THOUGHT] Step {i+1}: {response.split('Action:')[0].strip()}")

            # Parse Action
            action_match = re.search(r"Action:\s*(\w+)\((.*)\)", response)
            if not action_match:
                # No action, looking for Final Answer
                final_match = re.search(r"Final Answer:\s*(.*)", response, re.DOTALL)
                return final_match.group(1).strip() if final_match else response.strip()

            tool_name = action_match.group(1)
            tool_args_str = action_match.group(2).strip()

            # Hallucination Guard: Validate tool name
            if tool_name not in self.VALID_TOOLS:
                observation = f"Error: Tool '{tool_name}' is not recognized. Recognized tools: {', '.join(self.VALID_TOOLS)}"
            else:
                try:
                    tool_args = json.loads(tool_args_str)
                    observation = self._execute_tool(tool_name, tool_args)
                except Exception as e:
                    observation = f"Error executing tool: {str(e)}"

            print(f"[OBSERVATION] {observation}")
            
            # If observation is a security gate, return it immediately to the user
            if "⚠️ Action requires confirmation" in observation:
                return observation

            current_prompt += f"{response}\nObservation: {observation}\n"

        return "Error: Maximum iterations reached without final answer."

    def _execute_tool(self, name: str, args: Dict[str, Any]) -> str:
        """Securely execute a tool using the Permission Broker."""
        # 1. Determine resource and intent
        resource = args.get("path") or args.get("query") or "unknown"
        intent = name

        # 2. Request permission from Broker
        perm = self.broker.request_permission(intent, resource)

        if not perm["granted"]:
            request_id = perm["request_id"]
            return f"⚠️ Action requires confirmation. Tool: {name} on {resource}.\nRequest ID: {request_id}"

        # 3. Execute logic (only with token)
        token = perm.get("token")
        
        try:
            if name == "read_file":
                path = self.sandbox.resolve(args["path"])
                return path.read_text()
            
            elif name == "write_file":
                path = self.sandbox.resolve(args["path"])
                self.sandbox.ensure_parent(path)
                path.write_text(args["content"])
                self.memory.remember("file_write", {"path": args["path"]})
                return f"Success: Saved to {args['path']}"

            elif name == "append_to_file":
                path = self.sandbox.resolve(args["path"])
                self.sandbox.ensure_parent(path)
                with open(path, "a", encoding="utf-8") as f:
                    f.write(args["content"] + "\n")
                self.memory.remember("file_append", {"path": args["path"]})
                return f"Success: Appended to {args['path']}"

            elif name == "list_directory":
                path = self.sandbox.resolve(args.get("path", "."))
                items = os.listdir(path)
                return f"Contents of {args.get('path', '.')}: " + ", ".join(items)

            elif name in ["query_memory", "search_memory"]:
                results = self.memory.recall_similar(args["query"])
                return f"Memory Recall: {json.dumps(results)}"

            return f"Error: Implementation for tool '{name}' is missing."

        except Exception as e:
            return f"Error: {str(e)}"

    def _call_llm(self, prompt: str) -> str:
        """Call the local Ollama instance."""
        try:
            res = requests.post(
                f"{self.config.ollama_endpoint}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"num_predict": 256, "temperature": 0.1}
                }
            )
            return res.json().get("response", "").strip()
        except:
            return "Error: Could not connect to Ollama. Is it running?"
    
    def get_stats(self) -> Dict[str, Any]:
        """Collect and return operational statistics."""
        return {
            "active_tokens": len(self.broker.active_tokens),
            "pending_confirmations": len(self.broker.pending_confirmations),
            "memory_stats": self.memory.get_stats()
        }

    def close(self):
        """Cleanup connections."""
        self.broker.close()
        self.memory.close()
