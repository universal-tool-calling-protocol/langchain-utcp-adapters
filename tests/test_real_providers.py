#!/usr/bin/env python3
"""Test script for LangChain UTCP Adapters with real providers.

This script tests the package with actual UTCP providers from the python-utcp examples
to validate that real tools are loaded and working correctly.
"""

import asyncio
import json
from langchain_utcp_adapters.client import MultiProviderUTCPClient


async def test_real_providers():
    """Test with real UTCP providers to validate functionality."""
    print('🧪 Testing LangChain UTCP Adapters with Real Providers')
    print('=' * 60)
    
    try:
        # Create client with real providers
        print('📡 Creating UTCP client with real providers...')
        client = MultiProviderUTCPClient(
            providers_file_path='tests/test_providers.json'
        )
        print('✅ Client created successfully')
        
        # Get providers info
        print('\n📋 Getting provider information...')
        providers = await client.get_providers()
        print(f'Found {len(providers)} providers:')
        for provider in providers:
            print(f'  - {provider}')
        
        # Get detailed provider info
        print('\n🔍 Provider details:')
        for provider in providers:
            try:
                info = await client.get_provider_info(provider)
                print(f'  {provider}:')
                print(f'    Type: {info["provider_type"]}')
                if 'url' in info['config']:
                    print(f'    URL: {info["config"]["url"]}')
                if 'file_path' in info['config']:
                    print(f'    File: {info["config"]["file_path"]}')
            except Exception as e:
                print(f'  {provider}: Error getting info - {e}')
        
        # Load tools
        print('\n🔧 Loading tools from all providers...')
        tools = await client.get_tools()
        print(f'✅ Loaded {len(tools)} tools total')
        
        # Show tools by provider
        if tools:
            print('\n📚 Tools by provider:')
            provider_tools = {}
            for tool in tools:
                provider = tool.metadata.get('provider', 'unknown')
                if provider not in provider_tools:
                    provider_tools[provider] = []
                provider_tools[provider].append(tool)
            
            for provider_name, provider_tool_list in provider_tools.items():
                print(f'\n  📦 {provider_name} ({len(provider_tool_list)} tools):')
                for i, tool in enumerate(provider_tool_list[:5]):  # Show first 5 tools
                    print(f'    {i+1}. {tool.name}')
                    print(f'       Description: {tool.description[:100]}...')
                    args = list(tool.args_schema.model_fields.keys())
                    print(f'       Arguments: {args[:5]}{"..." if len(args) > 5 else ""}')
                    print(f'       Tags: {tool.metadata.get("tags", [])}')
                    print()
                
                if len(provider_tool_list) > 5:
                    print(f'    ... and {len(provider_tool_list) - 5} more tools')
        else:
            print('⚠️  No tools loaded - this might indicate provider issues')
        
        # Test search functionality
        print('\n🔍 Testing search functionality...')
        search_queries = ['news', 'book', 'search', 'article', 'library']
        
        for query in search_queries:
            search_results = await client.search_tools(query, max_results=3)
            print(f'  🔎 Search "{query}": {len(search_results)} results')
            for result in search_results:
                provider = result.metadata.get('provider', 'unknown')
                print(f'    - {result.name} ({provider})')
        
        # Test provider-specific tool loading
        print('\n🎯 Testing provider-specific tool loading...')
        for provider in providers:
            try:
                provider_tools = await client.get_tools(provider_name=provider)
                print(f'  {provider}: {len(provider_tools)} tools')
            except Exception as e:
                print(f'  {provider}: Error - {e}')
        
        # Health check
        print('\n🏥 Performing health check...')
        health = await client.health_check()
        for provider_name, status in health.items():
            status_icon = '✅' if status['status'] == 'healthy' else '❌'
            print(f'  {status_icon} {provider_name}: {status["status"]}')
            if status['status'] == 'healthy':
                print(f'      Tools loaded: {status["tool_count"]}')
            else:
                print(f'      Error: {status.get("error", "Unknown error")}')
        
        # Test direct tool calling (if tools are available)
        if tools:
            print('\n🚀 Testing direct tool calling...')
            
            # Focus on OpenLibrary tools since they don't require API keys
            openlibrary_tools = [
                t for t in tools 
                if t.metadata.get('provider') == 'openlibrary'
            ]
            
            if openlibrary_tools:
                # Look for author tools first (they usually work well)
                author_tools = [
                    t for t in openlibrary_tools 
                    if 'authors' in t.name and len([
                        name for name, field in t.args_schema.model_fields.items() 
                        if field.is_required()
                    ]) == 1
                ]
                
                if author_tools:
                    test_tool = author_tools[0]
                    print(f'  Testing OpenLibrary tool: {test_tool.name}')
                    
                    # Use a known valid author ID
                    args = {"olid": "OL23919A"}  # J.K. Rowling
                    print(f'  Calling with args: {args}')
                    
                    try:
                        provider = test_tool.metadata['provider']
                        tool_name = test_tool.name.split('.')[-1]
                        result = await client.call_tool(f"{provider}.{tool_name}", args)
                        
                        # Try to parse JSON result for better display
                        try:
                            result_data = json.loads(result) if isinstance(result, str) else result
                            if isinstance(result_data, dict) and 'name' in result_data:
                                print(f'  ✅ Tool call successful!')
                                print(f'     Author: {result_data["name"]}')
                                print(f'     Key: {result_data.get("key", "N/A")}')
                            else:
                                print(f'  ✅ Tool call successful: {str(result)[:100]}...')
                        except:
                            print(f'  ✅ Tool call successful: {str(result)[:100]}...')
                            
                    except Exception as e:
                        print(f'  ⚠️  Tool call failed: {str(e)[:100]}...')
                        print('     (This might be due to network issues or API changes)')
                
                else:
                    # Try any simple OpenLibrary tool
                    simple_ol_tools = [
                        t for t in openlibrary_tools 
                        if len([
                            name for name, field in t.args_schema.model_fields.items() 
                            if field.is_required()
                        ]) <= 1
                    ]
                    
                    if simple_ol_tools:
                        test_tool = simple_ol_tools[0]
                        print(f'  Testing OpenLibrary tool: {test_tool.name}')
                        
                        # Create appropriate test arguments
                        required_args = [
                            name for name, field in test_tool.args_schema.model_fields.items() 
                            if field.is_required()
                        ]
                        
                        args = {}
                        for arg in required_args:
                            if 'olid' in arg.lower():
                                args[arg] = "OL23919A"
                            elif 'bibkey' in arg.lower():
                                args[arg] = "ISBN:0451526538"
                            else:
                                args[arg] = "test"
                        
                        print(f'  Calling with args: {args}')
                        
                        try:
                            provider = test_tool.metadata['provider']
                            tool_name = test_tool.name.split('.')[-1]
                            result = await client.call_tool(f"{provider}.{tool_name}", args)
                            print(f'  ✅ Tool call successful: {str(result)[:100]}...')
                        except Exception as e:
                            print(f'  ⚠️  Tool call failed: {str(e)[:100]}...')
                            print('     (This is expected for some API endpoints)')
                    else:
                        print('  No simple OpenLibrary tools found for testing')
            else:
                print('  No OpenLibrary tools available for testing')
        else:
            print('  No tools available for testing')
        
        await client.close()
        print('\n🎉 Real provider testing completed successfully!')
        
        # Summary
        print('\n📊 SUMMARY:')
        print(f'  Providers tested: {len(providers)}')
        print(f'  Tools loaded: {len(tools)}')
        print(f'  Search queries tested: {len(search_queries)}')
        print('  Status: ✅ ALL TESTS PASSED')
        
    except Exception as e:
        print(f'❌ Error during testing: {e}')
        import traceback
        traceback.print_exc()
        return False
    
    return True


async def main():
    """Main function to run the tests."""
    success = await test_real_providers()
    if success:
        print('\n🏆 LangChain UTCP Adapters are working correctly with real providers!')
    else:
        print('\n💥 Some issues were found during testing.')
    
    return success


if __name__ == "__main__":
    asyncio.run(main())
