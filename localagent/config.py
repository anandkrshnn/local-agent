from pathlib import Path
from dataclasses import dataclass

@dataclass
class Config:
    sandbox_root: Path = Path.home() / "LocalAgentSandbox"
    default_model: str = "phi3:mini"
    ollama_endpoint: str = "http://localhost:11434"
    audit_db: str = "lpb_audit.db"
    memory_db: str = "agent_memory.duckdb"
    max_iterations: int = 4

    @classmethod
    def default(cls):
        return cls()
