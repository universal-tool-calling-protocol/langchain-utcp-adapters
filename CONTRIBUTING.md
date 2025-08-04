# Contributing to LangChain UTCP Adapters

Thank you for your interest in contributing! This guide will help you get started.

## Development Setup

### Using PDM (Recommended)

```bash
git clone <repository-url>
cd langchain-utcp-adapters
pdm install -G all
```

### Using pip

```bash
git clone <repository-url>
cd langchain-utcp-adapters
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e ".[all]"
```

### Dependency Groups

- `test` - Core testing dependencies (pytest, etc.)
- `dev` - Development tools (ruff, mypy, build tools)
- `examples` - Dependencies for LangGraph and OpenAI examples
- `server` - FastAPI and uvicorn for server-based examples
- `bedrock` - Amazon Bedrock integration dependencies
- `all` - Everything for complete development setup

## Making Changes

1. **Create a feature branch**: `git checkout -b feature/your-feature`
2. **Make your changes** with tests and documentation
3. **Run tests**: `pdm run pytest` or `pytest tests/`
4. **Format code**: `black . && isort .`
5. **Type check**: `mypy langchain_utcp_adapters/`
6. **Commit**: Use conventional commits (e.g., `feat: add new provider type`)
7. **Submit PR** with clear description

## Code Style

- Follow PEP 8 with Black formatting (88 char line length)
- Use type hints for all functions
- Write docstrings for public APIs
- Include tests for new features
- Update documentation as needed

## Testing

- Write async tests for async functionality
- Test both success and error cases
- Use meaningful test names and assertions
- Maintain or improve test coverage

### Running Tests

```bash
# Run all tests
pdm run pytest

# Run with coverage
pdm run pytest --cov=langchain_utcp_adapters

# Run specific test file
pdm run pytest tests/test_tools.py
```

## Pull Request Guidelines

- Use descriptive titles and descriptions
- Reference related issues
- Include tests and documentation updates
- Ensure all checks pass

## Questions?

Open an issue for questions or discussion before starting major changes.
