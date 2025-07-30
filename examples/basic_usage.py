"""Basic usage example for LangChain UTCP Adapters.

This example demonstrates how to:
1. Set up a UTCP client with providers
2. Load tools from UTCP providers
3. Convert them to LangChain tools
"""

import asyncio
import json
from pathlib import Path

from utcp.client.utcp_client import UtcpClient
from utcp.client.utcp_client_config import UtcpClientConfig
from utcp.shared.provider import HttpProvider
from langchain_utcp_adapters import load_utcp_tools, search_utcp_tools


async def main():
    """Main example function."""
    # Create a sample providers.json file with working OpenAPI endpoints
    providers_config = [
        {
            "name": "petstore",
            "provider_type": "http",
            "url": "https://petstore.swagger.io/v2/swagger.json",
            "http_method": "GET"
        }
    ]
    
    # Write providers config to file
    providers_file = Path("providers.json")
    with open(providers_file, "w") as f:
        json.dump(providers_config, f, indent=2)
    
    try:
        # Create UTCP client with providers file
        print("Creating UTCP client...")
        config = UtcpClientConfig(providers_file_path="providers.json")
        client = await UtcpClient.create(config=config)
        
        # Alternative: Register providers programmatically
        print("Registering additional provider...")
        try:
            # Use JSONPlaceholder which has a simple API structure
            jsonplaceholder_provider = HttpProvider(
                name="jsonplaceholder",
                provider_type="http",
                url="https://jsonplaceholder.typicode.com",
                http_method="GET"
            )
            await client.register_tool_provider(jsonplaceholder_provider)
        except Exception as e:
            print(f"Note: Additional provider registration failed: {e}")
        
        # Get all available tools and convert to LangChain format
        print("Loading tools...")
        tools = await load_utcp_tools(client)
        print(f"Found {len(tools)} LangChain tools:")
        
        for tool in tools[:5]:  # Show first 5 tools
            print(f"  - {tool.name}: {tool.description}")
            print(f"    Provider: {tool.metadata.get('provider', 'unknown')}")
            print(f"    Type: {tool.metadata.get('provider_type', 'unknown')}")
            print(f"    Tags: {tool.metadata.get('tags', [])}")
        
        if len(tools) > 5:
            print(f"  ... and {len(tools) - 5} more tools")
        
        # Search for tools
        if tools:
            print("\nSearching for tools with 'pet'...")
            search_results = await search_utcp_tools(client, "pet", max_results=3)
            print(f"Found {len(search_results)} matching tools:")
            for tool in search_results:
                print(f"  - {tool.name}: {tool.description}")
        
        # Get provider information from UTCP client
        print("\nProvider information:")
        providers = await client.tool_repository.get_providers()
        for provider in providers:
            print(f"  - {provider.name}: {provider.provider_type}")
            tools_for_provider = await client.tool_repository.get_tools_by_provider(provider.name)
            print(f"    Tools: {len(tools_for_provider) if tools_for_provider else 0}")
        
        # Show tool schemas
        if tools:
            print(f"\nExample tool schema for '{tools[0].name}':")
            print(f"  Description: {tools[0].description}")
            print(f"  Args schema: {tools[0].args_schema}")
            print(f"  Metadata: {tools[0].metadata}")
            
            # Show how the tool would be called
            print(f"\n  Usage example:")
            print(f"    # To call this tool:")
            print(f"    # result = await {tools[0].name}(**arguments)")
            print(f"    # where arguments match the schema above")
        
        if not tools:
            print("\n⚠️  No tools were loaded. This might be because:")
            print("   - The OpenAPI endpoints are not accessible")
            print("   - The endpoints don't provide valid OpenAPI specifications")
            print("   - Network connectivity issues")
        
    finally:
        # Clean up the providers file
        if providers_file.exists():
            providers_file.unlink()


if __name__ == "__main__":
    asyncio.run(main())
