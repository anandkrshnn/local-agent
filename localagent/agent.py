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
from .memory.memory_service import MemoryService
from .trace.decision_trace import DecisionTrace
from .config import Config
from .vault_context import VaultContext

class LocalAgent:
    """The central orchestrator for secure, local tool-use and semantic memory recall."""

    VALID_TOOLS = ["read_file", "write_file", "append_to_file", "list_directory", "query_memory", "search_memory"]

    def __init__(self, model: str = None, config: Config = None, vault_root: Optional[str] = None, password: Optional[str] = None):
        """Initialize agent with optional isolated and encrypted vault."""
        self.config = config or Config.default()
        self.model = model or self.config.default_model
        
        if vault_root is None:
            self.vault = VaultContext.default()
        else:
            self.vault = VaultContext(vault_root)

        # Unlock vault if password provided
        if password:
            self.vault.unlock(password)

        # Sandbox with vault path
        self.sandbox = SandboxPath(root=str(self.vault.sandbox))

        # Broker with vault-specific path and key manager
        self.broker = LocalPermissionBroker(
            audit_log_path=str(self.vault.audit_log),
            key_manager=self.vault.key_manager
        )

        # Memory service with vault paths
        self.memory_service = MemoryService(
            broker=self.broker,
            lancedb_path=str(self.vault.memory_lance),
            duckdb_path=str(self.vault.duckdb_path),
            key_manager=self.vault.key_manager
        )

        # ReAct loop settings
        self.max_iterations = self.config.max_iterations
        self.current_trace = None

        from .adapters.adapter_registry import AdapterRegistry
        self.adapter_registry = AdapterRegistry()

    def chat(self, user_input: str, override_token: str = None) -> Any:
        """Main entry point: Handle user prompt using ReAct loop and semantic context."""
        
        # Record immutable episode
        self.memory_service.lancedb_store.append_episode({
            "event_type": "user_message",
            "content_text": user_input,
            "actor": "user",
            "session_id": getattr(self, "current_session_id", "default"),
        })

        # 1. Governed Semantic Recall
        self.current_trace = DecisionTrace(user_input)
        
        # Record user message in legacy memory for retrieval
        self.memory_service.legacy_memory.remember("user_message", {"content": user_input})
        
        try:
            gov_context = self.memory_service.get_governed_context(user_input, {"session_id": "current"})
            
            context = ""
            if gov_context.get("reason") == "authorized":
                memories = gov_context.get("memories", [])
                for m in memories:
                    self.current_trace.add_retrieved_memory(m)
                context = "\nRELEVANT MEMORIES (Authorized):\n" + "\n".join([f"- {m['body']}" for m in memories])
            else:
                context = "\n⚠️ MEMORY ACCESS RESTRICTED by LPB.\n"

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

IMPORTANT: If the user mentions a file path, asks to save information, or queries the past, USE THE APPROPRIATE TOOL. Only use 'Final Answer' immediately for simple conversational greetings or non-technical chat. Always use the key 'path' for any file or folder argument in tool calls. Never use 'unknown'.

