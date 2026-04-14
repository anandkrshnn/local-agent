import os
from pathlib import Path
from dataclasses import dataclass

@dataclass
class Config:
    sandbox_root: Path = Path.home() / "LocalAgentSandbox"
    default_model: str = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")
    ollama_endpoint: str = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")
    audit_db: str = "lpb_audit.db"
    memory_db: str = "agent_memory.duckdb"
    max_iterations: int = 4

    @classmethod
    def default(cls):
        return cls()
