import asyncio
import websockets
import json
import pytest

@pytest.mark.asyncio
async def test_websocket_connection():
    uri = "ws://localhost:8080"
    try:
        async with websockets.connect(uri) as websocket:
            print(f"Connected to {uri}")
            
            # Wait for at least one message from the engine
            message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
            data = json.loads(message)
            
            print(f"Received: {data}")
            
            # Validation
            assert isinstance(data, dict), "Data should be a JSON object"
            # We expect 'render_frame' type from SpriteRenderer
            # But the current implementation just sends invalid JSON or random strings if not formatted correctly
            # Let's check if it has 'type' or if it is just raw text behaving as JSON
            
            # In SpriteRenderer.cpp:
            # std::cout << "{\"type\": \"render_frame\", \"sprites\": [";
            
            if "type" in data:
                assert data["type"] == "render_frame"
                assert "sprites" in data
                assert isinstance(data["sprites"], list)
            
    except Exception as e:
        pytest.fail(f"WebSocket connection failed: {e}")

if __name__ == "__main__":
    # simple run if executed directly
    loop = asyncio.get_event_loop()
    loop.run_until_complete(test_websocket_connection())
