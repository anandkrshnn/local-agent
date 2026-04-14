from datetime import datetime
from typing import Dict, Any, List
import uuid

class DecisionTrace:
    """Per-request decision trace for explainability in v0.2."""

    def __init__(self, user_input: str):
        self.trace_id = str(uuid.uuid4())
        self.created_at = datetime.utcnow()
        self.user_input = user_input
        self.retrieved_memories: List[Dict] = []
        self.applied_policies: List[Dict] = []
        self.risk_hints: List[str] = []
        self.adapter_state: List[str] = []
        self.tool_decisions: List[Dict] = []
        self.final_outcome: str = ""

    def add_retrieved_memory(self, memory: Dict):
        self.retrieved_memories.append(memory)

    def add_applied_policy(self, policy: Dict):
        self.applied_policies.append(policy)

    def add_risk_hint(self, hint: str):
        self.risk_hints.append(hint)

    def add_tool_decision(self, decision: Dict):
        self.tool_decisions.append(decision)

    def set_final_outcome(self, outcome: str):
        self.final_outcome = outcome

    def to_dict(self) -> Dict:
        return {
            "trace_id": self.trace_id,
            "created_at": self.created_at.isoformat(),
            "user_input": self.user_input,
            "retrieved_memories": self.retrieved_memories,
            "applied_policies": self.applied_policies,
            "risk_hints": self.risk_hints,
            "adapter_state": self.adapter_state,
            "tool_decisions": self.tool_decisions,
            "final_outcome": self.final_outcome
        }

    def save_to_jsonl(self, filepath: str = "decision_traces.jsonl", key_manager=None):
        """Append the trace to a persistent JSONL file, optionally encrypted."""
        import json
        from pathlib import Path

        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)

        data = json.dumps(self.to_dict())
        
        if key_manager and key_manager.is_encrypted():
            data = key_manager.encrypt(data)

        with open(path, "a", encoding="utf-8") as f:
            f.write(data + "\n")

        print(f"[DecisionTrace] Saved trace {self.trace_id} to {filepath}")
        if key_manager and key_manager.is_encrypted():
            print(f"[DecisionTrace] Trace {self.trace_id} was ENCRYPTED")
