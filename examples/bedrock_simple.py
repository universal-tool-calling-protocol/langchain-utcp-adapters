"""Simple Amazon Bedrock integration example for LangChain UTCP Adapters.

This is a streamlined example showing the core integration between
UTCP tools and Amazon Bedrock models, including proper tool name mapping
for Bedrock compatibility.
"""

import asyncio
import os
from utcp.client.utcp_client import UtcpClient
from utcp.client.utcp_client_config import UtcpClientConfig
from utcp.shared.provider import HttpProvider
from langchain_utcp_adapters import load_utcp_tools, create_bedrock_tool_mapping

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
    print("🤖 Simple Amazon Bedrock + UTCP Integration")
    print("=" * 50)
    
    if not BEDROCK_AVAILABLE:
        print("❌ Required dependencies not available.")
        print("Install with: pdm install -G bedrock")
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
    
    # Register only OpenLibrary provider (like the working bedrock_integration.py)
    print("📡 Registering OpenLibrary provider...")
    
    try:
        openlibrary_provider = HttpProvider(
            name="openlibrary",
            provider_type="http",
            http_method="GET",
            url="https://openlibrary.org/static/openapi.json",
            content_type="application/json"
        )
        await client.register_tool_provider(openlibrary_provider)
        print("  ✅ OpenLibrary API for book information")
    except Exception as e:
        print(f"  ❌ OpenLibrary registration failed: {e}")
        return
    
    # Load tools and convert to LangChain format
    print("\n🔧 Loading UTCP tools...")
    original_tools = await load_utcp_tools(client)
    print(f"Loaded {len(original_tools)} original tools")
    
    if not original_tools:
        print("❌ No tools available. Cannot create agent.")
        return
    
    # Create Bedrock-compatible tools with name mapping
    print("🔧 Creating Bedrock-compatible tools...")
    bedrock_tools, name_mapping = create_bedrock_tool_mapping(original_tools)
    print(f"Created {len(bedrock_tools)} Bedrock-compatible tools")
    
    # Show some examples of name mapping
    print("📝 Tool name mapping examples:")
    mapped_count = 0
    for bedrock_name, original_name in name_mapping.items():
        if bedrock_name != original_name and mapped_count < 3:
            print(f"  {original_name} -> {bedrock_name}")
            mapped_count += 1
    
    total_mapped = sum(1 for b, o in name_mapping.items() if b != o)
    if total_mapped > 3:
        print(f"  ... and {total_mapped - 3} more mappings")
    elif total_mapped == 0:
        print("  (No name changes needed - all names are Bedrock-compatible)")
    
    # Create Bedrock LLM
    print("\n🤖 Creating Bedrock LLM...")
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
    
    # Create LangGraph agent with Bedrock-compatible tools
    print("🤖 Creating LangGraph agent with Bedrock...")
    try:
        agent = create_react_agent(llm, bedrock_tools)
        print("✅ Agent created successfully")
    except Exception as e:
        print(f"❌ Failed to create agent: {e}")
        return
    
    # Test the agent with a simple query
    print("\n💬 Testing agent with a book search query...")
    try:
        response = await agent.ainvoke({
            "messages": [("user", "Can you search for books about Python programming?")]
        })
        
        print("🎉 Agent response:")
        print(response["messages"][-1].content)
        
        # Check if tools were used and show original names
        tool_calls = []
        for message in response["messages"]:
            if hasattr(message, 'tool_calls') and message.tool_calls:
                tool_calls.extend(message.tool_calls)
        
        if tool_calls:
            print(f"\n🔧 Tools Used:")
            for tool_call in tool_calls:
                bedrock_name = tool_call['name']
                original_name = name_mapping.get(bedrock_name, bedrock_name)
                print(f"  - {bedrock_name} (original: {original_name})")
                if 'args' in tool_call:
                    print(f"    Args: {tool_call['args']}")
        else:
            print("\n💭 No tools were called for this query")
        
    except Exception as e:
        print(f"❌ Agent execution failed: {e}")
        print("This might be due to AWS permissions or model access issues")
    
    print(f"\n📊 Summary:")
    print(f"  Providers registered: 1 (OpenLibrary)")
    print(f"  Original tools: {len(original_tools)}")
    print(f"  Bedrock-compatible tools: {len(bedrock_tools)}")
    print(f"  Tool name mappings: {len(name_mapping)}")
    print(f"  Bedrock model: anthropic.claude-3-haiku-20240307-v1:0")
    
    print("\n✅ Simple Bedrock integration example completed!")
    print("💡 Note: This example uses Amazon Bedrock which may incur AWS charges")
    print("💡 Tool names are automatically mapped to meet Bedrock's naming requirements")


if __name__ == "__main__":
    asyncio.run(main())
