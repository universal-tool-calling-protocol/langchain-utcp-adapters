# Contributing to LangChain UTCP Adapters

Thank you for your interest in contributing! This guide will help you get started.

## Development Setup

```bash
git clone <repository-url>
cd langchain-utcp-adapters
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e ".[all]"
pip install pytest pytest-asyncio black isort mypy
```

## Making Changes

1. **Create a feature branch**: `git checkout -b feature/your-feature`
2. **Make your changes** with tests and documentation
3. **Run tests**: `pytest tests/`
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

## Pull Request Guidelines

- Use descriptive titles and descriptions
- Reference related issues
- Include tests and documentation updates
- Ensure all checks pass

## Questions?

Open an issue for questions or discussion before starting major changes.
