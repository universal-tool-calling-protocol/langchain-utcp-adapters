"""Advanced LangGraph integration example for LangChain UTCP Adapters.

This example demonstrates advanced patterns for using UTCP tools with LangGraph agents,
including multiple providers, error handling, and tool search functionality.
"""

import asyncio
import os
from utcp.client.utcp_client import UtcpClient
from utcp.client.utcp_client_config import UtcpClientConfig
from utcp.shared.provider import HttpProvider
from langchain_utcp_adapters import load_utcp_tools, search_utcp_tools

# Optional: Only import if available
try:
    from langgraph.prebuilt import create_react_agent
    from langchain_openai import ChatOpenAI
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False
    print("LangGraph or OpenAI not available. Install with: pip install langgraph langchain-openai")


async def main():
    """Advanced LangGraph integration example."""
    print("🤖 Advanced LangGraph + UTCP Integration")
    print("=" * 45)
    
    if not LANGGRAPH_AVAILABLE:
        print("❌ Required dependencies not available.")
        print("Install with: pdm install -G examples")
        return
    
    # Check for OpenAI API key
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY environment variable not set")
        print("Set it with: export OPENAI_API_KEY=your_key_here")
        return
    
    # Check for OpenAI API key
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY environment variable not set")
        print("Set it with: export OPENAI_API_KEY=your_key_here")
        return
    
    print("✅ Dependencies and API key verified")
    
    # Create UTCP client
    print("\n📡 Setting up UTCP client...")
    config = UtcpClientConfig()
    client = await UtcpClient.create(config=config)
    
    # Register multiple providers for comprehensive testing
    print("📡 Registering multiple providers...")
    
    providers = [
        {
            "name": "openlibrary",
            "provider": HttpProvider(
                name="openlibrary",
                provider_type="http",
                http_method="GET",
                url="https://openlibrary.org/static/openapi.json",
                content_type="application/json"
            ),
            "description": "OpenLibrary API for book information"
        },
        {
            "name": "petstore",
            "provider": HttpProvider(
                name="petstore",
                provider_type="http",
                url="https://petstore.swagger.io/v2/swagger.json",
                http_method="GET"
            ),
            "description": "Swagger Petstore API for demo purposes"
        }
    ]
    
    registered_providers = []
    for provider_info in providers:
        try:
            print(f"  Registering {provider_info['name']}...")
            await client.register_tool_provider(provider_info["provider"])
            registered_providers.append(provider_info["name"])
            print(f"    ✅ {provider_info['description']}")
        except Exception as e:
            print(f"    ❌ Failed to register {provider_info['name']}: {e}")
    
    if not registered_providers:
        print("❌ No providers registered successfully. Cannot continue.")
        return
    
    print(f"✅ Successfully registered {len(registered_providers)} providers")
    
    # Load all tools and convert to LangChain format
    print("\n🔧 Loading UTCP tools...")
    tools = await load_utcp_tools(client)
    print(f"Loaded {len(tools)} tools from all providers:")
    
    # Group tools by provider for better organization
    tools_by_provider = {}
    for tool in tools:
        provider = tool.metadata.get('provider', 'unknown')
        if provider not in tools_by_provider:
            tools_by_provider[provider] = []
        tools_by_provider[provider].append(tool)
    
    for provider, provider_tools in tools_by_provider.items():
        print(f"  📦 {provider}: {len(provider_tools)} tools")
        for tool in provider_tools[:2]:  # Show first 2 tools per provider
            print(f"    - {tool.name}")
        if len(provider_tools) > 2:
            print(f"    ... and {len(provider_tools) - 2} more")
    
    if not tools:
        print("❌ No tools available. Cannot create agent.")
        return
    
    # Demonstrate tool search functionality
    print("\n🔍 Demonstrating tool search...")
    search_queries = ["book", "pet", "search", "get"]
    
    for query in search_queries:
        results = await search_utcp_tools(client, query, max_results=3)
        if results:
            print(f"  Query '{query}': {len(results)} tools found")
            for tool in results[:2]:
                provider = tool.metadata.get('provider', 'unknown')
                print(f"    - {tool.name} ({provider})")
    
    # Create LangGraph agent with UTCP tools
    print("\n🤖 Creating advanced LangGraph agent...")
    try:
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.1)
        agent = create_react_agent(llm, tools)
        print("✅ Agent created successfully with all available tools")
    except Exception as e:
        print(f"❌ Failed to create agent: {e}")
        return
    
    # Test the agent with multiple scenarios
    test_scenarios = [
        {
            "name": "Tool Discovery",
            "query": "What tools do you have available? List them by category.",
            "description": "Tests agent's ability to understand its capabilities"
        },
        {
            "name": "Book Search",
            "query": "Can you search for Hamlet by William Shakespeare?",
            "description": "Tests integration with OpenLibrary API"
        },
        {
            "name": "API Exploration", 
            "query": "What kind of information can you get about pets or animals?",
            "description": "Tests integration with Petstore API"
        }
    ]
    
    print("\n💬 Testing agent with multiple scenarios...")
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n{'='*50}")
        print(f"Test {i}: {scenario['name']}")
        print(f"{'='*50}")
        print(f"Query: {scenario['query']}")
        print(f"Purpose: {scenario['description']}")
        print()
        
        try:
            response = await agent.ainvoke({
                "messages": [("user", scenario["query"])]
            })
            
            print("🤖 Agent Response:")
            print(response["messages"][-1].content)
            
            # Check if tools were used
            tool_calls = []
            for message in response["messages"]:
                if hasattr(message, 'tool_calls') and message.tool_calls:
                    tool_calls.extend(message.tool_calls)
            
            if tool_calls:
                print(f"\n🔧 Tools Used:")
                for tool_call in tool_calls:
                    print(f"  - {tool_call['name']}")
                    if 'args' in tool_call:
                        print(f"    Args: {tool_call['args']}")
            else:
                print("\n💭 No tools were called for this query")
                
        except Exception as e:
            print(f"❌ Test failed: {e}")
    
    # Performance and statistics
    print(f"\n📊 Session Statistics:")
    print(f"  Total providers registered: {len(registered_providers)}")
    print(f"  Total tools available: {len(tools)}")
    print(f"  Tool categories: {len(tools_by_provider)}")
    print(f"  Average tools per provider: {len(tools) / len(tools_by_provider):.1f}")
    
    print("\n✅ Advanced LangGraph integration example completed!")
    print("\n💡 Key Features Demonstrated:")
    print("  • Multiple UTCP provider integration")
    print("  • Tool search and discovery")
    print("  • Advanced agent testing scenarios")
    print("  • Error handling and graceful degradation")
    print("  • Tool usage tracking and statistics")


if __name__ == "__main__":
    asyncio.run(main())
