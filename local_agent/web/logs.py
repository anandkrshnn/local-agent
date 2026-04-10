"""
Log Sanitization - Enhanced for PostgreSQL Schema
Blocks password_hash, email, settings, and other PII
"""

import json
import time
import re
from typing import List, Dict, Any, Optional
from collections import deque
from fastapi import WebSocket
import asyncio

# Comprehensive blacklist patterns for sensitive data
SENSITIVE_PATTERNS = [
    # API Keys & Tokens
    (r'api_key[\s]*[:=][\s]*["\']?([a-zA-Z0-9_\-]{8,64})["\']?', 'api_key=[REDACTED]'),
    (r'token[\s]*[:=][\s]*["\']?([a-zA-Z0-9_\-\.]{8,256})["\']?', 'token=[REDACTED]'),
    (r'password[\s]*[:=][\s]*["\']?([^"\'\s]{4,})["\']?', 'password=[REDACTED]'),
    (r'client_secret[\s]*[:=][\s]*["\']?([a-zA-Z0-9_\-]{8,64})["\']?', 'client_secret=[REDACTED]'),
    (r'authorization[\s]*[:=][\s]*["\']?([Bb]earer\s+[a-zA-Z0-9_\-\.]{20,})["\']?', 'authorization=[REDACTED]'),
    (r'X-API-Key[\s]*[:=][\s]*["\']?([a-zA-Z0-9_\-]{8,64})["\']?', 'X-API-Key=[REDACTED]'),
    (r'jwt[\s]*[:=][\s]*["\']?([a-zA-Z0-9_\-\.]{20,})["\']?', 'jwt=[REDACTED]'),
    (r'session_id[\s]*[:=][\s]*["\']?([a-zA-Z0-9_\-]{16,})["\']?', 'session_id=[REDACTED]'),
    
    # NEW: PostgreSQL User Schema Fields
    (r'password_hash[\s]*[:=][\s]*["\']?([$2y$0-9a-zA-Z/\.]{60})["\']?', 'password_hash=[REDACTED]'),
    (r'email[\s]*[:=][\s]*["\']?([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})["\']?', 'email=[REDACTED]'),
    (r'settings[\s]*[:=][\s]*["\']?(\{[^}]*\})["\']?', 'settings=[REDACTED]'),
    (r'avatar_url[\s]*[:=][\s]*["\']?(https?://[^\s"\']+)["\']?', 'avatar_url=[REDACTED]'),
    
    # Additional PII
    (r'phone[\s]*[:=][\s]*["\']?(\+?[\d\s-]{10,15})["\']?', 'phone=[REDACTED]'),
    (r'ssn[\s]*[:=][\s]*["\']?(\d{3}-\d{2}-\d{4})["\']?', 'ssn=[REDACTED]'),
    (r'credit_card[\s]*[:=][\s]*["\']?(\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4})["\']?', 'credit_card=[REDACTED]'),
    (r'ip_address[\s]*[:=][\s]*["\']?(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})["\']?', 'ip_address=[REDACTED]'),
]

class LogStreamer:
    """Manages WebSocket connections for real-time log streaming with ENHANCED SECURITY"""
    
    def __init__(self, max_history: int = 1000):
        self.active_connections: List[WebSocket] = []
        self.log_history: deque = deque(maxlen=max_history)
        self._event_queue = asyncio.Queue()
    
    def sanitize_log_entry(self, entry: Dict) -> Dict:
        """Remove ALL sensitive data from log entries"""
        # Convert to string for regex replacement
        entry_str = json.dumps(entry, default=str)
        
        # Apply all blacklist patterns
        for pattern, replacement in SENSITIVE_PATTERNS:
            entry_str = re.sub(pattern, replacement, entry_str, flags=re.IGNORECASE)
        
        # Also redact any field that might contain sensitive data
        try:
            sanitized = json.loads(entry_str)
        except:
            sanitized = {"error": "Unable to sanitize log entry"}
        
        # Recursively sanitize nested objects
        return self._deep_sanitize(sanitized)
    
    def _deep_sanitize(self, obj: Any) -> Any:
        """Recursively sanitize nested objects"""
        if isinstance(obj, dict):
            # List of sensitive keys to redact
            sensitive_keys = ['password', 'password_hash', 'token', 'api_key', 
                             'email', 'secret', 'key', 'authorization', 'jwt']
            
            result = {}
            for key, value in obj.items():
                if any(sensitive in key.lower() for sensitive in sensitive_keys):
                    result[key] = '[REDACTED]'
                else:
                    result[key] = self._deep_sanitize(value)
            return result
        elif isinstance(obj, list):
            return [self._deep_sanitize(item) for item in obj]
        else:
            return obj
    
    async def connect(self, websocket: WebSocket, user_role: str = "viewer"):
        """Accept a new WebSocket connection with role-based access"""
        await websocket.accept()
        
        # TODO: Implement RBAC - only admins should see all logs
        # For now, all connected users receive logs
        self.active_connections.append(websocket)
        
        # Send sanitized history on connection
        for log in self.log_history:
            sanitized_log = self.sanitize_log_entry(log)
            await websocket.send_text(json.dumps(sanitized_log))
    
    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
    
    async def broadcast(self, log_entry: Dict):
        """Broadcast a SANITIZED log entry to all connected clients"""
        # Add timestamp if not present
        if 'timestamp' not in log_entry:
            log_entry['timestamp'] = time.time()
        
        # SANITIZE before storing or broadcasting
        sanitized_entry = self.sanitize_log_entry(log_entry)
        
        # Store in history (already sanitized)
        self.log_history.append(sanitized_entry)
        
        # Broadcast to all connections
        for connection in self.active_connections[:]:
            try:
                await connection.send_text(json.dumps(sanitized_entry))
            except:
                # Remove dead connections
                self.disconnect(connection)
    
    def log(self, level: str, message: str, **kwargs):
        """Add a log entry with automatic sanitization"""
        entry = {
            "level": level,
            "message": message,
            **kwargs
        }
        
        # Schedule broadcast in event loop
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(self.broadcast(entry))
            else:
                asyncio.run(self.broadcast(entry))
        except:
            pass

# Global log streamer instance
log_streamer = LogStreamer()

def log_info(message: str, **kwargs):
    log_streamer.log("INFO", message, **kwargs)

def log_warning(message: str, **kwargs):
    log_streamer.log("WARNING", message, **kwargs)

def log_error(message: str, **kwargs):
    log_streamer.log("ERROR", message, **kwargs)

def log_debug(message: str, **kwargs):
    log_streamer.log("DEBUG", message, **kwargs)
