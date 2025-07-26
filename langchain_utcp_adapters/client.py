"""Client for connecting to multiple UTCP providers and loading LangChain tools.

This module provides the MultiProviderUTCPClient class for managing connections to multiple
UTCP providers and loading tools from them.
"""

import asyncio
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from langchain_core.tools import BaseTool
from utcp.client.utcp_client import UtcpClient
from utcp.client.utcp_client_config import UtcpClientConfig

from langchain_utcp_adapters.tools import (
    load_utcp_tools,
    search_utcp_tools,
)


class MultiProviderUTCPClient:
    """Client for connecting to multiple UTCP providers.

    Loads LangChain-compatible tools from UTCP providers with support for
    authentication, tool search, and multiple transport protocols.
    """

    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        providers_file_path: Optional[str] = None,
        providers: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        """Initialize a MultiProviderUTCPClient.

        Args:
            config: UTCP client configuration dictionary
            providers_file_path: Path to providers.json file
            providers: List of provider configurations
            
        Example: Using providers file
        
        ```python
        client = MultiProviderUTCPClient(
            providers_file_path="./providers.json"
        )
        ```
        
        Example: Using direct configuration
        
        ```python
        client = MultiProviderUTCPClient(
            config={
                "providers_file_path": "./providers.json",
                "load_variables_from": [{
                    "type": "dotenv",
                    "env_file_path": ".env"
                }]
            }
        )
        ```
        
        Example: Using inline providers
        
        ```python
        client = MultiProviderUTCPClient(
            providers=[
                {
                    "name": "math_api",
                    "provider_type": "http",
                    "url": "http://localhost:8080/utcp",
                    "http_method": "GET"
                }
            ]
        )
        ```
        """
        self._utcp_client: Optional[UtcpClient] = None
        self._config = config or {}
        
        # Handle different initialization methods
        if providers_file_path:
            self._config["providers_file_path"] = providers_file_path
        elif providers is not None:
            # Create a temporary providers file (even if empty for testing)
            self._create_temp_providers_file(providers)
        elif "providers_file_path" not in self._config:
            raise ValueError(
                "Must provide either config with providers_file_path, "
                "providers_file_path parameter, or providers list"
            )

    def _create_temp_providers_file(self, providers: List[Dict[str, Any]]) -> None:
        """Create a temporary providers file from inline configuration."""
        temp_path = Path.cwd() / ".temp_providers.json"
        with open(temp_path, "w") as f:
            json.dump(providers, f, indent=2)
        self._config["providers_file_path"] = str(temp_path)
        self._temp_file = temp_path

    async def _ensure_client(self) -> UtcpClient:
        """Ensure the UTCP client is initialized."""
        if self._utcp_client is None:
            client_config = UtcpClientConfig(**self._config)
            self._utcp_client = await UtcpClient.create(config=client_config)
        return self._utcp_client

    async def get_tools(
        self, 
        provider_name: Optional[str] = None
    ) -> List[BaseTool]:
        """Get a list of all tools from connected providers.

        Args:
            provider_name: Optional name of the provider to get tools from.
                If None, all tools from all providers will be returned.

        Returns:
            A list of LangChain tools
        """
        client = await self._ensure_client()
        return await load_utcp_tools(client, provider_name=provider_name)

    async def search_tools(
        self,
        query: str,
        provider_name: Optional[str] = None,
        max_results: Optional[int] = None,
    ) -> List[BaseTool]:
        """Search for tools using UTCP's search capabilities.

        Args:
            query: Search query string
            provider_name: Optional provider name to filter tools
            max_results: Maximum number of results to return

        Returns:
            A list of relevant LangChain tools
        """
        client = await self._ensure_client()
        return await search_utcp_tools(
            client, 
            query, 
            provider_name=provider_name,
            max_results=max_results
        )

    async def get_providers(self) -> List[str]:
        """Get a list of registered provider names.

        Returns:
            List of provider names
        """
        client = await self._ensure_client()
        providers = await client.tool_repository.get_providers()
        return [provider.name for provider in providers]

    async def get_provider_info(self, provider_name: str) -> Dict[str, Any]:
        """Get information about a specific provider.

        Args:
            provider_name: Name of the provider

        Returns:
            Dictionary containing provider information

        Raises:
            ValueError: If provider is not found
        """
        client = await self._ensure_client()
        providers = await client.tool_repository.get_providers()
        
        for provider in providers:
            if provider.name == provider_name:
                return {
                    "name": provider.name,
                    "provider_type": provider.provider_type,
                    "config": provider.model_dump(),
                }
        
        raise ValueError(f"Provider '{provider_name}' not found")

    async def call_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
    ) -> Any:
        """Call a UTCP tool directly.

        Args:
            tool_name: Name of the tool (with provider namespace)
            arguments: Tool arguments

        Returns:
            Tool execution result
        """
        client = await self._ensure_client()
        return await client.call_tool(tool_name, arguments)

    async def register_provider(self, provider_config: Dict[str, Any]) -> None:
        """Register a new provider dynamically.

        Args:
            provider_config: Provider configuration dictionary
        """
        client = await self._ensure_client()
        # This would require extending the UTCP client to support dynamic registration
        # For now, we'll raise a NotImplementedError
        raise NotImplementedError(
            "Dynamic provider registration is not yet supported. "
            "Please add providers to your providers.json file and recreate the client."
        )

    async def deregister_provider(self, provider_name: str) -> None:
        """Deregister a provider.

        Args:
            provider_name: Name of the provider to deregister
        """
        client = await self._ensure_client()
        await client.deregister_tool_provider(provider_name)

    async def health_check(self) -> Dict[str, Any]:
        """Perform a health check on all providers.

        Returns:
            Dictionary with health status of each provider
        """
        client = await self._ensure_client()
        providers = await self.get_providers()
        health_status = {}
        
        for provider_name in providers:
            try:
                # Try to get tools from the provider as a health check
                tools = await self.get_tools(provider_name=provider_name)
                health_status[provider_name] = {
                    "status": "healthy",
                    "tool_count": len(tools),
                }
            except Exception as e:
                health_status[provider_name] = {
                    "status": "unhealthy",
                    "error": str(e),
                }
        
        return health_status

    async def close(self) -> None:
        """Close the client and clean up resources."""
        if hasattr(self, '_temp_file') and self._temp_file.exists():
            self._temp_file.unlink()
        
        # The UTCP client doesn't have an explicit close method,
        # but we can reset our reference
        self._utcp_client = None

    async def __aenter__(self) -> "MultiProviderUTCPClient":
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.close()


# Convenience function for quick setup
async def create_utcp_client(
    providers_file_path: str,
    load_env: bool = True,
) -> MultiProviderUTCPClient:
    """Create a UTCP client with common configuration.

    Args:
        providers_file_path: Path to providers.json file
        load_env: Whether to load environment variables from .env file

    Returns:
        Configured MultiProviderUTCPClient
    """
    config = {"providers_file_path": providers_file_path}
    
    if load_env:
        config["load_variables_from"] = [{
            "type": "dotenv",
            "env_file_path": ".env"
        }]
    
    return MultiProviderUTCPClient(config=config)
