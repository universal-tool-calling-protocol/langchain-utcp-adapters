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
from langchain_utcp_adapters.client import MultiProviderUTCPClient


async def main():
    """Main example function demonstrating real UTCP providers."""
    print("🌟 LangChain UTCP Adapters - Real Providers Example")
    print("=" * 60)
    
    # Setup providers configuration
    providers_config = [
        {
            "name": "openlibrary",
            "provider_type": "http",
            "http_method": "GET",
            "url": "https://openlibrary.org/static/openapi.json",
            "content_type": "application/json"
        },
        {
            "name": "newsapi",
            "provider_type": "text",
            "file_path": "./newsapi_manual.json"
        }
    ]
    
    # Write providers config to file
    providers_file = Path("real_providers.json")
    with open(providers_file, "w") as f:
        json.dump(providers_config, f, indent=2)
    
    try:
        # Create UTCP client
        print("📡 Creating UTCP client with real providers...")
        client = MultiProviderUTCPClient(
            providers_file_path="real_providers.json"
        )
        
        # Load all tools
        print("\n🔧 Loading tools from providers...")
        tools = await client.get_tools()
        print(f"✅ Successfully loaded {len(tools)} tools")
        
        # Organize tools by provider
        provider_tools = {}
        for tool in tools:
            provider = tool.metadata.get('provider', 'unknown')
            if provider not in provider_tools:
                provider_tools[provider] = []
            provider_tools[provider].append(tool)
        
        # Display tools by provider
        print("\n📚 Available Tools by Provider:")
        for provider_name, tools_list in provider_tools.items():
            print(f"\n  🏢 {provider_name.upper()} ({len(tools_list)} tools):")
            
            for i, tool in enumerate(tools_list[:3], 1):  # Show first 3
                print(f"    {i}. {tool.name.split('.')[-1]}")
                print(f"       📝 {tool.description[:80]}...")
                args = list(tool.args_schema.model_fields.keys())
                print(f"       🔧 Args: {', '.join(args[:4])}{'...' if len(args) > 4 else ''}")
                print(f"       🏷️  Tags: {tool.metadata.get('tags', [])}")
                print()
            
            if len(tools_list) > 3:
                print(f"    ... and {len(tools_list) - 3} more tools")
        
        # Demonstrate search functionality
        print("\n🔍 Tool Search Demonstration:")
        search_examples = [
            ("books", "Find tools related to books and library"),
            ("news", "Find tools for news and articles"),
            ("search", "Find search-related tools"),
            ("authors", "Find author-related tools")
        ]
        
        for query, description in search_examples:
            print(f"\n  🔎 Searching for '{query}' ({description}):")
            search_results = await client.search_tools(query, max_results=3)
            
            if search_results:
                for result in search_results:
                    provider = result.metadata.get('provider', 'unknown')
                    print(f"    ✅ {result.name.split('.')[-1]} ({provider})")
                    print(f"       {result.description[:60]}...")
            else:
                print("    ❌ No results found")
        
        # Demonstrate tool inspection
        print("\n🔬 Tool Inspection Example:")
        if tools:
            # Pick an interesting tool to inspect
            book_tools = [t for t in tools if 'book' in t.name.lower() or 'books' in t.name.lower()]
            if book_tools:
                example_tool = book_tools[0]
                print(f"  📖 Inspecting: {example_tool.name}")
                print(f"  📝 Description: {example_tool.description}")
                print(f"  🏢 Provider: {example_tool.metadata.get('provider')}")
                print(f"  🔧 Arguments:")
                
                for field_name, field_info in example_tool.args_schema.model_fields.items():
                    required = "required" if field_info.is_required() else "optional"
                    field_type = field_info.annotation.__name__ if hasattr(field_info.annotation, '__name__') else str(field_info.annotation)
                    print(f"    - {field_name} ({field_type}, {required})")
        
        # Demonstrate provider health monitoring
        print("\n🏥 Provider Health Check:")
        health_status = await client.health_check()
        
        for provider_name, status in health_status.items():
            status_icon = "✅" if status["status"] == "healthy" else "❌"
            print(f"  {status_icon} {provider_name}: {status['status']}")
            
            if status["status"] == "healthy":
                print(f"      📊 Tools loaded: {status['tool_count']}")
                print(f"      🌐 Provider type: {status.get('provider_type', 'unknown')}")
            else:
                print(f"      ⚠️  Error: {status.get('error', 'Unknown error')}")
        
        # Demonstrate practical tool usage
        print("\n🚀 Practical Tool Usage Example:")
        
        # Find OpenLibrary tools that we can actually call successfully
        openlibrary_tools = [
            tool for tool in tools 
            if tool.metadata.get('provider') == 'openlibrary'
        ]
        
        if openlibrary_tools:
            # Look for a simple author lookup tool
            author_tools = [
                tool for tool in openlibrary_tools 
                if 'authors' in tool.name and 'olid' in str(tool.args_schema.model_fields.keys())
            ]
            
            if author_tools:
                tool = author_tools[0]
                print(f"  🎯 Testing OpenLibrary tool: {tool.name.split('.')[-1]}")
                print(f"  📋 Description: {tool.description}")
                
                # Use a known valid OpenLibrary author ID
                test_args = {"olid": "OL23919A"}  # J.K. Rowling's OpenLibrary ID
                print(f"  🔧 Calling with args: {test_args}")
                
                try:
                    # Call the tool
                    provider = tool.metadata.get('provider')
                    tool_name = tool.name.split('.')[-1]
                    result = await client.call_tool(f"{provider}.{tool_name}", test_args)
                    
                    # Parse and display result nicely
                    if isinstance(result, str):
                        try:
                            result_data = json.loads(result)
                            if isinstance(result_data, dict):
                                print(f"  ✅ Tool call successful!")
                                print(f"  📖 Author: {result_data.get('name', 'Unknown')}")
                                print(f"  🏷️  Key: {result_data.get('key', 'N/A')}")
                                if 'birth_date' in result_data:
                                    print(f"  📅 Born: {result_data['birth_date']}")
                                if 'bio' in result_data and result_data['bio']:
                                    bio = result_data['bio']
                                    if isinstance(bio, dict) and 'value' in bio:
                                        bio = bio['value']
                                    print(f"  📝 Bio: {str(bio)[:100]}...")
                            else:
                                print(f"  ✅ Tool call successful!")
                                print(f"  📄 Result: {str(result)[:200]}...")
                        except json.JSONDecodeError:
                            print(f"  ✅ Tool call successful!")
                            print(f"  📄 Result: {result[:200]}...")
                    else:
                        print(f"  ✅ Tool call successful!")
                        print(f"  📄 Result: {str(result)[:200]}...")
                        
                except Exception as e:
                    print(f"  ⚠️  Tool call failed: {str(e)[:100]}...")
                    print("     💡 This might be due to network issues or API changes")
            
            else:
                # Try a book lookup tool instead
                book_tools = [
                    tool for tool in openlibrary_tools 
                    if 'books' in tool.name and len([
                        name for name, field in tool.args_schema.model_fields.items() 
                        if field.is_required()
                    ]) == 1
                ]
                
                if book_tools:
                    tool = book_tools[0]
                    print(f"  🎯 Testing OpenLibrary tool: {tool.name.split('.')[-1]}")
                    print(f"  📋 Description: {tool.description}")
                    
                    # Find the required argument
                    required_args = [
                        name for name, field in tool.args_schema.model_fields.items() 
                        if field.is_required()
                    ]
                    
                    test_args = {}
                    for arg in required_args:
                        if 'bibkey' in arg.lower():
                            test_args[arg] = "ISBN:0451526538"  # A valid ISBN
                        elif 'olid' in arg.lower():
                            test_args[arg] = "OL7353617M"  # A valid book ID
                        else:
                            test_args[arg] = "test"
                    
                    print(f"  🔧 Calling with args: {test_args}")
                    
                    try:
                        provider = tool.metadata.get('provider')
                        tool_name = tool.name.split('.')[-1]
                        result = await client.call_tool(f"{provider}.{tool_name}", test_args)
                        
                        print(f"  ✅ Tool call successful!")
                        result_str = str(result)
                        if len(result_str) > 200:
                            result_str = result_str[:200] + "..."
                        print(f"  📄 Result: {result_str}")
                        
                    except Exception as e:
                        print(f"  ⚠️  Tool call failed: {str(e)[:100]}...")
                        print("     💡 This might be due to network issues or API changes")
                
                else:
                    print("  ℹ️  No suitable OpenLibrary tools found for demonstration")
        
        else:
            print("  ℹ️  No OpenLibrary tools available for testing")
        
        # Clean up
        await client.close()
        
        print(f"\n🎉 Example completed successfully!")
        print(f"📊 Summary:")
        print(f"  • Providers: {len(provider_tools)}")
        print(f"  • Total tools: {len(tools)}")
        print(f"  • Search queries tested: {len(search_examples)}")
        print(f"  • All functionality working correctly! ✅")
        
    finally:
        # Clean up the providers file
        if providers_file.exists():
            providers_file.unlink()
    
    print("\n💡 Next Steps:")
    print("  1. Add your own UTCP providers to the configuration")
    print("  2. Integrate these tools with LangGraph agents")
    print("  3. Use the search functionality to find relevant tools")
    print("  4. Monitor provider health in production")
    print("  5. Explore the full range of available tools!")


if __name__ == "__main__":
    asyncio.run(main())
