"""Multi-user session management"""

import uuid
import time
from typing import Dict, Optional, List
from dataclasses import dataclass, field

@dataclass
class Message:
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: float

@dataclass
class UserSession:
    session_id: str
    created_at: float
    last_active: float
    messages: List[Message] = field(default_factory=list)
    agent: Optional['LocalAgent'] = None
    
    def __post_init__(self):
        from ..core.agent import LocalAgent
        self.agent = LocalAgent(verbose=False)
    
    def add_message(self, role: str, content: str):
        self.messages.append(Message(role=role, content=content, timestamp=time.time()))
        self.last_active = time.time()
        
        # Keep last 100 messages for context
        if len(self.messages) > 100:
            self.messages = self.messages[-100:]

class SessionManager:
    """Manage multiple user sessions"""
    
    def __init__(self, max_sessions: int = 100):
        self.sessions: Dict[str, UserSession] = {}
        self.max_sessions = max_sessions
    
    def create(self) -> UserSession:
        """Create a new session"""
        # Clean up old sessions if at limit
        if len(self.sessions) >= self.max_sessions:
            oldest = min(self.sessions.items(), key=lambda x: x[1].last_active)
            del self.sessions[oldest[0]]
        
        session_id = str(uuid.uuid4())
        session = UserSession(
            session_id=session_id,
            created_at=time.time(),
            last_active=time.time()
        )
        self.sessions[session_id] = session
        return session
    
    def get(self, session_id: str) -> Optional[UserSession]:
        """Get session by ID"""
        session = self.sessions.get(session_id)
        if session:
            session.last_active = time.time()
        return session
    
    def get_or_create(self, session_id: Optional[str]) -> UserSession:
        """Get existing session or create new one"""
        if session_id and session_id in self.sessions:
            return self.sessions[session_id]
        return self.create()
    
    def get_active_count(self) -> int:
        """Get number of active sessions (last 5 minutes)"""
        cutoff = time.time() - 300  # 5 minutes
        return sum(1 for s in self.sessions.values() if s.last_active > cutoff)
    
    def delete(self, session_id: str):
        """Delete a session"""
        if session_id in self.sessions:
            del self.sessions[session_id]
