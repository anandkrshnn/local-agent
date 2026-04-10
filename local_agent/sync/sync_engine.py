"""
Real-time Sync Engine for Mobile & Desktop
WebSocket live updates + offline queue + conflict resolution
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from fastapi import WebSocket, WebSocketDisconnect

from local_agent.core.db import db_manager

logger = logging.getLogger(__name__)

@dataclass
class SyncMessage:
    """Message to sync across devices"""
    id: str
    type: str  # 'chat', 'file', 'setting'
    action: str  # 'create', 'update', 'delete'
    data: Dict
    timestamp: float
    device_id: str
    version: int

class SyncManager:
    """
    Real-time sync manager for cross-device synchronization
    Handles offline queue and conflict resolution using unified DB
    """
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, user_id: str, websocket: WebSocket):
        """Connect a device for real-time sync"""
        self.active_connections[user_id] = websocket
        
        # Send pending messages
        await self._send_pending_messages(user_id, websocket)
    
    def disconnect(self, user_id: str):
        """Disconnect a device"""
        if user_id in self.active_connections:
            del self.active_connections[user_id]
    
    async def broadcast(self, user_id: str, message: SyncMessage):
        """Broadcast message to all devices of user"""
        if user_id in self.active_connections:
            try:
                await self.active_connections[user_id].send_text(
                    json.dumps({
                        "type": "sync",
                        "message": message.__dict__
                    })
                )
            except Exception:
                # Device offline or connection closed, queue message
                self._queue_message(user_id, message)
        else:
            # Device not connected, queue for late sync
            self._queue_message(user_id, message)
    
    def _queue_message(self, user_id: str, message: SyncMessage):
        """Queue message for offline device in unified DB"""
        db_manager.execute(
            "INSERT OR REPLACE INTO sync_queue (id, user_id, message, created_at) VALUES (?, ?, ?, ?)",
            (message.id, user_id, json.dumps(message.__dict__), datetime.now().timestamp())
        )
    
    async def _send_pending_messages(self, user_id: str, websocket: WebSocket):
        """Send queued messages to newly connected device"""
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT id, message FROM sync_queue WHERE user_id = ? AND synced_at IS NULL",
                (user_id,)
            )
            
            rows = cursor.fetchall()
            for row in rows:
                msg_id, msg_json = row
                try:
                    await websocket.send_text(msg_json)
                    # Mark as synced
                    cursor.execute(
                        "UPDATE sync_queue SET synced_at = ? WHERE id = ?",
                        (datetime.now().timestamp(), msg_id)
                    )
                except Exception:
                    break
            
            conn.commit()
    
    def resolve_conflict(self, existing: Dict, incoming: Dict) -> Dict:
        """
        Resolve conflicts using last-write-wins strategy
        """
        if existing.get('version', 0) >= incoming.get('version', 0):
            return existing
        return incoming

sync_manager = SyncManager()
