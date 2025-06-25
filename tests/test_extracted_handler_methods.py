"""Tests for extracted handler methods."""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from wikijs_mcp.server import WikiJSMCPServer


class TestExtractedHandlerMethods:
    """Test cases for extracted handler methods."""
    
    @patch('wikijs_mcp.server.WikiJSConfig.load_config')
    async def test_handle_wiki_search_with_results(self, mock_load_config, mock_wiki_config):
        """Test _handle_wiki_search with results."""
        mock_load_config.return_value = mock_wiki_config
        server = WikiJSMCPServer()
        
        # Mock client
        mock_client = AsyncMock()
        mock_client.search_pages = AsyncMock(return_value=[
            {
                'title': 'Test Page',
                'path': '/test-page',
                'description': 'A test page',
                'updatedAt': '2024-01-01'
            },
            {
                'title': 'Another Page',
                'path': '/another-page',
                'updatedAt': '2024-01-02'
            }
        ])
        
        arguments = {"query": "test", "limit": 5}
        response = await server._handle_wiki_search(mock_client, arguments)
        
        assert "Found 2 pages for query 'test':" in response
        assert "**Test Page**" in response
        assert "**Another Page**" in response
        assert "/test-page" in response
        assert "A test page" in response
        mock_client.search_pages.assert_called_once_with("test", 5)
    
    @patch('wikijs_mcp.server.WikiJSConfig.load_config')
    async def test_handle_wiki_search_no_results(self, mock_load_config, mock_wiki_config):
        """Test _handle_wiki_search with no results."""
        mock_load_config.return_value = mock_wiki_config
        server = WikiJSMCPServer()
        
        mock_client = AsyncMock()
        mock_client.search_pages = AsyncMock(return_value=[])
        
        arguments = {"query": "nonexistent"}
        response = await server._handle_wiki_search(mock_client, arguments)
        
        assert response == "No pages found for query: nonexistent"
        mock_client.search_pages.assert_called_once_with("nonexistent", 10)  # default limit
    
    @patch('wikijs_mcp.server.WikiJSConfig.load_config')
    async def test_handle_wiki_get_page_by_path(self, mock_load_config, mock_wiki_config):
        """Test _handle_wiki_get_page by path."""
        mock_load_config.return_value = mock_wiki_config
        server = WikiJSMCPServer()
        
        mock_client = AsyncMock()
        page_data = {
            'id': '123',
            'title': 'Test Page',
            'path': '/test-page',
            'content': 'Page content here',
            'description': 'Test description',
            'editor': 'markdown',
            'locale': 'en',
            'author': {'name': 'Test Author'},
            'createdAt': '2024-01-01',
            'updatedAt': '2024-01-02',
            'tags': [{'tag': 'test'}, {'tag': 'example'}]
        }
        mock_client.get_page_by_path = AsyncMock(return_value=page_data)
        
        arguments = {"path": "/test-page"}
        response = await server._handle_wiki_get_page(mock_client, arguments)
        
        assert "# Test Page" in response
        assert "**Path:** /test-page" in response
        assert "**ID:** 123" in response
        assert "**Description:** Test description" in response
        assert "**Editor:** markdown" in response
        assert "**Locale:** en" in response
        assert "**Author:** Test Author" in response
        assert "**Tags:** test, example" in response
        assert "Page content here" in response
        mock_client.get_page_by_path.assert_called_once_with("/test-page")
    
    @patch('wikijs_mcp.server.WikiJSConfig.load_config')
    async def test_handle_wiki_get_page_by_id(self, mock_load_config, mock_wiki_config):
        """Test _handle_wiki_get_page by ID."""
        mock_load_config.return_value = mock_wiki_config
        server = WikiJSMCPServer()
        
        mock_client = AsyncMock()
        page_data = {
            'id': '456',
            'title': 'Test Page by ID',
            'path': '/test-by-id',
            'content': 'Content by ID',
            'createdAt': '2024-01-01',
            'updatedAt': '2024-01-02'
        }
        mock_client.get_page_by_id = AsyncMock(return_value=page_data)
        
        arguments = {"id": "456"}
        response = await server._handle_wiki_get_page(mock_client, arguments)
        
        assert "# Test Page by ID" in response
        assert "**ID:** 456" in response
        assert "Content by ID" in response
        mock_client.get_page_by_id.assert_called_once_with("456")
    
    @patch('wikijs_mcp.server.WikiJSConfig.load_config')
    async def test_handle_wiki_get_page_not_found(self, mock_load_config, mock_wiki_config):
        """Test _handle_wiki_get_page when page not found."""
        mock_load_config.return_value = mock_wiki_config
        server = WikiJSMCPServer()
        
        mock_client = AsyncMock()
        mock_client.get_page_by_path = AsyncMock(return_value=None)
        
        arguments = {"path": "/nonexistent"}
        response = await server._handle_wiki_get_page(mock_client, arguments)
        
        assert response == "Page not found"
    
    @patch('wikijs_mcp.server.WikiJSConfig.load_config')
    async def test_handle_wiki_list_pages(self, mock_load_config, mock_wiki_config):
        """Test _handle_wiki_list_pages."""
        mock_load_config.return_value = mock_wiki_config
        server = WikiJSMCPServer()
        
        mock_client = AsyncMock()
        pages_data = [
            {
                'id': '1',
                'title': 'Page 1',
                'path': '/page1',
                'description': 'First page',
                'updatedAt': '2024-01-01'
            },
            {
                'id': '2',
                'title': 'Page 2',
                'path': '/page2',
                'updatedAt': '2024-01-02'
            }
        ]
        mock_client.list_pages = AsyncMock(return_value=pages_data)
        
        arguments = {"limit": 10}
        response = await server._handle_wiki_list_pages(mock_client, arguments)
        
        assert "Found 2 pages (limit: 10):" in response
        assert "**Page 1**" in response
        assert "**Page 2**" in response
        assert "Path: /page1 (ID: 1)" in response
        assert "Description: First page" in response
        # Author field removed - not supported by Wiki.js API
        mock_client.list_pages.assert_called_once_with(10)
    
    @patch('wikijs_mcp.server.WikiJSConfig.load_config')
    async def test_handle_wiki_list_pages_no_results(self, mock_load_config, mock_wiki_config):
        """Test _handle_wiki_list_pages with no results."""
        mock_load_config.return_value = mock_wiki_config
        server = WikiJSMCPServer()
        
        mock_client = AsyncMock()
        mock_client.list_pages = AsyncMock(return_value=[])
        
        arguments = {}
        response = await server._handle_wiki_list_pages(mock_client, arguments)
        
        assert response == "No pages found"
        mock_client.list_pages.assert_called_once_with(50)  # default
    
    @patch('wikijs_mcp.server.WikiJSConfig.load_config')
    async def test_handle_wiki_get_tree(self, mock_load_config, mock_wiki_config):
        """Test _handle_wiki_get_tree."""
        mock_load_config.return_value = mock_wiki_config
        server = WikiJSMCPServer()
        
        mock_client = AsyncMock()
        tree_data = [
            {'title': 'Root Folder', 'isFolder': True, 'depth': 0},
            {'title': 'Sub Folder', 'isFolder': True, 'depth': 1},
            {'title': 'Page 1', 'path': '/page1', 'isFolder': False, 'depth': 1},
            {'title': 'Deep Page', 'path': '/deep/page', 'depth': 2}  # Missing isFolder
        ]
        mock_client.get_page_tree = AsyncMock(return_value=tree_data)
        
        arguments = {"parent_path": "/docs"}
        response = await server._handle_wiki_get_tree(mock_client, arguments)
        
        assert "Wiki page tree from '/docs':" in response
        assert "📁 Root Folder/" in response
        assert "  📁 Sub Folder/" in response
        assert "  📄 Page 1 (/page1)" in response
        assert "    📄 Deep Page (/deep/page)" in response
        mock_client.get_page_tree.assert_called_once_with("/docs")
    
    @patch('wikijs_mcp.server.WikiJSConfig.load_config')
    async def test_handle_wiki_get_tree_no_results(self, mock_load_config, mock_wiki_config):
        """Test _handle_wiki_get_tree with no results."""
        mock_load_config.return_value = mock_wiki_config
        server = WikiJSMCPServer()
        
        mock_client = AsyncMock()
        mock_client.get_page_tree = AsyncMock(return_value=[])
        
        arguments = {}
        response = await server._handle_wiki_get_tree(mock_client, arguments)
        
        assert response == "No pages found in tree"
        mock_client.get_page_tree.assert_called_once_with("")  # default
    
    @patch('wikijs_mcp.server.WikiJSConfig.load_config')
    async def test_handle_wiki_create_page(self, mock_load_config, mock_wiki_config):
        """Test _handle_wiki_create_page."""
        mock_load_config.return_value = mock_wiki_config
        server = WikiJSMCPServer()
        
        mock_client = AsyncMock()
        create_result = {
            'page': {
                'id': '789',
                'title': 'New Page',
                'path': '/new-page'
            }
        }
        mock_client.create_page = AsyncMock(return_value=create_result)
        
        arguments = {
            "path": "/new-page",
            "title": "New Page",
            "content": "New content",
            "description": "New description",
            "tags": ["new", "test"]
        }
        response = await server._handle_wiki_create_page(mock_client, arguments)
        
        assert "✅ Successfully created page:" in response
        assert "**Title:** New Page" in response
        assert "**Path:** /new-page" in response
        assert "**ID:** 789" in response
        mock_client.create_page.assert_called_once_with(
            path="/new-page",
            title="New Page",
            content="New content",
            description="New description",
            tags=["new", "test"]
        )
    
    @patch('wikijs_mcp.server.WikiJSConfig.load_config')
    async def test_handle_wiki_update_page(self, mock_load_config, mock_wiki_config):
        """Test _handle_wiki_update_page."""
        mock_load_config.return_value = mock_wiki_config
        server = WikiJSMCPServer()
        
        mock_client = AsyncMock()
        update_result = {
            'page': {
                'id': '123',
                'title': 'Updated Page',
                'path': '/updated-page',
                'updatedAt': '2024-01-03T10:00:00Z'
            }
        }
        mock_client.update_page = AsyncMock(return_value=update_result)
        
        arguments = {
            "id": "123",
            "content": "Updated content",
            "title": "Updated Page",
            "description": "Updated description",
            "tags": ["updated"]
        }
        response = await server._handle_wiki_update_page(mock_client, arguments)
        
        assert "✅ Successfully updated page:" in response
        assert "**Title:** Updated Page" in response
        assert "**Path:** /updated-page" in response
        assert "**ID:** 123" in response
        assert "**Updated:** 2024-01-03T10:00:00Z" in response
        mock_client.update_page.assert_called_once_with(
            page_id="123",
            content="Updated content",
            title="Updated Page",
            description="Updated description",
            tags=["updated"]
        )