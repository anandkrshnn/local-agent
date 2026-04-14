import os
from pathlib import Path
from dataclasses import dataclass, field

@dataclass
class Config:
    sandbox_root: Path = field(default_factory=lambda: Path(os.getenv("LOCAL_AGENT_SANDBOX", Path.home() / "LocalAgentSandbox")))
    default_model: str = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")
    ollama_endpoint: str = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")
    audit_db: str = os.getenv("LOCAL_AGENT_AUDIT_DB", "lpb_audit.db")
    memory_db: str = os.getenv("LOCAL_AGENT_MEMORY_DB", "agent_memory.duckdb")
    max_iterations: int = 4

    @classmethod
    def default(cls):
        return cls()