{context}
"""
            
            # 3. Execution Loop (ReAct)
            current_prompt = f"{system_prompt}\nUser: {user_input}\n"
            response = ""
            
            for i in range(self.max_iterations):
                try:
                    response = self._call_llm(current_prompt)
                except Exception as llm_e:
                    response = f"Error: Could not connect to Ollama. Is it running? ({str(llm_e)[:100]})"
                    break

                # Parse Action
                action_match = re.search(r"Action:\s*(\w+)\((.*)\)", response)
                if not action_match:
                    final_match = re.search(r"Final Answer:\s*(.*)", response, re.DOTALL)
                    response = final_match.group(1).strip() if final_match else response.strip()
                    break

                tool_name = action_match.group(1)
                tool_args_str = action_match.group(2).strip()

                if tool_name not in self.VALID_TOOLS:
                    observation = f"Error: Tool '{tool_name}' is not recognized."
                else:
                    try:
                        tool_args = json.loads(tool_args_str)
                        
                        # Tool Execution with Broker
                        observation = self._execute_tool(tool_name, tool_args, override_token)
                        
                        # Reset override_token after first use in the loop to prevent reuse
                        override_token = None
                        
                        # Check for Gated Response
                        if isinstance(observation, dict) and observation.get("requires_confirmation"):
                            # If gated, finalize trace and return dict
                            if self.current_trace:
                                self.current_trace.save_to_jsonl(str(self.vault.decision_traces), key_manager=self.vault.key_manager)
                            return observation 

                    except Exception as e:
                        observation = f"Error executing tool: {str(e)}"

                current_prompt += f"{response}\nObservation: {observation}\n"
            else:
                if not response:
                    response = "Error: Maximum iterations reached"

        except Exception as e:
            response = f"Error during execution: {str(e)}"

        # Finalize and save trace to vault-specific file
        if self.current_trace:
            self.current_trace.set_final_outcome(str(response))
            self.current_trace.save_to_jsonl(str(self.vault.decision_traces), key_manager=self.vault.key_manager)

        # 4. Record the final response episode
        res_episode_id = self.memory_service.lancedb_store.append_episode({
            "event_type": "agent_response",
            "content_text": str(response),
            "actor": "agent",
            "session_id": getattr(self, "current_session_id", "default"),
        })

        # 5. TRIGGER ASYNC PROMOTION (Milestone 4: Governed Memory)
        # In a real system, this would be a separate background task. 
        # For simplicity in v0.2, we trigger it synchronously but logically as a final step.
        self.memory_service.promotion_pipeline.run_cycle(res_episode_id, str(response))

        return response

    def _execute_tool(self, name: str, args: Dict[str, Any], token: str = None) -> Any:
        """Securely execute a tool using the Permission Broker."""
        # Normalize keys to lowercase to handle model variance (e.g., 'Path' instead of 'path')
        norm_args = {k.lower(): v for k, v in args.items()}
        
        # Robust resource extraction
        resource = None
        for key in ["path", "filename", "file", "target", "resource", "directory", "folder", "query", "key", "text"]:
            if key in norm_args and norm_args[key]:
                resource = str(norm_args[key])
                break
        
        if not resource:
            resource = "unknown"
            
        intent = name

        # 1. If no token provided, request permission
        if not token:
            perm = self.broker.request_permission(intent, resource)
            if not perm["granted"]:
                # Inject tool metadata for resumption bridge
                perm["tool_name"] = name
                perm["arguments"] = args
                return perm  # Return the permission requirement dictionary

        # 2. If token provided, validate it
        else:
            if not self.broker.validate_token(intent, resource, token):
                return f"Error: Invalid or expired security token for {intent} on {resource}."

        # 3. Execution logic
        try:
            result = None
            if name == "read_file":
                path = self.sandbox.resolve(args["path"])
                result = path.read_text()
            
            elif name == "write_file":
                path = self.sandbox.resolve(args["path"])
                self.sandbox.ensure_parent(path)
                path.write_text(args["content"])
                self.memory_service.legacy_memory.remember("file_write", {"path": args["path"]})
                result = f"Success: Saved to {args['path']}"

            elif name == "append_to_file":
                path = self.sandbox.resolve(args["path"])
                self.sandbox.ensure_parent(path)
                with open(path, "a", encoding="utf-8") as f:
                    f.write(args["content"] + "\n")
                self.memory_service.legacy_memory.remember("file_append", {"path": args["path"]})
                result = f"Success: Appended to {args['path']}"

            elif name == "list_directory":
                path = self.sandbox.resolve(args.get("path", "."))
                items = os.listdir(path)
                result = f"Contents: {', '.join(items)}"

            elif name in ["query_memory", "search_memory"]:
                # Gemma 2b sometimes uses 'key' or 'text' instead of 'query'
                q = args.get("query") or args.get("key") or args.get("text") or ""
                if not q:
                    result = "Error: No query provided in tool arguments."
                else:
                    results = self.memory_service.legacy_memory.recall_similar(q)
                    result = f"Memory Recall: {json.dumps(results)}"

            if result is None:
                result = f"Error: Implementation for tool '{name}' is missing."

            # --- MILESTONE 4: APPEND TO EPISODE LOG ---
            self.memory_service.lancedb_store.append_episode({
                "event_type": "tool_execution",
                "actor": "agent",
                "tool_name": name,
                "content_text": str(result),
                "content_json": json.dumps({"args": args, "result": str(result)})
            })

            return result

        except Exception as e:
            return f"Error: {str(e)}"

    def get_stats(self) -> Dict[str, Any]:
        return {
            "active_tokens": len(self.broker.active_tokens),
            "pending_confirmations": len(self.broker.pending_confirmations),
            "memory_stats": self.memory_service.legacy_memory.get_stats(),
            "active_model": self.model
        }

    def _call_llm(self, prompt: str) -> str:
        try:
            res = requests.post(
                f"{self.config.ollama_endpoint}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"num_predict": 512, "temperature": 0.1}
                },
                timeout=240,
                proxies={"http": None, "https": None}  # Bypass system proxies for local traffic
            )
            res.raise_for_status()
            return res.json().get("response", "").strip()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Ollama Connection Error: {str(e)} (Target: {self.config.ollama_endpoint})")
        except Exception as e:
            raise Exception(f"LLM Error: {str(e)}")

    def close(self):
        """Release resources when switching vaults."""
        try:
            if hasattr(self, 'memory_service') and self.memory_service is not None:
                self.memory_service.close()
        except:
            pass
        try:
            if hasattr(self, 'broker') and self.broker is not None:
                # Optional: close any open DB connections in broker if needed
                pass
        except:
            pass
