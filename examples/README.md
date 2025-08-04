# LangChain UTCP Adapters - Examples

This directory contains comprehensive examples demonstrating how to use the LangChain UTCP Adapters package to integrate Universal Tool Calling Protocol (UTCP) providers with LangChain applications.

## Quick Start

1. **Install the package**:
   ```bash
   pip install -e .
1. **Install the base package**:
   ```bash
   pip install langchain-utcp-adapters
   ```

2. **Install optional dependencies**:
   
   **Using PDM (for development)**:
   ```bash
   pdm install -G examples  # For LangGraph and OpenAI examples
   pdm install -G bedrock   # For Amazon Bedrock examples
   pdm install -G server    # For server-based examples
   ```
   
   **Using pip (for end users)**:
   ```bash
   pip install langchain-utcp-adapters[examples]  # LangGraph + OpenAI
   pip install langchain-utcp-adapters[bedrock]   # Amazon Bedrock
   pip install langchain-utcp-adapters[all]       # Everything
   ```

3. **Run a basic example**:
   ```bash
   python examples/basic_usage.py
   ```

## Examples Overview

| Example | Description | Dependencies | API Keys Required |
|---------|-------------|--------------|-------------------|
| [`basic_usage.py`](#basic-usage) | Core functionality demonstration | None | None |
| [`simple_direct_usage.py`](#simple-direct-usage) | Direct UTCP client usage | None | None |
| [`simple_langgraph.py`](#simple-langgraph) | Basic LangGraph integration | LangGraph, OpenAI | OPENAI_API_KEY |
| [`langgraph_integration.py`](#langgraph-integration) | Advanced LangGraph features | LangGraph, OpenAI | OPENAI_API_KEY |
| [`authentication_example.py`](#authentication) | Authentication methods | None | None (demo only) |
| [`openapi_integration.py`](#openapi-integration) | OpenAPI specification integration | None | None |
| [`bedrock_simple.py`](#bedrock-simple) | Basic Amazon Bedrock integration | LangChain-AWS, Boto3 | AWS credentials |
| [`bedrock_integration.py`](#bedrock-integration) | Advanced Bedrock features | LangChain-AWS, Boto3 | AWS credentials |
| [`real_providers_example.py`](#real-providers) | Real-world API integration | None | None |

## Detailed Examples

### Basic Usage

**File**: `basic_usage.py`  
**Purpose**: Demonstrates core functionality of loading and using UTCP tools  
**Requirements**: None  

```bash
python examples/basic_usage.py
```

**What it shows**:
- Creating UTCP client
- Registering multiple providers (Petstore, OpenLibrary)
- Loading tools and converting to LangChain format
- Tool search functionality
- Provider information display

### Simple Direct Usage

**File**: `simple_direct_usage.py`  
**Purpose**: Shows direct UTCP client usage without configuration files  
**Requirements**: None  

```bash
python examples/simple_direct_usage.py
```

**What it shows**:
- Direct provider registration
- Tool loading from OpenLibrary API
- Tool inspection and metadata

### Simple LangGraph

**File**: `simple_langgraph.py`  
**Purpose**: Basic LangGraph agent with UTCP tools  
**Requirements**: LangGraph, OpenAI  

**Setup**:
```bash
export OPENAI_API_KEY=your_key_here
python examples/simple_langgraph.py
```

**What it shows**:
- Creating LangGraph agents with UTCP tools
- Agent execution with tool calling
- Error handling for missing API keys

### LangGraph Integration

**File**: `langgraph_integration.py`  
**Purpose**: Advanced LangGraph features and patterns  
**Requirements**: LangGraph, OpenAI  

**Setup**:
```bash
export OPENAI_API_KEY=your_key_here
python examples/langgraph_integration.py
```

**What it shows**:
- Complex agent workflows
- Multiple provider integration
- Advanced error handling

### Authentication

**File**: `authentication_example.py`  
**Purpose**: Demonstrates various authentication methods  
**Requirements**: None (demo only)  

```bash
python examples/authentication_example.py
```

**What it shows**:
- API key authentication
- OAuth2 authentication
- Basic authentication
- Environment variable usage
- Provider health checking

**Note**: This is a demonstration only. Real authentication requires actual API keys.

### OpenAPI Integration

**File**: `openapi_integration.py`  
**Purpose**: Shows automatic OpenAPI specification integration  
**Requirements**: None  

```bash
python examples/openapi_integration.py
```

**What it shows**:
- Automatic OpenAPI to UTCP conversion
- Multiple OpenAPI provider integration
- Tool discovery and search
- Provider health monitoring

**Note**: This example may take longer to run as it fetches and processes OpenAPI specifications.

### Bedrock Simple

**File**: `bedrock_simple.py`  
**Purpose**: Basic Amazon Bedrock integration  
**Requirements**: LangChain-AWS, Boto3, AWS credentials  

**Setup**:
```bash
# Configure AWS credentials
aws configure

# Or set environment variables
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_DEFAULT_REGION=us-east-1

