#!/usr/bin/env python3
"""Test script for LangChain UTCP Adapters with real providers.

This script tests the package with actual UTCP providers to validate 
that real tools are loaded and working correctly.
"""

import asyncio
from utcp.utcp_client import UtcpClient
from utcp.data.utcp_client_config import UtcpClientConfig
from langchain_utcp_adapters import load_utcp_tools, search_utcp_tools


async def test_real_providers():
    """Test with real UTCP providers to validate functionality."""
    print('🧪 Testing LangChain UTCP Adapters with Real Providers')
    print('=' * 60)
    
    try:
        # Create UTCP client directly
        print('📡 Creating UTCP client...')
        config = UtcpClientConfig()
        client = await UtcpClient.create(config=config)
        print('✅ Client created successfully')
        
        # Register a real provider (OpenLibrary)
        print('\n📋 Registering OpenLibrary provider...')
        await client.register_tool_provider({
            "name": "openlibrary",
            "provider_type": "http",
            "http_method": "GET",
            "url": "https://openlibrary.org/static/openapi.json",
            "content_type": "application/json"
        })
        print('✅ Provider registered successfully')
        
        # Load tools
        print('\n🔧 Loading tools...')
        tools = await load_utcp_tools(client)
        print(f'✅ Successfully loaded {len(tools)} tools')
        
        # Validate tools
        assert len(tools) > 0, "Should have loaded at least one tool"
        
        # Check tool properties
        for tool in tools[:3]:  # Check first 3 tools
            print(f'  📖 Tool: {tool.name}')
            print(f'     Description: {tool.description}')
            print(f'     Provider: {tool.metadata.get("provider", "unknown")}')
            
            # Validate tool has required properties
            assert hasattr(tool, 'name'), "Tool should have name"
            assert hasattr(tool, 'description'), "Tool should have description"
            assert hasattr(tool, 'args_schema'), "Tool should have args_schema"
            assert tool.metadata.get('utcp_tool') is True, "Tool should be marked as UTCP tool"
        
        # Test search functionality
        print('\n🔍 Testing search functionality...')
        search_results = await search_utcp_tools(client, "books", max_results=3)
        print(f'✅ Search returned {len(search_results)} results')
        
        # Validate search results
        for tool in search_results:
            print(f'  🔎 Found: {tool.name}')
            assert 'books' in tool.name.lower() or 'books' in tool.description.lower() or any('books' in tag.lower() for tag in tool.metadata.get('tags', [])), \
                "Search result should be related to 'books'"
        
        print('\n🎉 All tests passed successfully!')
        return True
        
    except Exception as e:
        print(f'❌ Test failed with error: {e}')
        import traceback
        traceback.print_exc()
        return False


# Run the test
if __name__ == "__main__":
    success = asyncio.run(test_real_providers())
    exit(0 if success else 1)
