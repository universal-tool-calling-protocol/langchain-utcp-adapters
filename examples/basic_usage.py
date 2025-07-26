"""Basic usage example for LangChain UTCP Adapters.

This example demonstrates how to:
1. Set up a UTCP client with providers
2. Load tools from UTCP providers
3. Use the tools with a LangGraph agent
"""

import asyncio
import json
import os
from pathlib import Path

from langchain_utcp_adapters.client import MultiProviderUTCPClient


async def main():
    """Main example function."""
    # Create a sample providers.json file
    providers_config = [
        {
            "name": "example_api",
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
        
        # Get all available tools
        print("Loading tools...")
        tools = await client.get_tools()
        print(f"Found {len(tools)} tools:")
        
        for tool in tools:
            print(f"  - {tool.name}: {tool.description}")
            print(f"    Provider: {tool.metadata.get('provider', 'unknown')}")
            print(f"    Type: {tool.metadata.get('provider_type', 'unknown')}")
        
        # Search for tools
        print("\nSearching for tools with 'test'...")
        search_results = await client.search_tools("test")
        print(f"Found {len(search_results)} matching tools")
        
        # Get provider information
        print("\nProvider information:")
        providers = await client.get_providers()
        for provider_name in providers:
            try:
                info = await client.get_provider_info(provider_name)
                print(f"  - {provider_name}: {info['provider_type']}")
            except Exception as e:
                print(f"  - {provider_name}: Error getting info - {e}")
        
        # Health check
        print("\nPerforming health check...")
        health = await client.health_check()
        for provider_name, status in health.items():
            print(f"  - {provider_name}: {status['status']}")
            if status['status'] == 'healthy':
                print(f"    Tools: {status['tool_count']}")
            else:
                print(f"    Error: {status.get('error', 'Unknown error')}")
        
        # Clean up
        await client.close()
        
    finally:
        # Clean up the providers file
        if providers_file.exists():
            providers_file.unlink()


if __name__ == "__main__":
    asyncio.run(main())
