"""Tools adapter for converting UTCP tools to LangChain tools.

This module provides functionality to convert UTCP tools into LangChain-compatible
tools, handle tool execution, and manage tool conversion between the two formats.
"""

import json
import logging
from typing import Any, Dict, List, Optional

from langchain_core.tools import BaseTool, StructuredTool, ToolException
from pydantic import BaseModel, create_model, ConfigDict
from utcp.utcp_client import UtcpClient
from utcp.data.tool import Tool as UTCPTool

# Configure logger for this module
logger = logging.getLogger(__name__)


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
        schema: JSON schema dictionary (from UTCP JsonSchema object)
        model_name: Name for the generated model

    Returns:
        A Pydantic BaseModel class
    """
    # Handle the case where schema has properties directly (UTCP 1.0.1+ format)
    properties = schema.get("properties", {})
    required = schema.get("required", [])
    
    # Handle case where the schema itself might be empty or malformed
    if not isinstance(properties, dict):
        properties = {}
    
    if not isinstance(required, list):
        required = []
    
    # If no properties and schema type is not object, create a simple value model
    if not properties and schema.get("type") not in [None, "object"]:
        schema_type = schema.get("type", "string")
        field_type = _json_schema_to_python_type({"type": schema_type})
        return create_model(model_name, value=(field_type, ...))
    
    field_definitions = {}
    
    for field_name, field_schema in properties.items():
        if not isinstance(field_schema, dict):
            # Skip malformed field schemas
            continue
            
        field_type = _json_schema_to_python_type(field_schema)
        
        # Determine if field is required and set appropriate default
        if field_name in required:
            default_value = ...  # Required field
        else:
            # Optional field - use None as default, but wrap type in Optional
            field_type = Optional[field_type]
            default_value = None
        
        field_definitions[field_name] = (field_type, default_value)
    
    # If no valid field definitions, create a model that accepts any keyword arguments
    if not field_definitions:
        # Create a flexible model that can accept any arguments
        # This handles tools with no defined input schema
        class FlexibleModel(BaseModel):
            model_config = ConfigDict(extra="allow")  # Allow additional fields
        
        # Dynamically set the model name
        FlexibleModel.__name__ = model_name
        return FlexibleModel
    
    return create_model(model_name, **field_definitions)


def _json_schema_to_python_type(schema: Dict[str, Any]) -> type:
    """Convert JSON schema type to Python type.

    Args:
        schema: JSON schema for a field

    Returns:
        Python type corresponding to the schema
    """
    if not isinstance(schema, dict):
        return str  # Fallback for malformed schemas
    
    schema_type = schema.get("type", "string")
    
    # Handle None type (default to string)
    if schema_type is None:
        schema_type = "string"
    
    # Handle array types with items specification
    if schema_type == "array":
        items_schema = schema.get("items", {"type": "string"})
        if isinstance(items_schema, dict):
            item_type = _json_schema_to_python_type(items_schema)
            return List[item_type]
        else:
            return List[Any]  # Fallback for complex items schemas
    
    # Handle union types (anyOf, oneOf)
    if "anyOf" in schema or "oneOf" in schema:
        # For simplicity, use Any for union types
        # In a more sophisticated implementation, we could create Union types
        return Any
    
    type_mapping = {
        "string": str,
        "integer": int,
        "number": float,
        "boolean": bool,
        "array": List[Any],  # Fallback if not handled above
        "object": Dict[str, Any],
        "null": type(None),
    }
    
    return type_mapping.get(schema_type, str)  # Default to str for unknown types


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
            # Tool names from UTCP are already properly namespaced as 'manual_name.tool_name'
            # The UTCP client handles the namespacing during tool registration
            result = await utcp_client.call_tool(tool.name, arguments)
            return _convert_utcp_result(result)
        except Exception as e:
            raise ToolException(f"Error calling UTCP tool {tool.name}: {str(e)}") from e

    # Create Pydantic model from tool input schema
    # Handle JsonSchema object from UTCP 1.0.1+
    if hasattr(tool.inputs, 'model_dump'):
        # JsonSchema is a Pydantic model, use model_dump()
        schema_dict = tool.inputs.model_dump(by_alias=True, exclude_none=True)
    elif hasattr(tool.inputs, '__dict__'):
        # Fallback for older formats or plain objects
        schema_dict = tool.inputs.__dict__
    elif isinstance(tool.inputs, dict):
        # Already a dictionary
        schema_dict = tool.inputs
    else:
        # Unknown format, create empty schema
        schema_dict = {"type": "object", "properties": {}}
    
    args_schema = _create_pydantic_model_from_schema(
        schema_dict,
        f"{tool.name.replace('.', '_')}Input"
    )

    # Extract manual call template name from the namespaced tool name
    # UTCP tools are namespaced as 'manual_name.tool_name'
    manual_name = tool.name.split('.')[0] if '.' in tool.name else "unknown"
    
    # Get call template type from the tool's call template with proper validation
    call_template_type = "unknown"
    if (hasattr(tool, 'tool_call_template') and 
        tool.tool_call_template is not None and 
        hasattr(tool.tool_call_template, 'call_template_type')):
        call_template_type = tool.tool_call_template.call_template_type
    
    return StructuredTool(
        name=tool.name,  # Use the full namespaced name from UTCP (manual_name.tool_name)
        description=tool.description or f"UTCP tool: {tool.name}",
        args_schema=args_schema,
        coroutine=call_tool,
        metadata={
            "manual_name": manual_name,  # The manual/call template name
            "call_template": manual_name,  # For backward compatibility
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
    try:
        # Get all tools from the UTCP client using search with empty string and high limit
        all_tools = await utcp_client.search_tools("", limit=1000)
    except Exception as e:
        logger.error("Failed to load tools from UTCP client: %s", e)
        return []
    
    # Filter by call template if specified
    if call_template_name:
        # Improved filtering with better null checks
        filtered_tools = []
        for tool in all_tools:
            if (hasattr(tool, 'tool_call_template') and 
                tool.tool_call_template is not None and
                hasattr(tool.tool_call_template, 'name')):
                
                # Extract manual name from tool name for comparison
                tool_manual_name = tool.name.split('.')[0] if '.' in tool.name else "unknown"
                
                if tool_manual_name == call_template_name:
                    filtered_tools.append(tool)
        
        all_tools = filtered_tools
    
    # Convert each UTCP tool to a LangChain tool
    langchain_tools = []
    for utcp_tool in all_tools:
        try:
            langchain_tool = convert_utcp_tool_to_langchain_tool(utcp_client, utcp_tool)
            langchain_tools.append(langchain_tool)
        except Exception as e:
            # Log the error but continue with other tools
            logger.warning("Failed to convert tool %s: %s", utcp_tool.name, e)
    
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
    search_results = []
    
    # Try UTCP's built-in search functionality first
    try:
        limit = max_results if max_results is not None else 1000
        search_results = await utcp_client.search_tools(query, limit=limit)
    except Exception as e:
        logger.warning("UTCP search failed (%s), attempting fallback methods", e)
        
        # Fallback 1: Try to get all tools with empty query (sometimes works when specific queries fail)
        try:
            logger.info("Trying to get all tools with empty query...")
            all_tools = await utcp_client.search_tools("", limit=1000)
            
            # Manually filter the results
            query_lower = query.lower()
            search_results = []
            
            for tool in all_tools:
                # Search in name, description, and tags
                if (query_lower in tool.name.lower() or 
                    query_lower in tool.description.lower() or
                    any(query_lower in tag.lower() for tag in tool.tags)):
                    search_results.append(tool)
            
            logger.info("Fallback search found %d matching tools", len(search_results))
            
        except Exception as e2:
            logger.warning("Fallback search also failed (%s)", e2)
            
            # Fallback 2: Try to use load_utcp_tools and filter manually
            try:
                logger.info("Trying to load all tools via load_utcp_tools...")
                # Use the load function which might have different error handling
                all_langchain_tools = await load_utcp_tools(utcp_client, call_template_name)
                
                # Filter the LangChain tools by query
                query_lower = query.lower()
                filtered_tools = []
                
                for tool in all_langchain_tools:
                    if (query_lower in tool.name.lower() or 
                        query_lower in tool.description.lower() or
                        any(query_lower in tag.lower() for tag in tool.metadata.get("tags", []))):
                        filtered_tools.append(tool)
                
                # Apply max_results limit if specified
                if max_results:
                    filtered_tools = filtered_tools[:max_results]
                
                logger.info("Final fallback found %d matching tools", len(filtered_tools))
                return filtered_tools
                
            except Exception as e3:
                logger.error("All fallback methods failed (%s). Returning empty list.", e3)
                return []
    
    # Apply max_results limit if specified (for successful search)
    if max_results and len(search_results) > max_results:
        search_results = search_results[:max_results]
    
    # Filter by call template if specified
    if call_template_name:
        search_results = [
            tool for tool in search_results 
            if hasattr(tool, 'tool_call_template') and 
               tool.tool_call_template is not None and
               hasattr(tool.tool_call_template, 'name') and 
               tool.tool_call_template.name == call_template_name
        ]
    
    # Convert each UTCP tool to a LangChain tool
    langchain_tools = []
    for utcp_tool in search_results:
        try:
            langchain_tool = convert_utcp_tool_to_langchain_tool(utcp_client, utcp_tool)
            langchain_tools.append(langchain_tool)
        except Exception as e:
            # Log the error but continue with other tools
            logger.warning("Failed to convert tool %s: %s", utcp_tool.name, e)
    
    return langchain_tools
