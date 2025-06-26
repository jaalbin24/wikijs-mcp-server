"""Tests for HTTP server functionality."""

import asyncio
import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from wikijs_mcp.server import WikiJSHTTPServer


@pytest.mark.integration
class TestWikiJSHTTPServer:
    """Test cases for WikiJSHTTPServer class."""
    
    @patch('wikijs_mcp.server.WikiJSConfig.load_config')
    def test_init(self, mock_load_config, mock_wiki_config):
        """Test WikiJSHTTPServer initialization."""
        mock_load_config.return_value = mock_wiki_config
        
        server = WikiJSHTTPServer()
        
        assert server.config == mock_wiki_config
        assert server.app is not None
        mock_load_config.assert_called_once()
    
    
    @patch('wikijs_mcp.server.WikiJSConfig.load_config')
    def test_health_endpoint(self, mock_load_config, mock_wiki_config):
        """Test health check endpoint."""
        mock_load_config.return_value = mock_wiki_config
        server = WikiJSHTTPServer()
        
        with TestClient(server.app) as client:
            response = client.get("/health")
            assert response.status_code == 200
            assert response.json() == {"status": "healthy", "service": "wikijs-http-server"}
    
    @patch('wikijs_mcp.server.WikiJSConfig.load_config')
    def test_tools_endpoint(self, mock_load_config, mock_wiki_config):
        """Test tools listing endpoint."""
        mock_load_config.return_value = mock_wiki_config
        server = WikiJSHTTPServer()
        
        with TestClient(server.app) as client:
            response = client.get("/tools")
            assert response.status_code == 200
            data = response.json()
            assert "endpoints" in data
            assert len(data["endpoints"]) == 6  # 6 API endpoints
            
            endpoint_names = [ep["name"] for ep in data["endpoints"]]
            expected_names = ["search", "get_page", "list_pages", "get_tree", "create_page", "update_page"]
            assert set(endpoint_names) == set(expected_names)
    
    @patch('wikijs_mcp.server.WikiJSConfig.load_config')
    @patch('wikijs_mcp.server.WikiJSClient')
    def test_search_endpoint_success(self, mock_client_class, mock_load_config, mock_wiki_config):
        """Test search endpoint with successful response."""
        # Setup mocks
        mock_load_config.return_value = mock_wiki_config
        mock_client_instance = AsyncMock()
        mock_client_instance.__aenter__.return_value = mock_client_instance
        mock_client_instance.__aexit__.return_value = None
        mock_client_instance.search_pages.return_value = [
            {"title": "Test Page", "path": "/test", "updatedAt": "2023-01-01"}
        ]
        mock_client_class.return_value = mock_client_instance
        
        server = WikiJSHTTPServer()
        
        with TestClient(server.app) as client:
            response = client.post("/search", json={"query": "test", "limit": 10})
            assert response.status_code == 200
            data = response.json()
            assert "results" in data
            assert len(data["results"]) == 1
            assert data["results"][0]["title"] == "Test Page"
