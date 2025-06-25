"""Pytest configuration and fixtures."""

import os
import tempfile
import pytest
from unittest.mock import Mock, patch
from wikijs_mcp.config import WikiJSConfig
from wikijs_mcp.crypto import EnvEncryption


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


@pytest.fixture
def temp_env_file(temp_dir):
    """Create a temporary .env file for testing."""
    env_path = os.path.join(temp_dir, ".env")
    env_content = """WIKIJS_URL=https://test-wiki.example.com
WIKIJS_API_KEY=test-api-key-123
WIKIJS_GRAPHQL_ENDPOINT=/graphql
DEBUG=true
"""
    with open(env_path, 'w') as f:
        f.write(env_content)
    return env_path


@pytest.fixture
def sample_env_content():
    """Sample environment file content."""
    return """WIKIJS_URL=https://test-wiki.example.com
WIKIJS_API_KEY=test-api-key-123
WIKIJS_GRAPHQL_ENDPOINT=/graphql
DEBUG=true
"""


@pytest.fixture
def mock_wiki_config():
    """Mock WikiJS configuration."""
    return WikiJSConfig(
        url="https://test-wiki.example.com",
        api_key="test-api-key-123",
        graphql_endpoint="/graphql",
        debug=True
    )


@pytest.fixture
def encryption_instance(temp_dir):
    """Create an EnvEncryption instance with temp directory."""
    env_path = os.path.join(temp_dir, ".env")
    return EnvEncryption(env_path)


@pytest.fixture
def mock_httpx_client():
    """Mock httpx.AsyncClient for API testing."""
    with patch('httpx.AsyncClient') as mock_client:
        mock_instance = Mock()
        mock_client.return_value = mock_instance
        
        # Mock async context manager
        mock_instance.__aenter__ = Mock(return_value=mock_instance)
        mock_instance.__aexit__ = Mock(return_value=None)
        
        yield mock_instance


@pytest.fixture
def sample_graphql_response():
    """Sample GraphQL API response."""
    return {
        "data": {
            "pages": {
                "search": {
                    "results": [
                        {
                            "id": 1,
                            "path": "docs/getting-started",
                            "title": "Getting Started",
                            "description": "A guide to get started",
                            "updatedAt": "2024-01-01T00:00:00Z",
                            "createdAt": "2024-01-01T00:00:00Z"
                        }
                    ]
                }
            }
        }
    }


@pytest.fixture
def sample_page_data():
    """Sample page data for testing."""
    return {
        "id": 1,
        "path": "docs/test-page",
        "title": "Test Page",
        "description": "A test page",
        "content": "# Test Page\n\nThis is test content.",
        "contentType": "markdown",
        "createdAt": "2024-01-01T00:00:00Z",
        "updatedAt": "2024-01-01T00:00:00Z",
        "author": {
            "name": "Test User",
            "email": "test@example.com"
        },
        "editor": "markdown",
        "locale": "en",
        "tags": [
            {"tag": "test"},
            {"tag": "documentation"}
        ]
    }


@pytest.fixture
def mock_getpass():
    """Mock getpass for password input."""
    with patch('getpass.getpass') as mock_getpass:
        mock_getpass.return_value = "test-password-123"
        yield mock_getpass


@pytest.fixture(autouse=True)
def clean_env():
    """Clean environment variables before each test."""
    env_vars = [
        "WIKIJS_URL",
        "WIKIJS_API_KEY", 
        "WIKIJS_GRAPHQL_ENDPOINT",
        "DEBUG"
    ]
    
    # Store original values
    original_values = {}
    for var in env_vars:
        original_values[var] = os.environ.get(var)
        if var in os.environ:
            del os.environ[var]
    
    yield
    
    # Restore original values
    for var, value in original_values.items():
        if value is not None:
            os.environ[var] = value
        elif var in os.environ:
            del os.environ[var]