"""Tests for UTCP to LangChain tool conversion."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from langchain_utcp_adapters.tools import (
    convert_utcp_tool_to_langchain_tool,
    load_utcp_tools,
    search_utcp_tools,
    _convert_utcp_result,
    _create_pydantic_model_from_schema,
    _json_schema_to_python_type,
)
from utcp.data.tool import Tool as UTCPTool, JsonSchema
from utcp_http.http_call_template import HttpCallTemplate


class TestToolConversion:
    """Test UTCP to LangChain tool conversion."""

    def test_convert_utcp_result_string(self):
        """Test converting string result."""
        result = "Hello, world!"
        converted = _convert_utcp_result(result)
        assert converted == "Hello, world!"

    def test_convert_utcp_result_dict(self):
        """Test converting dictionary result."""
        result = {"message": "success", "data": [1, 2, 3]}
        converted = _convert_utcp_result(result)
        # Check that the JSON contains the expected content (formatting may vary)
        assert '"message"' in converted and '"success"' in converted
        assert '"data"' in converted and '1' in converted and '2' in converted and '3' in converted

    def test_convert_utcp_result_error(self):
        """Test converting error result."""
        result = {"error": "Something went wrong"}
        with pytest.raises(Exception) as exc_info:
            _convert_utcp_result(result)
        assert "Something went wrong" in str(exc_info.value)

    def test_json_schema_to_python_type(self):
        """Test JSON schema to Python type conversion."""
        assert _json_schema_to_python_type({"type": "string"}) == str
        assert _json_schema_to_python_type({"type": "integer"}) == int
        assert _json_schema_to_python_type({"type": "number"}) == float
        assert _json_schema_to_python_type({"type": "boolean"}) == bool

    def test_create_pydantic_model_from_schema(self):
        """Test creating Pydantic model from JSON schema."""
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"},
                "email": {"type": "string"}
            },
            "required": ["name", "age"]
        }
        
        model_class = _create_pydantic_model_from_schema(schema, "TestModel")
        
        # Test that required fields are properly set
        model_instance = model_class(name="John", age=30)
        assert model_instance.name == "John"
        assert model_instance.age == 30
        assert model_instance.email is None

    def test_create_pydantic_model_from_empty_schema(self):
        """Test creating Pydantic model from empty schema."""
        empty_schema = {"type": "object", "properties": {}}
        
        model_class = _create_pydantic_model_from_schema(empty_schema, "EmptyModel")
        
        # Test that the model can be created and accepts additional fields
        model_instance = model_class()
        assert model_instance is not None
        
        # Test that it can accept arbitrary keyword arguments
        model_instance_with_data = model_class(arbitrary_field="test")
        assert model_instance_with_data.arbitrary_field == "test"

    def test_create_pydantic_model_from_malformed_schema(self):
        """Test creating Pydantic model from malformed schema."""
        malformed_schema = {"properties": None, "required": "not_a_list"}
        
        model_class = _create_pydantic_model_from_schema(malformed_schema, "MalformedModel")
        
        # Should create a flexible model that doesn't crash
        model_instance = model_class()
        assert model_instance is not None

    def test_tool_name_without_namespace(self):
        """Test tool name handling for tools without namespace (edge case)."""
        from utcp_http.http_call_template import HttpCallTemplate
        
        provider = HttpCallTemplate(
            name="test_provider",
            call_template_type="http",
            url="http://example.com/api",
            http_method="POST"
        )
        
        # Create a tool without namespace (edge case)
        utcp_tool = UTCPTool(
            name="standalone_tool",  # No namespace
            description="A standalone tool",
            inputs=JsonSchema(type="object", properties={}),
            outputs=JsonSchema(type="object", properties={}),
            tags=[],
            tool_call_template=provider
        )
        
        mock_client = AsyncMock()
        langchain_tool = convert_utcp_tool_to_langchain_tool(mock_client, utcp_tool)
        
        # Should handle gracefully
        assert langchain_tool.name == "standalone_tool"
        assert langchain_tool.metadata["manual_name"] == "unknown"  # Fallback for no namespace
        assert langchain_tool.metadata["call_template"] == "unknown"  # Fallback for backward compatibility

    @pytest.mark.asyncio
    async def test_convert_utcp_tool_to_langchain_tool(self):
        """Test converting UTCP tool to LangChain tool."""
        # Create mock UTCP client
        mock_client = AsyncMock()
        mock_client.call_tool.return_value = {"result": "success"}
        
        # Create UTCP tool
        provider = HttpCallTemplate(
            name="test_provider",
            call_template_type="http",
            url="http://example.com/api",
            http_method="POST"
        )
        
        utcp_tool = UTCPTool(
            name="test_provider.test_tool",  # Use namespaced name as UTCP would provide
            description="A test tool",
            inputs=JsonSchema(
                type="object",
                properties={
                    "input_text": JsonSchema(type="string")
                },
                required=["input_text"]
            ),
            outputs=JsonSchema(
                type="object",
                properties={
                    "output_text": JsonSchema(type="string")
                }
            ),
            tags=["test"],
            tool_call_template=provider
        )
        
        # Convert to LangChain tool
        langchain_tool = convert_utcp_tool_to_langchain_tool(mock_client, utcp_tool)
        
        # Test tool properties
        assert langchain_tool.name == "test_provider.test_tool"  # UTCP provides namespaced names
        assert langchain_tool.description == "A test tool"
        assert langchain_tool.metadata["call_template"] == "test_provider"  # Extracted from tool name
        assert langchain_tool.metadata["manual_name"] == "test_provider"  # New explicit field
        assert langchain_tool.metadata["call_template_type"] == "http"
        assert langchain_tool.metadata["utcp_tool"] is True
        
        # Test tool execution
        result = await langchain_tool.ainvoke({"input_text": "hello"})
        assert "success" in result
        mock_client.call_tool.assert_called_once_with(
            "test_provider.test_tool",  # UTCP uses the namespaced tool name
            {"input_text": "hello"}
        )

    @pytest.mark.asyncio
    async def test_load_utcp_tools(self):
        """Test loading UTCP tools."""
        # Create mock UTCP client
        mock_client = AsyncMock()
        
        # Create mock call template
        provider = HttpCallTemplate(name="test_provider", call_template_type="http", url="http://example.com")
        
        utcp_tool = UTCPTool(
            name="test_provider.test_tool",  # Use namespaced name
            description="A test tool",
            inputs=JsonSchema(type="object", properties={}),
            outputs=JsonSchema(type="object", properties={}),
            tags=[],
            tool_call_template=provider
        )
        
        # Mock the search_tools method that load_utcp_tools actually uses
        mock_client.search_tools.return_value = [utcp_tool]
        
        # Load tools
        langchain_tools = await load_utcp_tools(mock_client)
        
        # Verify results
        assert len(langchain_tools) == 1
        assert langchain_tools[0].name == "test_provider.test_tool"
        assert langchain_tools[0].metadata["utcp_tool"] is True
        
        # Verify search_tools was called with empty string and high limit
        mock_client.search_tools.assert_called_once_with("", limit=1000)

    @pytest.mark.asyncio
    async def test_load_utcp_tools_with_provider_filter(self):
        """Test loading UTCP tools with call template filter."""
        # Create mock UTCP client
        mock_client = AsyncMock()
        
        # Create mock call templates
        provider1 = HttpCallTemplate(name="provider1", call_template_type="http", url="http://example1.com")
        provider2 = HttpCallTemplate(name="provider2", call_template_type="http", url="http://example2.com")
        
        tool1 = UTCPTool(
            name="provider1.tool1",  # Use namespaced name
            description="Tool 1",
            inputs=JsonSchema(type="object", properties={}),
            outputs=JsonSchema(type="object", properties={}),
            tags=[],
            tool_call_template=provider1
        )
        
        tool2 = UTCPTool(
            name="provider2.tool2",  # Use namespaced name
            description="Tool 2",
            inputs=JsonSchema(type="object", properties={}),
            outputs=JsonSchema(type="object", properties={}),
            tags=[],
            tool_call_template=provider2
        )
        
        # Mock search_tools to return both tools
        mock_client.search_tools.return_value = [tool1, tool2]
        
        # Load tools with call template filter
        langchain_tools = await load_utcp_tools(mock_client, call_template_name="provider1")
        
        # Verify only provider1 tools are returned
        assert len(langchain_tools) == 1
        assert langchain_tools[0].name == "provider1.tool1"

    @pytest.mark.asyncio
    async def test_search_utcp_tools(self):
        """Test searching UTCP tools."""
        # Create mock UTCP client
        mock_client = AsyncMock()
        
        provider = HttpCallTemplate(name="test_provider", call_template_type="http", url="http://example.com")
        utcp_tool = UTCPTool(
            name="test_provider.search_tool",  # Use namespaced name
            description="A searchable tool",
            inputs=JsonSchema(type="object", properties={}),
            outputs=JsonSchema(type="object", properties={}),
            tags=[],
            tool_call_template=provider
        )
        
        mock_client.search_tools.return_value = [utcp_tool]
        
        # Search tools
        langchain_tools = await search_utcp_tools(mock_client, "search query")
        
        # Verify results
        assert len(langchain_tools) == 1
        assert langchain_tools[0].name == "test_provider.search_tool"
        mock_client.search_tools.assert_called_once_with("search query", limit=1000)

    @pytest.mark.asyncio
    async def test_search_utcp_tools_with_fallback(self):
        """Test search tools fallback logic when primary search fails."""
        # Create mock UTCP client
        mock_client = AsyncMock()
        
        provider = HttpCallTemplate(name="test_provider", call_template_type="http", url="http://example.com")
        
        utcp_tool = UTCPTool(
            name="test_provider.fallback_tool",
            description="A tool for fallback testing",
            inputs=JsonSchema(type="object", properties={}),
            outputs=JsonSchema(type="object", properties={}),
            tags=["fallback"],
            tool_call_template=provider
        )
        
        # Mock the primary search to fail, but empty search to succeed
        def mock_search_side_effect(query, limit):
            if query == "fallback":
                raise Exception("Primary search failed")
            elif query == "":
                return [utcp_tool]  # Empty search succeeds
            else:
                return []
        
        mock_client.search_tools.side_effect = mock_search_side_effect
        
        # Search tools - should trigger fallback
        langchain_tools = await search_utcp_tools(mock_client, "fallback")
        
        # Verify fallback worked
        assert len(langchain_tools) == 1
        assert langchain_tools[0].name == "test_provider.fallback_tool"
        
        # Verify both calls were made (primary + fallback)
        assert mock_client.search_tools.call_count == 2
        mock_client.search_tools.assert_any_call("fallback", limit=1000)  # Primary call
        mock_client.search_tools.assert_any_call("", limit=1000)  # Fallback call

    @pytest.mark.asyncio
    async def test_search_utcp_tools_complete_failure(self):
        """Test search tools when all methods fail."""
        # Create mock UTCP client that always fails
        mock_client = AsyncMock()
        mock_client.search_tools.side_effect = Exception("All search methods failed")
        
        # Mock load_utcp_tools to also fail
        with patch('langchain_utcp_adapters.tools.load_utcp_tools') as mock_load:
            mock_load.side_effect = Exception("Load also failed")
            
            # Search tools - should return empty list
            langchain_tools = await search_utcp_tools(mock_client, "test query")
            
            # Verify graceful failure
            assert len(langchain_tools) == 0
