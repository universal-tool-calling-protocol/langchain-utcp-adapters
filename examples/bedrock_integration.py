"""Amazon Bedrock integration example for LangChain UTCP Adapters.

This example demonstrates how to use UTCP tools with Amazon Bedrock models
through LangGraph agents.
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
        
        # Define AWS-related tools
        calculator_tool = Tool(
            name="calculate",
            description="Perform basic mathematical calculations",
            inputs=ToolInputOutputSchema(
                type="object",
                properties={
                    "operation": {
                        "type": "string", 
                        "enum": ["add", "subtract", "multiply", "divide"],
                        "description": "Mathematical operation to perform"
                    },
                    "a": {"type": "number", "description": "First number"},
                    "b": {"type": "number", "description": "Second number"}
                },
                required=["operation", "a", "b"]
            ),
            outputs=ToolInputOutputSchema(
                type="object",
                properties={
                    "result": {"type": "number", "description": "Result of the calculation"},
                    "operation": {"type": "string", "description": "Operation performed"}
                }
            ),
            tags=["math", "calculator", "arithmetic"],
            tool_provider=HttpProvider(
                name="math_server",
                url="http://localhost:8081/calculate",
                http_method="POST"
            )
        )
        
        aws_info_tool = Tool(
            name="get_aws_region_info",
            description="Get information about AWS regions and their capabilities",
            inputs=ToolInputOutputSchema(
                type="object",
                properties={
                    "region": {
                        "type": "string",
                        "description": "AWS region code (e.g., us-east-1, eu-west-1)"
                    }
                },
                required=["region"]
            ),
            outputs=ToolInputOutputSchema(
                type="object",
                properties={
                    "region": {"type": "string", "description": "Region code"},
                    "name": {"type": "string", "description": "Region name"},
                    "bedrock_available": {"type": "boolean", "description": "Whether Bedrock is available in this region"}
                }
            ),
            tags=["aws", "regions", "bedrock", "cloud"],
            tool_provider=HttpProvider(
                name="aws_info_server",
                url="http://localhost:8081/aws-region-info",
                http_method="POST"
            )
        )
        
        @app.get("/utcp")
        def get_utcp_manual():
            """Return the UTCP manual."""
            return {
                "version": "1.0",
                "tools": [
                    calculator_tool.model_dump(),
                    aws_info_tool.model_dump()
                ]
            }
        
        @app.post("/calculate")
        def calculate(data: dict):
            """Perform the calculation."""
            operation = data.get("operation")
            a = data.get("a", 0)
            b = data.get("b", 0)
            
            operations = {
                "add": lambda x, y: x + y,
                "subtract": lambda x, y: x - y,
                "multiply": lambda x, y: x * y,
                "divide": lambda x, y: x / y if y != 0 else "Error: Division by zero"
            }
            
            if operation in operations:
                result = operations[operation](a, b)
                return {"result": result, "operation": f"{a} {operation} {b}"}
            else:
                return {"error": f"Unknown operation: {operation}"}
        
        @app.post("/aws-region-info")
        def get_aws_region_info(data: dict):
            """Get AWS region information."""
            region = data.get("region", "")
            
            # Sample AWS region data
            region_info = {
                "us-east-1": {"name": "US East (N. Virginia)", "bedrock_available": True},
                "us-west-2": {"name": "US West (Oregon)", "bedrock_available": True},
                "eu-west-1": {"name": "Europe (Ireland)", "bedrock_available": True},
                "ap-southeast-1": {"name": "Asia Pacific (Singapore)", "bedrock_available": False},
                "ca-central-1": {"name": "Canada (Central)", "bedrock_available": False},
            }
            
            if region in region_info:
                info = region_info[region]
                return {
                    "region": region,
                    "name": info["name"],
                    "bedrock_available": info["bedrock_available"]
                }
            else:
                return {
                    "region": region,
                    "name": "Unknown Region",
                    "bedrock_available": False
                }
        
        # Start server in a separate thread
        def run_server():
            uvicorn.run(app, host="localhost", port=8081, log_level="error")
        
        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()
        time.sleep(2)  # Give server time to start
        
        return True
        
    except ImportError:
        print("FastAPI not available for creating sample server")
        return False


async def main():
    """Main example function."""
    print("Amazon Bedrock Integration Example")
    print("=" * 50)
    
    if not BEDROCK_AVAILABLE:
        print("Required dependencies not available.")
        print("Please install: pip install langchain-aws boto3")
        return
    
    # Check AWS credentials and Bedrock access
    print("Checking AWS credentials and Bedrock access...")
    creds_ok, creds_msg = check_aws_credentials()
    print(f"AWS Status: {creds_msg}")
    
    if not creds_ok:
        print("\nTo use this example, you need:")
        print("1. AWS credentials configured (via AWS CLI, environment variables, or IAM role)")
        print("2. Bedrock service access in your AWS account")
        print("3. Permissions to invoke Bedrock models")
        print("\nSetup instructions:")
        print("- Run 'aws configure' to set up credentials")
        print("- Ensure your AWS account has Bedrock access")
        print("- Request access to foundation models in Bedrock console")
        return
    
    # Try to create a sample server
    server_created = await create_sample_utcp_server()
    
    # Create providers configuration
    providers_config = [
        {
            "name": "demo_tools",
            "provider_type": "http",
            "url": "http://localhost:8081/utcp",
            "http_method": "GET"
        }
    ]
    
    # If no local server, use a simpler example
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
        print("\nCreating UTCP client...")
        client = MultiProviderUTCPClient(
            providers_file_path="providers.json"
        )
        
        # Get tools
        print("Loading tools...")
        tools = await client.get_tools()
        print(f"Found {len(tools)} tools:")
        
        for tool in tools:
            provider = tool.metadata.get('provider', 'unknown')
            print(f"  - {tool.name} ({provider})")
            print(f"    {tool.description}")
        
        if not tools:
            print("No tools found. Cannot proceed with Bedrock example.")
            return
        
        # Available Bedrock models
        bedrock_models = [
            "anthropic.claude-3-sonnet-20240229-v1:0",
            "anthropic.claude-3-haiku-20240307-v1:0", 
            "amazon.titan-text-express-v1",
            "ai21.j2-ultra-v1",
            "cohere.command-text-v14"
        ]
        
        print(f"\nAvailable Bedrock models: {', '.join(bedrock_models)}")
        
        # Try different models
        for model_id in bedrock_models[:2]:  # Test first 2 models
            print(f"\n{'='*60}")
            print(f"Testing with Bedrock model: {model_id}")
            print('='*60)
            
            try:
                # Create Bedrock LLM
                print(f"Initializing {model_id}...")
                
                # Configure model parameters based on model type
                model_kwargs = {}
                if "anthropic.claude" in model_id:
                    model_kwargs = {
                        "temperature": 0.1,
                        "max_tokens": 1000,
                    }
                elif "amazon.titan" in model_id:
                    model_kwargs = {
                        "temperature": 0.1,
                        "maxTokenCount": 1000,
                    }
                elif "ai21" in model_id:
                    model_kwargs = {
                        "temperature": 0.1,
                        "maxTokens": 1000,
                    }
                elif "cohere" in model_id:
                    model_kwargs = {
                        "temperature": 0.1,
                        "max_tokens": 1000,
                    }
                
                llm = ChatBedrock(
                    model_id=model_id,
                    region_name="us-east-1",  # Bedrock is available in us-east-1
                    model_kwargs=model_kwargs
                )
                
                # Create LangGraph agent
                print("Creating LangGraph agent...")
                agent = create_react_agent(llm, tools)
                
                # Test the agent with different queries
                test_queries = []
                
                if server_created:
                    test_queries = [
                        "What is 25 multiplied by 4?",
                        "Is Amazon Bedrock available in the us-west-2 region?",
                        "Calculate 100 divided by 8 and tell me about the eu-west-1 region"
                    ]
                else:
                    test_queries = [
                        "Can you help me test the available tools?",
                        "What tools do you have access to?"
                    ]
                
                for i, query in enumerate(test_queries, 1):
                    print(f"\nTest {i}: {query}")
                    print("-" * 50)
                    
                    try:
                        response = await agent.ainvoke({
                            "messages": [{"role": "user", "content": query}]
                        })
                        
                        # Extract the final response
                        final_message = response["messages"][-1]
                        print(f"Agent Response: {final_message.content}")
                        
                        # Show tool usage if any
                        tool_calls = [
                            msg for msg in response["messages"] 
                            if hasattr(msg, 'tool_calls') and msg.tool_calls
                        ]
                        
                        if tool_calls:
                            print(f"Tools used: {len(tool_calls)} tool call(s)")
                            for msg in tool_calls:
                                for tool_call in msg.tool_calls:
                                    print(f"  - {tool_call['name']}: {tool_call['args']}")
                        
                    except Exception as e:
                        print(f"Error with query '{query}': {e}")
                        continue
                
                print(f"\n✅ Successfully tested {model_id}")
                break  # If one model works, we can stop testing others
                
            except Exception as e:
                print(f"❌ Error with {model_id}: {e}")
                if "AccessDeniedException" in str(e):
                    print("   → This model may not be enabled in your account")
                    print("   → Enable it in the Bedrock console under 'Model access'")
                elif "ValidationException" in str(e):
                    print("   → This model may not be available in us-east-1")
                elif "ThrottlingException" in str(e):
                    print("   → Rate limit exceeded, try again later")
                continue
        
        # Clean up
        await client.close()
        
    finally:
        # Clean up the providers file
        if providers_file.exists():
            providers_file.unlink()
    
    print(f"\n{'='*60}")
    print("BEDROCK INTEGRATION SUMMARY")
    print('='*60)
    print("This example demonstrated:")
    print("1. ✅ AWS credentials and Bedrock access verification")
    print("2. ✅ UTCP tool loading and integration")
    print("3. ✅ Multiple Bedrock model testing")
    print("4. ✅ LangGraph agent creation with Bedrock LLMs")
    print("5. ✅ Tool execution through Bedrock-powered agents")
    print()
    print("Key benefits of using Bedrock:")
    print("- 🏢 Enterprise-grade security and compliance")
    print("- 🌍 Multiple model providers (Anthropic, Amazon, AI21, Cohere)")
    print("- 🔒 Data stays within your AWS account")
    print("- 📊 Built-in monitoring and logging")
    print("- 💰 Pay-per-use pricing model")
    print()
    print("Next steps:")
    print("- Enable additional models in Bedrock console")
    print("- Experiment with different model parameters")
    print("- Integrate with your existing AWS infrastructure")
    print("- Set up CloudWatch monitoring for usage tracking")


if __name__ == "__main__":
    asyncio.run(main())
