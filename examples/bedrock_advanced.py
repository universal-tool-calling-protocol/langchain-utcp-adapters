"""Amazon Bedrock integration example for LangChain UTCP Adapters.

This example demonstrates how to use UTCP tools with Amazon Bedrock models
through LangGraph agents using the current UTCP client API.
"""

import asyncio
import os
from utcp.utcp_client import UtcpClient
from utcp.data.utcp_client_config import UtcpClientConfig
from utcp_http.http_call_template import HttpCallTemplate
from langchain_utcp_adapters import load_utcp_tools, search_utcp_tools, create_bedrock_tool_mapping

# Optional: Only import if available
try:
    from langgraph.prebuilt import create_react_agent
    from langchain_aws import ChatBedrock
    import boto3
    BEDROCK_AVAILABLE = True
except ImportError:
    BEDROCK_AVAILABLE = False
    print("Bedrock dependencies not available. Install with: pip install langchain-aws boto3")


def check_aws_credentials():
    """Check if AWS credentials are configured."""
    try:
        # Try to create a session to check credentials
        session = boto3.Session()
        credentials = session.get_credentials()
        if credentials is None:
            return False, "No AWS credentials found"
        
        # Check if we can access Bedrock
        bedrock_client = session.client('bedrock', region_name='us-east-1')
        try:
            # Try to list foundation models to verify access
            bedrock_client.list_foundation_models()
            return True, "AWS credentials and Bedrock access verified"
        except Exception as e:
            return False, f"Bedrock access error: {str(e)}"
            
    except Exception as e:
        return False, f"AWS credential error: {str(e)}"


# Removed server creation code - this is CLIENT-SIDE only
# LangChain UTCP Adapters should consume existing APIs, not create servers


async def main():
    """Main example function."""
    print("🤖 Amazon Bedrock + UTCP Integration Example")
    print("=" * 50)
    
    if not BEDROCK_AVAILABLE:
        print("❌ Required dependencies not available.")
        print("Install with: pip install langchain-aws boto3")
        return
    
    # Check AWS credentials and Bedrock access
    print("🔍 Checking AWS credentials and Bedrock access...")
    creds_ok, creds_msg = check_aws_credentials()
    print(f"AWS Status: {creds_msg}")
    
    if not creds_ok:
        print("\n💡 To use this example, you need:")
        print("1. AWS credentials configured (via AWS CLI, environment variables, or IAM role)")
        print("2. Bedrock service access in your AWS account")
        print("3. Permissions to invoke Bedrock models")
        print("\n🛠️  Setup instructions:")
        print("- Run 'aws configure' to set up credentials")
        print("- Ensure your AWS account has Bedrock access")
        print("- Request access to foundation models in Bedrock console")
        return
    
    # Create UTCP client directly
    print("\n📡 Creating UTCP client...")
    # Create UTCP client with call templates
    print("📡 Creating UTCP client...")
    config = UtcpClientConfig(
        manual_call_templates=[
            HttpCallTemplate(
                name="openlibrary",
                call_template_type="http",
                url="https://openlibrary.org/static/openapi.json",
                http_method="GET",
                content_type="application/json"
            )
        ]
    )
    client = await UtcpClient.create(config=config)
    
    print("✅ Successfully created UTCP client with call templates")
    
    try:
        # Load tools
        print("\n🔧 Loading tools...")
        original_tools = await load_utcp_tools(client)
        print(f"Found {len(original_tools)} tools")
        
        if not original_tools:
            print("❌ No tools available for this example")
            return
        
        # Create Bedrock-compatible tools
        print("🔧 Creating Bedrock-compatible tool names...")
        bedrock_tools, name_mapping = create_bedrock_tool_mapping(original_tools)
        
        # Show name mappings for long tool names
        long_names = [name for name in name_mapping.keys() if name != name_mapping[name]]
        if long_names:
            print(f"📝 Mapped {len(long_names)} tool names for Bedrock compatibility:")
            for bedrock_name, original_name in name_mapping.items():
                if bedrock_name != original_name:
                    print(f"  {original_name} -> {bedrock_name}")
        
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
        
        # Create agent with Bedrock-compatible tools
        print("\n🎯 Creating LangGraph agent...")
        agent = create_react_agent(llm, bedrock_tools)
        
        # Test queries
        test_queries = [
            "What tools do you have available?",
            "Can you search for Hamlet by William Shakespeare?",
            "Help me understand what you can do with the available tools"
        ]
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n{'='*50}")
            print(f"Test {i}: {query}")
            print('='*50)
            
            try:
                response = await agent.ainvoke({
                    "messages": [("user", query)]
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
        print("🔍 Tool Search Demonstration")
        print('='*50)
        
        search_queries = ["books", "http", "api"]
        for search_query in search_queries:
            print(f"\n🔍 Searching for: '{search_query}'")
            search_results = await search_utcp_tools(client, search_query, max_results=3)
            
            if search_results:
                for tool in search_results:
                    provider = tool.metadata.get('provider', 'unknown')
                    original_name = tool.name
                    # Find the corresponding Bedrock name
                    bedrock_name = None
                    for b_name, o_name in name_mapping.items():
                        if o_name == original_name:
                            bedrock_name = b_name
                            break
                    
                    if bedrock_name and bedrock_name != original_name:
                        print(f"  ✅ {original_name} -> {bedrock_name} ({provider})")
                    else:
                        print(f"  ✅ {original_name} ({provider})")
            else:
                print("  ❌ No matching tools found")
        
    finally:
        print("\n🧹 Cleaning up...")
        # No providers file to clean up in direct approach
        pass
    
    print(f"\n{'='*50}")
    print("✅ Example completed successfully!")
    print('='*50)
    print("What you just saw:")
    print("1. 🔧 UTCP tools loaded from real APIs")
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
