"""Tools adapter for converting UTCP tools to LangChain tools.

This module provides functionality to convert UTCP tools into LangChain-compatible
tools, handle tool execution, and manage tool conversion between the two formats.
"""

import json
from typing import Any, Dict, List, Optional

from langchain_core.tools import BaseTool, StructuredTool, ToolException
from pydantic import BaseModel, create_model
from utcp.utcp_client import UtcpClient
from utcp.data.tool import Tool as UTCPTool


def _convert_utcp_result(result: Any) -> str:
    """Convert UTCP tool result to LangChain tool result format.

    Args:
        result: The result from calling a UTCP tool.

    Returns:
        A string representation of the result.

    Raises:
        ToolException: If the tool call resulted in an error.
    """
    if isinstance(result, dict) and result.get("error"):
        raise ToolException(str(result["error"]))
    
    if isinstance(result, (dict, list)):
        return json.dumps(result, indent=2)
    
    return str(result)


def _create_pydantic_model_from_schema(
    schema: Dict[str, Any], 
    model_name: str = "ToolInput"
) -> type[BaseModel]:
    """Create a Pydantic model from a JSON schema.

    Args:
        schema: JSON schema dictionary
        model_name: Name for the generated model

    Returns:
        A Pydantic BaseModel class
    """
    # Handle the case where schema has properties directly (UTCP 1.0.0+ format)
    properties = schema.get("properties", {})
    required = schema.get("required", [])
    
    # If no properties but has type, create a simple model
    if not properties and schema.get("type") != "object":
        return create_model(model_name, value=(Any, ...))
    
    field_definitions = {}
    
    for field_name, field_schema in properties.items():
        field_type = _json_schema_to_python_type(field_schema)
        default_value = ... if field_name in required else None
        field_definitions[field_name] = (field_type, default_value)
    
    if not field_definitions:
        # Empty schema, create a model with no required fields
        field_definitions["_empty"] = (Optional[str], None)
    
    return create_model(model_name, **field_definitions)


def _json_schema_to_python_type(schema: Dict[str, Any]) -> type:
    """Convert JSON schema type to Python type.

    Args:
        schema: JSON schema for a field

    Returns:
        Python type corresponding to the schema
    """
    schema_type = schema.get("type", "string")
    
    # Handle None type (default to string)
    if schema_type is None:
        schema_type = "string"
    
    type_mapping = {
        "string": str,
        "integer": int,
        "number": float,
        "boolean": bool,
        "array": List[Any],
        "object": Dict[str, Any],
    }
    
    return type_mapping.get(schema_type, str)  # Default to str instead of Any


def convert_utcp_tool_to_langchain_tool(
    utcp_client: UtcpClient,
    tool: UTCPTool,
) -> BaseTool:
    """Convert a UTCP tool to a LangChain tool.

    Args:
        utcp_client: UTCP client instance for tool execution
        tool: UTCP tool to convert

    Returns:
        A LangChain tool
    """
    
    async def call_tool(**arguments: Dict[str, Any]) -> str:
        """Execute the UTCP tool with given arguments."""
        try:
            # Use the tool name as-is since UTCP client already namespaces it
            result = await utcp_client.call_tool(tool.name, arguments)
            return _convert_utcp_result(result)
        except Exception as e:
            raise ToolException(f"Error calling UTCP tool {tool.name}: {str(e)}") from e

    # Create Pydantic model from tool input schema
    schema_dict = tool.inputs.model_dump() if hasattr(tool.inputs, 'model_dump') else tool.inputs.__dict__
    args_schema = _create_pydantic_model_from_schema(
        schema_dict,
        f"{tool.name.replace('.', '_')}Input"
    )

    # Extract call template name from the tool call template
    call_template_name = tool.tool_call_template.name if hasattr(tool.tool_call_template, 'name') else "unknown"
    call_template_type = tool.tool_call_template.call_template_type if hasattr(tool.tool_call_template, 'call_template_type') else "unknown"
    
    return StructuredTool(
        name=tool.name,  # Use the full namespaced name from UTCP
        description=tool.description or f"UTCP tool: {tool.name}",
        args_schema=args_schema,
        coroutine=call_tool,
        metadata={
            "call_template": call_template_name,
            "call_template_type": call_template_type,
            "tags": tool.tags,
            "utcp_tool": True,
        },
    )


async def load_utcp_tools(
    utcp_client: UtcpClient,
    call_template_name: Optional[str] = None,
) -> List[BaseTool]:
    """Load all available UTCP tools and convert them to LangChain tools.

    Args:
        utcp_client: The UTCP client instance
        call_template_name: Optional call template name to filter tools

    Returns:
        List of LangChain tools
    """
    # Get all tools from the UTCP client using search with empty string and high limit
    all_tools = await utcp_client.search_tools("", limit=1000)  # Use high limit to get all tools
    
    # Filter by call template if specified
    if call_template_name:
        all_tools = [
            tool for tool in all_tools 
            if hasattr(tool.tool_call_template, 'name') and tool.tool_call_template.name == call_template_name
        ]
    
    # Convert each UTCP tool to a LangChain tool
    langchain_tools = []
    for utcp_tool in all_tools:
        try:
            langchain_tool = convert_utcp_tool_to_langchain_tool(utcp_client, utcp_tool)
            langchain_tools.append(langchain_tool)
        except Exception as e:
            # Log the error but continue with other tools
            print(f"Warning: Failed to convert tool {utcp_tool.name}: {e}")
    
    return langchain_tools


async def search_utcp_tools(
    utcp_client: UtcpClient,
    query: str,
    call_template_name: Optional[str] = None,
    max_results: Optional[int] = None,
) -> List[BaseTool]:
    """Search for UTCP tools and convert them to LangChain tools.

    Args:
        utcp_client: The UTCP client instance
        query: Search query string
        call_template_name: Optional call template name to filter tools
        max_results: Maximum number of results to return

    Returns:
        List of relevant LangChain tools
    """
    # Use UTCP's built-in search functionality
    try:
        # Use max_results if provided, otherwise use a high limit to get all matching tools
        limit = max_results if max_results is not None else 1000
        search_results = await utcp_client.search_tools(query, limit=limit)
    except Exception as e:
        print(f"Warning: UTCP search failed ({e}), falling back to manual search")
        # Fallback: get all tools and search manually
        all_tools = await utcp_client.search_tools("", limit=1000)
        query_lower = query.lower()
        
        search_results = []
        for tool in all_tools:
            # Search in name, description, and tags
            if (query_lower in tool.name.lower() or 
                query_lower in tool.description.lower() or
                any(query_lower in tag.lower() for tag in tool.tags)):
                search_results.append(tool)
        
        # Apply max_results limit if specified
        if max_results:
            search_results = search_results[:max_results]
    
    # Filter by call template if specified
    if call_template_name:
        search_results = [
            tool for tool in search_results 
            if hasattr(tool.tool_call_template, 'name') and tool.tool_call_template.name == call_template_name
        ]
    
    # Convert each UTCP tool to a LangChain tool
    langchain_tools = []
    for utcp_tool in search_results:
        try:
            langchain_tool = convert_utcp_tool_to_langchain_tool(utcp_client, utcp_tool)
            langchain_tools.append(langchain_tool)
        except Exception as e:
            # Log the error but continue with other tools
            print(f"Warning: Failed to convert tool {utcp_tool.name}: {e}")
    
    return langchain_tools
