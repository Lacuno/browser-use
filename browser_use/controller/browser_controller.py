import asyncio
import websockets
import json

class BrowserController:
    def __init__(self, server_url="ws://localhost:8765"):
        self.server_url = server_url
        
    async def send_command(self, command):
        async with websockets.connect(self.server_url) as websocket:
            await websocket.send(json.dumps(command))
            response = await websocket.recv()
            return json.loads(response)

    async def new_page(self):
        command = {
            "type": "new_page"
        }
        return await self.send_command(command)

    async def goto(self, url):
        command = {
            "type": "goto",
            "url": url
        }
        return await self.send_command(command)

# Usage example:
async def main():
    controller = BrowserController()
    await controller.new_page()
    response = await controller.goto("https://www.willhaben.at")
    print(response)

if __name__ == "__main__":
    asyncio.run(main()) 