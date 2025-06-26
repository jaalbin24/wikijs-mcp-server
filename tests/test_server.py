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

    @patch('wikijs_mcp.server.WikiJSConfig.load_config')
    @patch('wikijs_mcp.server.WikiJSClient')
    async def test_call_tool_search_no_results(self, mock_client_class, mock_load_config, mock_wiki_config):
        """Test calling search tool with no results."""
        mock_load_config.return_value = mock_wiki_config
        mock_client_instance = AsyncMock()
        mock_client_instance.__aenter__.return_value = mock_client_instance
        mock_client_instance.__aexit__.return_value = None
        mock_client_instance.search_pages.return_value = []
        mock_client_class.return_value = mock_client_instance
        
        server = WikiJSMCPServer()
        
        result = await server.app.call_tool("wiki_search", {"query": "nonexistent", "limit": 10})
        assert len(result) == 1
        assert "No pages found for query: nonexistent" in result[0].text

    @patch('wikijs_mcp.server.WikiJSConfig.load_config')
    @patch('wikijs_mcp.server.WikiJSClient')
    async def test_call_tool_search_with_description(self, mock_client_class, mock_load_config, mock_wiki_config):
        """Test calling search tool with page description."""
        mock_load_config.return_value = mock_wiki_config
        mock_client_instance = AsyncMock()
        mock_client_instance.__aenter__.return_value = mock_client_instance
        mock_client_instance.__aexit__.return_value = None
        mock_client_instance.search_pages.return_value = [
            {"title": "Test Page", "path": "/test", "description": "Test description", "updatedAt": "2023-01-01"}
        ]
        mock_client_class.return_value = mock_client_instance
        
        server = WikiJSMCPServer()
        
        result = await server.app.call_tool("wiki_search", {"query": "test", "limit": 10})
        assert len(result) == 1
        assert "Test description" in result[0].text

    @patch('wikijs_mcp.server.WikiJSConfig.load_config')
    @patch('wikijs_mcp.server.WikiJSClient')
    async def test_call_tool_get_page_by_path(self, mock_client_class, mock_load_config, mock_wiki_config):
        """Test calling get_page tool with path."""
        mock_load_config.return_value = mock_wiki_config
        mock_client_instance = AsyncMock()
        mock_client_instance.__aenter__.return_value = mock_client_instance
        mock_client_instance.__aexit__.return_value = None
        mock_client_instance.get_page_by_path.return_value = {
            "id": 1, "title": "Test Page", "path": "/test", "content": "Test content",
            "createdAt": "2023-01-01", "updatedAt": "2023-01-02"
        }
        mock_client_class.return_value = mock_client_instance
        
        server = WikiJSMCPServer()
        
        result = await server.app.call_tool("wiki_get_page", {"path": "/test"})
        assert len(result) == 1
        assert "Test Page" in result[0].text
        assert "Test content" in result[0].text

    @patch('wikijs_mcp.server.WikiJSConfig.load_config')
    @patch('wikijs_mcp.server.WikiJSClient')
    async def test_call_tool_get_page_by_id(self, mock_client_class, mock_load_config, mock_wiki_config):
        """Test calling get_page tool with ID."""
        mock_load_config.return_value = mock_wiki_config
        mock_client_instance = AsyncMock()
        mock_client_instance.__aenter__.return_value = mock_client_instance
        mock_client_instance.__aexit__.return_value = None
        mock_client_instance.get_page_by_id.return_value = {
            "id": 1, "title": "Test Page", "path": "/test", "content": "Test content",
            "createdAt": "2023-01-01", "updatedAt": "2023-01-02"
        }
        mock_client_class.return_value = mock_client_instance
        
        server = WikiJSMCPServer()
        
        result = await server.app.call_tool("wiki_get_page", {"id": 1})
        assert len(result) == 1
        assert "Test Page" in result[0].text
        assert "Test content" in result[0].text

    @patch('wikijs_mcp.server.WikiJSConfig.load_config')
    @patch('wikijs_mcp.server.WikiJSClient')
    async def test_call_tool_get_page_not_found(self, mock_client_class, mock_load_config, mock_wiki_config):
        """Test calling get_page tool with non-existent page."""
        mock_load_config.return_value = mock_wiki_config
        mock_client_instance = AsyncMock()
        mock_client_instance.__aenter__.return_value = mock_client_instance
        mock_client_instance.__aexit__.return_value = None
        mock_client_instance.get_page_by_path.return_value = None
        mock_client_class.return_value = mock_client_instance
        
        server = WikiJSMCPServer()
        
        result = await server.app.call_tool("wiki_get_page", {"path": "/nonexistent"})
        assert len(result) == 1
        assert "Page not found" in result[0].text

    @patch('wikijs_mcp.server.WikiJSConfig.load_config')
    @patch('wikijs_mcp.server.WikiJSClient')
    async def test_call_tool_get_page_validation_errors(self, mock_client_class, mock_load_config, mock_wiki_config):
        """Test get_page tool validation errors."""
        from mcp.server.fastmcp.exceptions import ToolError
        
        mock_load_config.return_value = mock_wiki_config
        server = WikiJSMCPServer()
        
        # Test no parameters
        with pytest.raises(ToolError, match="Either 'path' or 'id' parameter is required"):
            await server.app.call_tool("wiki_get_page", {})
        
        # Test both parameters
        with pytest.raises(ToolError, match="Cannot specify both 'path' and 'id' parameters"):
            await server.app.call_tool("wiki_get_page", {"path": "/test", "id": 1})

    @patch('wikijs_mcp.server.WikiJSConfig.load_config')
    @patch('wikijs_mcp.server.WikiJSClient')
    async def test_call_tool_get_page_with_metadata(self, mock_client_class, mock_load_config, mock_wiki_config):
        """Test get_page tool with full metadata."""
        mock_load_config.return_value = mock_wiki_config
        mock_client_instance = AsyncMock()
        mock_client_instance.__aenter__.return_value = mock_client_instance
        mock_client_instance.__aexit__.return_value = None
        mock_client_instance.get_page_by_path.return_value = {
            "id": 1, "title": "Test Page", "path": "/test", "content": "Test content",
            "description": "Test description", "editor": "markdown", "locale": "en",
            "author": {"name": "Test Author"}, "tags": [{"tag": "test"}, {"tag": "example"}],
            "createdAt": "2023-01-01", "updatedAt": "2023-01-02"
        }
        mock_client_class.return_value = mock_client_instance
        
        server = WikiJSMCPServer()
        
        result = await server.app.call_tool("wiki_get_page", {"path": "/test"})
        assert len(result) == 1
        assert "Test description" in result[0].text
        assert "Test Author" in result[0].text
        assert "test, example" in result[0].text

    @patch('wikijs_mcp.server.WikiJSConfig.load_config')
    @patch('wikijs_mcp.server.WikiJSClient')
    async def test_call_tool_list_pages(self, mock_client_class, mock_load_config, mock_wiki_config):
        """Test calling list_pages tool."""
        mock_load_config.return_value = mock_wiki_config
        mock_client_instance = AsyncMock()
        mock_client_instance.__aenter__.return_value = mock_client_instance
        mock_client_instance.__aexit__.return_value = None
        mock_client_instance.list_pages.return_value = [
            {"id": 1, "title": "Test Page", "path": "/test", "updatedAt": "2023-01-01"}
        ]
        mock_client_class.return_value = mock_client_instance
        
        server = WikiJSMCPServer()
        
        result = await server.app.call_tool("wiki_list_pages", {"limit": 50})
        assert len(result) == 1
        assert "Found 1 pages" in result[0].text
        assert "Test Page" in result[0].text

    @patch('wikijs_mcp.server.WikiJSConfig.load_config')
    @patch('wikijs_mcp.server.WikiJSClient')
    async def test_call_tool_list_pages_no_results(self, mock_client_class, mock_load_config, mock_wiki_config):
        """Test calling list_pages tool with no results."""
        mock_load_config.return_value = mock_wiki_config
        mock_client_instance = AsyncMock()
        mock_client_instance.__aenter__.return_value = mock_client_instance
        mock_client_instance.__aexit__.return_value = None
        mock_client_instance.list_pages.return_value = []
        mock_client_class.return_value = mock_client_instance
        
        server = WikiJSMCPServer()
        
        result = await server.app.call_tool("wiki_list_pages", {"limit": 50})
        assert len(result) == 1
        assert "No pages found" in result[0].text

    @patch('wikijs_mcp.server.WikiJSConfig.load_config')
    @patch('wikijs_mcp.server.WikiJSClient')
    async def test_call_tool_list_pages_with_description(self, mock_client_class, mock_load_config, mock_wiki_config):
        """Test calling list_pages tool with page description."""
        mock_load_config.return_value = mock_wiki_config
        mock_client_instance = AsyncMock()
        mock_client_instance.__aenter__.return_value = mock_client_instance
        mock_client_instance.__aexit__.return_value = None
        mock_client_instance.list_pages.return_value = [
            {"id": 1, "title": "Test Page", "path": "/test", "description": "Test description", "updatedAt": "2023-01-01"}
        ]
        mock_client_class.return_value = mock_client_instance
        
        server = WikiJSMCPServer()
        
        result = await server.app.call_tool("wiki_list_pages", {"limit": 50})
        assert len(result) == 1
        assert "Test description" in result[0].text

    @patch('wikijs_mcp.server.WikiJSConfig.load_config')
    @patch('wikijs_mcp.server.WikiJSClient')
    async def test_call_tool_get_tree(self, mock_client_class, mock_load_config, mock_wiki_config):
        """Test calling get_tree tool."""
        mock_load_config.return_value = mock_wiki_config
        mock_client_instance = AsyncMock()
        mock_client_instance.__aenter__.return_value = mock_client_instance
        mock_client_instance.__aexit__.return_value = None
        mock_client_instance.get_page_tree.return_value = [
            {"title": "Folder", "isFolder": True, "depth": 0},
            {"title": "Page", "path": "/page", "isFolder": False, "depth": 1}
        ]
        mock_client_class.return_value = mock_client_instance
        
        server = WikiJSMCPServer()
        
        result = await server.app.call_tool("wiki_get_tree", {"parent_path": ""})
        assert len(result) == 1
        assert "📁 Folder/" in result[0].text
        assert "📄 Page" in result[0].text

    @patch('wikijs_mcp.server.WikiJSConfig.load_config')
    @patch('wikijs_mcp.server.WikiJSClient')
    async def test_call_tool_get_tree_no_results(self, mock_client_class, mock_load_config, mock_wiki_config):
        """Test calling get_tree tool with no results."""
        mock_load_config.return_value = mock_wiki_config
        mock_client_instance = AsyncMock()
        mock_client_instance.__aenter__.return_value = mock_client_instance
        mock_client_instance.__aexit__.return_value = None
        mock_client_instance.get_page_tree.return_value = []
        mock_client_class.return_value = mock_client_instance
        
        server = WikiJSMCPServer()
        
        result = await server.app.call_tool("wiki_get_tree", {"parent_path": ""})
        assert len(result) == 1
        assert "No pages found in tree" in result[0].text

    @patch('wikijs_mcp.server.WikiJSConfig.load_config')
    @patch('wikijs_mcp.server.WikiJSClient')
    async def test_call_tool_create_page(self, mock_client_class, mock_load_config, mock_wiki_config):
        """Test calling create_page tool."""
        mock_load_config.return_value = mock_wiki_config
        mock_client_instance = AsyncMock()
        mock_client_instance.__aenter__.return_value = mock_client_instance
        mock_client_instance.__aexit__.return_value = None
        mock_client_instance.create_page.return_value = {
            "page": {"id": 1, "title": "New Page", "path": "/new"}
        }
        mock_client_class.return_value = mock_client_instance
        
        server = WikiJSMCPServer()
        
        result = await server.app.call_tool("wiki_create_page", {
            "path": "/new", "title": "New Page", "content": "New content"
        })
        assert len(result) == 1
        assert "Successfully created page" in result[0].text
        assert "New Page" in result[0].text

    @patch('wikijs_mcp.server.WikiJSConfig.load_config')
    @patch('wikijs_mcp.server.WikiJSClient')
    async def test_call_tool_create_page_with_tags(self, mock_client_class, mock_load_config, mock_wiki_config):
        """Test calling create_page tool with tags."""
        mock_load_config.return_value = mock_wiki_config
        mock_client_instance = AsyncMock()
        mock_client_instance.__aenter__.return_value = mock_client_instance
        mock_client_instance.__aexit__.return_value = None
        mock_client_instance.create_page.return_value = {
            "page": {"id": 1, "title": "New Page", "path": "/new"}
        }
        mock_client_class.return_value = mock_client_instance
        
        server = WikiJSMCPServer()
        
        result = await server.app.call_tool("wiki_create_page", {
            "path": "/new", "title": "New Page", "content": "New content", 
            "description": "Test description", "tags": ["test", "example"]
        })
        assert len(result) == 1
        assert "Successfully created page" in result[0].text
        mock_client_instance.create_page.assert_called_once_with(
            path="/new", title="New Page", content="New content", 
            description="Test description", tags=["test", "example"]
        )

    @patch('wikijs_mcp.server.WikiJSConfig.load_config')
    @patch('wikijs_mcp.server.WikiJSClient')
    async def test_call_tool_update_page(self, mock_client_class, mock_load_config, mock_wiki_config):
        """Test calling update_page tool."""
        mock_load_config.return_value = mock_wiki_config
        mock_client_instance = AsyncMock()
        mock_client_instance.__aenter__.return_value = mock_client_instance
        mock_client_instance.__aexit__.return_value = None
        mock_client_instance.update_page.return_value = {
            "page": {"id": 1, "title": "Updated Page", "path": "/updated", "updatedAt": "2023-01-02"}
        }
        mock_client_class.return_value = mock_client_instance
        
        server = WikiJSMCPServer()
        
        result = await server.app.call_tool("wiki_update_page", {
            "id": 1, "content": "Updated content"
        })
        assert len(result) == 1
        assert "Successfully updated page" in result[0].text
        assert "Updated Page" in result[0].text

    @patch('wikijs_mcp.server.WikiJSConfig.load_config')
    @patch('wikijs_mcp.server.WikiJSClient')
    async def test_call_tool_update_page_with_metadata(self, mock_client_class, mock_load_config, mock_wiki_config):
        """Test calling update_page tool with metadata."""
        mock_load_config.return_value = mock_wiki_config
        mock_client_instance = AsyncMock()
        mock_client_instance.__aenter__.return_value = mock_client_instance
        mock_client_instance.__aexit__.return_value = None
        mock_client_instance.update_page.return_value = {
            "page": {"id": 1, "title": "Updated Page", "path": "/updated", "updatedAt": "2023-01-02"}
        }
        mock_client_class.return_value = mock_client_instance
        
        server = WikiJSMCPServer()
        
        result = await server.app.call_tool("wiki_update_page", {
            "id": 1, "content": "Updated content", "title": "New Title", 
            "description": "New description", "tags": ["updated"]
        })
        assert len(result) == 1
        assert "Successfully updated page" in result[0].text
        mock_client_instance.update_page.assert_called_once_with(
            page_id=1, content="Updated content", title="New Title", 
            description="New description", tags=["updated"]
        )

    @patch('wikijs_mcp.server.WikiJSConfig.load_config')
    @patch('wikijs_mcp.config.WikiJSConfig.validate_config')
    async def test_run_stdio(self, mock_validate, mock_load_config, mock_wiki_config):
        """Test run_stdio method."""
        mock_load_config.return_value = mock_wiki_config
        
        server = WikiJSMCPServer()
        
        with patch.object(server.app, 'run_stdio_async') as mock_run:
            await server.run_stdio()
            mock_run.assert_called_once()
            mock_validate.assert_called_once()

    @patch('wikijs_mcp.server.WikiJSConfig.load_config')
    @patch('wikijs_mcp.config.WikiJSConfig.validate_config')
    async def test_run_stdio_validation_error(self, mock_validate, mock_load_config, mock_wiki_config):
        """Test run_stdio method with validation error."""
        mock_load_config.return_value = mock_wiki_config
        mock_validate.side_effect = ValueError("Invalid config")
        
        server = WikiJSMCPServer()
        
        with pytest.raises(ValueError, match="Invalid config"):
            await server.run_stdio()

    @patch('wikijs_mcp.server.WikiJSConfig.load_config')
    @patch('uvicorn.Config')
    @patch('uvicorn.Server')
    @patch('wikijs_mcp.config.WikiJSConfig.validate_config')
    async def test_run_http(self, mock_validate, mock_server_class, mock_config_class, mock_load_config, mock_wiki_config):
        """Test run_http method."""
        mock_load_config.return_value = mock_wiki_config
        mock_wiki_config.http_host = "localhost"
        mock_wiki_config.http_port = 8000
        
        mock_server = AsyncMock()
        mock_server_class.return_value = mock_server
        
        server = WikiJSMCPServer()
        
        await server.run_http()
        
        mock_validate.assert_called_once()
        mock_config_class.assert_called_once()
        mock_server_class.assert_called_once()
        mock_server.serve.assert_called_once()

    @patch('wikijs_mcp.server.WikiJSConfig.load_config')
    @patch('uvicorn.Config')
    @patch('uvicorn.Server')
    async def test_run_http_with_custom_host_port(self, mock_server_class, mock_config_class, mock_load_config, mock_wiki_config):
        """Test run_http method with custom host and port."""
        mock_load_config.return_value = mock_wiki_config
        
        mock_server = AsyncMock()
        mock_server_class.return_value = mock_server
        
        server = WikiJSMCPServer()
        
        await server.run_http(host="0.0.0.0", port=9000)
        
        mock_config_class.assert_called_once()
        config_call = mock_config_class.call_args
        assert config_call[1]["host"] == "0.0.0.0"
        assert config_call[1]["port"] == 9000

    @patch('wikijs_mcp.server.WikiJSConfig.load_config')
    @patch('wikijs_mcp.config.WikiJSConfig.validate_config')
    async def test_run_http_validation_error(self, mock_validate, mock_load_config, mock_wiki_config):
        """Test run_http method with validation error."""
        mock_load_config.return_value = mock_wiki_config
        mock_validate.side_effect = ValueError("Invalid config")
        
        server = WikiJSMCPServer()
        
        with pytest.raises(ValueError, match="Invalid config"):
            await server.run_http()


