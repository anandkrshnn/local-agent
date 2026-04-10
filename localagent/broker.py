import uuid
import time
import sqlite3
from typing import Dict, Any, Optional

class LocalPermissionBroker:
    """Just-in-Time Security: Manages tool tokens and auto-learning trust"""

    def __init__(self, db_path: str = "lpb_audit.db"):
        self.db_path = db_path
        self.conn = self._init_db()
        self.pending_confirmations = {}
        self.active_tokens = {}
        
        # Default policies for each capability
        self.policies = self._load_default_policies()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                request_id TEXT,
                intent TEXT,
                resource TEXT,
                granted BOOLEAN,
                token TEXT,
                reason TEXT,
                timestamp REAL,
                context TEXT
            )
        """)
        conn.commit()
        return conn

    def _load_default_policies(self):
        """Standard high-assurance defaults"""
        return {
            "read_file": {"requires_confirmation": False}, # Safe for reads
            "list_directory": {"requires_confirmation": False},
            "write_file": {"requires_confirmation": True}, # Gated
            "append_to_file": {"requires_confirmation": True}, # Gated
            "query_memory": {"requires_confirmation": False},
            "search_memory": {"requires_confirmation": False}
        }

    def request_permission(self, intent: str, resource: str, context: str = "") -> Dict[str, Any]:
        """Verify intent/resource against policy and return a token or requirement for confirmation."""
        request_id = str(uuid.uuid4())
        policy = self.policies.get(intent)

        # Policy check: confirmation required?
        if policy and policy.get("requires_confirmation", True):
            self.pending_confirmations[request_id] = {
                "intent": intent, 
                "resource": resource, 
                "timestamp": time.time(),
                "context": context
            }
            return {"granted": False, "request_id": request_id, "message": "Awaiting confirmation"}

        # Auto-grant
        token = uuid.uuid4().hex
        expires_at = time.time() + 60  # 60 sec TTL
        self.active_tokens[token] = {
            "intent": intent, 
            "resource": resource, 
            "expires_at": expires_at
        }

        # Audit
        self._audit(request_id, intent, resource, True, token, "Granted", context)

        # Auto-policy learning: check if trust threshold is reached
        self._update_policy_from_audit(intent, resource)

        return {"granted": True, "token": token, "expires_at": expires_at}

    def _update_policy_from_audit(self, intent: str, resource: str):
        """Internal runtime auto-learning: reduce confirmation after repeated successful uses."""
        # Simple count of successful approvals for this pattern in the last 24h
        cutoff = time.time() - 86400  # 24 hours
        count = self.conn.execute("""
            SELECT COUNT(*) FROM audit_log 
            WHERE intent = ? 
              AND resource = ? 
              AND granted = 1 
              AND timestamp > ?
        """, (intent, resource, cutoff)).fetchone()[0]

        # Trust Threshold: 8 successful manual approvals
        if count >= 8:
            policy = self.policies.get(intent)
            if policy and policy.get("requires_confirmation") is True:
                policy["requires_confirmation"] = False
                msg = f"Auto-policy update: Confirmation disabled for '{intent}' on '{resource}' (learned from {count} successful uses in last 24h)"
                try:
                    print(f"🔄 {msg}")
                except UnicodeEncodeError:
                    print(f"[TRUST] {msg}")

    def confirm_permission(self, request_id: str, approved: bool) -> Dict[str, Any]:
        """Manually approve/deny a pending request."""
        pending = self.pending_confirmations.get(request_id)
        if not pending:
            return {"error": "Request ID not found"}

        if approved:
            token = uuid.uuid4().hex
            expires_at = time.time() + 60
            self.active_tokens[token] = {
                "intent": pending["intent"], 
                "resource": pending["resource"], 
                "expires_at": expires_at
            }
            self._audit(request_id, pending["intent"], pending["resource"], True, token, "Manually Approved", pending.get("context"))
            
            # Auto-policy learning: re-assess trust after manual approval
            self._update_policy_from_audit(pending["intent"], pending["resource"])
            
            del self.pending_confirmations[request_id]
            return {"granted": True, "token": token, "expires_at": expires_at}
        else:
            self._audit(request_id, pending["intent"], pending["resource"], False, None, "Manually Denied", pending.get("context"))
            del self.pending_confirmations[request_id]
            return {"granted": False, "message": "Permission denied by user"}

    def validate_token(self, intent: str, resource: str, token: str) -> bool:
        """Runtime token validation before execution."""
        if not token: return False
        t_data = self.active_tokens.get(token)
        if not t_data: return False

        if t_data["expires_at"] < time.time():
            del self.active_tokens[token]
            return False

        if t_data["intent"] == intent and t_data["resource"] == resource:
            return True
        return False

    def _audit(self, request_id, intent, resource, granted, token, reason, context):
        try:
            self.conn.execute("""
                INSERT INTO audit_log (request_id, intent, resource, granted, token, reason, timestamp, context)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (request_id, intent, resource, 1 if granted else 0, token, reason, time.time(), str(context)))
            self.conn.commit()
        except:
            pass

    def close(self):
        if self.conn:
            self.conn.close()
            self.conn = None
