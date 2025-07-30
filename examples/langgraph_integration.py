"""LangGraph integration example for LangChain UTCP Adapters.

This example demonstrates how to use UTCP tools with LangGraph agents.
"""

import asyncio
import json
import os
from pathlib import Path

from utcp.client.utcp_client import UtcpClient
from utcp.client.utcp_client_config import UtcpClientConfig
from utcp.shared.provider import HttpProvider
from langchain_utcp_adapters import load_utcp_tools

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
            tool_provider=HttpProvider(
                name="calculator",
                url="http://localhost:8000/add",
                http_method="POST"
            )
        )
        
        @app.get("/utcp")
        def get_utcp_manual():
            """Return UTCP manual with available tools."""
            return {
                "version": "1.0",
                "tools": [calculator_tool.model_dump()]
            }
        
        @app.post("/add")
        def add_numbers(a: float, b: float):
            """Add two numbers."""
            return {"result": a + b}
        
        # Start server in background thread
        def run_server():
            uvicorn.run(app, host="127.0.0.1", port=8000, log_level="error")
        
        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()
        time.sleep(2)  # Give server time to start
        
        return "http://localhost:8000/utcp"
        
    except ImportError:
        print("FastAPI not available for demo server. Using httpbin instead.")
        return None


async def main():
    """Main example function."""
    print("🤖 LangGraph + UTCP Integration Example")
    print("=" * 40)
    
    if not LANGGRAPH_AVAILABLE:
        return
    
    # Check for OpenAI API key
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY environment variable not set")
        print("Set it with: export OPENAI_API_KEY=your_key_here")
        return
    
    # Create UTCP client
    print("📡 Setting up UTCP client...")
    config = UtcpClientConfig()
    client = await UtcpClient.create(config=config)
    
    # Try to create a demo server, fallback to httpbin
    demo_server_url = await create_sample_utcp_server()
    
    if demo_server_url:
        # Register the demo server
        demo_provider = HttpProvider(
            name="calculator_demo",
            provider_type="http",
            url=demo_server_url,
            http_method="GET"
        )
        await client.register_tool_provider(demo_provider)
    else:
        # Fallback: Register httpbin for testing
        httpbin_provider = HttpProvider(
            name="httpbin_test",
            provider_type="http",
            url="http://httpbin.org/anything",
            http_method="POST"
        )
        await client.register_tool_provider(httpbin_provider)
    
    # Load tools and convert to LangChain format
    print("🔧 Loading UTCP tools...")
    tools = await load_utcp_tools(client)
    print(f"Loaded {len(tools)} tools for the agent:")
    
    for tool in tools:
        print(f"  - {tool.name}: {tool.description}")
    
    if not tools:
        print("❌ No tools available. Cannot create agent.")
        return
    
    # Create LangGraph agent with UTCP tools
    print("🤖 Creating LangGraph agent...")
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    agent = create_react_agent(llm, tools)
    
    # Test the agent
    print("💬 Testing agent...")
    try:
        if demo_server_url:
            # Test with calculator if available
            response = await agent.ainvoke({
                "messages": [("user", "Add 15 and 27 together")]
            })
        else:
            # Test with httpbin
            response = await agent.ainvoke({
                "messages": [("user", "Make a test HTTP request with some data")]
            })
        
        print("🎉 Agent response:")
        print(response["messages"][-1].content)
        
    except Exception as e:
        print(f"❌ Agent execution failed: {e}")
    
    print("\n✅ Example completed!")


if __name__ == "__main__":
    asyncio.run(main())
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