@pytest.mark.integration
class TestMainFunction:
    """Test cases for main function."""
    
    @patch('wikijs_mcp.server.WikiJSMCPServer')
    @patch('logging.basicConfig')
    @patch('os.getenv')
    @patch('sys.argv', ['server.py'])
    async def test_main_default_http(self, mock_getenv, mock_logging, mock_server_class):
        """Test main function with default HTTP transport."""
        from wikijs_mcp.server import main
        
        mock_getenv.return_value = "http"
        mock_server = AsyncMock()
        mock_server_class.return_value = mock_server
        
        await main()
        
        mock_server.run_http.assert_called_once()
        mock_server.run_stdio.assert_not_called()

    @patch('wikijs_mcp.server.WikiJSMCPServer')
    @patch('logging.basicConfig')
    @patch('os.getenv')
    @patch('sys.argv', ['server.py', '--stdio'])
    async def test_main_stdio_arg(self, mock_getenv, mock_logging, mock_server_class):
        """Test main function with --stdio argument."""
        from wikijs_mcp.server import main
        
        mock_getenv.return_value = "http"
        mock_server = AsyncMock()
        mock_server_class.return_value = mock_server
        
        await main()
        
        mock_server.run_stdio.assert_called_once()
        mock_server.run_http.assert_not_called()

    @patch('wikijs_mcp.server.WikiJSMCPServer')
    @patch('logging.basicConfig')
    @patch('os.getenv')
    @patch('sys.argv', ['server.py', '--http'])
    async def test_main_http_arg(self, mock_getenv, mock_logging, mock_server_class):
        """Test main function with --http argument."""
        from wikijs_mcp.server import main
        
        mock_getenv.return_value = "stdio"
        mock_server = AsyncMock()
        mock_server_class.return_value = mock_server
        
        await main()
        
        mock_server.run_http.assert_called_once()
        mock_server.run_stdio.assert_not_called()

    @patch('wikijs_mcp.server.WikiJSMCPServer')
    @patch('logging.basicConfig')
    @patch('os.getenv')
    @patch('sys.argv', ['server.py', '--help'])
    @patch('builtins.print')
    async def test_main_help_arg(self, mock_print, mock_getenv, mock_logging, mock_server_class):
        """Test main function with --help argument."""
        from wikijs_mcp.server import main
        
        await main()
        
        mock_print.assert_called()
        mock_server_class.assert_called_once()
        
        # Check that help text was printed
        print_calls = [call[0][0] for call in mock_print.call_args_list]
        assert any("WikiJS MCP Server" in call for call in print_calls)
        assert any("Usage:" in call for call in print_calls)

    @patch('wikijs_mcp.server.WikiJSMCPServer')
    @patch('logging.basicConfig')
    @patch('os.getenv')
    @patch('sys.argv', ['server.py'])
    async def test_main_stdio_env(self, mock_getenv, mock_logging, mock_server_class):
        """Test main function with stdio environment variable."""
        from wikijs_mcp.server import main
        
        mock_getenv.return_value = "stdio"
        mock_server = AsyncMock()
        mock_server_class.return_value = mock_server
        
        await main()
        
        mock_server.run_stdio.assert_called_once()
        mock_server.run_http.assert_not_called()
