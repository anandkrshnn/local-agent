"""Permission Broker with Ephemeral Tokens"""

import logging
import uuid
import time
import hashlib
import json
from dataclasses import dataclass
from typing import Dict, Any, Optional, List, Tuple
from enum import Enum

class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class PermissionToken:
    token: str
    intent: str
    resource: str
    expires_at: float
    scope: Dict

@dataclass
class PolicyRule:
    intent: str
    resource_pattern: str
    max_frequency_per_min: int
    ephemeral_seconds: int
    requires_confirmation: bool
    risk_level: RiskLevel
    auto_learn_threshold: int = 10

class LocalPermissionBroker:
    """Manages permissions with ephemeral tokens and unified DB auditing"""
    
    def __init__(self, learning_enabled: bool = True):
        self.learning_enabled = learning_enabled
        self.policies = self._load_default_policies()
        self.active_tokens: Dict[str, PermissionToken] = {}
        self.pending_confirmations: Dict[str, Dict] = {}
        self.success_counts: Dict[str, int] = {}
        self.pre_approved_cache: Dict[str, float] = {} # intent:resource -> expiry
        self._load_success_counts()
    
    def _load_default_policies(self) -> Dict[str, PolicyRule]:
        # ... (same as before)
        return {
            "read_file": PolicyRule(
                intent="read_file",
                resource_pattern="*.txt|*.md|*.json|*.log|config/*|events/*",
                max_frequency_per_min=60,
                ephemeral_seconds=10,
                requires_confirmation=False,
                risk_level=RiskLevel.LOW
            ),
            "write_file": PolicyRule(
                intent="write_file",
                resource_pattern="logs/*|temp/*|output/*",
                max_frequency_per_min=10,
                ephemeral_seconds=15,
                requires_confirmation=True,
                risk_level=RiskLevel.MEDIUM
            ),
            "delete_file": PolicyRule(
                intent="delete_file",
                resource_pattern="temp/*",
                max_frequency_per_min=2,
                ephemeral_seconds=30,
                requires_confirmation=True,
                risk_level=RiskLevel.HIGH
            ),
            "search_memory": PolicyRule(
                intent="search_memory",
                resource_pattern="*",
                max_frequency_per_min=100,
                ephemeral_seconds=5,
                requires_confirmation=False,
                risk_level=RiskLevel.LOW
            ),
            "vector_search": PolicyRule(
                intent="vector_search",
                resource_pattern="*",
                max_frequency_per_min=50,
                ephemeral_seconds=5,
                requires_confirmation=False,
                risk_level=RiskLevel.LOW
            ),
            "semantic_search": PolicyRule(
                intent="semantic_search",
                resource_pattern="*",
                max_frequency_per_min=50,
                ephemeral_seconds=5,
                requires_confirmation=False,
                risk_level=RiskLevel.LOW
            ),
            "conversation": PolicyRule(
                intent="conversation",
                resource_pattern="*",
                max_frequency_per_min=100,
                ephemeral_seconds=30,
                requires_confirmation=False,
                risk_level=RiskLevel.LOW
            ),
            "web_search": PolicyRule(
                intent="web_search",
                resource_pattern="*",
                max_frequency_per_min=20,
                ephemeral_seconds=60,
                requires_confirmation=False,
                risk_level=RiskLevel.LOW
            ),
            "http_request": PolicyRule(
                intent="http_request",
                resource_pattern="*",
                max_frequency_per_min=10,
                ephemeral_seconds=0,
                requires_confirmation=True,
                risk_level=RiskLevel.MEDIUM
            ),
            "send_email": PolicyRule(
                intent="send_email",
                resource_pattern="*",
                max_frequency_per_min=5,
                ephemeral_seconds=0,
                requires_confirmation=True,
                risk_level=RiskLevel.HIGH
            ),
            "run_command": PolicyRule(
                intent="run_command",
                resource_pattern="*",
                max_frequency_per_min=5,
                ephemeral_seconds=0,
                requires_confirmation=True,
                risk_level=RiskLevel.HIGH
            )
        }
    
    def _load_success_counts(self):
        """Load learned policies from unified DB"""
        with db_manager.get_connection() as conn:
            cursor = conn.execute("SELECT intent, resource_pattern, success_count FROM broker_policy_learned")
            for row in cursor.fetchall():
                key = f"{row[0]}:{row[1]}"
                self.success_counts[key] = row[2]
    
    def request_permission(self, request: Dict[str, Any]) -> Dict[str, Any]:
        start_time = time.time()
        intent = request.get("intent")
        resource = request.get("resource")
        request_id = request.get("request_id", str(uuid.uuid4()))
        context = request.get("context", {})
        
        if intent not in self.policies:
            self._audit(request_id, intent, resource, False, None, f"Unknown intent: {intent}", context, time.time() - start_time)
            return {"granted": False, "reason": f"Unknown intent: {intent}"}
        
        policy = self.policies[intent]
        key = f"{intent}:{resource}"
        auto_approved = self.learning_enabled and self.success_counts.get(key, 0) >= policy.auto_learn_threshold
        
        is_pre_approved = self.pre_approved_cache.get(key, 0) > time.time()
        
        if not self._resource_allowed(resource, policy.resource_pattern):
            self._audit(request_id, intent, resource, False, None, "Resource pattern not allowed", context, time.time() - start_time)
            return {"granted": False, "reason": f"Resource '{resource}' not allowed for {intent}"}
        
        if not self._check_frequency(intent, resource, policy.max_frequency_per_min):
            self._audit(request_id, intent, resource, False, None, "Frequency limit exceeded", context, time.time() - start_time)
            return {"granted": False, "reason": f"Frequency limit exceeded for {intent}"}
        
        requires_confirm = policy.requires_confirmation and not auto_approved and not context.get("pre_approved", False) and not is_pre_approved
        
        if requires_confirm:
            self.pending_confirmations[request_id] = {
                "intent": intent,
                "resource": resource,
                "context": context,
                "timestamp": time.time()
            }
            self._audit(request_id, intent, resource, False, None, "Awaiting user confirmation", context, time.time() - start_time)
            return {
                "granted": False,
                "reason": "Requires user confirmation",
                "requires_confirmation": True,
                "request_id": request_id
            }
        
        token = self._generate_token(intent, resource, policy.ephemeral_seconds)
        self.active_tokens[token.token] = token
        self._audit(request_id, intent, resource, True, token.token, "Granted", context, time.time() - start_time)
        
        # Update learning (Cross-DB compatible ON CONFLICT)
        self.success_counts[key] = self.success_counts.get(key, 0) + 1
        with db_manager.get_connection() as conn:
            # Note: We use the REPLACE pattern for multi-DB compatibility if possible, or standard SQL
            conn.execute(
                """INSERT OR REPLACE INTO broker_policy_learned (intent, resource_pattern, success_count, last_updated)
                   VALUES (?, ?, ?, ?)""",
                (intent, resource, self.success_counts[key], time.time())
            )
            conn.commit()
        
        return {
            "granted": True,
            "token": token.token,
            "expires_at": token.expires_at,
            "expires_in": policy.ephemeral_seconds,
            "scope": token.scope
        }
    
    def _resource_allowed(self, resource: str, pattern: str) -> bool:
        patterns = pattern.split('|')
        for pat in patterns:
            if pat.startswith("*") and not pat.endswith("*"):
                suffix = pat[1:]
                if resource.endswith(suffix): return True
            elif pat.endswith("*"):
                prefix = pat[:-1]
                if resource.startswith(prefix): return True
            elif pat == resource: return True
        return False
    
    def _check_frequency(self, intent: str, resource: str, max_per_min: int) -> bool:
        cutoff = time.time() - 60
        with db_manager.get_connection() as conn:
            cursor = conn.execute(
                "SELECT COUNT(*) FROM broker_audit_log WHERE intent = ? AND resource = ? AND timestamp > ? AND granted = 1",
                (intent, resource, cutoff)
            )
            count = cursor.fetchone()[0]
        return count < max_per_min
    
    def _generate_token(self, intent: str, resource: str, ttl: int) -> PermissionToken:
        token_str = hashlib.sha256(
            f"{intent}{resource}{time.time()}{uuid.uuid4()}".encode()
        ).hexdigest()[:32]
        return PermissionToken(
            token=token_str,
            intent=intent,
            resource=resource,
            expires_at=time.time() + ttl,
            scope={"intent": intent, "resource": resource, "issued_at": time.time()}
        )
    
    def validate_and_consume(self, token_str: str, intent: str, resource: str) -> bool:
        if token_str not in self.active_tokens: return False
        token = self.active_tokens[token_str]
        if time.time() > token.expires_at:
            del self.active_tokens[token_str]
            return False
        if token.intent != intent or token.resource != resource:
            del self.active_tokens[token_str]
            return False
        del self.active_tokens[token_str]
        return True
    
    def _audit(self, request_id: str, intent: str, resource: str, granted: bool, 
               token: Optional[str], reason: str, context: Dict, response_time_ms: float):
        db_manager.execute(
            """INSERT INTO broker_audit_log 
               (timestamp, request_id, intent, resource, granted, token, reason, context, response_time_ms) 
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (time.time(), request_id, intent, resource, granted, token, reason, json.dumps(context), response_time_ms * 1000)
        )
    
    def confirm_permission(self, request_id: str, approved: bool) -> Dict[str, Any]:
        if request_id not in self.pending_confirmations:
            return {"confirmed": False, "reason": "Request not found"}
        
        pending = self.pending_confirmations[request_id]
        del self.pending_confirmations[request_id]
        
        if not approved:
            self._audit(request_id, pending["intent"], pending["resource"], False, None, "Rejected by user", pending["context"], 0)
            return {"confirmed": False, "reason": "Rejected by user"}
        
        self.pre_approved_cache[f"{pending['intent']}:{pending['resource']}"] = time.time() + 60
        
        return self.request_permission({
            "request_id": request_id,
            "intent": pending["intent"],
            "resource": pending["resource"],
            "context": {**pending["context"], "pre_approved": True}
        })
    
    def get_audit_summary(self, minutes: int = 60) -> List[Dict]:
        cutoff = time.time() - (minutes * 60)
        with db_manager.get_connection() as conn:
            cursor = conn.execute(
                """SELECT intent, COUNT(*) as total, 
                          SUM(CASE WHEN granted THEN 1 ELSE 0 END) as granted_count,
                          SUM(CASE WHEN granted THEN 0 ELSE 1 END) as denied_count,
                          AVG(response_time_ms) as avg_response_ms
                   FROM broker_audit_log WHERE timestamp > ? GROUP BY intent""",
                (cutoff,)
            )
            return [{"intent": row[0], "total": row[1], "granted": row[2], "denied": row[3], "avg_ms": round(row[4] or 0, 2)} for row in cursor.fetchall()]

# Update class instantiation to use unified db logic
LocalPermissionBroker = LocalPermissionBroker
