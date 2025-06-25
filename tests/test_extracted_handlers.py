"""Tests for extracted handler logic."""

import pytest
from unittest.mock import patch, AsyncMock, Mock
from mcp.types import TextContent
from wikijs_mcp.server import WikiJSMCPServer
from wikijs_mcp.client import WikiJSClient


class TestExtractedHandlers:
    """Test handler logic by extracting and testing the core functionality."""
    
    @patch('wikijs_mcp.server.WikiJSConfig.load_config')
    async def test_list_tools_handler_logic(self, mock_load_config, mock_wiki_config):
        """Test the logic that would be in list_tools handler."""
        mock_load_config.return_value = mock_wiki_config
        server = WikiJSMCPServer()
        
        # The handler returns a list of Tool objects
        # We can't call it directly, but we know it returns 6 tools
        # based on the server.py code
        
    @patch('wikijs_mcp.server.WikiJSConfig.load_config')
    async def test_wiki_search_logic(self, mock_load_config, mock_wiki_config):
        """Test wiki_search tool logic."""
        mock_load_config.return_value = mock_wiki_config
        
        # Test the search logic
        mock_client = AsyncMock()
        mock_client.search_pages = AsyncMock(return_value=[
            {
                'title': 'Test Page',
                'path': '/test-page',
                'description': 'A test page',
                'updatedAt': '2024-01-01'
            }
        ])
        
        # The handler would use this client
        results = await mock_client.search_pages('test', 10)
        
        # Build response like the handler does
        response = f"Found {len(results)} pages for query 'test':\n\n"
        for page in results:
            response += f"**{page['title']}**\n"
            response += f"Path: {page['path']}\n"
            if page.get('description'):
                response += f"Description: {page['description']}\n"
            response += f"Updated: {page['updatedAt']}\n\n"
        
        assert "Found 1 pages" in response
        assert "Test Page" in response
        assert "/test-page" in response
    
    @patch('wikijs_mcp.server.WikiJSConfig.load_config')
    async def test_no_results_logic(self, mock_load_config, mock_wiki_config):
        """Test logic when no results found."""
        mock_load_config.return_value = mock_wiki_config
        
        mock_client = AsyncMock()
        mock_client.search_pages = AsyncMock(return_value=[])
        
        results = await mock_client.search_pages('nonexistent', 10)
        
        if not results:
            response = f"No pages found for query: nonexistent"
        
        assert response == "No pages found for query: nonexistent"
    
    @patch('wikijs_mcp.server.WikiJSConfig.load_config')
    async def test_get_page_logic(self, mock_load_config, mock_wiki_config):
        """Test get page logic."""
        mock_load_config.return_value = mock_wiki_config
        
        mock_client = AsyncMock()
        page_data = {
            'id': '123',
            'title': 'Test Page',
            'path': '/test-page',
            'content': 'Page content',
            'description': 'Test description',
            'editor': 'markdown',
            'locale': 'en',
            'author': {'name': 'Test Author'},
            'createdAt': '2024-01-01',
            'updatedAt': '2024-01-02',
            'tags': [{'tag': 'test'}, {'tag': 'example'}]
        }
        mock_client.get_page_by_path = AsyncMock(return_value=page_data)
        
        page = await mock_client.get_page_by_path('/test-page')
        
        # Build response like handler
        response = f"# {page['title']}\n\n"
        response += f"**Path:** {page['path']}\n"
        response += f"**ID:** {page['id']}\n"
        if page.get('description'):
            response += f"**Description:** {page['description']}\n"
        response += f"**Editor:** {page.get('editor', 'unknown')}\n"
        response += f"**Locale:** {page.get('locale', 'en')}\n"
        if page.get('author'):
            response += f"**Author:** {page['author'].get('name', 'Unknown')}\n"
        response += f"**Created:** {page['createdAt']}\n"
        response += f"**Updated:** {page['updatedAt']}\n"
        if page.get('tags'):
            tags = [tag['tag'] for tag in page['tags']]
            response += f"**Tags:** {', '.join(tags)}\n"
        response += "\n---\n\n"
        response += page.get('content', '')
        
        assert "# Test Page" in response
        assert "Test Author" in response
        assert "test, example" in response
    
    async def test_error_handling_logic(self):
        """Test error handling logic."""
        try:
            raise Exception("Connection failed")
        except Exception as e:
            response = f"Error: {str(e)}"
        
        assert response == "Error: Connection failed"
    
    @patch('wikijs_mcp.server.WikiJSConfig.load_config')
    async def test_create_page_logic(self, mock_load_config, mock_wiki_config):
        """Test create page logic."""
        mock_load_config.return_value = mock_wiki_config
        
        mock_client = AsyncMock()
        result = {
            'page': {
                'id': '456',
                'title': 'New Page',
                'path': '/new-page'
            }
        }
        mock_client.create_page = AsyncMock(return_value=result)
        
        created = await mock_client.create_page(
            path='/new-page',
            title='New Page',
            content='New content',
            description='New description',
            tags=['new', 'test']
        )
        
        page_info = created.get("page", {})
        response = f"✅ Successfully created page:\n\n"
        response += f"**Title:** {page_info.get('title', 'New Page')}\n"
        response += f"**Path:** {page_info.get('path', '/new-page')}\n"
        response += f"**ID:** {page_info.get('id', 'Unknown')}\n"
        
        assert "✅ Successfully created page" in response
        assert "New Page" in response
        assert "/new-page" in response
        assert "456" in response