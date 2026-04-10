import asyncio
import websockets
import json

async def test_ws():
    uri = "ws://localhost:8000/ws/test-session"
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ Connected to WebSocket")
            await websocket.send(json.dumps({"type": "chat", "content": "Hello"}))
            response = await websocket.recv()
            print(f"📩 Received: {response}")
    except Exception as e:
        print(f"❌ Failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_ws())
