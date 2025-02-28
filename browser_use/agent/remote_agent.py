from __future__ import annotations

import asyncio
import json
from typing import Optional, Any, Dict
import websockets
from dataclasses import asdict
from langchain_core.language_models.chat_models import BaseChatModel

from browser_use.agent.service import Agent
from browser_use.controller.service import Controller
from browser_use.browser.views import BrowserState

class RemoteAgent(Agent):
    def __init__(
        self,
        task: str,
        llm: BaseChatModel,
        server_url: str = "ws://localhost:8765",
        controller: Controller[Any] = Controller(),
        **kwargs
    ):
        # Initialize connection settings
        self.server_url = server_url
        self.websocket = None
        
        # Initialize the Agent without browser
        super().__init__(
            task=task,
            llm=llm,
            browser=None,  # No local browser
            controller=controller,
            **kwargs
        )
        
    async def _connect(self):
        """Establish WebSocket connection to browser server"""
        if not self.websocket:
            self.websocket = await websockets.connect(self.server_url)
            
    async def _disconnect(self):
        """Close WebSocket connection"""
        if self.websocket:
            await self.websocket.close()
            self.websocket = None
            
    async def _send_command(self, command: Dict):
        """Send command to browser server and get response"""
        if not self.websocket:
            await self._connect()
        await self.websocket.send(json.dumps(command))
        response = await self.websocket.recv()
        return json.loads(response)
        
    async def navigate(self, url: str):
        """Navigate to URL on remote browser"""
        response = await self._send_command({
            "type": "goto",
            "url": url
        })
        if response["status"] != "success":
            raise Exception(f"Navigation failed: {response.get('message', 'Unknown error')}")
            
    async def get_browser_state(self) -> BrowserState:
        """Get current state from remote browser"""
        response = await self._send_command({
            "type": "get_state"
        })
        if response["status"] != "success":
            raise Exception(f"Failed to get state: {response.get('message', 'Unknown error')}")
        return BrowserState(**response["state"])
        
    async def execute_action(self, action: Dict):
        """Execute action on remote browser"""
        response = await self._send_command({
            "type": "execute_action",
            "action": action
        })
        if response["status"] != "success":
            raise Exception(f"Action failed: {response.get('message', 'Unknown error')}")
        return response.get("result")
        
    async def get_page_content(self) -> str:
        """Get current page content from remote browser"""
        response = await self._send_command({
            "type": "get_page_content"
        })
        if response["status"] != "success":
            raise Exception(f"Failed to get content: {response.get('message', 'Unknown error')}")
        return response["content"]
        
    async def run(self, max_steps: int = 100):
        """Run the agent using remote browser"""
        try:
            await self._connect()
            return await super().run(max_steps)
        finally:
            await self._disconnect() 