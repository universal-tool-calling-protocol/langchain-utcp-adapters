"""Authentication example for LangChain UTCP Adapters.

This example demonstrates how to use different authentication methods
with UTCP providers.
"""

import asyncio
import json
import os
from pathlib import Path

from langchain_utcp_adapters.client import MultiProviderUTCPClient


async def main():
    """Main example function demonstrating different authentication methods."""
    
    # Create .env file with example credentials
    env_content = """
# Example API credentials
WEATHER_API_KEY=your_weather_api_key_here
OAUTH_CLIENT_ID=your_oauth_client_id
OAUTH_CLIENT_SECRET=your_oauth_client_secret
BASIC_AUTH_USERNAME=your_username
BASIC_AUTH_PASSWORD=your_password
"""
    
    env_file = Path(".env")
    with open(env_file, "w") as f:
        f.write(env_content)
    
    # Create providers configuration with different auth methods
    providers_config = [
        {
            "name": "weather_api_key",
            "provider_type": "http",
            "url": "https://api.weather.com/utcp",
            "http_method": "GET",
            "auth": {
                "auth_type": "api_key",
                "api_key": "${WEATHER_API_KEY}",
                "var_name": "X-API-Key"
            }
        },
        {
            "name": "oauth_service",
            "provider_type": "http", 
            "url": "https://api.example.com/utcp",
            "http_method": "POST",
            "auth": {
                "auth_type": "oauth2",
                "token_url": "https://auth.example.com/token",
                "client_id": "${OAUTH_CLIENT_ID}",
                "client_secret": "${OAUTH_CLIENT_SECRET}",
                "scope": "read write"
            }
        },
        {
            "name": "basic_auth_service",
            "provider_type": "http",
            "url": "https://secure.example.com/utcp", 
            "http_method": "GET",
            "auth": {
                "auth_type": "basic",
                "username": "${BASIC_AUTH_USERNAME}",
                "password": "${BASIC_AUTH_PASSWORD}"
            }
        },
        {
            "name": "no_auth_service",
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
        # Create UTCP client with environment variable loading
        print("Creating UTCP client with authentication...")
        client = MultiProviderUTCPClient(
            config={
                "providers_file_path": "providers.json",
                "load_variables_from": [{
                    "type": "dotenv",
                    "env_file_path": ".env"
                }]
            }
        )
        
        # Get provider information to show auth configuration
        print("\nProvider configurations:")
        providers = await client.get_providers()
        
        for provider_name in providers:
            try:
                info = await client.get_provider_info(provider_name)
                print(f"\n{provider_name}:")
                print(f"  Type: {info['provider_type']}")
                print(f"  URL: {info['config'].get('url', 'N/A')}")
                
                auth_config = info['config'].get('auth')
                if auth_config:
                    auth_type = auth_config.get('auth_type', 'unknown')
                    print(f"  Auth: {auth_type}")
                    
                    if auth_type == 'api_key':
                        print(f"    Header: {auth_config.get('var_name', 'Authorization')}")
                    elif auth_type == 'oauth2':
                        print(f"    Token URL: {auth_config.get('token_url')}")
                        print(f"    Scope: {auth_config.get('scope', 'default')}")
                    elif auth_type == 'basic':
                        print(f"    Username: {auth_config.get('username', '[configured]')}")
                else:
                    print("  Auth: None")
                    
            except Exception as e:
                print(f"  Error getting info: {e}")
        
        # Perform health check to test authentication
        print("\nPerforming health check (this will test authentication)...")
        health = await client.health_check()
        
        for provider_name, status in health.items():
            print(f"\n{provider_name}: {status['status']}")
            if status['status'] == 'healthy':
                print(f"  ✓ Authentication successful")
                print(f"  ✓ Found {status['tool_count']} tools")
            else:
                print(f"  ✗ Authentication failed: {status.get('error', 'Unknown error')}")
        
        # Try to load tools (this will also test authentication)
        print("\nAttempting to load tools...")
        try:
            tools = await client.get_tools()
            print(f"Successfully loaded {len(tools)} tools across all providers")
            
            # Show tools by provider
            provider_tools = {}
            for tool in tools:
                provider = tool.metadata.get('provider', 'unknown')
                if provider not in provider_tools:
                    provider_tools[provider] = []
                provider_tools[provider].append(tool.name)
            
            for provider, tool_names in provider_tools.items():
                print(f"\n{provider} tools:")
                for tool_name in tool_names:
                    print(f"  - {tool_name}")
                    
        except Exception as e:
            print(f"Error loading tools: {e}")
        
        # Clean up
        await client.close()
        
    finally:
        # Clean up files
        if providers_file.exists():
            providers_file.unlink()
        if env_file.exists():
            env_file.unlink()


if __name__ == "__main__":
    print("Authentication Example for LangChain UTCP Adapters")
    print("=" * 50)
    print("This example demonstrates different authentication methods:")
    print("- API Key authentication")
    print("- OAuth2 authentication") 
    print("- Basic authentication")
    print("- No authentication")
    print("\nNote: This example uses placeholder credentials.")
    print("In a real scenario, you would provide actual API keys and credentials.")
    print("=" * 50)
    
    asyncio.run(main())
