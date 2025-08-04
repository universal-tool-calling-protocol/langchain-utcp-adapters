"""Simple Amazon Bedrock integration example for LangChain UTCP Adapters.

This is a streamlined example showing the core integration between
UTCP tools and Amazon Bedrock models.
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
    from langchain_aws import ChatBedrock
    import boto3
    BEDROCK_AVAILABLE = True
except ImportError:
    BEDROCK_AVAILABLE = False
    print("Install Bedrock dependencies: pip install langchain-aws boto3")


async def main():
    """Simple Bedrock integration example."""
    print("Simple Amazon Bedrock + UTCP Integration")
    print("=" * 45)
    
    if not BEDROCK_AVAILABLE:
        return
    
    # Check AWS credentials
    try:
        session = boto3.Session()
        credentials = session.get_credentials()
        if not credentials:
            print("❌ No AWS credentials found")
            print("Run 'aws configure' or set environment variables:")
            print("  export AWS_ACCESS_KEY_ID=your_key")
            print("  export AWS_SECRET_ACCESS_KEY=your_secret")
            print("  export AWS_DEFAULT_REGION=us-east-1")
            return
        print("✅ AWS credentials found")
    except Exception as e:
        print(f"❌ AWS credential error: {e}")
        return
    
    # Create UTCP client
    print("📡 Setting up UTCP client...")
    config = UtcpClientConfig()
    client = await UtcpClient.create(config=config)
    
    # Register simple providers using public APIs
    print("📡 Registering tool providers...")
    
    # Register HTTPBin for testing
    httpbin_provider = HttpProvider(
        name="httpbin",
        provider_type="http",
        url="http://httpbin.org/anything",
        http_method="POST"
    )
    await client.register_tool_provider(httpbin_provider)
    
    # Register JSONPlaceholder for demo data
    jsonplaceholder_provider = HttpProvider(
        name="jsonplaceholder",
        provider_type="http",
        url="https://jsonplaceholder.typicode.com",
        http_method="GET"
    )
    await client.register_tool_provider(jsonplaceholder_provider)
    
    # Load tools and convert to LangChain format
    print("🔧 Loading UTCP tools...")
    tools = await load_utcp_tools(client)
    print(f"Loaded {len(tools)} tools for Bedrock agent:")
    
    for tool in tools[:3]:  # Show first 3 tools
        print(f"  - {tool.name}: {tool.description}")
    if len(tools) > 3:
        print(f"  ... and {len(tools) - 3} more tools")
    
    if not tools:
        print("❌ No tools available. Cannot create agent.")
        return
    
    # Create Bedrock LLM
    print("🤖 Creating Bedrock LLM...")
    try:
        # Use Claude 3 Haiku (most cost-effective)
        llm = ChatBedrock(
            model_id="anthropic.claude-3-haiku-20240307-v1:0",
            region_name=os.getenv("AWS_DEFAULT_REGION", "us-east-1"),
            model_kwargs={
                "temperature": 0.1,
                "max_tokens": 1000,
            }
        )
        print("✅ Bedrock LLM initialized")
    except Exception as e:
        print(f"❌ Failed to initialize Bedrock LLM: {e}")
        print("Make sure you have access to Claude 3 Haiku in your AWS region")
        return
    
    # Create LangGraph agent with UTCP tools
    print("🤖 Creating LangGraph agent with Bedrock...")
    try:
        agent = create_react_agent(llm, tools)
        print("✅ Agent created successfully")
    except Exception as e:
        print(f"❌ Failed to create agent: {e}")
        return
    
    # Test the agent
    print("💬 Testing agent with a simple query...")
    try:
        response = await agent.ainvoke({
            "messages": [("user", "Make a test HTTP request to check if the tools are working")]
        })
        
        print("🎉 Agent response:")
        print(response["messages"][-1].content)
        
    except Exception as e:
        print(f"❌ Agent execution failed: {e}")
        print("This might be due to AWS permissions or model access issues")
    
    print("\n✅ Bedrock integration example completed!")
    print("Note: This example uses Amazon Bedrock which may incur AWS charges")


if __name__ == "__main__":
    asyncio.run(main())
