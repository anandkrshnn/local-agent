"""
Persistent Session Manager with unified DatabaseManager backend
Maintains chat history across server restarts
"""

import json
import uuid
import time
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field

from local_agent.core.db import db_manager

logger = logging.getLogger(__name__)

@dataclass
class StoredMessage:
    """Message stored in database"""
    role: str
    content: str
    timestamp: float
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class StoredSession:
    """Session stored in database"""
    session_id: str
    created_at: float
    last_active: float
    user_id: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    messages: List[StoredMessage] = field(default_factory=list)
    agent: Any = None
    
    def __post_init__(self):
        from ..core.agent import LocalAgent
        self.agent = LocalAgent(verbose=False)

class PersistentSessionManager:
    """
    Session manager with unified persistence.
    Automatically recovers sessions after server restart.
    """
    
    def __init__(self):
        self._cache: Dict[str, StoredSession] = {}  # In-memory cache
    
    def create_session(self, user_id: str = None, metadata: Dict = None) -> StoredSession:
        """Create a new session in unified DB"""
        session_id = str(uuid.uuid4())
        user_id = user_id or f"user_{uuid.uuid4().hex[:8]}"
        now = time.time()
        
        db_manager.execute(
            "INSERT INTO active_sessions (session_id, created_at, last_active, user_id, metadata) VALUES (?, ?, ?, ?, ?)",
            (session_id, now, now, user_id, json.dumps(metadata or {}))
        )
        
        # Create cache entry
        session = StoredSession(
            session_id=session_id,
            created_at=now,
            last_active=now,
            user_id=user_id,
            metadata=metadata or {}
        )
        self._cache[session_id] = session
        
        return session
    
    def get_session(self, session_id: str) -> Optional[StoredSession]:
        """Get session by ID (with cache)"""
        if session_id in self._cache:
            return self._cache[session_id]
        
        # Load from database
        with db_manager.get_connection() as conn:
            cursor = conn.execute(
                "SELECT session_id, created_at, last_active, user_id, metadata FROM active_sessions WHERE session_id = ? AND is_active = 1",
                (session_id,)
            )
            row = cursor.fetchone()
            
            if not row:
                return None
            
            # Load messages
            messages = self._load_messages(session_id)
            
            session = StoredSession(
                session_id=row['session_id'],
                created_at=row['created_at'],
                last_active=row['last_active'],
                user_id=row['user_id'],
                metadata=json.loads(row['metadata']) if row['metadata'] else {},
                messages=messages
            )
            
            self._cache[session_id] = session
            return session
    
    def get_or_create_session(self, session_id: str = None, user_id: str = None) -> StoredSession:
        """Get existing session or create new one"""
        if session_id:
            session = self.get_session(session_id)
            if session:
                return session
        
        return self.create_session(user_id)
    
    def add_message(self, session_id: str, role: str, content: str, metadata: Dict = None):
        """Add a message to session history in unified DB"""
        now = time.time()
        
        with db_manager.get_connection() as conn:
            # Insert message
            conn.execute(
                "INSERT INTO session_messages (session_id, role, content, timestamp, metadata) VALUES (?, ?, ?, ?, ?)",
                (session_id, role, content, now, json.dumps(metadata or {}))
            )
            
            # Update last_active
            conn.execute(
                "UPDATE active_sessions SET last_active = ? WHERE session_id = ?",
                (now, session_id)
            )
            conn.commit()
        
        # Update cache
        if session_id in self._cache:
            self._cache[session_id].last_active = now
            self._cache[session_id].messages.append(
                StoredMessage(role=role, content=content, timestamp=now, metadata=metadata or {})
            )
    
    def _load_messages(self, session_id: str, limit: int = 100) -> List[StoredMessage]:
        """Load messages from database"""
        with db_manager.get_connection() as conn:
            cursor = conn.execute(
                "SELECT role, content, timestamp, metadata FROM session_messages WHERE session_id = ? ORDER BY timestamp ASC LIMIT ?",
                (session_id, limit)
            )
            
            messages = []
            for row in cursor.fetchall():
                messages.append(StoredMessage(
                    role=row['role'],
                    content=row['content'],
                    timestamp=row['timestamp'],
                    metadata=json.loads(row['metadata']) if row['metadata'] else {}
                ))
            
            return messages
    
    def get_conversation(self, session_id: str, limit: int = 50) -> List[Dict]:
        """Get conversation history"""
        session = self.get_session(session_id)
        if not session:
            return []
        
        return [
            {
                "role": msg.role,
                "content": msg.content,
                "timestamp": msg.timestamp
            }
            for msg in session.messages[-limit:]
        ]
    
    def get_stats(self) -> Dict:
        """Get session statistics from unified DB"""
        with db_manager.get_connection() as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM active_sessions WHERE is_active = 1")
            active_sessions = cursor.fetchone()[0]
            
            cursor = conn.execute("SELECT COUNT(*) FROM session_messages")
            total_messages = cursor.fetchone()[0]
            
            return {
                "active_sessions": active_sessions,
                "cached_sessions": len(self._cache),
                "total_messages": total_messages
            }
