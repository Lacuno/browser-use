import asyncio
import json
from websockets.server import serve
from dataclasses import asdict
from browser_use.browser.browser import Browser, BrowserConfig
from browser_use.controller.browser_controller import BrowserController

class BrowserServer:
    def __init__(self, host="0.0.0.0", port=8765):
        self.host = host
        self.port = port

        config = BrowserConfig(headless=False)
        self.browser = Browser(config)
        
    async def start(self):
        async with serve(self.handle_connection, self.host, self.port):
            print(f"Browser server running on ws://{self.host}:{self.port}")
            await asyncio.Future()  # run forever

    async def handle_connection(self, websocket):
        try:
            async for message in websocket:
                command = json.loads(message)
                response = await self.execute_command(command)
                await websocket.send(json.dumps(response))
        except Exception as e:
            print(f"Error: {e}")
            
    async def execute_command(self, command):
        try:
            # Handle different command types
            if command["type"] == "goto":
                print(f"Visiting {command['url']}")
                context = await self.browser.new_context()
                page = await context.get_current_page()
                print(f"Page: {page}")
                await page.goto(command["url"])
                return {"status": "success"}
            # Add more command types as needed
            return {"status": "error", "message": "Unknown command"}
        except Exception as e:
            return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    server = BrowserServer()
    asyncio.run(server.start())