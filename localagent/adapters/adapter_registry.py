from typing import Dict, Any, Optional
from datetime import datetime
import uuid

class AdapterRegistry:
    """Lightweight registry for optional LoRA adapters in v0.2."""

    def __init__(self):
        self.adapters: Dict[str, Dict] = {}   # adapter_id -> metadata

    def register_adapter(self, name: str, description: str, risk_level: str = "low") -> str:
        """Register a new adapter."""
        adapter_id = str(uuid.uuid4())
        self.adapters[adapter_id] = {
            "adapter_id": adapter_id,
            "name": name,
            "description": description,
            "risk_level": risk_level,
            "status": "registered",
            "created_at": datetime.utcnow().isoformat(),
            "last_used": None
        }
        print(f"[AdapterRegistry] Registered adapter '{name}' (ID: {adapter_id}, risk: {risk_level})")
        return adapter_id

    def activate_adapter(self, adapter_id: str, lpb_approval: bool = False) -> bool:
        """Activate an adapter only if LPB approves."""
        if adapter_id not in self.adapters:
            print(f"[AdapterRegistry] Adapter {adapter_id} not found")
            return False

        if not lpb_approval:
            print(f"[AdapterRegistry] Activation denied for {adapter_id} - no LPB approval")
            return False

        self.adapters[adapter_id]["status"] = "active"
        self.adapters[adapter_id]["last_used"] = datetime.utcnow().isoformat()
        print(f"[AdapterRegistry] Adapter {adapter_id} ACTIVATED")
        return True

    def get_active_adapters(self) -> Dict:
        return {k: v for k, v in self.adapters.items() if v["status"] == "active"}

    def get_all_adapters(self) -> Dict:
        return self.adapters
