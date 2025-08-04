"""Simple LangGraph integration example using direct UTCP client.

This example shows how to use UTCP tools with LangGraph agents
using the simplified direct approach.
"""

import asyncio
import os
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


async def main():
    """Simple LangGraph integration example."""
    print("🤖 Simple LangGraph + UTCP Integration")
    print("=" * 40)
    
    if not LANGGRAPH_AVAILABLE:
        return
    
    # Check for OpenAI API key
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY environment variable not set")
        print("Set it with: export OPENAI_API_KEY=your_key_here")
        return
    
    # Create UTCP client directly
    print("📡 Setting up UTCP client...")
    config = UtcpClientConfig()
    utcp_client = await UtcpClient.create(config=config)
    
    # Register a simple provider for demonstration
    openlibrary_provider = HttpProvider(
        name="openlibrary",
        provider_type="http",
        http_method="GET", 
        url="https://openlibrary.org/static/openapi.json",
        content_type="application/json"
    )
    await utcp_client.register_tool_provider(openlibrary_provider)
    
    # Load tools and convert to LangChain format
    print("🔧 Loading UTCP tools...")
    tools = await load_utcp_tools(utcp_client)
    print(f"Loaded {len(tools)} tools for the agent")
    
    # Create LangGraph agent with UTCP tools
    print("🤖 Creating LangGraph agent...")
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    agent = create_react_agent(llm, tools)
    
    # Test the agent
    print("💬 Testing agent with book search query...")
    try:
        response = await agent.ainvoke({
            "messages": [("user", "Find information about books by George Orwell")]
        })
        
        print("🎉 Agent response:")
        print(response["messages"][-1].content)
        
    except Exception as e:
        print(f"❌ Agent execution failed: {e}")
    
    print("\n✅ Example completed!")


if __name__ == "__main__":
    asyncio.run(main())
