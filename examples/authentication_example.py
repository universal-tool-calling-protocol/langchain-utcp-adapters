"""Authentication example for LangChain UTCP Adapters.

This example demonstrates how to configure different authentication methods
for UTCP providers when connecting to real APIs that require authentication.

Note: This is a demonstration of authentication patterns. The examples use
working test endpoints where possible, but real API usage would require
valid credentials.
"""

import asyncio
from pathlib import Path

from utcp.client.utcp_client import UtcpClient
from utcp.client.utcp_client_config import UtcpClientConfig
from utcp.shared.provider import HttpProvider
from utcp.shared.auth import ApiKeyAuth, BasicAuth, OAuth2Auth
from langchain_utcp_adapters import load_utcp_tools


async def demonstrate_api_key_auth():
    """Demonstrate API key authentication with a working test endpoint."""
    print("🔑 API Key Authentication Example")
    print("-" * 40)
    
    config = UtcpClientConfig()
    client = await UtcpClient.create(config=config)
    
    # Example 1: API key in header (most common)
    api_key_provider = HttpProvider(
        name="httpbin_headers",
        provider_type="http",
        url="http://httpbin.org/headers",
        http_method="GET",
        auth=ApiKeyAuth(
            api_key="demo-api-key-12345",
            var_name="X-API-Key",
            location="header"
        )
    )
    
    try:
        await client.register_tool_provider(api_key_provider)
        tools = await load_utcp_tools(client, provider_name="httpbin_headers")
        
        if tools:
            print(f"✅ Successfully registered provider with API key auth")
            print(f"   Tool: {tools[0].name}")
            print(f"   Auth: API key in header 'X-API-Key'")
        else:
            print("⚠️  Provider registered but no tools found")
            
    except Exception as e:
        print(f"❌ API key auth failed: {e}")
    
    print()


async def demonstrate_basic_auth():
    """Demonstrate basic authentication with HTTPBin test endpoint."""
    print("🔐 Basic Authentication Example")
    print("-" * 40)
    
    config = UtcpClientConfig()
    client = await UtcpClient.create(config=config)
    
    # HTTPBin provides a working basic auth test endpoint
    basic_auth_provider = HttpProvider(
        name="httpbin_basic_auth",
        provider_type="http",
        url="http://httpbin.org/basic-auth/testuser/testpass",
        http_method="GET",
        auth=BasicAuth(
            username="testuser",
            password="testpass"
        )
    )
    
    try:
        await client.register_tool_provider(basic_auth_provider)
        tools = await load_utcp_tools(client, provider_name="httpbin_basic_auth")
        
        if tools:
            print(f"✅ Successfully registered provider with basic auth")
            print(f"   Tool: {tools[0].name}")
            print(f"   Auth: Basic authentication (username/password)")
        else:
            print("⚠️  Provider registered but no tools found")
            
    except Exception as e:
        print(f"❌ Basic auth failed: {e}")
    
    print()


async def demonstrate_oauth2_auth():
    """Demonstrate OAuth2 authentication configuration."""
    print("🌐 OAuth2 Authentication Example")
    print("-" * 40)
    
    config = UtcpClientConfig()
    client = await UtcpClient.create(config=config)
    
    # OAuth2 example (this would require real OAuth2 endpoints)
    oauth2_provider = HttpProvider(
        name="oauth2_demo",
        provider_type="http",
        url="https://api.github.com",  # GitHub API as example
        http_method="GET",
        auth=OAuth2Auth(
            token_url="https://github.com/login/oauth/access_token",
            client_id="your_github_client_id",
            client_secret="your_github_client_secret",
            scope="repo read:user"
        )
    )
    
    try:
        # This will fail without real credentials, but shows the pattern
        await client.register_tool_provider(oauth2_provider)
        tools = await load_utcp_tools(client, provider_name="oauth2_demo")
        
        if tools:
            print(f"✅ Successfully registered provider with OAuth2")
            print(f"   Tools found: {len(tools)}")
        else:
            print("⚠️  Provider registered but no tools found")
            
    except Exception as e:
        print(f"❌ OAuth2 auth failed (expected without real credentials): {e}")
        print("   This demonstrates the OAuth2 configuration pattern")
    
    print()


async def demonstrate_environment_variables():
    """Show how to use environment variables for credentials."""
    print("🌍 Environment Variables for Authentication")
    print("-" * 40)
    
    # Create a temporary .env file for demonstration
    env_file = Path(".env.demo")
    env_content = """# Demo environment variables for authentication
API_KEY=demo-key-from-env
OAUTH_CLIENT_ID=demo-client-id
OAUTH_CLIENT_SECRET=demo-client-secret
BASIC_USERNAME=demo-user
BASIC_PASSWORD=demo-pass
"""
    
    with open(env_file, "w") as f:
        f.write(env_content)
    
    print("📝 Created demo .env file with example credentials")
    print("   In real usage, you would set these environment variables:")
    print("   export API_KEY=your_real_api_key")
    print("   export OAUTH_CLIENT_ID=your_real_client_id")
    print("   # etc.")
    print()
    
    # Show how to reference environment variables in auth config
    print("🔧 Authentication with environment variables:")
    print("   API Key: ${API_KEY}")
    print("   OAuth Client ID: ${OAUTH_CLIENT_ID}")
    print("   Basic Auth Username: ${BASIC_USERNAME}")
    print()
    
    # Example of using environment variables in provider config
    config = UtcpClientConfig()
    client = await UtcpClient.create(config=config)
    
    # This would use environment variables if they were set
    env_provider = HttpProvider(
        name="env_auth_demo",
        provider_type="http",
        url="http://httpbin.org/headers",
        http_method="GET",
        auth=ApiKeyAuth(
            api_key="${API_KEY}",  # Would be replaced with env var value
            var_name="Authorization",
            location="header"
        )
    )
    
    print("✅ Provider configured to use ${API_KEY} environment variable")
    
    # Clean up
    if env_file.exists():
        env_file.unlink()
    
    print()


async def main():
    """Main example function demonstrating different authentication methods."""
    print("🔐 LangChain UTCP Adapters - Authentication Examples")
    print("=" * 60)
    print("This example shows how to configure authentication for UTCP providers.")
    print("These patterns work with real APIs that require authentication.")
    print()
    
    await demonstrate_api_key_auth()
    await demonstrate_basic_auth()
    await demonstrate_oauth2_auth()
    await demonstrate_environment_variables()
    
    print("📚 Summary of Authentication Methods:")
    print("   • API Key: Most common, key in header or query parameter")
    print("   • Basic Auth: Username/password, base64 encoded")
    print("   • OAuth2: Token-based, requires client credentials")
    print("   • Environment Variables: Secure credential storage")
    print()
    print("💡 Best Practices:")
    print("   • Never hardcode credentials in source code")
    print("   • Use environment variables for sensitive data")
    print("   • Rotate API keys regularly")
    print("   • Use least-privilege access scopes")
    print()
    print("✅ Authentication examples completed!")


if __name__ == "__main__":
    asyncio.run(main())
