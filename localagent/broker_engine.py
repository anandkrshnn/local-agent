from pathlib import Path
import json
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field, asdict
import uuid
from datetime import datetime
import fnmatch
import copy

@dataclass
class PolicyRule:
    rule_id: str
    intent: str
    resource_pattern: str
    effect: str = "allow"  # allow | confirm | deny
    requires_confirmation: bool = True
    risk_level: str = "medium"
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    version: int = 1
    status: str = "active"  # candidate | active | rejected | archived
    description: str = ""
    source: str = "manual"
    approval_count: int = 0
    history: List[Dict] = field(default_factory=list)  # version history

class PolicyEngine:
    """Advanced policy engine with persistent trust patterns and deterministic matching."""

    def __init__(self, broker, db_path: str = "policies.json", key_manager=None):
        self.broker = broker
        self.policies_path = Path(db_path)
        self.key_manager = key_manager
        self.active_rules: Dict[str, PolicyRule] = {}
        self.candidate_rules: Dict[str, PolicyRule] = {}
        self._load_policies()

    def _load_policies(self):
        if not self.policies_path.exists():
            return
        try:
            raw = self.policies_path.read_text(encoding="utf-8")
            if self.key_manager and self.key_manager.is_encrypted():
                raw = self.key_manager.decrypt(raw)
            data = json.loads(raw)
            
            from dataclasses import fields
            valid_fields = {f.name for f in fields(PolicyRule)}

            # Load active rules
            active_data = data.get("active", {})
            for rid, r in active_data.items():
                # Filter out keys not in the dataclass
                filtered_r = {k: v for k, v in r.items() if k in valid_fields}
                self.active_rules[rid] = PolicyRule(**filtered_r)

            # Load candidates
            cand_data = data.get("candidates", {})
            for rid, r in cand_data.items():
                filtered_r = {k: v for k, v in r.items() if k in valid_fields}
                self.candidate_rules[rid] = PolicyRule(**filtered_r)
                    
        except Exception as e:
            print(f"[PolicyEngine] Error loading policies: {e}")

    def _save_policies(self):
        print(f"[PolicyEngine] Saving {len(self.active_rules)} active and {len(self.candidate_rules)} candidate rules to {self.policies_path}")
        print(f"[PolicyEngine] File exists before save: {self.policies_path.exists()}")
        
        data = {
            "active": {rid: asdict(r) for rid, r in self.active_rules.items()},
            "candidates": {rid: asdict(r) for rid, r in self.candidate_rules.items()}
        }
        
        raw = json.dumps(data, indent=2)
        if self.key_manager and self.key_manager.is_encrypted():
            raw = self.key_manager.encrypt(raw)
            
        self.policies_path.write_text(raw, encoding="utf-8")
        print(f"[PolicyEngine] File exists after save: {self.policies_path.exists()}")
        if self.policies_path.exists():
            print(f"[PolicyEngine] Content length: {len(self.policies_path.read_text())}")

    def match(self, intent: str, resource: str) -> Optional[Dict]:
        """
        Return the highest precedence matching rule.
        Logic: 
        1. Specificity (longest pattern first)
        2. Deny beats Allow on same specificity.
        """
        matching: List[PolicyRule] = []
        for rule in self.active_rules.values():
            if rule.intent == intent or rule.intent == "*":
                if fnmatch.fnmatch(resource, rule.resource_pattern):
                    matching.append(rule)

        if not matching:
            return None

        # Sort by specificity (longer pattern = more specific)
        matching.sort(key=lambda r: (
            -len(r.resource_pattern), 
            0 if r.effect == "deny" else 1
        ))

        return asdict(matching[0])

    def create_active_rule(self, intent: str, resource_pattern: str, description: str, effect: str = "allow", source: str = "manual") -> str:
        rule_id = str(uuid.uuid4())
        rule = PolicyRule(
            rule_id=rule_id,
            intent=intent,
            resource_pattern=resource_pattern,
            effect=effect,
            requires_confirmation=False,
            status="active",
            description=description,
            source=source
        )
        self.active_rules[rule_id] = rule
        self._record_history(rule_id, asdict(rule))
        self._save_policies()
        print(f"[PolicyEngine] PERSISTED ACTIVE rule {rule_id} ({effect.upper()}) for '{intent}' on '{resource_pattern}'")
        return rule_id

    def create_candidate_rule(self, intent: str, resource_pattern: str, reason: str = "") -> str:
        rule_id = str(uuid.uuid4())
        rule = PolicyRule(
            rule_id=rule_id,
            intent=intent,
            resource_pattern=resource_pattern,
            requires_confirmation=True,
            status="candidate",
            description=reason,
            source="auto"
        )
        self.candidate_rules[rule_id] = rule
        self._save_policies()
        return rule_id

    def promote_rule(self, rule_id: str) -> bool:
        if rule_id not in self.candidate_rules:
            return False
        rule = self.candidate_rules.pop(rule_id)
        rule.status = "active"
        rule.requires_confirmation = False
        rule.version += 1
        rule.updated_at = datetime.utcnow().isoformat()
        self.active_rules[rule_id] = rule
        self._record_history(rule_id, asdict(rule))
        self._save_policies()
        return True

    def reject_rule(self, rule_id: str) -> bool:
        if rule_id in self.candidate_rules:
            del self.candidate_rules[rule_id]
            self._save_policies()
            return True
        return False

    def rollback_rule(self, rule_id: str, version: int) -> bool:
        if rule_id not in self.active_rules:
            return False
        rule = self.active_rules[rule_id]
        
        # history is a list of dicts. version is internal to the dict.
        target_v = next((v for v in rule.history if v.get("version") == version), None)
        if not target_v:
            return False
            
        # Restore state (excluding history itself to avoid duplicates if not handled)
        # Actually simplified: deepcopy the historical version and update its own version counter for the new head state.
        new_v_counter = max([v.get("version", 0) for v in rule.history]) + 1
        
        # Re-set fields from target_v
        rule.effect = target_v.get("effect", "allow")
        rule.intent = target_v.get("intent")
        rule.resource_pattern = target_v.get("resource_pattern")
        rule.requires_confirmation = target_v.get("requires_confirmation", True)
        rule.description = target_v.get("description", "")
        rule.status = "active"
        rule.version = new_v_counter
        rule.updated_at = datetime.utcnow().isoformat()
        
        self._record_history(rule_id, asdict(rule))
        self._save_policies()
        print(f"[PolicyEngine] Rule {rule_id} ROLLED BACK to version {version}")
        return True

    def simulate_policy_impact(self, intent: str, pattern: str, effect: str = "allow") -> Dict[str, Any]:
        """Backtest against LanceDB episodes."""
        impact_count = 0
        try:
            episodes = self.broker.get_recent_episodes(limit=100)
            for ep in episodes:
                if ep.get("event_type") == "tool_execution":
                    if ep.get("tool_name") == intent or intent == "*":
                        resource = ep.get("resource_ref") or ""
                        if fnmatch.fnmatch(resource, pattern):
                            impact_count += 1
        except Exception as e:
            return {"success": False, "error": str(e)}

        return {
            "success": True, 
            "matches_found": impact_count,
            "risk_level": "High" if effect == "deny" else "Low",
            "message": f"This rule would have impacted {impact_count} of the last 100 interactions."
        }

    def _record_history(self, rule_id: str, rule_dict: Dict):
        rule = self.active_rules.get(rule_id)
        if rule:
            # Prevent history field itself from being nested in history
            # Actually asdict(rule) includes history. We should strip it for the storage.
            history_copy = copy.deepcopy(rule_dict)
            if 'history' in history_copy:
                del history_copy['history']
            rule.history.append(history_copy)

    def get_candidate_rules(self) -> Dict[str, Dict]:
        return {rid: asdict(r) for rid, r in self.candidate_rules.items()}

    def get_active_rules(self) -> Dict[str, Dict]:
        return {rid: asdict(r) for rid, r in self.active_rules.items()}

    def get_rule_history(self, rule_id: str) -> List[Dict]:
        rule = self.active_rules.get(rule_id)
        return rule.history if rule else []

    def revoke_rule(self, rule_id: str) -> bool:
        if rule_id in self.active_rules:
            rule = self.active_rules.pop(rule_id)
            # Logic: mark as archived/deleted? 
            # In simple local agent, just delete but we could save history somewhere.
            self._save_policies()
            return True
        return False
