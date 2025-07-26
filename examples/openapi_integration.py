"""OpenAPI integration example for LangChain UTCP Adapters.

This example demonstrates how UTCP can automatically convert OpenAPI specifications
into UTCP tools that can be used with LangChain.
"""

import asyncio
import json
from pathlib import Path

from langchain_utcp_adapters.client import MultiProviderUTCPClient


async def main():
    """Main example function demonstrating OpenAPI integration."""
    
    print("OpenAPI Integration Example")
    print("=" * 40)
    print("This example shows how UTCP can automatically convert")
    print("OpenAPI specifications into usable tools.")
    print()
    
    # Example 1: Public OpenAPI specs
    public_apis = [
        {
            "name": "jsonplaceholder",
            "provider_type": "http",
            "url": "https://jsonplaceholder.typicode.com",
            "description": "JSONPlaceholder - Fake REST API for testing"
        },
        {
            "name": "httpbin",
            "provider_type": "http", 
            "url": "https://httpbin.org/spec.json",
            "description": "HTTPBin - HTTP testing service"
        }
    ]
    
    # Example 2: Local OpenAPI spec (if available)
    local_openapi_example = {
        "name": "petstore",
        "provider_type": "http",
        "url": "https://petstore.swagger.io/v2/swagger.json",
        "description": "Swagger Petstore - Classic OpenAPI example"
    }
    
    # Create providers configuration
    providers_config = [
        # Direct UTCP provider (for comparison)
        {
            "name": "direct_utcp",
            "provider_type": "http",
            "url": "http://httpbin.org/anything",
            "http_method": "POST"
        },
        # OpenAPI-based providers
        local_openapi_example
    ]
    
    # Write providers config to file
    providers_file = Path("providers.json")
    with open(providers_file, "w") as f:
        json.dump(providers_config, f, indent=2)
    
    try:
        print("Creating UTCP client with OpenAPI integration...")
        client = MultiProviderUTCPClient(
            providers_file_path="providers.json"
        )
        
        print("\nLoading tools from providers...")
        print("(This may take a moment as OpenAPI specs are fetched and converted)")
        
        try:
            # Get all tools
            all_tools = await client.get_tools()
            print(f"\nFound {len(all_tools)} total tools across all providers")
            
            # Group tools by provider
            tools_by_provider = {}
            for tool in all_tools:
                provider = tool.metadata.get('provider', 'unknown')
                if provider not in tools_by_provider:
                    tools_by_provider[provider] = []
                tools_by_provider[provider].append(tool)
            
            # Display tools by provider
            for provider_name, tools in tools_by_provider.items():
                print(f"\n{provider_name} ({len(tools)} tools):")
                for tool in tools[:5]:  # Show first 5 tools
                    print(f"  - {tool.name}")
                    print(f"    Description: {tool.description[:100]}...")
                    print(f"    Args: {list(tool.args_schema.model_fields.keys())}")
                
                if len(tools) > 5:
                    print(f"  ... and {len(tools) - 5} more tools")
            
            # Demonstrate tool search
            print("\n" + "="*50)
            print("TOOL SEARCH DEMONSTRATION")
            print("="*50)
            
            search_queries = [
                "get user information",
                "create post", 
                "upload file",
                "authentication",
                "pet store"
            ]
            
            for query in search_queries:
                print(f"\nSearching for: '{query}'")
                search_results = await client.search_tools(query, max_results=3)
                
                if search_results:
                    print(f"Found {len(search_results)} relevant tools:")
                    for tool in search_results:
                        provider = tool.metadata.get('provider', 'unknown')
                        print(f"  - {tool.name} ({provider})")
                        print(f"    {tool.description[:80]}...")
                else:
                    print("  No relevant tools found")
            
            # Demonstrate calling a tool (if available)
            print("\n" + "="*50)
            print("TOOL EXECUTION DEMONSTRATION")
            print("="*50)
            
            # Try to find a simple GET endpoint to call
            get_tools = [
                tool for tool in all_tools 
                if 'get' in tool.name.lower() and 
                len(tool.args_schema.model_fields) <= 2
            ]
            
            if get_tools:
                test_tool = get_tools[0]
                print(f"\nTesting tool: {test_tool.name}")
                print(f"Provider: {test_tool.metadata.get('provider')}")
                print(f"Description: {test_tool.description}")
                
                try:
                    # Try to call with minimal arguments
                    args = {}
                    for field_name, field_info in test_tool.args_schema.model_fields.items():
                        if field_info.is_required():
                            # Provide a simple default value
                            if 'id' in field_name.lower():
                                args[field_name] = "1"
                            elif 'name' in field_name.lower():
                                args[field_name] = "test"
                            else:
                                args[field_name] = "example"
                    
                    print(f"Calling with args: {args}")
                    result = await test_tool.ainvoke(args)
                    print(f"Result: {result[:200]}...")
                    
                except Exception as e:
                    print(f"Tool execution failed (expected for demo): {e}")
            else:
                print("No suitable tools found for demonstration")
            
        except Exception as e:
            print(f"Error loading tools: {e}")
            print("This might be due to network issues or API changes.")
        
        # Provider health check
        print("\n" + "="*50)
        print("PROVIDER HEALTH CHECK")
        print("="*50)
        
        health = await client.health_check()
        for provider_name, status in health.items():
            print(f"\n{provider_name}:")
            print(f"  Status: {status['status']}")
            if status['status'] == 'healthy':
                print(f"  Tools loaded: {status['tool_count']}")
            else:
                print(f"  Error: {status.get('error', 'Unknown error')}")
        
        # Clean up
        await client.close()
        
    finally:
        # Clean up the providers file
        if providers_file.exists():
            providers_file.unlink()
    
    print("\n" + "="*50)
    print("SUMMARY")
    print("="*50)
    print("This example demonstrated:")
    print("1. Automatic OpenAPI to UTCP conversion")
    print("2. Loading tools from OpenAPI specifications")
    print("3. Tool search across converted APIs")
    print("4. Provider health monitoring")
    print("5. Tool execution (with error handling)")
    print()
    print("Benefits of OpenAPI integration:")
    print("- No manual tool definition required")
    print("- Automatic schema validation")
    print("- Support for thousands of existing APIs")
    print("- Consistent tool interface")
    print("- Built-in documentation from OpenAPI specs")


if __name__ == "__main__":
    asyncio.run(main())
