import asyncio
from langchain_openai import ChatOpenAI
from browser_use.agent.server_agent import ServerAgent

async def main():
    # Initialize the ServerAgent
    agent = ServerAgent(
        task="Initial task - will be updated via WebSocket commands",
        llm=ChatOpenAI(model="gpt-4o"),
        host="localhost",  # Use localhost for testing
        port=8765
    )
    
    # Run the agent with the WebSocket server
    try:
        history = await agent.run_with_server()
        print("Agent completed with result:", history.final_result())
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Make sure to clean up resources
        if agent.browser:
            await agent.browser.close()

if __name__ == "__main__":
    asyncio.run(main()) 