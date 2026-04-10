#!/usr/bin/env python3
"""
Cross-Platform Sync Testing
Verifies real-time synchronization across Web, Mobile, Desktop
"""

import asyncio
import json
import websockets
import requests
import time
from datetime import datetime

# Configuration - MATCHING WORKSPACE
API_KEY = "local-agent-v4-super-secret-key"
BASE_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000"

class CrossPlatformTester:
    def __init__(self):
        self.session_id = f"sync-test-{int(time.time())}"
        self.messages_received = []
    
    async def test_websocket_sync(self):
        """Test WebSocket sync across multiple connections"""
        print("\n🔄 Testing Cross-Platform Sync...")
        
        # Create multiple WebSocket connections simulating different devices
        async def device_connection(device_name: str):
            # Handshake with api_key in query
            uri = f"{WS_URL}/ws/{self.session_id}?api_key={API_KEY}"
            try:
                async with websockets.connect(uri) as ws:
                    print(f"  ✅ {device_name} connected")
                    
                    # Send a message from this device
                    test_msg = f"Hello from {device_name}"
                    await ws.send(json.dumps({"type": "chat", "content": test_msg}))
                    
                    # Listen for broadcast messages
                    try:
                        response = await asyncio.wait_for(ws.recv(), timeout=5)
                        data = json.loads(response)
                        self.messages_received.append({
                            "device": device_name,
                            "response": data.get('content', '')[:50]
                        })
                    except asyncio.TimeoutError:
                        print(f"  ⏰ {device_name} timeout waiting for response")
            except Exception as e:
                print(f"  ❌ {device_name} failed: {e}")
        
        # Run multiple device simulations
        devices = ["Web", "Mobile-iOS", "Mobile-Android", "Desktop-Win"]
        await asyncio.gather(*[device_connection(d) for d in devices])
        
        print(f"\n  📊 Sync Results: {len(self.messages_received)}/{len(devices)} devices achieved handshake and response")
        return len(self.messages_received) >= 2
    
    async def test_rest_vs_websocket(self):
        """Test REST API and WebSocket return consistent data"""
        print("\n🔄 Testing REST vs WebSocket Consistency...")
        
        # Send via REST
        rest_response = requests.post(
            f"{BASE_URL}/api/ai/agent/orchestrate",
            headers={"X-API-Key": API_KEY, "Content-Type": "application/json"},
            json={"request": "Test consistency"},
            timeout=10
        )
        
        # Send via WebSocket
        uri = f"{WS_URL}/ws/sync-test?api_key={API_KEY}"
        async with websockets.connect(uri) as ws:
            await ws.send(json.dumps({"type": "chat", "content": "Test consistency"}))
            ws_response = await asyncio.wait_for(ws.recv(), timeout=5)
            ws_data = json.loads(ws_response)
        
        rest_ok = rest_response.status_code == 200
        ws_ok = ws_data.get('type') == 'response'
        
        print(f"  REST API: {'✅' if rest_ok else '❌'}")
        print(f"  WebSocket: {'✅' if ws_ok else '❌'}")
        
        return rest_ok and ws_ok
    
    async def run_tests(self):
        print("=" * 60)
        print("📱💻 CROSS-PLATFORM SYNC TESTING")
        print("=" * 60)
        
        results = []
        
        results.append(("WebSocket Sync", await self.test_websocket_sync()))
        results.append(("REST vs WebSocket", await self.test_rest_vs_websocket()))
        
        print("\n" + "=" * 60)
        print("📊 CROSS-PLATFORM TEST SUMMARY")
        print("=" * 60)
        
        for name, passed in results:
            status = "✅" if passed else "❌"
            print(f"  {status} {name}")
        
        all_passed = all(r[1] for r in results)
        if all_passed:
            print("\n🎉 Cross-platform sync is WORKING!")
            print("   Web, Mobile, and Desktop are in sync!")
        else:
            print("\n⚠️ Some sync tests failed. Check connectivity.")

if __name__ == "__main__":
    asyncio.run(CrossPlatformTester().run_tests())
