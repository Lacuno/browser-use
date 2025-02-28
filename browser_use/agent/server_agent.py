from __future__ import annotations

import asyncio
import json
from typing import Optional, Any
import websockets.server
from langchain_core.language_models.chat_models import BaseChatModel

from browser_use.agent.service import Agent
from browser_use.browser.browser import Browser, BrowserConfig
from browser_use.controller.service import Controller
from browser_use.browser.context import BrowserContext

class ServerAgent(Agent):
    def __init__(
        self,
        task: str,
        llm: BaseChatModel,
        host: str = "0.0.0.0",
        port: int = 8765,
        browser: Optional[Browser] = None,
        browser_context: Optional[BrowserContext] = None,
        controller: Controller[Any] = Controller(),
        **kwargs
    ):
        # Initialize the WebSocket server settings
        self.host = host
        self.port = port
        self.server_task = None
        
        # Create browser if not provided
        if not browser and not browser_context:
            config = BrowserConfig(headless=False)
            browser = Browser(config)
            
        # Initialize the Agent
        super().__init__(
            task=task,
            llm=llm,
            browser=browser,
            browser_context=browser_context,
            controller=controller,
            **kwargs
        )
        
    async def start_server(self):
        """Start the WebSocket server"""
        self.server_task = asyncio.create_task(self._run_server())
        print(f"Browser server running on ws://{self.host}:{self.port}")
        
    async def _run_server(self):
        """Run the WebSocket server"""
        async with websockets.server.serve(self._handle_connection, self.host, self.port):
            await asyncio.Future()  # run forever
            
    async def _handle_connection(self, websocket):
        """Handle WebSocket connections"""
        try:
            async for message in websocket:
                command = json.loads(message)
                response = await self._execute_command(command)
                await websocket.send(json.dumps(response))
        except Exception as e:
            print(f"Error: {e}")
            await websocket.send(json.dumps({"status": "error", "message": str(e)}))
            
    async def _execute_command(self, command):
        """Execute commands received through WebSocket"""
        try:
            if command["type"] == "goto":
                if not self.browser:
                    return {"status": "error", "message": "No browser instance available"}
                context = await self.browser.new_context()
                page = await context.get_current_page()
                await page.goto(command["url"])
                return {"status": "success"}
            elif command["type"] == "run_agent":
                # Run the agent with the provided task
                if "task" in command:
                    self.task = command["task"]
                history = await self.run(max_steps=command.get("max_steps", 100))
                return {
                    "status": "success",
                    "result": history.final_result(),
                    "is_done": history.is_done(),
                    "has_errors": history.has_errors(),
                    "errors": history.errors()
                }
            return {"status": "error", "message": "Unknown command"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
            
    async def run_with_server(self, max_steps: int = 100):
        """Run both the agent and the WebSocket server"""
        # Start the WebSocket server
        await self.start_server()
        
        try:
            # Run the agent
            history = await self.run(max_steps=max_steps)
            return history
        except Exception as e:
            print(f"Error running agent: {e}")
            raise
        finally:
            # Clean up server task if it exists
            if self.server_task:
                self.server_task.cancel()
                try:
                    await self.server_task
                except asyncio.CancelledError:
                    pass 