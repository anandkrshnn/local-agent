import uuid
import time
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

class LocalPermissionBroker:
    """Just-in-Time Security: Manages tool tokens and auto-learning trust with Encrypted JSONL Audit."""

    def __init__(self, audit_log_path: str = "audit_log.jsonl", key_manager=None):
        self.audit_log_path = Path(audit_log_path)
        self.key_manager = key_manager
        self.audit_log_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.pending_confirmations = {}
        self.active_tokens = {}
        
        # Default policies for each capability
        self.policies = self._load_default_policies()
        
        from localagent.broker_engine import PolicyEngine
        # Construct PolicyEngine path based on audit log path for vault consistency
        policies_path = self.audit_log_path.parent / "policies.json"
        self.policy_engine = PolicyEngine(self, db_path=str(policies_path), key_manager=self.key_manager)

    def _load_default_policies(self):
        """Standard high-assurance defaults"""
        return {
            "read_file": {"requires_confirmation": False},
            "list_directory": {"requires_confirmation": False},
            "write_file": {"requires_confirmation": True},
            "append_to_file": {"requires_confirmation": True},
            "query_memory": {"requires_confirmation": False},
            "search_memory": {"requires_confirmation": False},
            "read_memory": {
                "allowed_resources": ["semantic_memory", "*"],
                "max_frequency_per_min": 60,
                "ephemeral_seconds": 30,
                "requires_confirmation": False,
                "risk_level": "low"
            }
        }

    def _get_policy(self, intent: str, resource: str) -> dict:
        """Fetch policy with override from persistent engine."""
        # 1. Check persistent engine first (learned/manual rules)
        active_rule = self.policy_engine.match(intent, resource)
        if active_rule:
            return active_rule
        
        # 2. Fallback to default memory policies
        return self.policies.get(intent)

    def _generate_token(self, intent: str, resource: str) -> str:
        """Generate a short-lived token."""
        token = uuid.uuid4().hex
        expires_at = time.time() + 60
        self.active_tokens[token] = {
            "intent": intent, 
            "resource": resource, 
            "expires_at": expires_at
        }
        return token

    def request_permission(self, intent: str, resource: str, context: str = "") -> dict:
        """
        Request permission for an operation.
        Deterministic: Persistent Engine > Default Policies.
        """
        # 1. Check if we have a matching rule in the persistent engine
        rule = self.policy_engine.match(intent, resource)
        
        if rule:
            effect = rule.get("effect", "allow").lower()
            if effect == "deny":
                msg = f"Operation BLOCKED via persistent {rule.get('source', 'learned')} NEGATIVE policy"
                self._append_audit(str(uuid.uuid4()), intent, resource, False, None, msg, context)
                return {
                    "granted": False,
                    "reason": msg,
                    "auto_blocked": True,
                    "rule_id": rule.get("rule_id")
                }
            
            if not rule.get("requires_confirmation", True):
                # Auto-approved by persistent rule (manual or learned)
                token = self._generate_token(intent, resource)
                msg = f"Auto-approved via persistent {rule.get('source', 'learned')} policy"
                self._append_audit(str(uuid.uuid4()), intent, resource, True, token, msg, context)
                
                return {
                    "granted": True,
                    "reason": msg,
                    "token": token,
                    "auto_approved": True,
                    "rule_id": rule.get("rule_id")
                }
            
        # 2. Fallback to default hardcoded policies
        default_policy = self.policies.get(intent, {"requires_confirmation": True})
        if not default_policy.get("requires_confirmation", True):
            token = self._generate_token(intent, resource)
            self._append_audit(str(uuid.uuid4()), intent, resource, True, token, "Auto-approved by default policy", context)
            return {"granted": True, "token": token, "auto_approved": True}
        
        # 3. Need user confirmation
        approval_count = self._count_approvals(intent, resource)
        risk_score = self._calculate_risk(intent, resource)
        request_id = str(uuid.uuid4())
        
        return {
            "granted": False,
            "requires_confirmation": True,
            "request_id": request_id,
            "intent": intent,
            "resource": resource,
            "risk_score": risk_score,
            "approval_count": approval_count,
            "threshold": 8
        }

    def confirm_permission(self, intent: str, resource: str, approved: bool, context: str = "") -> dict:
        """
        Called after user confirms or denies a permission request.
        """
        if not approved:
            self._append_audit(str(uuid.uuid4()), intent, resource, False, None, "User denied", context)
            return {"granted": False, "reason": "User denied"}
        
        token = self._generate_token(intent, resource)
        self._append_audit(str(uuid.uuid4()), intent, resource, True, token, "User approved", context)
        
        # Update/Create candidate rule for learning
        self._update_learning_state(intent, resource)
        
        # Check if the policy JUST flipped to auto
        rule = self.policy_engine.match(intent, resource)
        approval_count = self._count_approvals(intent, resource)
        
        result = {
            "granted": True,
            "token": token,
            "reason": "User approved",
            "approval_count": approval_count,
            "threshold": 8
        }
        
        if rule and not rule.get("requires_confirmation", True):
            result["pattern_learned"] = True
            result["message"] = f"Pattern learned! Future requests for {resource} will auto-approve."
        else:
            remaining = 8 - approval_count
            result["message"] = f"Approved. {remaining} more needed to learn this pattern."
        
        return result

    def promote_to_always_allow(self, intent: str, resource_pattern: str, description: str = None) -> dict:
        """Explicit user request to 'Always Allow' a folder."""
        if not description:
            description = f"Manually trusted pattern for {intent}"
            
        rule_id = self.policy_engine.create_active_rule(
            intent=intent,
            resource_pattern=resource_pattern,
            description=description,
            effect="allow",
            source="manual"
        )
        return {"success": True, "rule_id": rule_id, "message": f"Successfully trusted {resource_pattern} forever."}

    def promote_to_never_allow(self, intent: str, resource_pattern: str, description: str = None) -> dict:
        """Explicit user request to 'Never Allow' a folder (Negative Policy)."""
        if not description:
            description = f"Manually BLOCKED pattern for {intent}"
            
        rule_id = self.policy_engine.create_active_rule(
            intent=intent,
            resource_pattern=resource_pattern,
            description=description,
            effect="deny",
            source="manual"
        )
        return {"success": True, "rule_id": rule_id, "message": f"Successfully BLOCKED {resource_pattern} forever."}

    def get_recent_episodes(self, limit: int = 100) -> List[Dict]:
        """Bridge to memory system to fetch episodes for simulation."""
        # For the broker to access episodes, we need a link to the environment/agent or memory store
        # In this architecture, app.py sets this up. We'll use a lazy injection or explicit set.
        if hasattr(self, 'memory_service') and self.memory_service:
            return self.memory_service.lancedb_store.get_recent_episodes(limit=limit)
        return []

    def _update_learning_state(self, intent: str, resource: str):
        """Internal learning logic: candidate -> active promotion."""
        count = self._count_approvals(intent, resource)
        resource_pattern = self._get_resource_pattern(resource)
        
        # Check if we already have a candidate
        found_candidate = None
        for cid, cand in self.policy_engine.get_candidate_rules().items():
            if cand.get("intent") == intent and cand.get("resource_pattern") == resource_pattern:
                found_candidate = cid
                # We can't update 'cand' directly here as it's a dict from get_candidate_rules()
                # We should update the object in the engine
                eng_cand = self.policy_engine.candidate_rules[cid]
                eng_cand.approval_count = count
                eng_cand.updated_at = datetime.utcnow().isoformat()
                break
        
        if not found_candidate:
            found_candidate = self.policy_engine.create_candidate_rule(intent, resource_pattern)
            
        # Threshold promotion
        if count >= 8:
            self.policy_engine.promote_rule(found_candidate)
            print(f"[TRUST] Persistent pattern learned for {intent} on {resource_pattern}")
        else:
            self.policy_engine._save_policies()

    def _count_approvals(self, intent: str, resource: str) -> int:
        """
        Count how many times this pattern has been approved in the last 24 hours.
        Reads from JSONL audit log.
        """
        if not self.audit_log_path.exists():
            return 0

        resource_pattern = self._get_resource_pattern(resource)
        cutoff = time.time() - 86400  # 24 hours
        count = 0

        try:
            with open(self.audit_log_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line: continue
                    
                    try:
                        # Decrypt if needed
                        if self.key_manager and self.key_manager.is_encrypted():
                            line = self.key_manager.decrypt(line)
                        
                        entry = json.loads(line)
                        
                        # Filter criteria
                        if (entry.get("intent") == intent and 
                            entry.get("resource", "").startswith(resource_pattern) and 
                            entry.get("granted") is True and 
                            entry.get("timestamp", 0) > cutoff):
                            count += 1
                    except:
                        continue
            return count
        except Exception as e:
            print(f"[Broker] Error counting approvals from JSONL: {e}")
            return 0

    def _get_resource_pattern(self, resource: str) -> str:
        """Extract the pattern from a resource path (e.g. 'sandbox/test.txt' -> 'sandbox/')"""
        if "/" in resource:
            return resource.split("/")[0] + "/"
        return resource

    def _calculate_risk(self, intent: str, resource: str) -> float:
        """Calculate risk score for an operation (0.0 = safe, 1.0 = dangerous)."""
        risk_scores = {
            "read_file": 0.2,
            "write_file": 0.4,
            "list_directory": 0.1,
            "append_to_file": 0.4,
            "query_memory": 0.1,
            "search_memory": 0.2
        }
        base_risk = risk_scores.get(intent, 0.5)
        
        # Increase risk for paths outside sandbox
        if not resource.startswith("sandbox"):
            base_risk = min(1.0, base_risk + 0.3)
        return base_risk

    def validate_token(self, intent: str, resource: str, token: str) -> bool:
        """Runtime token validation before execution."""
        if not token: return False
        t_data = self.active_tokens.get(token)
        if not t_data: return False

        if t_data["expires_at"] < time.time():
            del self.active_tokens[token]
            return False

        # Support pattern matching for tokens as well (if needed, but usually exact)
        if t_data["intent"] == intent and t_data["resource"] == resource:
            del self.active_tokens[token]
            return True
        return False

    def _append_audit(self, request_id, intent, resource, granted, token, reason, context):
        """Append entry to JSONL audit log and rotate if exceeding 1,000 entries."""
        entry = {
            "request_id": request_id,
            "intent": intent,
            "resource": resource,
            "granted": granted,
            "token": token,
            "reason": reason,
            "timestamp": time.time(),
            "context": str(context)
        }
        
        try:
            line = json.dumps(entry)
            if self.key_manager and self.key_manager.is_encrypted():
                line = self.key_manager.encrypt(line)
            
            # Rotation logic: check file size (1MB cap)
            if os.path.exists(self.audit_log_path):
                file_size = os.path.getsize(self.audit_log_path)
                if file_size > 1024 * 1024: # 1MB
                    print(f"[Broker] Audit log size ({file_size} bytes) exceeds 1MB. Rotating...")
                    with open(self.audit_log_path, "r", encoding="utf-8") as f:
                        lines = f.readlines()
                    # Keep only the last 80% of lines to stay well under the cap
                    lines = lines[len(lines)//5:] 
                    with open(self.audit_log_path, "w", encoding="utf-8") as f:
                        f.writelines(lines)
            
            with open(self.audit_log_path, "a", encoding="utf-8") as f:
                f.write(line + "\n")
                
        except Exception as e:
            print(f"[Broker] Error appending audit: {e}")

    def get_audit_history(self, limit: int = 500) -> List[Dict]:
        """Fetch and decrypt the audit log for compliance reporting with memory efficiency."""
        if not self.audit_log_path.exists():
            return []
            
        history = []
        try:
            # We use a memory-efficient approach by reading lines one by one.
            # For a really large file, we'd use a reverse file reader, 
            # but for our 1MB-capped log, reading and filtering is fast enough.
            with open(self.audit_log_path, "r", encoding="utf-8") as f:
                # Optimized: Read all lines but avoid readlines() overhead if path is large
                # Actually, for 1MB, simple iteration is fine. 
                # To get 'newest first' without readlines, we'd need to seek to end.
                # Here we'll just buffer locally up to the limit.
                all_entries = []
                for line in f:
                    line = line.strip()
                    if not line: continue
                    all_entries.append(line)
                    # Simple sliding window for the last 'limit' lines
                    if len(all_entries) > limit:
                        all_entries.pop(0)

                for line in reversed(all_entries):
                    try:
                        if self.key_manager and self.key_manager.is_encrypted():
                            line = self.key_manager.decrypt(line)
                        history.append(json.loads(line))
                    except:
                        continue
            return history
        except Exception as e:
            print(f"[Broker] Error reading audit history: {e}")
            return []

    def close(self):
        # No SQLite connection to close
        pass

if __name__ == "__main__":
    # Self-test
    broker = LocalPermissionBroker("test_audit_migration.jsonl")
    print(broker.request_permission("write_file", "sandbox/test.txt"))
