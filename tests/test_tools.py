"""Tests for UTCP to LangChain tool conversion."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from langchain_utcp_adapters.tools import (
    convert_utcp_tool_to_langchain_tool,
    load_utcp_tools,
    search_utcp_tools,
    _convert_utcp_result,
    _create_pydantic_model_from_schema,
    _json_schema_to_python_type,
)
from utcp.data.tool import Tool as UTCPTool
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
            name="test_tool",
            description="A test tool",
            inputs={
                "type": "object",
                "properties": {
                    "input_text": {"type": "string"}
                },
                "required": ["input_text"]
            },
            outputs={
                "type": "object",
                "properties": {
                    "output_text": {"type": "string"}
                }
            },
            tags=["test"],
            tool_call_template=provider
        )
        
        # Convert to LangChain tool
        langchain_tool = convert_utcp_tool_to_langchain_tool(mock_client, utcp_tool)
        
        # Test tool properties
        assert langchain_tool.name == "test_tool"  # UTCP provides the name as-is
        assert langchain_tool.description == "A test tool"
        assert langchain_tool.metadata["call_template"] == "test_provider"
        assert langchain_tool.metadata["call_template_type"] == "http"
        assert langchain_tool.metadata["utcp_tool"] is True
        
        # Test tool execution
        result = await langchain_tool.ainvoke({"input_text": "hello"})
        assert "success" in result
        mock_client.call_tool.assert_called_once_with(
            "test_tool",  # UTCP uses the tool name as-is
            {"input_text": "hello"}
        )

    @pytest.mark.asyncio
    async def test_load_utcp_tools(self):
        """Test loading UTCP tools."""
        # Create mock UTCP client
        mock_client = AsyncMock()
        
        # Create mock tool repository
        mock_tool_repo = AsyncMock()
        provider = HttpCallTemplate(name="test_provider", call_template_type="http", url="http://example.com")
        
        utcp_tool = UTCPTool(
            name="test_tool",
            description="A test tool",
            inputs={"type": "object", "properties": {}},
            outputs={"type": "object", "properties": {}},
            tags=[],
            tool_call_template=provider
        )
        
        mock_tool_repo.get_tools.return_value = [utcp_tool]
        mock_client.tool_repository = mock_tool_repo
        
        # Load tools
        langchain_tools = await load_utcp_tools(mock_client)
        
        # Verify results
        assert len(langchain_tools) == 1
        assert langchain_tools[0].name == "test_tool"  # UTCP provides the name as-is
        assert langchain_tools[0].metadata["utcp_tool"] is True

    @pytest.mark.asyncio
    async def test_load_utcp_tools_with_provider_filter(self):
        """Test loading UTCP tools with provider filter."""
        # Create mock UTCP client
        mock_client = AsyncMock()
        
        # Create mock tool repository
        mock_tool_repo = AsyncMock()
        
        provider1 = HttpCallTemplate(name="provider1", call_template_type="http", url="http://example1.com")
        provider2 = HttpCallTemplate(name="provider2", call_template_type="http", url="http://example2.com")
        
        tool1 = UTCPTool(
            name="tool1",
            description="Tool 1",
            inputs={"type": "object", "properties": {}},
            outputs={"type": "object", "properties": {}},
            tags=[],
            tool_call_template=provider1
        )
        
        tool2 = UTCPTool(
            name="tool2", 
            description="Tool 2",
            inputs={"type": "object", "properties": {}},
            outputs={"type": "object", "properties": {}},
            tags=[],
            tool_call_template=provider2
        )
        
        mock_tool_repo.get_tools.return_value = [tool1, tool2]
        mock_client.tool_repository = mock_tool_repo
        
        # Load tools with provider filter
        langchain_tools = await load_utcp_tools(mock_client, provider_name="provider1")
        
        # Verify only provider1 tools are returned
        assert len(langchain_tools) == 1
        assert langchain_tools[0].name == "tool1"  # UTCP provides the name as-is

    @pytest.mark.asyncio
    async def test_search_utcp_tools(self):
        """Test searching UTCP tools."""
        # Create mock UTCP client
        mock_client = AsyncMock()
        
        provider = HttpCallTemplate(name="test_provider", call_template_type="http", url="http://example.com")
        utcp_tool = UTCPTool(
            name="search_tool",
            description="A searchable tool",
            inputs={"type": "object", "properties": {}},
            outputs={"type": "object", "properties": {}},
            tags=[],
            tool_call_template=provider
        )
        
        mock_client.search_tools.return_value = [utcp_tool]
        
        # Search tools
        langchain_tools = await search_utcp_tools(mock_client, "search query")
        
        # Verify results
        assert len(langchain_tools) == 1
        assert langchain_tools[0].name == "search_tool"  # UTCP provides the name as-is
        mock_client.search_tools.assert_called_once_with("search query")