python examples/bedrock_simple.py
```

**What it shows**:
- AWS credential verification
- Bedrock model initialization
- UTCP tools with Bedrock models
- Error handling for missing credentials

**Prerequisites**:
1. AWS account with Bedrock access
2. Model access enabled in Bedrock console
3. Appropriate IAM permissions

### Bedrock Integration

**File**: `bedrock_integration.py`  
**Purpose**: Advanced Amazon Bedrock features  
**Requirements**: LangChain-AWS, Boto3, AWS credentials  

**Setup**: Same as Bedrock Simple

**What it shows**:
- Advanced Bedrock model configuration
- Multiple model testing
- Tool integration patterns
- Production-ready error handling

**Note**: Tool names from OpenLibrary API may exceed Bedrock's 64-character limit, causing validation errors. This is expected behavior.

### Real Providers

**File**: `real_providers_example.py`  
**Purpose**: Integration with real-world APIs  
**Requirements**: None  

```bash
python examples/real_providers_example.py
```

**What it shows**:
- OpenLibrary API integration
- Tool organization by provider
- Search functionality across providers
- Practical tool usage examples
- Provider health monitoring

## Environment Variables

### Required for OpenAI Examples
```bash
export OPENAI_API_KEY=your_openai_api_key
```

### Required for Bedrock Examples
```bash
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_DEFAULT_REGION=us-east-1
```

### Optional for Authentication Examples
```bash
export API_KEY=your_api_key
export OAUTH_CLIENT_ID=your_client_id
export OAUTH_CLIENT_SECRET=your_client_secret
export BASIC_AUTH_USERNAME=your_username
export BASIC_AUTH_PASSWORD=your_password
```

## Troubleshooting

### Common Issues

#### 1. Missing Dependencies
**Error**: `ModuleNotFoundError: No module named 'langgraph'`  
**Solution**: Install optional dependencies:
```bash
# Using PDM
pdm install -G examples

# Using pip
pip install langchain-utcp-adapters[examples]
```

#### 2. Missing API Keys
**Error**: `OPENAI_API_KEY environment variable not set`  
**Solution**: Set the required environment variable:
```bash
export OPENAI_API_KEY=your_key_here
```

#### 3. AWS Credentials Not Found
**Error**: `AWS credential error`  
**Solution**: Configure AWS credentials:
```bash
aws configure
```

#### 4. Bedrock Access Denied
**Error**: `AccessDeniedException`  
**Solution**: 
1. Enable model access in AWS Bedrock console
2. Ensure proper IAM permissions
3. Verify account has Bedrock access

#### 5. Tool Name Validation Errors (Bedrock)
**Error**: `string [...] does not match pattern ^[a-zA-Z0-9_-]{1,64}$`  
**Solution**: This is expected behavior. Bedrock has strict tool naming requirements that some APIs don't meet.

#### 6. Network Timeouts
**Error**: Connection timeouts when loading tools  
**Solution**: 
- Check internet connectivity
- Some APIs may be temporarily unavailable
- Increase timeout values if needed

### Getting Help

1. **Check the logs**: Most examples include detailed error messages
2. **Verify prerequisites**: Ensure all required dependencies and credentials are set up
3. **Test connectivity**: Try simpler examples first (e.g., `basic_usage.py`)
4. **Check API status**: Verify that external APIs (OpenLibrary, etc.) are accessible

## Development

### Running All Examples
```bash
# Basic examples (no external dependencies)
python examples/basic_usage.py
python examples/simple_direct_usage.py
python examples/authentication_example.py
python examples/openapi_integration.py
python examples/real_providers_example.py

# OpenAI examples (requires OPENAI_API_KEY)
export OPENAI_API_KEY=your_key
python examples/simple_langgraph.py
python examples/langgraph_integration.py

# Bedrock examples (requires AWS credentials)
python examples/bedrock_simple.py
python examples/bedrock_integration.py
```

### Creating New Examples

1. **Follow the naming convention**: `your_example.py`
2. **Include comprehensive error handling**
3. **Add clear documentation and comments**
4. **Test with and without optional dependencies**
5. **Update this README with your example**

### Example Template

```python
"""
Your Example - Brief description

This example demonstrates [specific functionality].
"""

import asyncio
from utcp.client.utcp_client import UtcpClient
from utcp.client.utcp_client_config import UtcpClientConfig
from langchain_utcp_adapters import load_utcp_tools

async def main():
    """Main example function."""
    print("🚀 Your Example")
    print("=" * 50)
    
    try:
        # Your example code here
        pass
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("✅ Example completed!")

if __name__ == "__main__":
    asyncio.run(main())
```

## Next Steps

1. **Start with basic examples** to understand core concepts
2. **Explore authentication patterns** for secure API integration
3. **Try LangGraph integration** for building AI agents
4. **Experiment with Bedrock** for enterprise AI applications
5. **Build your own providers** using the patterns shown

## Additional Resources

- [LangChain Documentation](https://python.langchain.com/)
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [UTCP Specification](https://github.com/universal-tool-calling-protocol)
- [Amazon Bedrock Documentation](https://docs.aws.amazon.com/bedrock/)
- [OpenAPI Specification](https://swagger.io/specification/)
