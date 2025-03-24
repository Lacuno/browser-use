import asyncio
import json
from aiohttp import web
import aiohttp_cors
import websockets.server
from dataclasses import asdict
from browser_use.browser.browser import Browser, BrowserConfig
from browser_use.controller.browser_controller import BrowserController

class BrowserServer:
    def __init__(self, host="0.0.0.0", port=8765, http_port=8766):
        self.host = host
        self.port = port
        self.http_port = http_port
        
        config = BrowserConfig(headless=False)
        self.browser = Browser(config)
        self.controller = BrowserController()
        self.contexts = {}  # Store browser contexts by session ID
        
        # Setup HTTP server
        self.app = web.Application()
        self.setup_cors()
        self.setup_routes()
        
    def setup_cors(self):
        # Configure CORS to allow requests from any origin
        self.cors = aiohttp_cors.setup(self.app, defaults={
            "*": aiohttp_cors.ResourceOptions(
                allow_credentials=True,
                expose_headers="*",
                allow_headers="*",
                max_age=3600,
                allow_methods=["GET", "OPTIONS"]
            )
        })
    
    def setup_routes(self):
        # Add routes
        route = self.app.router.add_resource('/status/{agentId}')
        route.add_route('GET', self.handle_status)
        
        # Add CORS to all routes
        self.cors.add(route)
    
    async def handle_status(self, request):
        """HTTP endpoint to check if a specific agent is connected
        
        Must be accessed with an agentId parameter:
        - /status/{agentId} - returns status of a specific agent
        """
        agent_id = request.match_info.get('agentId')
        
        if not agent_id:
            return web.json_response({
                "status": "error",
                "message": "Missing required parameter: agentId"
            }, status=400)
            
        # Check for specific agent
        if agent_id in self.contexts:
            return web.json_response({
                "status": "connected",
                "agent_id": agent_id,
                "connected_since": getattr(self.contexts[agent_id], 'connected_since', 'unknown')
            })
        else:
            return web.json_response({
                "status": "disconnected",
                "agent_id": agent_id
            })
    
    async def start(self):
        # Start HTTP server
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, self.host, self.http_port)
        await site.start()
        print(f"HTTP server running on http://{self.host}:{self.http_port}")
        
        # Start WebSocket server
        async with websockets.server.serve(self.handle_connection, self.host, self.port):
            print(f"WebSocket server running on ws://{self.host}:{self.port}")
            await asyncio.Future()  # run forever

    async def handle_connection(self, websocket):
        session_id = str(id(websocket))
        context = await self.browser.new_context()
        # Add connection timestamp
        context.connected_since = asyncio.get_event_loop().time()
        self.contexts[session_id] = context
        
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