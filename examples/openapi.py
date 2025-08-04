"""OpenAPI integration example for LangChain UTCP Adapters.

This example demonstrates how UTCP can automatically convert OpenAPI specifications
into UTCP tools that can be used with LangChain.
"""

import asyncio
import json
from pathlib import Path

from utcp.client.utcp_client import UtcpClient
from utcp.client.utcp_client_config import UtcpClientConfig
from utcp.shared.provider import HttpProvider
from langchain_utcp_adapters import load_utcp_tools, search_utcp_tools


async def main():
    """Main example function demonstrating OpenAPI integration."""
    
    print("OpenAPI Integration Example")
    print("=" * 40)
    print("This example shows how UTCP can automatically convert")
    print("OpenAPI specifications into usable tools.")
    print()
    
    # Create UTCP client
    config = UtcpClientConfig()
    client = await UtcpClient.create(config=config)
    
    # Example 1: Register OpenAPI specs directly as providers
    print("📡 Registering OpenAPI providers...")
    
    openapi_providers = [
        {
            "name": "petstore",
            "url": "https://petstore.swagger.io/v2/swagger.json",
            "description": "Swagger Petstore - Classic OpenAPI example"
        },
        {
            "name": "httpbin", 
            "url": "https://httpbin.org/spec.json",
            "description": "HTTPBin - HTTP testing service"
        }
    ]
    
    registered_providers = []
    for provider_info in openapi_providers:
        try:
            print(f"  Registering {provider_info['name']}...")
            provider = HttpProvider(
                name=provider_info["name"],
                provider_type="http",
                url=provider_info["url"],
                http_method="GET"
            )
            tools = await client.register_tool_provider(provider)
            registered_providers.append(provider_info["name"])
            print(f"    ✅ Registered {len(tools)} tools from {provider_info['name']}")
        except Exception as e:
            print(f"    ❌ Failed to register {provider_info['name']}: {e}")
    
    # Example 2: Create providers.json with OpenAPI URLs
    print("\n📄 Creating providers.json with OpenAPI specs...")
    providers_config = [
        {
            "name": "jsonplaceholder",
            "provider_type": "http",
            "url": "https://jsonplaceholder.typicode.com",
            "http_method": "GET"
        }
    ]
    
    providers_file = Path("openapi_providers.json")
    with open(providers_file, "w") as f:
        json.dump(providers_config, f, indent=2)
    
    # Load additional providers from file
    try:
        additional_providers = await client.load_providers("openapi_providers.json")
        print(f"✅ Loaded {len(additional_providers)} additional providers from file")
    except Exception as e:
        print(f"❌ Failed to load providers from file: {e}")
    
    # Load all tools and convert to LangChain format
    print("\n🔧 Loading all tools...")
    tools = await load_utcp_tools(client)
    print(f"Found {len(tools)} LangChain tools from OpenAPI specs:")
    
    # Group tools by provider
    tools_by_provider = {}
    for tool in tools:
        provider = tool.metadata.get('provider', 'unknown')
        if provider not in tools_by_provider:
            tools_by_provider[provider] = []
        tools_by_provider[provider].append(tool)
    
    for provider, provider_tools in tools_by_provider.items():
        print(f"\n  📦 {provider} ({len(provider_tools)} tools):")
        for tool in provider_tools[:3]:  # Show first 3 tools
            print(f"    - {tool.name}: {tool.description}")
        if len(provider_tools) > 3:
            print(f"    ... and {len(provider_tools) - 3} more tools")
    
    # Search for specific functionality
    print("\n🔍 Searching for specific functionality...")
    search_queries = ["user", "post", "get", "pet"]
    
    for query in search_queries:
        results = await search_utcp_tools(client, query, max_results=3)
        if results:
            print(f"\n  Query '{query}' found {len(results)} tools:")
            for tool in results:
                print(f"    - {tool.name} ({tool.metadata.get('provider')})")
    
    # Show detailed schema for one tool
    if tools:
        example_tool = tools[0]
        print(f"\n📋 Example tool schema for '{example_tool.name}':")
        print(f"  Description: {example_tool.description}")
        print(f"  Provider: {example_tool.metadata.get('provider')}")
        print(f"  Args schema: {example_tool.args_schema}")
        print(f"  Metadata: {example_tool.metadata}")
    
    # Cleanup
    if providers_file.exists():
        providers_file.unlink()
    
    print("\n✅ OpenAPI integration example completed!")
    print(f"Successfully integrated {len(tools)} tools from OpenAPI specifications")


if __name__ == "__main__":
    asyncio.run(main())
