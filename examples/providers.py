#!/usr/bin/env python3
"""Real providers example for LangChain UTCP Adapters.

This example demonstrates the package working with actual UTCP providers:
- OpenLibrary API (via OpenAPI specification)
- NewsAPI (via UTCP manual definition)

It shows how to load real tools, search them, and use them in practice.
"""

import asyncio
import json
from pathlib import Path

from utcp.client.utcp_client import UtcpClient
from utcp.client.utcp_client_config import UtcpClientConfig
from utcp.shared.provider import HttpProvider, TextProvider
from langchain_utcp_adapters import load_utcp_tools, search_utcp_tools


async def main():
    """Main example function demonstrating real UTCP providers."""
    print("🌟 LangChain UTCP Adapters - Real Providers Example")
    print("=" * 60)
    
    # Create UTCP client
    print("📡 Creating UTCP client...")
    config = UtcpClientConfig()
    client = await UtcpClient.create(config=config)
    
    # Register providers programmatically
    print("📡 Registering real providers...")
    
    # Register OpenLibrary via OpenAPI
    try:
        print("  Registering OpenLibrary API...")
        openlibrary_provider = HttpProvider(
            name="openlibrary",
            provider_type="http",
            http_method="GET",
            url="https://openlibrary.org/static/openapi.json",
            content_type="application/json"
        )
        openlibrary_tools = await client.register_tool_provider(openlibrary_provider)
        print(f"    ✅ Registered {len(openlibrary_tools)} OpenLibrary tools")
    except Exception as e:
        print(f"    ❌ Failed to register OpenLibrary: {e}")
    
    # Register NewsAPI via text file (if available)
    newsapi_file = Path("newsapi_manual.json")
    if newsapi_file.exists():
        try:
            print("  Registering NewsAPI from manual...")
            newsapi_provider = TextProvider(
                name="newsapi",
                provider_type="text",
                file_path="./newsapi_manual.json"
            )
            newsapi_tools = await client.register_tool_provider(newsapi_provider)
            print(f"    ✅ Registered {len(newsapi_tools)} NewsAPI tools")
        except Exception as e:
            print(f"    ❌ Failed to register NewsAPI: {e}")
    else:
        print("  ⚠️  NewsAPI manual not found, skipping")
    
    # Alternative: Setup providers via configuration file
    print("\n📄 Alternative: Using providers.json configuration...")
    providers_config = [
        {
            "name": "httpbin_demo",
            "provider_type": "http",
            "http_method": "POST",
            "url": "http://httpbin.org/anything",
            "content_type": "application/json"
        }
    ]
    
    providers_file = Path("real_providers.json")
    with open(providers_file, "w") as f:
        json.dump(providers_config, f, indent=2)
    
    try:
        additional_providers = await client.load_providers("real_providers.json")
        print(f"✅ Loaded {len(additional_providers)} additional providers from file")
    except Exception as e:
        print(f"❌ Failed to load providers from file: {e}")
    
    # Load all tools and convert to LangChain format
    print("\n🔧 Loading all tools...")
    tools = await load_utcp_tools(client)
    print(f"Found {len(tools)} LangChain tools from real providers:")
    
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
            print(f"    - {tool.name}")
            print(f"      Description: {tool.description}")
        if len(provider_tools) > 3:
            print(f"    ... and {len(provider_tools) - 3} more tools")
    
    # Demonstrate search functionality
    print("\n🔍 Searching for specific functionality...")
    search_queries = ["book", "search", "author", "news", "article"]
    
    for query in search_queries:
        results = await search_utcp_tools(client, query, max_results=3)
        if results:
            print(f"\n  Query '{query}' found {len(results)} tools:")
            for tool in results:
                provider = tool.metadata.get('provider', 'unknown')
                print(f"    - {tool.name} ({provider})")
                print(f"      {tool.description}")
    
    # Show detailed information for one tool
    if tools:
        example_tool = tools[0]
        print(f"\n📋 Detailed example: '{example_tool.name}'")
        print(f"  Provider: {example_tool.metadata.get('provider')}")
        print(f"  Provider Type: {example_tool.metadata.get('provider_type')}")
        print(f"  Description: {example_tool.description}")
        print(f"  Tags: {example_tool.metadata.get('tags', [])}")
        print(f"  Args Schema: {example_tool.args_schema}")
        
        # Show how to call the tool (without actually calling it)
        print(f"\n  Example usage:")
        print(f"    result = await {example_tool.name}(**arguments)")
        print(f"    # Where arguments match the schema: {example_tool.args_schema}")
    
    # Demonstrate provider-specific tool loading
    print("\n🎯 Loading tools from specific provider...")
    if 'Open Library API' in [tool.metadata.get('provider') for tool in tools]:
        openlibrary_tools = await load_utcp_tools(client, provider_name="Open Library API")
        print(f"Found {len(openlibrary_tools)} tools specifically from OpenLibrary:")
        for tool in openlibrary_tools[:3]:
            print(f"  - {tool.name}")
    
    # Performance and statistics
    print(f"\n📊 Summary Statistics:")
    print(f"  Total tools loaded: {len(tools)}")
    print(f"  Total providers: {len(tools_by_provider)}")
    print(f"  Average tools per provider: {len(tools) / len(tools_by_provider) if tools_by_provider else 0:.1f}")
    
    # Cleanup
    if providers_file.exists():
        providers_file.unlink()
    
    print("\n✅ Real providers example completed successfully!")
    print("This demonstrates how UTCP can integrate with real-world APIs")
    print("and make them available as LangChain tools with minimal configuration.")


if __name__ == "__main__":
    asyncio.run(main())
