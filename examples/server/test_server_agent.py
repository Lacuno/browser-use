import asyncio
import websockets
import json

async def test_server():
    uri = "ws://localhost:8765"
    async with websockets.connect(uri) as websocket:
        # Test navigation
        await websocket.send(json.dumps({
            "type": "goto",
            "url": "https://www.example.com"
        }))
        response = await websocket.recv()
        print("Navigation response:", response)
        
        # Test running agent with a new task
        await websocket.send(json.dumps({
            "type": "run_agent",
            "task": "Extract the title and first paragraph from the current page",
            "max_steps": 5
        }))
        response = await websocket.recv()
        print("Agent response:", response)

if __name__ == "__main__":
    asyncio.run(test_server()) 