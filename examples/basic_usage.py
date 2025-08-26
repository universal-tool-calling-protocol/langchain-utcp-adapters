"""Basic usage example for LangChain UTCP Adapters.

This example demonstrates how to:
1. Set up a UTCP client with call templates (UTCP 1.0.0+)
2. Load tools from UTCP call templates
3. Convert them to LangChain tools
"""

import asyncio
from utcp.utcp_client import UtcpClient
from utcp.data.utcp_client_config import UtcpClientConfig
from utcp_http.http_call_template import HttpCallTemplate
from langchain_utcp_adapters import load_utcp_tools, search_utcp_tools


async def main():
    """Main example function."""
    print("🚀 Basic LangChain UTCP Adapters Usage (UTCP 1.0.0+)")
    print("=" * 50)
    
    # Create UTCP client with new 1.0.0+ configuration
    print("📡 Creating UTCP client...")
    config = UtcpClientConfig(
        manual_call_templates=[
            HttpCallTemplate(
                name="petstore",
                call_template_type="http",
                url="https://petstore.swagger.io/v2/swagger.json",
                http_method="GET"
            ),
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
    
    # Get all available tools and convert to LangChain format
    print("\n🔧 Loading tools...")
    tools = await load_utcp_tools(client)
    print(f"Found {len(tools)} LangChain tools:")
    
    for tool in tools[:5]:  # Show first 5 tools
        print(f"  - {tool.name}: {tool.description}")
        print(f"    Call Template: {tool.metadata.get('call_template', 'unknown')}")
        print(f"    Type: {tool.metadata.get('call_template_type', 'unknown')}")
        print(f"    Tags: {tool.metadata.get('tags', [])}")
    
    if len(tools) > 5:
        print(f"  ... and {len(tools) - 5} more tools")
    
    # Search for tools
    if tools:
        print("\n🔍 Searching for tools with 'pet'...")
        search_results = await search_utcp_tools(client, "pet", max_results=3)
        print(f"Found {len(search_results)} matching tools:")
        for tool in search_results:
            print(f"  - {tool.name}: {tool.description}")
    
    # Show tool schemas
    if tools:
        print(f"\n🔧 Example tool schema for '{tools[0].name}':")
        print(f"  Description: {tools[0].description}")
        print(f"  Args schema: {tools[0].args_schema}")
        print(f"  Metadata: {tools[0].metadata}")
        
        # Show how the tool would be called
        print(f"\n💡 Usage example:")
        print(f"    # To call this tool:")
        print(f"    # result = await {tools[0].name}(**arguments)")
        print(f"    # where arguments match the schema above")
    
    if not tools:
        print("\n⚠️  No tools were loaded. This might be because:")
        print("   - The OpenAPI endpoints are not accessible")
        print("   - The endpoints don't provide valid OpenAPI specifications")
        print("   - Network connectivity issues")
    
    print("\n✅ Example completed successfully!")


if __name__ == "__main__":
    asyncio.run(main())
