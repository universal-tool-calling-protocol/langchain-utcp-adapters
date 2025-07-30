# LangChain UTCP Adapters

A Python package that bridges Universal Tool Calling Protocol (UTCP) providers with LangChain, enabling seamless integration of external tools and APIs into LangChain applications.

## Features

- **Direct UTCP Integration**: Work directly with UTCP clients for maximum flexibility
- **Automatic Tool Conversion**: Convert UTCP tools to LangChain-compatible tools with proper schemas
- **Tool Discovery**: Search and filter tools by name, description, and tags
- **Dynamic Provider Registration**: Register providers programmatically at runtime
- **Async Support**: Full async/await implementation for optimal performance
- **Type Safety**: Complete type hints and Pydantic v2 compatibility

## Installation

```bash
pip install langchain-utcp-adapters
```

### Optional Dependencies

```bash
# For examples with OpenAI and LangGraph
pip install langchain-utcp-adapters[examples]

# For Amazon Bedrock integration
pip install langchain-utcp-adapters[bedrock]

# Install everything
pip install langchain-utcp-adapters[all]
```

## Quick Start

### Basic Usage

```python
import asyncio
from utcp.client.utcp_client import UtcpClient
from utcp.client.utcp_client_config import UtcpClientConfig
from utcp.shared.provider import HttpProvider
from langchain_utcp_adapters import load_utcp_tools, search_utcp_tools

async def main():
    # Create UTCP client
    config = UtcpClientConfig()
    client = await UtcpClient.create(config=config)
    
    # Register providers using Provider objects
    provider = HttpProvider(
        name="petstore",
        provider_type="http",
        url="https://petstore.swagger.io/v2/swagger.json",
        http_method="GET"
    )
    await client.register_tool_provider(provider)
    
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
from utcp.client.utcp_client import UtcpClient
from utcp.client.utcp_client_config import UtcpClientConfig
from langchain_utcp_adapters import load_utcp_tools

async def main():
    # Create client with providers.json configuration
    config = UtcpClientConfig(providers_file_path="providers.json")
    client = await UtcpClient.create(config=config)
    
    # Load tools from all configured providers
    tools = await load_utcp_tools(client)
    
    # Use tools with LangChain agents...

asyncio.run(main())
```

**providers.json:**
```json
[
  {
    "name": "petstore",
    "provider_type": "http",
    "url": "https://petstore.swagger.io/v2/swagger.json",
    "http_method": "GET"
  }
]
```

### LangGraph Integration

```python
import asyncio
import os
from utcp.client.utcp_client import UtcpClient
from utcp.client.utcp_client_config import UtcpClientConfig
from utcp.shared.provider import HttpProvider
from langchain_utcp_adapters import load_utcp_tools
from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI

async def main():
    # Set up UTCP client
    config = UtcpClientConfig()
    client = await UtcpClient.create(config=config)
    
    # Register provider
    provider = HttpProvider(
        name="petstore",
        provider_type="http",
        url="https://petstore.swagger.io/v2/swagger.json",
        http_method="GET"
    )
    await client.register_tool_provider(provider)
    
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

## API Reference

### Core Functions

#### `load_utcp_tools(utcp_client, provider_name=None)`

Load all available UTCP tools and convert them to LangChain tools.

**Parameters:**
- `utcp_client` (UtcpClient): The UTCP client instance
- `provider_name` (str, optional): Filter tools by provider name

**Returns:**
- `List[BaseTool]`: List of LangChain-compatible tools

#### `search_utcp_tools(utcp_client, query, provider_name=None, max_results=None)`

Search for UTCP tools and convert them to LangChain tools.

**Parameters:**
- `utcp_client` (UtcpClient): The UTCP client instance
- `query` (str): Search query string
- `provider_name` (str, optional): Filter tools by provider name
- `max_results` (int, optional): Maximum number of results

**Returns:**
- `List[BaseTool]`: List of relevant LangChain tools

#### `convert_utcp_tool_to_langchain_tool(utcp_client, tool)`

Convert a single UTCP tool to a LangChain tool.

**Parameters:**
- `utcp_client` (UtcpClient): The UTCP client instance
- `tool` (UTCPTool): The UTCP tool to convert

**Returns:**
- `BaseTool`: A LangChain-compatible tool

## Authentication

UTCP supports various authentication methods that work seamlessly with the adapters:

```python
from utcp.shared.provider import HttpProvider
from utcp.shared.auth import ApiKeyAuth, BasicAuth, OAuth2Auth

