"""
Bedrock-specific utilities for LangChain UTCP Adapters.

This module provides utilities for formatting UTCP tools to work with Amazon Bedrock's
strict tool naming requirements.
"""

import uuid
from typing import Dict, List, Tuple, Any, Optional
from langchain_core.tools import BaseTool
from langchain_core.runnables import RunnableConfig


def format_tool_name_for_bedrock(tool_name: str) -> str:
    """
    Format a tool name to meet Bedrock's requirements.
    
    Bedrock requires tool names to:
    - Be 64 characters or less
    - Match pattern ^[a-zA-Z0-9_-]{1,64}$
    
    Args:
        tool_name: Original tool name
        
    Returns:
        Formatted tool name that meets Bedrock requirements
    """
    # Replace periods with underscores (common in UTCP tool names)
    bedrock_name = tool_name.replace(".", "_")
    
    # Remove any other invalid characters and replace with underscores
    valid_chars = []
    for char in bedrock_name:
        if char.isalnum() or char in ['_', '-']:
            valid_chars.append(char)
        else:
            valid_chars.append('_')
    
    bedrock_name = ''.join(valid_chars)
    
    # Truncate if longer than 64 characters
    if len(bedrock_name) > 64:
        # Use first 55 chars + underscore + 8-char UUID
        short_uuid = str(uuid.uuid4()).replace('-', '')[:8]
        bedrock_name = f"{bedrock_name[:55]}_{short_uuid}"
    
    return bedrock_name


def create_bedrock_tool_mapping(tools: List[BaseTool]) -> Tuple[List[BaseTool], Dict[str, str]]:
    """
    Create Bedrock-compatible tools with name mapping.
    
    Args:
        tools: List of LangChain tools with potentially incompatible names
        
    Returns:
        Tuple containing:
        - List of tools with Bedrock-compatible names
        - Mapping from Bedrock names to original names
    """
    bedrock_tools = []
    name_mapping = {}
    
    for tool in tools:
        original_name = tool.name
        bedrock_name = format_tool_name_for_bedrock(original_name)
        
        # Store the mapping
        name_mapping[bedrock_name] = original_name
        
        if bedrock_name == original_name:
            # Name is already compatible, use original tool
            bedrock_tools.append(tool)
        else:
            # Create a wrapper tool with the Bedrock-compatible name
            bedrock_tool = BedrockCompatibleTool(
                original_tool=tool,
                bedrock_name=bedrock_name
            )
            bedrock_tools.append(bedrock_tool)
    
    return bedrock_tools, name_mapping


class BedrockCompatibleTool(BaseTool):
    """
    A wrapper tool that provides Bedrock-compatible naming while preserving
    all original tool functionality.
    """
    
    def __init__(self, original_tool: BaseTool, bedrock_name: str):
        """
        Initialize the Bedrock-compatible tool wrapper.
        
        Args:
            original_tool: The original LangChain tool
            bedrock_name: The Bedrock-compatible name
        """
        # Create metadata that includes the original name
        metadata = dict(original_tool.metadata) if original_tool.metadata else {}
        metadata['original_name'] = original_tool.name
        
        # Initialize the parent class with Bedrock-compatible name
        super().__init__(
            name=bedrock_name,
            description=original_tool.description,
            args_schema=original_tool.args_schema,
            return_direct=getattr(original_tool, 'return_direct', False),
            verbose=getattr(original_tool, 'verbose', False),
            callbacks=getattr(original_tool, 'callbacks', None),
            callback_manager=getattr(original_tool, 'callback_manager', None),
            tags=getattr(original_tool, 'tags', None),
            metadata=metadata,
        )
        
        # Store the original tool using object.__setattr__ to bypass Pydantic validation
        object.__setattr__(self, '_original_tool', original_tool)
    
    def _run(self, *args, **kwargs) -> Any:
        """Run the original tool synchronously (required abstract method)."""
        # This method is required by BaseTool but we prefer to use invoke
        return self._original_tool._run(*args, **kwargs)
    
    async def _arun(self, *args, **kwargs) -> Any:
        """Run the original tool asynchronously (required abstract method)."""
        # This method is required by BaseTool but we prefer to use ainvoke
        return await self._original_tool._arun(*args, **kwargs)
    
    def invoke(self, input: Dict[str, Any], config: Optional[RunnableConfig] = None, **kwargs) -> Any:
        """Invoke the original tool synchronously."""
        return self._original_tool.invoke(input, config, **kwargs)
    
    async def ainvoke(self, input: Dict[str, Any], config: Optional[RunnableConfig] = None, **kwargs) -> Any:
        """Invoke the original tool asynchronously."""
        return await self._original_tool.ainvoke(input, config, **kwargs)
    
    @property
    def original_name(self) -> str:
        """Get the original tool name."""
        return self._original_tool.name
    
    @property
    def original_tool(self) -> BaseTool:
        """Get the original tool."""
        return self._original_tool


def restore_original_tool_names(tool_calls: List[Dict], name_mapping: Dict[str, str]) -> List[Dict]:
    """
    Restore original tool names in tool calls from Bedrock.
    
    Args:
        tool_calls: List of tool calls with Bedrock names
        name_mapping: Mapping from Bedrock names to original names
        
    Returns:
        List of tool calls with original names restored
    """
    restored_calls = []
    
    for call in tool_calls:
        restored_call = call.copy()
        
        # Restore the original name if it exists in mapping
        if 'name' in restored_call and restored_call['name'] in name_mapping:
            restored_call['name'] = name_mapping[restored_call['name']]
        
        restored_calls.append(restored_call)
    
    return restored_calls
