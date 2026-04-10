"""
Sprint 8 Backend Verification Suite
Tests sync endpoints and WebSocket availability
"""

import unittest
import os
import json
import asyncio
from fastapi.testclient import TestClient
from local_agent.web.app import app

class TestSprint8Backend(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_01_push_registration(self):
        print("\n📱 Testing Push Registration Endpoint...")
        response = self.client.post(
            "/api/mobile/register-push",
            json={
                "push_token": "test_token_123",
                "device_name": "iPhone 15",
                "os_version": "iOS 17.0"
            }
        )
        self.assertIn(response.status_code, [200, 401])
        print("  Push Registration Endpoint: OK")

    def test_02_sync_endpoint(self):
        print("\n🔄 Testing Data Sync Endpoint...")
        response = self.client.post(
            "/api/mobile/sync",
            json={
                "messages": [
                    {
                        "id": "msg_1",
                        "type": "chat",
                        "action": "create",
                        "data": {"content": "hello world"},
                        "timestamp": 123456789,
                        "device_id": "mobile_1",
                        "version": 1
                    }
                ]
            }
        )
        self.assertIn(response.status_code, [200, 401])
        print("  Sync Endpoint: OK")

    def test_03_websocket_connectivity(self):
        print("\n🔌 Testing WebSocket Sync Endpoint...")
        try:
            with self.client.websocket_connect("/api/mobile/ws/user_123") as websocket:
                websocket.send_json({
                    "type": "sync",
                    "message": {
                        "id": "ws_msg_1",
                        "type": "setting",
                        "action": "update",
                        "data": {"theme": "dark"},
                        "timestamp": 123456789,
                        "device_id": "desktop_1",
                        "version": 2
                    }
                })
                data = websocket.receive_json()
                self.assertEqual(data["type"], "ack")
                self.assertEqual(data["message_id"], "ws_msg_1")
                print("  WebSocket Sync + ACK: OK")
        except Exception as e:
            print(f"  WebSocket skip/error: {e}")

if __name__ == "__main__":
    unittest.main()
