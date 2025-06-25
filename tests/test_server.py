"""Tests for MCP server functionality."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from mcp.types import TextContent
from wikijs_mcp.server import WikiJSMCPServer


@pytest.mark.integration
@pytest.mark.asyncio
class TestWikiJSMCPServer:
    """Test cases for WikiJSMCPServer class."""
    
    @patch('wikijs_mcp.server.WikiJSConfig.load_config')
    def test_init(self, mock_load_config, mock_wiki_config):
        """Test WikiJSMCPServer initialization."""
        mock_load_config.return_value = mock_wiki_config
        
        server = WikiJSMCPServer()
        
        assert server.config == mock_wiki_config
        assert server.client is None
        mock_load_config.assert_called_once()
    
    @patch('wikijs_mcp.server.WikiJSConfig.load_config')
    async def test_list_tools(self, mock_load_config, mock_wiki_config):
        """Test listing available tools."""
        mock_load_config.return_value = mock_wiki_config
        server = WikiJSMCPServer()
        
        # Get the list_tools handler
        tools = await server.server._handlers["list_tools"]()
        
        assert len(tools) == 6
        tool_names = [tool.name for tool in tools]
        
        expected_tools = [
            "wiki_search",
            "wiki_get_page", 
            "wiki_list_pages",
            "wiki_get_tree",
            "wiki_create_page",
            "wiki_update_page"
        ]
        
        for expected_tool in expected_tools:
            assert expected_tool in tool_names
    
    @patch('wikijs_mcp.server.WikiJSConfig.load_config')
    @patch('wikijs_mcp.server.WikiJSClient')
    async def test_wiki_search_success(self, mock_client_class, mock_load_config, mock_wiki_config):
        """Test successful wiki search tool call."""
        mock_load_config.return_value = mock_wiki_config
        server = WikiJSMCPServer()
        
        # Mock client and search results
        mock_client = AsyncMock()
        mock_client.search_pages.return_value = [
            {
                "title": "Test Page",
                "path": "docs/test",
                "description": "A test page",
                "updatedAt": "2024-01-01T00:00:00Z"
            }
        ]
        
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        # Call the tool
        result = await server.server._handlers["call_tool"]("wiki_search", {"query": "test"})
        
        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        assert "Test Page" in result[0].text
        assert "docs/test" in result[0].text
        mock_client.search_pages.assert_called_with("test", 10)
    
    @patch('wikijs_mcp.server.WikiJSConfig.load_config')
    @patch('wikijs_mcp.server.WikiJSClient')
    async def test_wiki_search_no_results(self, mock_client_class, mock_load_config, mock_wiki_config):
        """Test wiki search with no results."""
        mock_load_config.return_value = mock_wiki_config
        server = WikiJSMCPServer()
        
        mock_client = AsyncMock()
        mock_client.search_pages.return_value = []
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        result = await server.server._handlers["call_tool"]("wiki_search", {"query": "nonexistent"})
        
        assert len(result) == 1
        assert "No pages found" in result[0].text
    
    @patch('wikijs_mcp.server.WikiJSConfig.load_config')
    @patch('wikijs_mcp.server.WikiJSClient')
    async def test_wiki_get_page_by_path(self, mock_client_class, mock_load_config, 
                                       mock_wiki_config, sample_page_data):
        """Test getting page by path."""
        mock_load_config.return_value = mock_wiki_config
        server = WikiJSMCPServer()
        
        mock_client = AsyncMock()
        mock_client.get_page_by_path.return_value = sample_page_data
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        result = await server.server._handlers["call_tool"](
            "wiki_get_page", 
            {"path": "docs/test-page"}
        )
        
        assert len(result) == 1
        response_text = result[0].text
        assert "Test Page" in response_text
        assert "docs/test-page" in response_text
        assert "This is test content." in response_text
        mock_client.get_page_by_path.assert_called_with("docs/test-page")
    
    @patch('wikijs_mcp.server.WikiJSConfig.load_config')
    @patch('wikijs_mcp.server.WikiJSClient')
    async def test_wiki_get_page_by_id(self, mock_client_class, mock_load_config, 
                                     mock_wiki_config, sample_page_data):
        """Test getting page by ID."""
        mock_load_config.return_value = mock_wiki_config
        server = WikiJSMCPServer()
        
        mock_client = AsyncMock()
        mock_client.get_page_by_id.return_value = sample_page_data
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        result = await server.server._handlers["call_tool"](
            "wiki_get_page", 
            {"id": 123}
        )
        
        assert len(result) == 1
        assert "Test Page" in result[0].text
        mock_client.get_page_by_id.assert_called_with(123)
    
    @patch('wikijs_mcp.server.WikiJSConfig.load_config')
    @patch('wikijs_mcp.server.WikiJSClient')
    async def test_wiki_get_page_not_found(self, mock_client_class, mock_load_config, mock_wiki_config):
        """Test getting page that doesn't exist."""
        mock_load_config.return_value = mock_wiki_config
        server = WikiJSMCPServer()
        
        mock_client = AsyncMock()
        mock_client.get_page_by_path.return_value = None
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        result = await server.server._handlers["call_tool"](
            "wiki_get_page", 
            {"path": "nonexistent"}
        )
        
        assert len(result) == 1
        assert "Page not found" in result[0].text
    
    @patch('wikijs_mcp.server.WikiJSConfig.load_config')
    @patch('wikijs_mcp.server.WikiJSClient')
    async def test_wiki_list_pages(self, mock_client_class, mock_load_config, mock_wiki_config):
        """Test listing pages."""
        mock_load_config.return_value = mock_wiki_config
        server = WikiJSMCPServer()
        
        mock_client = AsyncMock()
        mock_client.list_pages.return_value = [
            {
                "id": 1,
                "title": "Page 1",
                "path": "docs/page1",
                "description": "First page",
                "author": {"name": "User 1"},
                "updatedAt": "2024-01-01T00:00:00Z"
            }
        ]
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        result = await server.server._handlers["call_tool"](
            "wiki_list_pages", 
            {"limit": 25, "offset": 5}
        )
        
        assert len(result) == 1
        response_text = result[0].text
        assert "Page 1" in response_text
        assert "offset: 5, limit: 25" in response_text
        mock_client.list_pages.assert_called_with(25, 5)
    
    @patch('wikijs_mcp.server.WikiJSConfig.load_config')
    @patch('wikijs_mcp.server.WikiJSClient')
    async def test_wiki_get_tree(self, mock_client_class, mock_load_config, mock_wiki_config):
        """Test getting page tree."""
        mock_load_config.return_value = mock_wiki_config
        server = WikiJSMCPServer()
        
        mock_client = AsyncMock()
        mock_client.get_page_tree.return_value = [
            {
                "title": "Documentation",
                "path": "docs",
                "isFolder": True
            },
            {
                "title": "Getting Started", 
                "path": "docs/getting-started",
                "isFolder": False
            }
        ]
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        result = await server.server._handlers["call_tool"](
            "wiki_get_tree", 
            {"parent_path": "docs"}
        )
        
        assert len(result) == 1
        response_text = result[0].text
        assert "📁 Documentation/" in response_text
        assert "📄 Getting Started" in response_text
        mock_client.get_page_tree.assert_called_with("docs", "PATH")
    
    @patch('wikijs_mcp.server.WikiJSConfig.load_config')
    @patch('wikijs_mcp.server.WikiJSClient')
    async def test_wiki_create_page_success(self, mock_client_class, mock_load_config, mock_wiki_config):
        """Test successful page creation."""
        mock_load_config.return_value = mock_wiki_config
        server = WikiJSMCPServer()
        
        mock_client = AsyncMock()
        mock_client.create_page.return_value = {
            "page": {
                "id": 456,
                "title": "New Page",
                "path": "docs/new-page"
            }
        }
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        result = await server.server._handlers["call_tool"](
            "wiki_create_page", 
            {
                "path": "docs/new-page",
                "title": "New Page", 
                "content": "# New Page\n\nContent",
                "description": "A new page",
                "tags": ["test"]
            }
        )
        
        assert len(result) == 1
        response_text = result[0].text
        assert "✅ Successfully created page" in response_text
        assert "New Page" in response_text
        assert "456" in response_text
        
        mock_client.create_page.assert_called_with(
            path="docs/new-page",
            title="New Page",
            content="# New Page\n\nContent",
            description="A new page",
            tags=["test"]
        )
    
    @patch('wikijs_mcp.server.WikiJSConfig.load_config')
    @patch('wikijs_mcp.server.WikiJSClient')
    async def test_wiki_update_page_success(self, mock_client_class, mock_load_config, mock_wiki_config):
        """Test successful page update."""
        mock_load_config.return_value = mock_wiki_config
        server = WikiJSMCPServer()
        
        mock_client = AsyncMock()
        mock_client.update_page.return_value = {
            "page": {
                "id": 123,
                "title": "Updated Page",
                "path": "docs/updated",
                "updatedAt": "2024-01-01T12:00:00Z"
            }
        }
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        result = await server.server._handlers["call_tool"](
            "wiki_update_page", 
            {
                "id": 123,
                "content": "# Updated Content",
                "title": "Updated Page"
            }
        )
        
        assert len(result) == 1
        response_text = result[0].text
        assert "✅ Successfully updated page" in response_text
        assert "Updated Page" in response_text
        
        mock_client.update_page.assert_called_with(
            page_id=123,
            content="# Updated Content",
            title="Updated Page",
            description=None,
            tags=None
        )
    
    @patch('wikijs_mcp.server.WikiJSConfig.load_config')
    @patch('wikijs_mcp.server.WikiJSClient')
    async def test_tool_call_exception_handling(self, mock_client_class, mock_load_config, mock_wiki_config):
        """Test that tool call exceptions are handled gracefully."""
        mock_load_config.return_value = mock_wiki_config
        server = WikiJSMCPServer()
        
        mock_client = AsyncMock()
        mock_client.search_pages.side_effect = Exception("API Error")
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        result = await server.server._handlers["call_tool"]("wiki_search", {"query": "test"})
        
        assert len(result) == 1
        assert "Error: API Error" in result[0].text
    
    @patch('wikijs_mcp.server.WikiJSConfig.load_config')
    async def test_unknown_tool_call(self, mock_load_config, mock_wiki_config):
        """Test calling unknown tool."""
        mock_load_config.return_value = mock_wiki_config
        server = WikiJSMCPServer()
        
        result = await server.server._handlers["call_tool"]("unknown_tool", {})
        
        assert len(result) == 1
        assert "Unknown tool: unknown_tool" in result[0].text
    
    @patch('wikijs_mcp.server.WikiJSConfig.load_config')
    async def test_run_with_valid_config(self, mock_load_config, mock_wiki_config):
        """Test running server with valid configuration."""
        mock_load_config.return_value = mock_wiki_config
        server = WikiJSMCPServer()
        
        with patch.object(server.server, 'run', new_callable=AsyncMock) as mock_run:
            await server.run()
            mock_run.assert_called_once()
    
    @patch('wikijs_mcp.server.WikiJSConfig.load_config')
    async def test_run_with_invalid_config(self, mock_load_config):
        """Test running server with invalid configuration."""
        invalid_config = Mock()
        invalid_config.validate_config.side_effect = ValueError("Invalid config")
        mock_load_config.return_value = invalid_config
        
        server = WikiJSMCPServer()
        
        with pytest.raises(ValueError, match="Invalid config"):
            await server.run()
    
    @pytest.mark.parametrize("tool_name,args,client_method", [
        ("wiki_search", {"query": "test", "limit": 5}, "search_pages"),
        ("wiki_get_page", {"path": "docs/test"}, "get_page_by_path"),
        ("wiki_get_page", {"id": 123}, "get_page_by_id"),
        ("wiki_list_pages", {"limit": 25, "offset": 10}, "list_pages"),
        ("wiki_get_tree", {"parent_path": "docs"}, "get_page_tree"),
    ])
    @patch('wikijs_mcp.server.WikiJSConfig.load_config')
    @patch('wikijs_mcp.server.WikiJSClient')
    async def test_tool_parameter_passing(self, mock_client_class, mock_load_config, 
                                        tool_name, args, client_method, mock_wiki_config):
        """Test that tool parameters are correctly passed to client methods."""
        mock_load_config.return_value = mock_wiki_config
        server = WikiJSMCPServer()
        
        mock_client = AsyncMock()
        # Set up return values to avoid errors
        getattr(mock_client, client_method).return_value = [] if client_method in ["search_pages", "list_pages", "get_page_tree"] else None
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        await server.server._handlers["call_tool"](tool_name, args)
        
        # Verify the client method was called
        getattr(mock_client, client_method).assert_called_once()