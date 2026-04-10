"""
Mobile-specific API endpoints
Push notifications, offline sync, device management
"""

import json
import sqlite3
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Request, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from typing import Optional, List
import asyncio

from .auth import get_current_active_user
from ..sync.sync_engine import sync_manager, SyncMessage

router = APIRouter(prefix="/api/mobile", tags=["Mobile"])

class PushTokenRequest(BaseModel):
    push_token: str
    device_name: Optional[str] = None
    os_version: Optional[str] = None

class SyncRequest(BaseModel):
    messages: List[dict]
    last_sync: Optional[float] = None

@router.post("/register-push")
async def register_push_token(
    request: PushTokenRequest,
    current_user: dict = Depends(get_current_active_user)
):
    """Register device for push notifications in unified DB"""
    with db_manager.get_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO device_tokens (user_id, push_token, device_name, os_version, registered_at)
            VALUES (?, ?, ?, ?, ?)
        """, (current_user['id'], request.push_token, request.device_name, 
              request.os_version, datetime.now().timestamp()))
        
        conn.commit()
    
    return {"status": "registered"}

@router.post("/sync")
async def sync_data(
    request: SyncRequest,
    current_user: dict = Depends(get_current_active_user)
):
    """Sync local changes with server"""
    
    # Process incoming messages
    for msg_data in request.messages:
        message = SyncMessage(**msg_data)
        
        # Broadcast to other devices
        await sync_manager.broadcast(current_user['id'], message)
    
    # Return new messages (simplified)
    return {"synced": True, "timestamp": datetime.now().timestamp()}

@router.websocket("/ws/{user_id}")
async def websocket_sync(websocket: WebSocket, user_id: str):
    """WebSocket endpoint for real-time sync"""
    await websocket.accept()
    await sync_manager.connect(user_id, websocket)
    
    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            if message_data.get('type') == 'sync':
                # Process sync message
                sync_msg = SyncMessage(**message_data['message'])
                
                # Broadcast to other devices
                await sync_manager.broadcast(user_id, sync_msg)
                
                # Acknowledge
                await websocket.send_text(json.dumps({
                    "type": "ack",
                    "message_id": sync_msg.id
                }))
    
    except WebSocketDisconnect:
        sync_manager.disconnect(user_id)
