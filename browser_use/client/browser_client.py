import asyncio
import websockets
import json

class BrowserClient:
    def __init__(self, server_url="ws://localhost:8765"):
        self.server_url = server_url
        
    async def connect(self):
        async with websockets.connect(self.server_url) as websocket:
            print("Connected to browser server")
            # Keep connection alive and wait for commands
            while True:
                try:
                    message = await websocket.recv()
                    command = json.loads(message)
                    response = await self.execute_command(command)
                    await websocket.send(json.dumps(response))
                except Exception as e:
                    print(f"Error: {e}")
                    break

    async def execute_command(self, command):
        try:
            # Execute the browser command locally
            if command["type"] == "browser_command":
                # Handle browser commands using the existing Browser class
                return {"status": "success", "result": "Command executed"}
            return {"status": "error", "message": "Unknown command"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    client = BrowserClient()
    asyncio.run(client.connect()) 