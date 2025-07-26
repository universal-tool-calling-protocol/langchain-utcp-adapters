"""Simple Amazon Bedrock integration example for LangChain UTCP Adapters.

This is a streamlined example showing the core integration between
UTCP tools and Amazon Bedrock models.
"""

import asyncio
import json
import os
from pathlib import Path

from langchain_utcp_adapters.client import MultiProviderUTCPClient

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
    
    # Create a simple providers configuration using public APIs
    providers_config = [
        {
            "name": "httpbin",
            "provider_type": "http",
            "url": "http://httpbin.org/anything",
            "http_method": "POST",
            "description": "HTTP testing service"
        },
        {
            "name": "jsonplaceholder",
            "provider_type": "http", 
            "url": "https://jsonplaceholder.typicode.com/posts",
            "http_method": "GET",
            "description": "Fake REST API for testing"
        }
    ]
    
    # Write providers config
    providers_file = Path("providers.json")
    with open(providers_file, "w") as f:
        json.dump(providers_config, f, indent=2)
    
    try:
        # Create UTCP client
        print("\n📡 Creating UTCP client...")
        client = MultiProviderUTCPClient(
            providers_file_path="providers.json"
        )
        
        # Load tools
        print("🔧 Loading tools...")
        tools = await client.get_tools()
        print(f"Found {len(tools)} tools")
        
        if not tools:
            print("No tools available for this example")
            return
        
        # Create Bedrock LLM
        print("\n🤖 Initializing Amazon Bedrock...")
        
        # Use Claude 3 Haiku (fast and cost-effective)
        model_id = "anthropic.claude-3-haiku-20240307-v1:0"
        
        try:
            llm = ChatBedrock(
                model_id=model_id,
                region_name="us-east-1",
                model_kwargs={
                    "temperature": 0.1,
                    "max_tokens": 500,
                }
            )
            print(f"✅ Bedrock model initialized: {model_id}")
        except Exception as e:
            print(f"❌ Bedrock initialization failed: {e}")
            if "AccessDeniedException" in str(e):
                print("💡 Enable model access in Bedrock console:")
                print("   1. Go to AWS Bedrock console")
                print("   2. Navigate to 'Model access'")
                print("   3. Request access to Anthropic Claude models")
            return
        
        # Create agent
        print("\n🎯 Creating LangGraph agent...")
        agent = create_react_agent(llm, tools)
        
        # Test queries
        test_queries = [
            "What tools do you have available?",
            "Can you make a test HTTP request?",
            "Help me understand what you can do with the available tools"
        ]
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n{'='*50}")
            print(f"Test {i}: {query}")
            print('='*50)
            
            try:
                response = await agent.ainvoke({
                    "messages": [{"role": "user", "content": query}]
                })
                
                # Get the final response
                final_message = response["messages"][-1]
                print(f"🤖 Bedrock Response:")
                print(final_message.content)
                
                # Show any tool usage
                tool_messages = [
                    msg for msg in response["messages"] 
                    if hasattr(msg, 'tool_calls') and msg.tool_calls
                ]
                
                if tool_messages:
                    print(f"\n🔧 Tools Used:")
                    for msg in tool_messages:
                        for tool_call in msg.tool_calls:
                            print(f"  - {tool_call['name']}")
                            print(f"    Args: {tool_call['args']}")
                
            except Exception as e:
                print(f"❌ Error: {e}")
        
        # Demonstrate tool search
        print(f"\n{'='*50}")
        print("Tool Search Demonstration")
        print('='*50)
        
        search_queries = ["http", "test", "api"]
        for search_query in search_queries:
            print(f"\n🔍 Searching for: '{search_query}'")
            search_results = await client.search_tools(search_query)
            
            if search_results:
                for tool in search_results:
                    provider = tool.metadata.get('provider', 'unknown')
                    print(f"  ✅ {tool.name} ({provider})")
            else:
                print("  No matching tools found")
        
        await client.close()
        
    finally:
        if providers_file.exists():
            providers_file.unlink()
    
    print(f"\n{'='*50}")
    print("✅ Example completed successfully!")
    print('='*50)
    print("What you just saw:")
    print("1. 🔧 UTCP tools loaded from public APIs")
    print("2. 🤖 Amazon Bedrock Claude model integration")
    print("3. 🎯 LangGraph agent with tool capabilities")
    print("4. 🔍 Tool search functionality")
    print()
    print("💡 Next steps:")
    print("- Try different Bedrock models")
    print("- Add your own UTCP providers")
    print("- Integrate with your AWS infrastructure")
    print("- Monitor usage in CloudWatch")


if __name__ == "__main__":
    asyncio.run(main())
