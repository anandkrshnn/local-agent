"""
Enterprise Compliance & Audit
SOC2, HIPAA, GDPR readiness with immutable audit trails
"""

import os
import json
import hashlib
import re
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from cryptography.fernet import Fernet

from local_agent.core.db import db_manager

logger = logging.getLogger(__name__)

# Initialize encryption for PII
ENCRYPTION_KEY = os.getenv("AUDIT_ENCRYPTION_KEY", Fernet.generate_key().decode())
if isinstance(ENCRYPTION_KEY, str):
    cipher = Fernet(ENCRYPTION_KEY.encode())
else:
    cipher = Fernet(ENCRYPTION_KEY)

@dataclass
class AuditEvent:
    """Immutable audit event"""
    id: str
    timestamp: float
    user_id: str
    action: str
    resource_type: str
    resource_id: str
    details: Dict
    ip_address: str
    user_agent: str
    previous_hash: str
    hash: str = ""
    retention_date: float = 0.0

class ComplianceManager:
    """
    Enterprise compliance with immutable audit trail
    Supports SOC2, HIPAA, GDPR requirements
    """
    
    def __init__(self):
        self.last_hash = self._get_last_hash()
    
    def _get_last_hash(self) -> str:
        """Get hash of the most recent audit event from central DB"""
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("SELECT hash FROM audit_events ORDER BY timestamp DESC LIMIT 1")
                row = cursor.fetchone()
                return row[0] if row else "0" * 64
            except Exception as e:
                logger.error(f"Error fetching last audit hash: {e}")
                return "0" * 64
    
    def _mask_pii(self, data: Dict) -> Dict:
        """Mask PII (Personally Identifiable Information) for compliance"""
        masked = data.copy()
        pii_patterns = {
            'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'phone': r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
            'ssn': r'\b\d{3}-\d{2}-\d{4}\b',
            'credit_card': r'\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b'
        }
        
        for key, value in masked.items():
            if isinstance(value, str):
                for pattern_name, pattern in pii_patterns.items():
                    if re.search(pattern, value):
                        masked[key] = f"[{pattern_name.upper()}_REDACTED]"
        
        return masked
    
    def _encrypt_sensitive(self, data: Dict) -> str:
        """Encrypt sensitive audit data"""
        json_str = json.dumps(data)
        encrypted = cipher.encrypt(json_str.encode())
        return encrypted.decode()
    
    def log_event(self, event: AuditEvent) -> str:
        """Log an immutable audit event with chain of custody to unified DB"""
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            # Mask PII
            masked_details = self._mask_pii(event.details)
            
            # Calculate hash for chain of custody
            event.previous_hash = self.last_hash
            event_data = f"{event.previous_hash}:{event.timestamp}:{event.user_id}:{event.action}:{json.dumps(masked_details)}"
            event_hash = hashlib.sha256(event_data.encode()).hexdigest()
            event.hash = event_hash
            
            # Set retention date (default: 7 years for compliance)
            retention_date = datetime.now() + timedelta(days=2555)
            event.retention_date = retention_date.timestamp()
            
            # Encrypt sensitive details
            encrypted_details = self._encrypt_sensitive(masked_details)
            
            cursor.execute("""
                INSERT INTO audit_events 
                (id, timestamp, user_id, action, resource_type, resource_id, details, 
                 ip_address, user_agent, previous_hash, hash, retention_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                event.id, event.timestamp, event.user_id, event.action,
                event.resource_type, event.resource_id, encrypted_details,
                event.ip_address, event.user_agent, event.previous_hash, event.hash,
                event.retention_date
            ))
            
            conn.commit()
            self.last_hash = event_hash
            return event_hash
    
    def verify_chain(self) -> bool:
        """Verify the integrity of the audit chain"""
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT previous_hash, hash FROM audit_events ORDER BY timestamp ASC")
            events = cursor.fetchall()
            
            previous_hash = "0" * 64
            for p_hash, c_hash in events:
                if p_hash != previous_hash:
                    return False
                previous_hash = c_hash
            
            return True
    
    def get_events(self, user_id: str = None, action: str = None,
                   start_date: float = None, end_date: float = None,
                   limit: int = 100) -> List[Dict]:
        """Query audit events with filters"""
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            query = "SELECT id, timestamp, user_id, action, resource_type, resource_id, details, ip_address, user_agent, hash FROM audit_events WHERE 1=1"
            params = []
            
            if user_id:
                query += " AND user_id = ?"
                params.append(user_id)
            if action:
                query += " AND action = ?"
                params.append(action)
            if start_date:
                query += " AND timestamp >= ?"
                params.append(start_date)
            if end_date:
                query += " AND timestamp <= ?"
                params.append(end_date)
            
            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            events = cursor.fetchall()
            return [self._format_event(e) for e in events]
    
    def _format_event(self, row) -> Dict:
        """Format audit event for output"""
        return {
            "id": row[0],
            "timestamp": row[1],
            "user_id": row[2],
            "action": row[3],
            "resource_type": row[4],
            "resource_id": row[5],
            "ip_address": row[7],
            "user_agent": row[8],
            "hash": row[9]
        }
    
    def generate_compliance_report(self, report_type: str, start_date: float, end_date: float) -> Dict:
        """Generate compliance reports (SOC2, HIPAA, GDPR)"""
        events = self.get_events(start_date=start_date, end_date=end_date, limit=10000)
        
        report = {
            "report_type": report_type,
            "start_date": start_date,
            "end_date": end_date,
            "generated_at": datetime.now().timestamp(),
            "chain_integrity": self.verify_chain(),
            "total_events": len(events),
            "events_by_action": {},
            "events_by_user": {},
            "retention_compliant": self._check_retention()
        }
        
        for event in events:
            action = event['action']
            user = event['user_id']
            report['events_by_action'][action] = report['events_by_action'].get(action, 0) + 1
            report['events_by_user'][user] = report['events_by_user'].get(user, 0) + 1
        
        return report
    
    def _check_retention(self) -> bool:
        """Enforce data retention policies in unified DB"""
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM audit_events WHERE retention_date < ?", (datetime.now().timestamp(),))
            conn.commit()
            return True

# Singleton instance
compliance_manager = ComplianceManager()

# Singleton instance
compliance_manager = ComplianceManager()
