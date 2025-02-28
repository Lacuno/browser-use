import asyncio
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from browser_use.browser.server.browser_server import BrowserServer

async def main():
    # Start the browser server
    server = BrowserServer(
        host="0.0.0.0",  # Allow external connections
        port=8765
    )
    
    print("Starting browser server...")
    await server.start()

if __name__ == "__main__":
    asyncio.run(main()) 