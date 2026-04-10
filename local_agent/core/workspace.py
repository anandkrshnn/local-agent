"""
Team Collaboration - Workspace Management
Shared spaces for teams to collaborate
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel

from local_agent.core.db import db_manager

logger = logging.getLogger(__name__)

class WorkspaceCreate(BaseModel):
    name: str
    description: Optional[str] = None

class WorkspaceResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    owner_id: int
    member_count: int
    created_at: float

class WorkspaceManager:
    """
    Manages team workspaces using the unified database layer.
    Supports SQLite and PostgreSQL.
    """
    
    def create_workspace(self, name: str, owner_id: int, description: str = None) -> int:
        """Create a new team workspace"""
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            now = datetime.utcnow().timestamp()
            cursor.execute("""
                INSERT INTO workspaces (name, description, owner_id, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
            """, (name, description, owner_id, now, now))
            
            workspace_id = cursor.lastrowid
            
            # Add owner as admin
            cursor.execute("""
                INSERT INTO workspace_members (workspace_id, user_id, role)
                VALUES (?, ?, ?)
            """, (workspace_id, owner_id, 'admin'))
            
            conn.commit()
            return workspace_id
    
    def add_member(self, workspace_id: int, user_id: int, role: str = 'member'):
        """Add or update a workspace member"""
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            # Using standard REPLACE pattern supported by db_manager or cross-DB equivalent
            cursor.execute("""
                INSERT OR REPLACE INTO workspace_members (workspace_id, user_id, role, joined_at)
                VALUES (?, ?, ?, ?)
            """, (workspace_id, user_id, role, datetime.utcnow().timestamp()))
            
            conn.commit()
    
    def remove_member(self, workspace_id: int, user_id: int):
        """Remove a member from a workspace"""
        db_manager.execute(
            "DELETE FROM workspace_members WHERE workspace_id = ? AND user_id = ?",
            (workspace_id, user_id)
        )
    
    def get_workspace_members(self, workspace_id: int) -> List[Dict]:
        """Get all members of a specific workspace"""
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT u.id, u.username, u.email, u.full_name, wm.role, wm.joined_at
                FROM workspace_members wm
                JOIN users u ON wm.user_id = u.id
                WHERE wm.workspace_id = ?
            """, (workspace_id,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_user_workspaces(self, user_id: int) -> List[Dict]:
        """List all workspaces a user is part of"""
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT w.*, COUNT(wm.user_id) as member_count
                FROM workspaces w
                JOIN workspace_members wm ON w.id = wm.workspace_id
                WHERE wm.user_id = ?
                GROUP BY w.id
            """, (user_id,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def share_chat_session(self, workspace_id: int, chat_id: int, name: str, created_by: int):
        """Share a chat session with a workspace"""
        db_manager.execute(
            "INSERT INTO shared_chats (workspace_id, id, name, created_by, created_at) VALUES (?, ?, ?, ?, ?)",
            (workspace_id, chat_id, name, created_by, datetime.utcnow().timestamp())
        )
    
    def share_knowledge_base(self, workspace_id: int, kb_name: str, 
                               vector_db_path: str, created_by: int) -> int:
        """Share a knowledge base with a workspace"""
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO shared_knowledge_bases (workspace_id, name, vector_db_path, created_by, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (workspace_id, kb_name, vector_db_path, created_by, datetime.utcnow().timestamp()))
            
            kb_id = cursor.lastrowid
            conn.commit()
            return kb_id

workspace_manager = WorkspaceManager()
