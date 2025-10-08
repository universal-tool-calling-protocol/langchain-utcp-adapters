# LangChain UTCP Adapters

[![PyPI version](https://badge.fury.io/py/langchain-utcp-adapters.svg)](https://badge.fury.io/py/langchain-utcp-adapters)
[![Python Support](https://img.shields.io/pypi/pyversions/langchain-utcp-adapters.svg)](https://pypi.org/project/langchain-utcp-adapters/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A Python package that bridges Universal Tool Calling Protocol (UTCP) with LangChain, enabling seamless integration of external tools and APIs into LangChain applications.

## Features

- **Direct UTCP Integration**: Work directly with UTCP clients for maximum flexibility
- **Automatic Tool Conversion**: Convert UTCP tools to LangChain-compatible tools with proper schemas
- **Tool Discovery**: Search and filter tools by name, description, and tags
- **Dynamic Call Template Registration**: Register call templates programmatically at runtime
- **Async Support**: Full async/await implementation for optimal performance
- **Type Safety**: Complete type hints and Pydantic v2 compatibility
- **UTCP 1.0.1+ Compatible**: Works with the latest UTCP plugin architecture

## Installation

### Basic Installation

```bash
pip install langchain-utcp-adapters
```

### Required UTCP Plugins

The adapters require UTCP core and relevant protocol plugins:

```bash
# Core UTCP library (automatically installed)
pip install utcp>=1.0.0

# Protocol plugins (install as needed)
pip install utcp-http>=1.0.0    # For HTTP/REST APIs
pip install utcp-text>=1.0.0    # For text-based manuals
pip install utcp-mcp>=1.0.0     # For MCP integration
```

### Optional Dependencies

```bash
# Using pip
pip install langchain-utcp-adapters[examples]  # LangGraph + OpenAI
pip install langchain-utcp-adapters[bedrock]   # Amazon Bedrock
pip install langchain-utcp-adapters[all]       # Everything

# Using PDM
pdm install -G examples  # LangGraph + OpenAI examples
pdm install -G bedrock   # Amazon Bedrock integration
pdm install -G test      # Testing dependencies
pdm install -G dev       # Development tools
pdm install -G all       # Everything for development
```

## Quick Start

### Basic Usage

```python
import asyncio
from utcp.utcp_client import UtcpClient
from utcp.data.utcp_client_config import UtcpClientConfig
from utcp_http.http_call_template import HttpCallTemplate
from langchain_utcp_adapters import load_utcp_tools, search_utcp_tools

async def main():
    # Create UTCP client with call templates
    config = UtcpClientConfig(
        manual_call_templates=[
            HttpCallTemplate(
                name="petstore",
                call_template_type="http",
                url="https://petstore.swagger.io/v2/swagger.json",
                http_method="GET"
            )
        ]
    )
    client = await UtcpClient.create(config=config)
    
    # Load all tools and convert to LangChain format
    tools = await load_utcp_tools(client)
    print(f"Loaded {len(tools)} tools")
    
    # Search for specific tools
    pet_tools = await search_utcp_tools(client, "pet", max_results=5)
    print(f"Found {len(pet_tools)} pet-related tools")

asyncio.run(main())
```

### Using Configuration Files

```python
import asyncio
from utcp.utcp_client import UtcpClient
from langchain_utcp_adapters import load_utcp_tools

async def main():
    # Create client with config.json configuration
    client = await UtcpClient.create(config="config.json")
    
    # Load tools from all configured call templates
    tools = await load_utcp_tools(client)
    
    # Use tools with LangChain agents...

asyncio.run(main())
```

**config.json:**
```json
{
  "manual_call_templates": [
    {
      "name": "petstore",
      "call_template_type": "http",
      "url": "https://petstore.swagger.io/v2/swagger.json",
      "http_method": "GET"
    }
  ]
}
```

### LangGraph Integration

```python
import asyncio
from utcp.utcp_client import UtcpClient
from utcp.data.utcp_client_config import UtcpClientConfig
from utcp_http.http_call_template import HttpCallTemplate
from langchain_utcp_adapters import load_utcp_tools
from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI

async def main():
    # Set up UTCP client
    config = UtcpClientConfig(
        manual_call_templates=[
            HttpCallTemplate(
                name="petstore",
                call_template_type="http",
                url="https://petstore.swagger.io/v2/swagger.json",
                http_method="GET"
            )
        ]
    )
    client = await UtcpClient.create(config=config)
    
    # Load tools
    tools = await load_utcp_tools(client)
    
    # Create LangGraph agent
    llm = ChatOpenAI(model="gpt-4o-mini")
    agent = create_react_agent(llm, tools)
    
    # Use the agent
    response = await agent.ainvoke({
        "messages": [("user", "Find information about pets in the store")]
    })
    
    print(response["messages"][-1].content)

# Make sure to set OPENAI_API_KEY environment variable
asyncio.run(main())
```

### Amazon Bedrock Integration

```python
import asyncio
from utcp.utcp_client import UtcpClient
from utcp.data.utcp_client_config import UtcpClientConfig
from utcp_http.http_call_template import HttpCallTemplate
from langchain_utcp_adapters import load_utcp_tools, create_bedrock_tool_mapping
from langgraph.prebuilt import create_react_agent
from langchain_aws import ChatBedrock

async def main():
    # Set up UTCP client
    config = UtcpClientConfig(
        manual_call_templates=[
            HttpCallTemplate(
                name="openlibrary",
                call_template_type="http",
                http_method="GET",
                url="https://openlibrary.org/static/openapi.json",
                content_type="application/json"
            )
        ]
    )
    client = await UtcpClient.create(config=config)
    
    # Load tools and create Bedrock-compatible versions
    original_tools = await load_utcp_tools(client)
    bedrock_tools, name_mapping = create_bedrock_tool_mapping(original_tools)
    
    # Create Bedrock LLM
    llm = ChatBedrock(
        model_id="anthropic.claude-3-haiku-20240307-v1:0",
        region_name="us-east-1"
    )
    
    # Create LangGraph agent
    agent = create_react_agent(llm, bedrock_tools)
    
    # Use the agent
    response = await agent.ainvoke({
        "messages": [("user", "Search for books about Python programming")]
    })
    
    print(response["messages"][-1].content)

# Make sure AWS credentials are configured
asyncio.run(main())
```

## Authentication

UTCP supports various authentication methods:

```python
from utcp_http.http_call_template import HttpCallTemplate
from utcp.data.auth_implementations.api_key_auth import ApiKeyAuth
from utcp.data.auth_implementations.basic_auth import BasicAuth
from utcp.data.auth_implementations.oauth2_auth import OAuth2Auth

# API Key authentication
call_template = HttpCallTemplate(
    name="authenticated_api",
    call_template_type="http",
    url="https://api.example.com/openapi.json",
    http_method="GET",
    auth=ApiKeyAuth(
        api_key="${API_KEY}",  # Use environment variable
        var_name="X-API-Key",
        location="header"
    )
)

# OAuth2 authentication
call_template = HttpCallTemplate(
    name="oauth_api",
    call_template_type="http",
    url="https://api.example.com/openapi.json",
    http_method="GET",
    auth=OAuth2Auth(
        token_url="https://api.example.com/oauth/token",
        client_id="${CLIENT_ID}",
        client_secret="${CLIENT_SECRET}",
        scope="read write"
    )
)
```

## Supported Call Template Types

The adapters work with all UTCP call template types:

- **HTTP/HTTPS APIs** - Including automatic OpenAPI conversion
- **Server-Sent Events (SSE)** - For streaming data
- **Streamable HTTP** - For streaming HTTP responses
- **Text-based Manuals** - Direct UTCP manual definitions
- **Model Context Protocol (MCP)** - For interoperability

## API Reference

### Core Functions

```python
from langchain_utcp_adapters import (
    load_utcp_tools,
    search_utcp_tools,
    convert_utcp_tool_to_langchain_tool,
    # Bedrock-specific utilities
    create_bedrock_tool_mapping,
    format_tool_name_for_bedrock,
    BedrockCompatibleTool,
    restore_original_tool_names
)
```

#### `load_utcp_tools(utcp_client, call_template_name=None)`
Load all tools from UTCP client and convert to LangChain format.

**Parameters:**
- `utcp_client`: UTCP client instance
- `call_template_name`: Optional call template name to filter tools

**Returns:** List of LangChain BaseTool instances

#### `search_utcp_tools(utcp_client, query, call_template_name=None, max_results=None)`
Search for tools and convert to LangChain format.

**Parameters:**
- `utcp_client`: UTCP client instance  
- `query`: Search query string
- `call_template_name`: Optional call template name to filter
- `max_results`: Maximum number of results

**Returns:** List of relevant LangChain BaseTool instances

#### `convert_utcp_tool_to_langchain_tool(utcp_client, tool)`
Convert a single UTCP tool to LangChain format.

**Parameters:**
- `utcp_client`: UTCP client instance
- `tool`: UTCP Tool instance

**Returns:** LangChain BaseTool instance

### Bedrock Utilities

#### `create_bedrock_tool_mapping(tools)`
Create Bedrock-compatible tools with name mapping for tools that don't meet Bedrock's naming requirements.

**Parameters:**
- `tools`: List of LangChain BaseTool instances

**Returns:** Tuple containing:
- List of Bedrock-compatible tools
- Dictionary mapping Bedrock names to original names

## Examples

The `examples/` directory contains comprehensive examples:

- `basic_usage.py` - ✅ Basic tool loading and usage (31 tools from Petstore + OpenLibrary)
- `providers.py` - ✅ Real-world call template examples (11 OpenLibrary tools)
- `direct_usage.py` - ✅ Direct UTCP client usage
- `authentication.py` - ✅ Authentication methods demonstration
- `openapi.py` - ✅ OpenAPI specification integration
- `openai_langgraph.py` - 🔑 LangGraph integration (requires OPENAI_API_KEY)
- `openai_advanced.py` - 🔑 Advanced LangGraph integration (requires OPENAI_API_KEY)
- `bedrock_langgraph.py` - 🔐 Simple Amazon Bedrock integration (requires AWS credentials)
- `bedrock_advanced.py` - 🔐 Comprehensive Amazon Bedrock integration (requires AWS credentials)

**Legend:**
- ✅ Works immediately without external dependencies
- 🔑 Requires API keys (OpenAI)
- 🔐 Requires AWS credentials and Bedrock access

### Running Examples

```bash
# Basic examples (no external dependencies)
python examples/basic_usage.py
python examples/providers.py
python examples/authentication.py

# Examples requiring API keys
export OPENAI_API_KEY=your_key_here
python examples/openai_langgraph.py

# Bedrock examples (requires AWS credentials)
python examples/bedrock_langgraph.py
```

## Development

### Setup

```bash
# Clone the repository
git clone https://github.com/universal-tool-calling-protocol/langchain-utcp-adapters
cd langchain-utcp-adapters

# Using PDM (recommended)
pdm install -G all

# Or using pip
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e ".[all]"
```

### Running Tests

```bash
# With PDM
pdm run pytest

# With pip
pytest

# Run with coverage
pytest tests/ --cov=langchain_utcp_adapters
```

### Code Quality

```bash
# Format code
ruff format langchain_utcp_adapters/ tests/ examples/

# Lint code
ruff check langchain_utcp_adapters/ tests/ examples/

# Type checking
mypy langchain_utcp_adapters/
```

## Requirements

- Python 3.10+
- LangChain Core 0.3.36+
- UTCP 1.0.0+
- Pydantic 2.0+

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Related Projects

- [UTCP Python Client](https://github.com/universal-tool-calling-protocol/python-utcp) - The core UTCP implementation
- [LangChain](https://github.com/langchain-ai/langchain) - Framework for developing applications with LLMs
- [LangGraph](https://github.com/langchain-ai/langgraph) - Library for building stateful, multi-actor applications
