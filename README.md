# LangChain UTCP Adapters

A Python package that bridges Universal Tool Calling Protocol (UTCP) providers with LangChain, enabling seamless integration of external tools and APIs into LangChain applications.

## Features

- **Multi-Provider Support**: Connect to HTTP (OpenAPI), Text (UTCP Manual), and other provider types
- **Automatic Tool Conversion**: Convert UTCP tools to LangChain-compatible tools with proper schemas
- **Tool Discovery**: Search and filter tools by name, description, and tags
- **Health Monitoring**: Real-time provider health checking
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
from langchain_utcp_adapters import MultiProviderUTCPClient

async def main():
    # Configure providers
    providers = [
        {
            "name": "openlibrary",
            "provider_type": "http",
            "http_method": "GET",
            "url": "https://openlibrary.org/static/openapi.json",
            "content_type": "application/json"
        }
    ]
    
    # Create client
    client = MultiProviderUTCPClient(providers=providers)
    
    # Load tools
    tools = await client.get_tools()
    print(f"Loaded {len(tools)} tools")
    
    # Search for specific tools
    book_tools = await client.search_tools("books", max_results=5)
    
    # Use a tool
    if book_tools:
        tool = book_tools[0]
        result = await tool.ainvoke({"bibkeys": "ISBN:0451526538"})
        print(result)
    
    await client.close()

asyncio.run(main())
```

### With LangGraph Agents

```python
from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI
from langchain_utcp_adapters import MultiProviderUTCPClient

async def create_agent():
    # Load UTCP tools
    client = MultiProviderUTCPClient(providers_file_path="providers.json")
    tools = await client.get_tools()
    
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
from langchain_aws import ChatBedrock
from langchain_utcp_adapters import MultiProviderUTCPClient

async def bedrock_example():
    # Initialize Bedrock model
    llm = ChatBedrock(
        model_id="anthropic.claude-3-sonnet-20240229-v1:0",
        region_name="us-east-1"
    )
    
    # Load UTCP tools
    client = MultiProviderUTCPClient(providers_file_path="providers.json")
    tools = await client.get_tools()
    
    # Bind tools to model
    llm_with_tools = llm.bind_tools(tools)
    
    # Use with tool calling
    response = await llm_with_tools.ainvoke("Search for Python programming books")
    return response

response = asyncio.run(bedrock_example())
```

## Provider Configuration

### HTTP Provider (OpenAPI)

```json
{
  "name": "openlibrary",
  "provider_type": "http",
  "http_method": "GET",
  "url": "https://openlibrary.org/static/openapi.json",
  "content_type": "application/json"
}
```

### Text Provider (UTCP Manual)

```json
{
  "name": "newsapi",
  "provider_type": "text",
  "file_path": "./newsapi_manual.json"
}
```

### Configuration File

Create a `providers.json` file:

```json
[
  {
    "name": "openlibrary",
    "provider_type": "http",
    "http_method": "GET",
    "url": "https://openlibrary.org/static/openapi.json",
    "content_type": "application/json"
  },
  {
    "name": "newsapi",
    "provider_type": "text",
    "file_path": "./newsapi_manual.json"
  }
]
```

## API Reference

### MultiProviderUTCPClient

The main client class for managing UTCP providers.

```python
class MultiProviderUTCPClient:
    def __init__(
        self,
        providers: Optional[List[Dict[str, Any]]] = None,
        providers_file_path: Optional[str] = None
    )
    
    async def get_tools(self, provider_name: Optional[str] = None) -> List[BaseTool]
    async def search_tools(self, query: str, max_results: int = 10) -> List[BaseTool]
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any
    async def health_check(self) -> Dict[str, Dict[str, Any]]
    async def get_providers(self) -> List[str]
    async def close(self) -> None
```

### Key Methods

- **`get_tools()`**: Load all tools or tools from a specific provider
- **`search_tools()`**: Search tools by query string
- **`call_tool()`**: Execute a tool directly
- **`health_check()`**: Check provider health status
- **`get_providers()`**: List available providers

## Examples

The `examples/` directory contains working examples:

- **`basic_usage.py`**: Simple client usage
- **`real_providers_example.py`**: Integration with real APIs
- **`langgraph_integration.py`**: LangGraph agent integration
- **`bedrock_integration.py`**: Amazon Bedrock integration
- **`authentication_example.py`**: Authentication patterns

Run examples:

```bash
cd examples
python basic_usage.py
python real_providers_example.py
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
