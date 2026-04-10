# test_websocket_fixed.py
import asyncio
import websockets
import json

async def test_websocket():
    """Test WebSocket connection with API key query parameter"""
    
    API_KEY = "local-agent-v4-super-secret-key" # Matching our .env
    SESSION_ID = "test-session-final"
    
    print("=" * 50)
    print("Testing WebSocket Connection (Handshake Fix)")
    print("=" * 50)
    
    # 1. Test without API key (should be rejected with 4001)
    uri_fail = f"ws://localhost:8000/ws/{SESSION_ID}"
    print(f"\n1. Connecting WITHOUT API key: {uri_fail}")
    try:
        async with websockets.connect(uri_fail) as ws:
            print("   ❌ Connected without API key (Should have failed!)")
    except websockets.exceptions.InvalidStatusCode as e:
        print(f"   ✅ Rejected as expected: {e}")
    except Exception as e:
        print(f"   ✅ Connection closed as expected: {e}")

    # 2. Test WITH API key
    uri_pass = f"ws://localhost:8000/ws/{SESSION_ID}?api_key={API_KEY}"
    print(f"\n2. Connecting WITH API key: {uri_pass.replace(API_KEY, '***')}")
    
    try:
        async with websockets.connect(uri_pass) as ws:
            print("   ✅ Connected successfully!")
            
            # Send a test message
            test_msg = {"type": "chat", "content": "Explain advanced features"}
            await ws.send(json.dumps(test_msg))
            print("   📤 Sent test message")
            
            # Wait for response
            response = await asyncio.wait_for(ws.recv(), timeout=10)
            data = json.loads(response)
            print(f"   📥 Received response: {data.get('content', '')[:100]}...")
            print("\n✅ WebSocket Handshake & Chat Test: PASSED")
            return True
            
    except Exception as e:
        print(f"   ❌ WebSocket test FAILED: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_websocket())
    exit(0 if result else 1)
