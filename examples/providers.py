#!/usr/bin/env python3
"""Real providers example for LangChain UTCP Adapters.

This example demonstrates the package working with actual UTCP call templates:
- OpenLibrary API (via OpenAPI specification)
- NewsAPI (via UTCP manual definition)

It shows how to load real tools, search them, and use them in practice.
"""

import asyncio
import json
from pathlib import Path

from utcp.utcp_client import UtcpClient
from utcp.data.utcp_client_config import UtcpClientConfig
from utcp_http.http_call_template import HttpCallTemplate
from utcp_text.text_call_template import TextCallTemplate
from langchain_utcp_adapters import load_utcp_tools, search_utcp_tools


async def main():
    """Main example function demonstrating real UTCP call templates."""
    print("🌟 LangChain UTCP Adapters - Real Call Templates Example")
    print("=" * 60)
    
    # Create UTCP client with call templates
    print("📡 Creating UTCP client...")
    
    # Check if NewsAPI manual exists
    newsapi_file = Path("newsapi_manual.json")
    call_templates = [
        HttpCallTemplate(
            name="openlibrary",
            call_template_type="http",
            http_method="GET",
            url="https://openlibrary.org/static/openapi.json",
            content_type="application/json"
        )
    ]
    
    if newsapi_file.exists():
        call_templates.append(
            TextCallTemplate(
                name="newsapi",
                call_template_type="text",
                file_path="./newsapi_manual.json"
            )
        )
        print("  📄 Found NewsAPI manual, including in configuration")
    else:
        print("  ⚠️  NewsAPI manual not found, using OpenLibrary only")
    
    config = UtcpClientConfig(manual_call_templates=call_templates)
    client = await UtcpClient.create(config=config)
    
    # Load all available tools
    print("\n🔧 Loading UTCP tools...")
    try:
        langchain_tools = await load_utcp_tools(client)
        print(f"✅ Successfully loaded {len(langchain_tools)} tools")
        
        # Display available tools
        print("\n📋 Available tools:")
        for tool in langchain_tools:
            print(f"  • {tool.name}: {tool.description}")
    
    except Exception as e:
        print(f"❌ Failed to load tools: {e}")
        return
    
    # Demonstrate tool search
    print("\n🔍 Searching for specific tools...")
    search_queries = ["search", "book", "author", "news"]
    
    for query in search_queries:
        try:
            matching_tools = await search_utcp_tools(client, query, max_results=3)
            if matching_tools:
                print(f"\n  Query: '{query}' -> {len(matching_tools)} matches:")
                for tool in matching_tools:
                    print(f"    • {tool.name}")
            else:
                print(f"\n  Query: '{query}' -> No matches")
        except Exception as e:
            print(f"  ❌ Search failed for '{query}': {e}")
    
    # Demonstrate tool execution (if tools are available)
    if langchain_tools:
        print(f"\n🚀 Testing tool execution...")
        
        # Try to find a simple tool to test
        test_tool = None
        for tool in langchain_tools:
            if "search" in tool.name.lower() and "author" in tool.name.lower():
                test_tool = tool
                break
        
        if test_tool:
            try:
                print(f"  Testing tool: {test_tool.name}")
                # Use a simple test query
                result = await test_tool.ainvoke({"q": "J.K. Rowling"})
                print(f"  ✅ Tool execution successful")
                print(f"  📄 Result preview: {str(result)[:200]}...")
            except Exception as e:
                print(f"  ❌ Tool execution failed: {e}")
        else:
            print("  ⚠️  No suitable test tool found")
    
    print(f"\n✨ Example completed!")


if __name__ == "__main__":
    asyncio.run(main())
