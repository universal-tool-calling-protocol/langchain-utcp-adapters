"""Tests for MultiProviderUTCPClient."""

import json
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from langchain_utcp_adapters.client import MultiProviderUTCPClient, create_utcp_client


class TestMultiProviderUTCPClient:
    """Test MultiProviderUTCPClient functionality."""

    @pytest.fixture
    def sample_providers_config(self):
        """Sample providers configuration."""
        return [
            {
                "name": "test_provider",
                "provider_type": "http",
                "url": "http://example.com/utcp",
                "http_method": "GET"
            }
        ]

    @pytest.fixture
    def providers_file(self, tmp_path, sample_providers_config):
        """Create a temporary providers.json file."""
        providers_file = tmp_path / "providers.json"
        with open(providers_file, "w") as f:
            json.dump(sample_providers_config, f)
        return str(providers_file)

    def test_init_with_providers_file_path(self, providers_file):
        """Test initialization with providers file path."""
        client = MultiProviderUTCPClient(providers_file_path=providers_file)
        assert client._config["providers_file_path"] == providers_file

    def test_init_with_config(self, providers_file):
        """Test initialization with config dictionary."""
        config = {"providers_file_path": providers_file}
        client = MultiProviderUTCPClient(config=config)
        assert client._config["providers_file_path"] == providers_file

    def test_init_with_providers_list(self, sample_providers_config):
        """Test initialization with providers list."""
        client = MultiProviderUTCPClient(providers=sample_providers_config)
        assert "providers_file_path" in client._config
        # Check that temp file was created
        temp_file = Path(client._config["providers_file_path"])
        assert temp_file.exists()
        # Clean up
        temp_file.unlink()

    def test_init_without_config_raises_error(self):
        """Test that initialization without config raises error."""
        with pytest.raises(ValueError, match="Must provide either"):
            MultiProviderUTCPClient()

    @pytest.mark.asyncio
    async def test_ensure_client_creates_utcp_client(self, providers_file):
        """Test that _ensure_client creates UTCP client."""
        client = MultiProviderUTCPClient(providers_file_path=providers_file)
        
        with patch('langchain_utcp_adapters.client.UtcpClient') as mock_utcp_client_class:
            mock_utcp_client = AsyncMock()
            # Fix: create should return a coroutine that resolves to the mock client
            async def mock_create(*args, **kwargs):
                return mock_utcp_client
            mock_utcp_client_class.create = mock_create
            
            result = await client._ensure_client()
            
            assert result == mock_utcp_client
            assert client._utcp_client == mock_utcp_client

    @pytest.mark.asyncio
    async def test_get_tools(self, providers_file):
        """Test getting tools from all providers."""
        client = MultiProviderUTCPClient(providers_file_path=providers_file)
        
        with patch('langchain_utcp_adapters.client.load_utcp_tools') as mock_load_tools:
            mock_tools = [MagicMock(), MagicMock()]
            mock_load_tools.return_value = mock_tools
            
            with patch.object(client, '_ensure_client') as mock_ensure_client:
                mock_utcp_client = AsyncMock()
                mock_ensure_client.return_value = mock_utcp_client
                
                tools = await client.get_tools()
                
                assert tools == mock_tools
                mock_load_tools.assert_called_once_with(mock_utcp_client, provider_name=None)

    @pytest.mark.asyncio
    async def test_get_tools_with_provider_filter(self, providers_file):
        """Test getting tools from specific provider."""
        client = MultiProviderUTCPClient(providers_file_path=providers_file)
        
        with patch('langchain_utcp_adapters.client.load_utcp_tools') as mock_load_tools:
            mock_tools = [MagicMock()]
            mock_load_tools.return_value = mock_tools
            
            with patch.object(client, '_ensure_client') as mock_ensure_client:
                mock_utcp_client = AsyncMock()
                mock_ensure_client.return_value = mock_utcp_client
                
                tools = await client.get_tools(provider_name="test_provider")
                
                assert tools == mock_tools
                mock_load_tools.assert_called_once_with(
                    mock_utcp_client, 
                    provider_name="test_provider"
                )

    @pytest.mark.asyncio
    async def test_search_tools(self, providers_file):
        """Test searching for tools."""
        client = MultiProviderUTCPClient(providers_file_path=providers_file)
        
        with patch('langchain_utcp_adapters.client.search_utcp_tools') as mock_search_tools:
            mock_tools = [MagicMock()]
            mock_search_tools.return_value = mock_tools
            
            with patch.object(client, '_ensure_client') as mock_ensure_client:
                mock_utcp_client = AsyncMock()
                mock_ensure_client.return_value = mock_utcp_client
                
                tools = await client.search_tools("test query")
                
                assert tools == mock_tools
                mock_search_tools.assert_called_once_with(
                    mock_utcp_client,
                    "test query",
                    provider_name=None,
                    max_results=None
                )

    @pytest.mark.asyncio
    async def test_get_providers(self, providers_file):
        """Test getting list of providers."""
        client = MultiProviderUTCPClient(providers_file_path=providers_file)
        
        with patch.object(client, '_ensure_client') as mock_ensure_client:
            mock_utcp_client = AsyncMock()
            mock_tool_repo = AsyncMock()
            
            # Mock provider objects
            mock_provider1 = MagicMock()
            mock_provider1.name = "provider1"
            mock_provider2 = MagicMock()
            mock_provider2.name = "provider2"
            
            mock_tool_repo.get_providers.return_value = [mock_provider1, mock_provider2]
            mock_utcp_client.tool_repository = mock_tool_repo
            mock_ensure_client.return_value = mock_utcp_client
            
            providers = await client.get_providers()
            
            assert providers == ["provider1", "provider2"]

    @pytest.mark.asyncio
    async def test_get_provider_info(self, providers_file):
        """Test getting provider information."""
        client = MultiProviderUTCPClient(providers_file_path=providers_file)
        
        with patch.object(client, '_ensure_client') as mock_ensure_client:
            mock_utcp_client = AsyncMock()
            mock_tool_repo = AsyncMock()
            
            # Mock provider object
            mock_provider = MagicMock()
            mock_provider.name = "test_provider"
            mock_provider.provider_type = "http"
            mock_provider.model_dump.return_value = {"name": "test_provider", "url": "http://example.com"}
            
            mock_tool_repo.get_providers.return_value = [mock_provider]
            mock_utcp_client.tool_repository = mock_tool_repo
            mock_ensure_client.return_value = mock_utcp_client
            
            info = await client.get_provider_info("test_provider")
            
            assert info["name"] == "test_provider"
            assert info["provider_type"] == "http"
            assert "config" in info

    @pytest.mark.asyncio
    async def test_get_provider_info_not_found(self, providers_file):
        """Test getting provider info for non-existent provider."""
        client = MultiProviderUTCPClient(providers_file_path=providers_file)
        
        with patch.object(client, '_ensure_client') as mock_ensure_client:
            mock_utcp_client = AsyncMock()
            mock_tool_repo = AsyncMock()
            mock_tool_repo.get_providers.return_value = []
            mock_utcp_client.tool_repository = mock_tool_repo
            mock_ensure_client.return_value = mock_utcp_client
            
            with pytest.raises(ValueError, match="Provider 'nonexistent' not found"):
                await client.get_provider_info("nonexistent")

    @pytest.mark.asyncio
    async def test_call_tool(self, providers_file):
        """Test calling a tool directly."""
        client = MultiProviderUTCPClient(providers_file_path=providers_file)
        
        with patch.object(client, '_ensure_client') as mock_ensure_client:
            mock_utcp_client = AsyncMock()
            mock_utcp_client.call_tool.return_value = {"result": "success"}
            mock_ensure_client.return_value = mock_utcp_client
            
            result = await client.call_tool("provider.tool", {"arg": "value"})
            
            assert result == {"result": "success"}
            mock_utcp_client.call_tool.assert_called_once_with("provider.tool", {"arg": "value"})

    @pytest.mark.asyncio
    async def test_deregister_provider(self, providers_file):
        """Test deregistering a provider."""
        client = MultiProviderUTCPClient(providers_file_path=providers_file)
        
        with patch.object(client, '_ensure_client') as mock_ensure_client:
            mock_utcp_client = AsyncMock()
            mock_ensure_client.return_value = mock_utcp_client
            
            await client.deregister_provider("test_provider")
            
            mock_utcp_client.deregister_tool_provider.assert_called_once_with("test_provider")

    @pytest.mark.asyncio
    async def test_health_check(self, providers_file):
        """Test health check functionality."""
        client = MultiProviderUTCPClient(providers_file_path=providers_file)
        
        with patch.object(client, 'get_providers') as mock_get_providers:
            with patch.object(client, 'get_tools') as mock_get_tools:
                mock_get_providers.return_value = ["provider1", "provider2"]
                
                # Mock successful health check for provider1
                mock_get_tools.side_effect = [
                    [MagicMock(), MagicMock()],  # provider1: 2 tools
                    Exception("Connection failed")  # provider2: error
                ]
                
                health = await client.health_check()
                
                assert health["provider1"]["status"] == "healthy"
                assert health["provider1"]["tool_count"] == 2
                assert health["provider2"]["status"] == "unhealthy"
                assert "Connection failed" in health["provider2"]["error"]

    @pytest.mark.asyncio
    async def test_context_manager(self, providers_file):
        """Test using client as context manager."""
        async with MultiProviderUTCPClient(providers_file_path=providers_file) as client:
            assert isinstance(client, MultiProviderUTCPClient)

    @pytest.mark.asyncio
    async def test_close_cleans_up_temp_file(self, sample_providers_config):
        """Test that close() cleans up temporary files."""
        client = MultiProviderUTCPClient(providers=sample_providers_config)
        temp_file = Path(client._config["providers_file_path"])
        
        assert temp_file.exists()
        await client.close()
        assert not temp_file.exists()


class TestCreateUtcpClient:
    """Test create_utcp_client convenience function."""

    @pytest.mark.asyncio
    async def test_create_utcp_client_basic(self, tmp_path):
        """Test basic client creation."""
        providers_file = tmp_path / "providers.json"
        providers_file.write_text("[]")
        
        client = await create_utcp_client(str(providers_file), load_env=False)
        
        assert isinstance(client, MultiProviderUTCPClient)
        assert client._config["providers_file_path"] == str(providers_file)

    @pytest.mark.asyncio
    async def test_create_utcp_client_with_env(self, tmp_path):
        """Test client creation with environment loading."""
        providers_file = tmp_path / "providers.json"
        providers_file.write_text("[]")
        
        client = await create_utcp_client(str(providers_file), load_env=True)
        
        assert isinstance(client, MultiProviderUTCPClient)
        assert "load_variables_from" in client._config
        assert client._config["load_variables_from"][0]["type"] == "dotenv"
