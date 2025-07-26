# Changelog

All notable changes to LangChain UTCP Adapters will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [0.1.0] - 2025-01-26

### Added
- Initial release of LangChain UTCP Adapters
- `MultiProviderUTCPClient` for managing multiple UTCP providers
- Automatic tool conversion from UTCP to LangChain format
- Support for HTTP (OpenAPI) and Text (UTCP Manual) provider types
- Tool search and discovery functionality
- Provider health monitoring
- Comprehensive test suite with real provider integration
- Examples for basic usage, LangGraph, and Amazon Bedrock
- Full async/await support with proper resource management

### Features
- Multi-provider support with dynamic configuration
- Dynamic Pydantic schema generation from JSON schemas
- Semantic search across tools by name, description, and tags
- Real-time provider health checking
- Robust error handling with graceful fallbacks
- Complete type hints and Pydantic v2 compatibility

### Tested Providers
- OpenLibrary API (11 tools for books, authors, search)
- NewsAPI (2 tools for news articles)

### Dependencies
- LangChain Core 0.3.36+
- UTCP 0.1.7+
- Python 3.8+
