import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class VaultContext:
    """Manages isolated storage for one Sovereign Vault (user/session)."""
    vault_root: str = field(default_factory=lambda: os.getenv("LOCAL_AGENT_VAULT", "~/local_agent"))

    def __post_init__(self):
        self.vault_root = Path(self.vault_root).expanduser().resolve()
        self.vault_root.mkdir(parents=True, exist_ok=True)

        # Derived paths
        self.sandbox = self.vault_root / "sandbox"
        self.audit_log = self.vault_root / "audit_log.jsonl"
        self.memory_lance = self.vault_root / "memory.lance"
        self.policies_json = self.vault_root / "policies.json"
        self.decision_traces = self.vault_root / "decision_traces.jsonl"
        self.duckdb_path = self.vault_root / "agent_memory.duckdb"

        # Key manager (initialized via unlock)
        self.key_manager = None

        # Create required directories
        self.sandbox.mkdir(parents=True, exist_ok=True)
        self.memory_lance.mkdir(parents=True, exist_ok=True)

    def unlock(self, password: Optional[str] = None):
        """Unlock the vault with a password."""
        from .vault_key_manager import VaultKeyManager
        self.key_manager = VaultKeyManager(self.vault_root, password)

    @classmethod
    def default(cls) -> "VaultContext":
        """Default single-user vault (backward compatible)."""
        return cls("~/local_agent")
