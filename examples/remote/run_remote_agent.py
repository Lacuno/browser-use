import asyncio
import sys
from pathlib import Path

from langchain_anthropic import ChatAnthropic

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from browser_use.agent.remote_agent import RemoteAgent


async def main():
    # Initialize the remote agent
    agent = RemoteAgent(
        task="Search for 'Python WebSocket' on Google and extract the first result",
        llm=ChatAnthropic(model_name="claude-3-5-sonnet-20240620", timeout=100, max_retries=2, stop=None),
        server_url="ws://localhost:8765"  # Connect to local server
        # For remote server use: "ws://server-ip:8765"
    )
    
    try:
        # Run the agent
        history = await agent.run()
        print("Agent completed with result:", history.final_result())
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 