"""Simple direct usage example for LangChain UTCP Adapters.

This example demonstrates the simplified approach:
1. Create a UTCP client directly
2. Register providers dynamically
3. Load and use tools with LangChain
"""

import asyncio
from utcp.utcp_client import UtcpClient
from utcp.data.utcp_client_config import UtcpClientConfig
from utcp_http.http_call_template import HttpCallTemplate
from langchain_utcp_adapters import load_utcp_tools, search_utcp_tools


async def main():
    """Main example function."""
    print("🚀 Simple Direct UTCP + LangChain Integration")
    print("=" * 50)
    
    # Create UTCP client directly
    config = UtcpClientConfig()
    client = await UtcpClient.create(config=config)
    
    # Register providers dynamically using Provider objects
    print("📡 Registering providers...")
    
    # Register OpenLibrary provider
    openlibrary_provider = HttpProvider(
        name="openlibrary",
        provider_type="http",
        http_method="GET",
        url="https://openlibrary.org/static/openapi.json",
        content_type="application/json"
    )
    await client.register_tool_provider(openlibrary_provider)
    
    # Register a simple HTTP test provider
    httpbin_provider = HttpProvider(
        name="httpbin",
        provider_type="http",
        http_method="POST",
        url="http://httpbin.org/anything",
        content_type="application/json"
    )
    await client.register_tool_provider(httpbin_provider)
    
    print("✅ Providers registered successfully")
    
    # Load all tools and convert to LangChain format
    print("\n🔧 Loading tools...")
    tools = await load_utcp_tools(client)
    print(f"Found {len(tools)} LangChain tools:")
    
    for tool in tools:
        print(f"  - {tool.name}")
        print(f"    Description: {tool.description}")
        print(f"    Provider: {tool.metadata.get('provider')}")
        print()
    
    # Search for specific tools
    print("🔍 Searching for book-related tools...")
    book_tools = await search_utcp_tools(client, "books", max_results=3)
    print(f"Found {len(book_tools)} book-related tools:")
    
    for tool in book_tools:
        print(f"  - {tool.name}: {tool.description}")
    
    # Use a tool if available
    if book_tools:
        print(f"\n🎯 Testing tool: {book_tools[0].name}")
        try:
            # This would depend on the specific tool's schema
            # For demonstration, we'll just show the tool is ready
            print(f"Tool ready for execution with schema: {book_tools[0].args_schema}")
        except Exception as e:
            print(f"Tool test failed: {e}")
    
    print("\n✅ Example completed successfully!")


if __name__ == "__main__":
    asyncio.run(main())
