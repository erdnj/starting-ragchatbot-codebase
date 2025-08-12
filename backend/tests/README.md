# Testing Framework

This directory contains the enhanced testing framework for the RAG system.

## Structure

- `conftest.py` - Shared fixtures and test configuration
- `test_api_endpoints.py` - API endpoint tests for FastAPI routes
- `test_ai_generator.py` - Unit tests for AI generator component
- `test_utils.py` - Utility classes and helpers for testing
- `test_utilities_demo.py` - Demo tests showing utility usage

## Running Tests

```bash
# Run all tests
uv run pytest backend/tests/

# Run with verbose output
uv run pytest backend/tests/ -v

# Run only API tests
uv run pytest backend/tests/ -m "api"

# Run only unit tests  
uv run pytest backend/tests/ -m "unit"

# Run specific test file
uv run pytest backend/tests/test_api_endpoints.py

# Run with coverage (after installing pytest-cov)
uv add --dev pytest-cov
uv run pytest backend/tests/ --cov=backend --cov-report=html
```

## Test Markers

- `@pytest.mark.api` - API endpoint tests
- `@pytest.mark.unit` - Unit tests
- `@pytest.mark.integration` - Integration tests

## Key Features

### API Testing Infrastructure
- Complete FastAPI test client setup avoiding static file mounting issues
- Tests for all endpoints: `/api/query`, `/api/courses`, `/api/session/clear`, `/`
- Error handling and edge case testing
- Request/response validation

### Shared Fixtures
- Mock RAG system with configurable behavior
- Mock vector store and AI generator
- Sample test data generators
- Test app client without static file dependencies

### Test Utilities
- `MockRAGSystemBuilder` - Builder pattern for creating test RAG systems
- `TestDataGenerator` - Generate sample data for various test scenarios
- `APITestHelpers` - Validation helpers for API responses
- `MockChromaDBCollection` - In-memory ChromaDB mock for testing

### Configuration
- pytest.ini_options in pyproject.toml for clean execution
- Asyncio mode auto-detection
- Structured test organization and discovery

## Example Usage

```python
def test_custom_rag_behavior(test_app_client):
    """Example using the test utilities"""
    # Configure mock RAG system behavior
    app = test_app_client.app
    app.mock_rag.query.return_value = (
        "Custom response",
        [{"text": "Custom source", "link": "http://example.com"}]
    )
    
    # Make API request
    response = test_app_client.post("/api/query", json={
        "query": "Test question"
    })
    
    # Validate response
    assert response.status_code == 200
    APITestHelpers.assert_valid_query_response(response.json())
```

## Adding New Tests

1. Create test file following naming convention: `test_*.py`
2. Use appropriate markers: `@pytest.mark.api`, `@pytest.mark.unit`, etc.
3. Leverage shared fixtures from `conftest.py`
4. Use utility classes from `test_utils.py` for common operations
5. Follow existing patterns for mock setup and assertions