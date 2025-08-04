"""LangChain UTCP Adapters.

This package provides adapters to make Universal Tool Calling Protocol (UTCP) tools
compatible with LangChain and LangGraph.
"""

from langchain_utcp_adapters.tools import (
    convert_utcp_tool_to_langchain_tool,
    load_utcp_tools,
    search_utcp_tools,
)

from langchain_utcp_adapters.bedrock_utils import (
    format_tool_name_for_bedrock,
    create_bedrock_tool_mapping,
    BedrockCompatibleTool,
    restore_original_tool_names,
)

__version__ = "0.1.0"

__all__ = [
    # Core tool conversion functions
    "convert_utcp_tool_to_langchain_tool", 
    "load_utcp_tools",
    "search_utcp_tools",
    # Bedrock compatibility utilities
    "format_tool_name_for_bedrock",
    "create_bedrock_tool_mapping",
    "BedrockCompatibleTool",
    "restore_original_tool_names",
]
