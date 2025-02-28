import asyncio
import json
import websockets.server
from dataclasses import asdict
from browser_use.browser.browser import Browser, BrowserConfig
from browser_use.controller.browser_controller import BrowserController

class BrowserServer:
    def __init__(self, host="0.0.0.0", port=8765):
        self.host = host
        self.port = port
        
        config = BrowserConfig(headless=False)
        self.browser = Browser(config)
        self.controller = BrowserController()
        self.contexts = {}  # Store browser contexts by session ID
        
    async def start(self):
        async with websockets.server.serve(self.handle_connection, self.host, self.port):
            print(f"Browser server running on ws://{self.host}:{self.port}")
            await asyncio.Future()  # run forever

    async def handle_connection(self, websocket):
        session_id = str(id(websocket))
        self.contexts[session_id] = await self.browser.new_context()
        try:
            async for message in websocket:
                command = json.loads(message)
                response = await self.execute_command(command, session_id)
                await websocket.send(json.dumps(response))
        except Exception as e:
            print(f"Error: {e}")
        finally:
            # Clean up context when connection closes
            if session_id in self.contexts:
                await self.contexts[session_id].close()
                del self.contexts[session_id]
            
    async def execute_command(self, command, session_id):
        try:
            print(f"Executing command: {command}")
            context = self.contexts.get(session_id)
            if not context:
                return {"status": "error", "message": "No browser context available"}

            if command["type"] == "goto":
                page = await context.get_current_page()
                await page.goto(command["url"])
                return {"status": "success"}
                
            elif command["type"] == "get_state":
                state = await context.get_state()
                return {
                    "status": "success",
                    "state": asdict(state)
                }
                
            elif command["type"] == "execute_action":
                if "action" not in command:
                    return {"status": "error", "message": "No action specified"}
                result = await self.controller.act(
                    context,
                    command["action"]
                )
                return {
                    "status": "success",
                    "result": asdict(result) if result else None
                }
                
            elif command["type"] == "get_page_content":
                page = await context.get_current_page()
                content = await page.content()
                return {
                    "status": "success",
                    "content": content
                }
                
            return {"status": "error", "message": "Unknown command"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    server = BrowserServer()
    asyncio.run(server.start()) 