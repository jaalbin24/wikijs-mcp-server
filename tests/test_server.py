"""Tests for MCP server functionality."""

import asyncio
import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from wikijs_mcp.server import WikiJSMCPServer


@pytest.mark.integration
class TestWikiJSMCPServer:
    """Test cases for WikiJSMCPServer class."""
    
    @patch('wikijs_mcp.server.WikiJSConfig.load_config')
    def test_init(self, mock_load_config, mock_wiki_config):
        """Test WikiJSMCPServer initialization."""
        mock_load_config.return_value = mock_wiki_config
        
        server = WikiJSMCPServer()
        
        assert server.config == mock_wiki_config
        assert server.app is not None
        mock_load_config.assert_called_once()
    
    
    @patch('wikijs_mcp.server.WikiJSConfig.load_config')
    async def test_list_tools(self, mock_load_config, mock_wiki_config):
        """Test MCP tools listing."""
        mock_load_config.return_value = mock_wiki_config
        server = WikiJSMCPServer()
        
        tools = await server.app.list_tools()
        assert len(tools) == 6  # 6 wiki tools
        
        tool_names = [tool.name for tool in tools]
        expected_names = [
            "wiki_search", "wiki_get_page", "wiki_list_pages", 
            "wiki_get_tree", "wiki_create_page", "wiki_update_page"
        ]
        assert set(tool_names) == set(expected_names)
    
    @patch('wikijs_mcp.server.WikiJSConfig.load_config')
    def test_get_streamable_http_app(self, mock_load_config, mock_wiki_config):
        """Test getting StreamableHTTP app for HTTP transport."""
        mock_load_config.return_value = mock_wiki_config
        server = WikiJSMCPServer()
        
        app = server.get_streamable_http_app()
        assert app is not None
        # The app should be a Starlette/FastAPI app
        assert hasattr(app, 'routes')
    
    @patch('wikijs_mcp.server.WikiJSConfig.load_config')
    @patch('wikijs_mcp.server.WikiJSClient')
    async def test_call_tool_search_success(self, mock_client_class, mock_load_config, mock_wiki_config):
        """Test calling search tool with successful response."""
        # Setup mocks
        mock_load_config.return_value = mock_wiki_config
        mock_client_instance = AsyncMock()
        mock_client_instance.__aenter__.return_value = mock_client_instance
        mock_client_instance.__aexit__.return_value = None
        mock_client_instance.search_pages.return_value = [
            {"title": "Test Page", "path": "/test", "updatedAt": "2023-01-01"}
        ]
        mock_client_class.return_value = mock_client_instance
        
        server = WikiJSMCPServer()
        
        result = await server.app.call_tool("wiki_search", {"query": "test", "limit": 10})
        assert len(result) == 1
        assert "Found 1 pages for query 'test'" in result[0].text
        assert "Test Page" in result[0].text