# API Key authentication
provider = HttpProvider(
    name="authenticated_api",
    provider_type="http",
    url="https://api.example.com/openapi.json",
    http_method="GET",
    auth=ApiKeyAuth(
        api_key="${API_KEY}",  # Use environment variable
        var_name="X-API-Key",
        location="header"
    )
)

# OAuth2 authentication
provider = HttpProvider(
    name="oauth_api",
    provider_type="http",
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

## Supported Provider Types

The adapters work with all UTCP provider types:

- **HTTP/HTTPS APIs** - Including automatic OpenAPI conversion
- **Server-Sent Events (SSE)** - For streaming data
- **Command Line Tools** - Wrap CLI tools as LangChain tools
- **WebSocket** - Real-time bidirectional communication
- **gRPC** - High-performance RPC calls
- **GraphQL** - Query language APIs
- **Model Context Protocol (MCP)** - For interoperability

## Examples

The `examples/` directory contains comprehensive examples:

- `basic_usage.py` - Basic tool loading and usage
- `simple_direct_usage.py` - Direct UTCP client usage
- `simple_langgraph.py` - LangGraph integration
- `authentication_example.py` - Authentication methods
- `openapi_integration.py` - OpenAPI specification integration
- `bedrock_simple.py` - Amazon Bedrock integration
- `real_providers_example.py` - Real-world provider examples

## Development

```bash
# Clone the repository
git clone https://github.com/universal-tool-calling-protocol/langchain-utcp-adapters
cd langchain-utcp-adapters

# Install in development mode
pip install -e ".[dev,test,examples]"

# Run tests
pytest

# Run examples
python examples/basic_usage.py
```

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Related Projects

- [UTCP Python Client](https://github.com/universal-tool-calling-protocol/python-utcp) - The core UTCP implementation
- [LangChain](https://github.com/langchain-ai/langchain) - Framework for developing applications with LLMs
- [LangGraph](https://github.com/langchain-ai/langgraph) - Library for building stateful, multi-actor applications
        "provider_type": "http",
        "http_method": "GET",
        "url": "https://openlibrary.org/static/openapi.json",
        "content_type": "application/json"
    })
    
    # Load tools and convert to LangChain format
    tools = await load_utcp_tools(client)
    print(f"Loaded {len(tools)} tools")
    
    # Search for specific tools
    book_tools = await search_utcp_tools(client, "books", max_results=5)
    
    # Use a tool
    if book_tools:
        tool = book_tools[0]
        result = await tool.ainvoke({"bibkeys": "ISBN:0451526538"})
        print(result)

asyncio.run(main())
```

### With LangGraph Agents

```python
from utcp.client.utcp_client import UtcpClient
from utcp.client.utcp_client_config import UtcpClientConfig
from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI
from langchain_utcp_adapters import load_utcp_tools

async def create_agent():
    # Create UTCP client
    config = UtcpClientConfig()
    client = await UtcpClient.create(config=config)
    
    # Register providers
    await client.register_tool_provider({
        "name": "openlibrary",
        "provider_type": "http",
        "http_method": "GET",
        "url": "https://openlibrary.org/static/openapi.json",
        "content_type": "application/json"
    })
    
    # Load UTCP tools
    tools = await load_utcp_tools(client)
    
    # Create agent with UTCP tools
    llm = ChatOpenAI(model="gpt-4")
    agent = create_react_agent(llm, tools)
    
    # Use the agent
    response = await agent.ainvoke({
        "messages": [("user", "Find information about the book '1984' by George Orwell")]
    })
    
    return response

# Run the agent
response = asyncio.run(create_agent())
print(response["messages"][-1].content)
```

### Amazon Bedrock Integration

```python
from utcp.client.utcp_client import UtcpClient
from utcp.client.utcp_client_config import UtcpClientConfig
from langchain_aws import ChatBedrock
from langchain_utcp_adapters import load_utcp_tools

async def bedrock_example():
    # Initialize Bedrock model
    llm = ChatBedrock(
        model_id="anthropic.claude-3-sonnet-20240229-v1:0",
        region_name="us-east-1"
    )
    
    # Create UTCP client and register providers
    config = UtcpClientConfig()
    client = await UtcpClient.create(config=config)
    
    await client.register_tool_provider({
        "name": "openlibrary",
        "provider_type": "http",
        "http_method": "GET",
        "url": "https://openlibrary.org/static/openapi.json",
        "content_type": "application/json"
    })
    
    # Load UTCP tools
    tools = await load_utcp_tools(client)
    
    # Bind tools to model
    llm_with_tools = llm.bind_tools(tools)
    
    # Use with tool calling
    response = await llm_with_tools.ainvoke("Search for Python programming books")
    return response

response = asyncio.run(bedrock_example())
```

## API Reference

### Core Functions

```python
from langchain_utcp_adapters import (
    load_utcp_tools,
    search_utcp_tools,
    convert_utcp_tool_to_langchain_tool
)
```

#### `load_utcp_tools(utcp_client, provider_name=None)`
Load all tools from UTCP client and convert to LangChain format.

**Parameters:**
- `utcp_client`: UTCP client instance
- `provider_name`: Optional provider name to filter tools

**Returns:** List of LangChain BaseTool instances

#### `search_utcp_tools(utcp_client, query, provider_name=None, max_results=None)`
Search for tools and convert to LangChain format.

**Parameters:**
- `utcp_client`: UTCP client instance  
- `query`: Search query string
- `provider_name`: Optional provider name to filter
- `max_results`: Maximum number of results

**Returns:** List of relevant LangChain BaseTool instances

#### `convert_utcp_tool_to_langchain_tool(utcp_client, tool)`
Convert a single UTCP tool to LangChain format.

**Parameters:**
- `utcp_client`: UTCP client instance
- `tool`: UTCP Tool instance

**Returns:** LangChain BaseTool instance

## Provider Registration

Register providers dynamically using the UTCP client:

### HTTP Provider (OpenAPI)

```python
await client.register_tool_provider({
    "name": "openlibrary",
    "provider_type": "http",
    "http_method": "GET",
    "url": "https://openlibrary.org/static/openapi.json",
    "content_type": "application/json"
})
```

### Text Provider (UTCP Manual)

```python
await client.register_tool_provider({
    "name": "newsapi",
    "provider_type": "text",
    "file_path": "./newsapi_manual.json"
})
```

## Examples

The `examples/` directory contains working examples:

- **`simple_direct_usage.py`**: Direct UTCP client usage
- **`simple_langgraph.py`**: LangGraph agent integration
- **`bedrock_integration.py`**: Amazon Bedrock integration

Run examples:

```bash
cd examples
python simple_direct_usage.py
python simple_langgraph.py
```

## Testing

Run the test suite:

```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run tests
pytest tests/

# Run with coverage
pytest tests/ --cov=langchain_utcp_adapters
```

## Development

### Setup

```bash
cd langchain-utcp-adapters
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e ".[all]"
```

### Code Quality

```bash
# Format code
black langchain_utcp_adapters/ tests/ examples/

# Sort imports
isort langchain_utcp_adapters/ tests/ examples/

# Type checking
mypy langchain_utcp_adapters/
```

## Supported Providers

### Tested Providers

- **OpenLibrary API**: 11 tools for books, authors, and search
- **NewsAPI**: 2 tools for news articles (requires API key)

### Provider Types

- **HTTP**: OpenAPI/Swagger specifications
- **Text**: UTCP manual definitions
- **Extensible**: Easy to add new provider types

## Requirements

- Python 3.8+
- LangChain Core 0.3.36+
- UTCP 0.1.7+
- Pydantic 2.0+

## License

MIT License - see [LICENSE](LICENSE) file.

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history and changes.
