"""LangGraph integration example for LangChain UTCP Adapters.

This example demonstrates how to use UTCP tools with LangGraph agents.
"""

import asyncio
import json
import os
from pathlib import Path

from langchain_utcp_adapters.client import MultiProviderUTCPClient

# Optional: Only import if available
try:
    from langgraph.prebuilt import create_react_agent
    from langchain_openai import ChatOpenAI
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False
    print("LangGraph or OpenAI not available. Install with: pip install langgraph langchain-openai")


async def create_sample_utcp_server():
    """Create a simple UTCP server for demonstration."""
    try:
        from fastapi import FastAPI
        from utcp.shared.tool import Tool, ToolInputOutputSchema
        from utcp.shared.provider import HttpProvider
        import uvicorn
        import threading
        import time
        
        app = FastAPI()
        
        # Define a simple tool
        calculator_tool = Tool(
            name="add_numbers",
            description="Add two numbers together",
            inputs=ToolInputOutputSchema(
                type="object",
                properties={
                    "a": {"type": "number", "description": "First number"},
                    "b": {"type": "number", "description": "Second number"}
                },
                required=["a", "b"]
            ),
            outputs=ToolInputOutputSchema(
                type="object",
                properties={
                    "result": {"type": "number", "description": "Sum of the two numbers"}
                }
            ),
            tags=["math", "calculator"],
            tool_provider=HttpProvider(
                name="math_server",
                url="http://localhost:8080/calculate",
                http_method="POST"
            )
        )
        
        @app.get("/utcp")
        def get_utcp_manual():
            """Return the UTCP manual."""
            return {
                "version": "1.0",
                "tools": [calculator_tool.model_dump()]
            }
        
        @app.post("/calculate")
        def calculate(data: dict):
            """Perform the calculation."""
            a = data.get("a", 0)
            b = data.get("b", 0)
            return {"result": a + b}
        
        # Start server in a separate thread
        def run_server():
            uvicorn.run(app, host="localhost", port=8080, log_level="error")
        
        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()
        time.sleep(2)  # Give server time to start
        
        return True
        
    except ImportError:
        print("FastAPI not available for creating sample server")
        return False


async def main():
    """Main example function."""
    if not LANGGRAPH_AVAILABLE:
        return
    
    # Check for OpenAI API key
    if not os.getenv("OPENAI_API_KEY"):
        print("Please set OPENAI_API_KEY environment variable")
        return
    
    # Try to create a sample server
    server_created = await create_sample_utcp_server()
    
    # Create providers configuration
    providers_config = [
        {
            "name": "math_server",
            "provider_type": "http",
            "url": "http://localhost:8080/utcp",
            "http_method": "GET"
        }
    ]
    
    # If no local server, use a public API example
    if not server_created:
        providers_config = [
            {
                "name": "httpbin",
                "provider_type": "http", 
                "url": "http://httpbin.org/anything",
                "http_method": "POST"
            }
        ]
    
    # Write providers config to file
    providers_file = Path("providers.json")
    with open(providers_file, "w") as f:
        json.dump(providers_config, f, indent=2)
    
    try:
        # Create UTCP client
        print("Creating UTCP client...")
        client = MultiProviderUTCPClient(
            providers_file_path="providers.json"
        )
        
        # Get tools
        print("Loading tools...")
        tools = await client.get_tools()
        print(f"Found {len(tools)} tools")
        
        if not tools:
            print("No tools found. Cannot proceed with LangGraph example.")
            return
        
        # Create LangGraph agent
        print("Creating LangGraph agent...")
        llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)
        agent = create_react_agent(llm, tools)
        
        # Test the agent
        if server_created:
            test_message = "What is 15 + 27?"
        else:
            test_message = "Can you help me test the available tools?"
        
        print(f"\nTesting agent with message: '{test_message}'")
        
        try:
            response = await agent.ainvoke({"messages": [{"role": "user", "content": test_message}]})
            print("\nAgent response:")
            print(response["messages"][-1].content)
        except Exception as e:
            print(f"Error running agent: {e}")
        
        # Clean up
        await client.close()
        
    finally:
        # Clean up the providers file
        if providers_file.exists():
            providers_file.unlink()


if __name__ == "__main__":
    asyncio.run(main())
