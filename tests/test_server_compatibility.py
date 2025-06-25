"""Tests for MCP server compatibility with Wiki.js responses."""

import pytest
from unittest.mock import AsyncMock, Mock
import inspect
from wikijs_mcp.server import WikiJSMCPServer
from wikijs_mcp.client import WikiJSClient


@pytest.mark.unit
class TestServerCompatibility:
    """Test cases for ensuring MCP server handles Wiki.js responses correctly."""
    
    async def test_handle_list_pages_without_author(self):
        """Test that _handle_wiki_list_pages doesn't expect author field."""
        server = WikiJSMCPServer()
        mock_client = Mock(spec=WikiJSClient)
        
        # Simulate Wiki.js response without author field
        pages_data = [
            {
                "id": 1,
                "path": "home",
                "title": "Home Page",
                "description": "Welcome page",
                "updatedAt": "2024-01-01T00:00:00Z",
                "createdAt": "2024-01-01T00:00:00Z",
                "locale": "en"
                # No author field
            },
            {
                "id": 2,
                "path": "docs/guide",
                "title": "User Guide",
                "description": None,  # No description
                "updatedAt": "2024-01-02T00:00:00Z",
                "createdAt": "2024-01-01T00:00:00Z",
                "locale": "en"
            }
        ]
        
        mock_client.list_pages = AsyncMock(return_value=pages_data)
        
        # Call the handler
        result = await server._handle_wiki_list_pages(mock_client, {"limit": 10})
        
        # Verify the response format
        assert "Found 2 pages" in result
        assert "Home Page" in result
        assert "User Guide" in result
        assert "Path: home (ID: 1)" in result
        assert "Description: Welcome page" in result
        
        # Ensure no author reference in output
        assert "Author:" not in result
        assert "Unknown" not in result
        
        # Verify limit is shown correctly (no offset)
        assert "(limit: 10)" in result
        assert "offset" not in result
    
    async def test_handle_list_pages_empty_response(self):
        """Test handling empty page list."""
        server = WikiJSMCPServer()
        mock_client = Mock(spec=WikiJSClient)
        
        mock_client.list_pages = AsyncMock(return_value=[])
        
        result = await server._handle_wiki_list_pages(mock_client, {})
        
        assert result == "No pages found"
    
    async def test_handle_list_pages_with_missing_fields(self):
        """Test handling pages with missing optional fields."""
        server = WikiJSMCPServer()
        mock_client = Mock(spec=WikiJSClient)
        
        # Minimal page data
        pages_data = [
            {
                "id": 3,
                "path": "minimal",
                "title": "Minimal Page",
                # No description, dates, or other fields
                "updatedAt": "2024-01-01T00:00:00Z"
            }
        ]
        
        mock_client.list_pages = AsyncMock(return_value=pages_data)
        
        result = await server._handle_wiki_list_pages(mock_client, {"limit": 50})
        
        # Should handle missing fields gracefully
        assert "Minimal Page" in result
        assert "Path: minimal (ID: 3)" in result
        assert "Updated: 2024-01-01T00:00:00Z" in result
        
        # Should not show description line if not present
        assert "Description: None" not in result
    
    async def test_tool_schema_compatibility(self):
        """Test that tool schemas match Wiki.js API capabilities."""
        server = WikiJSMCPServer()
        
        # Find the registered handler for list_tools
        list_tools_handler = None
        for handler_name in ['list_tools', 'handle_list_tools']:
            if hasattr(server, handler_name):
                list_tools_handler = getattr(server, handler_name)
                break
        
        # If not found, try through the decorated methods
        if list_tools_handler is None:
            # The handler is registered via decorator, we need to call it directly
            import inspect
            for name, method in inspect.getmembers(server):
                if name == 'handle_list_tools' or (hasattr(method, '__name__') and method.__name__ == 'handle_list_tools'):
                    list_tools_handler = method
                    break
        
        # As a fallback, we can test the tool definition directly by looking at the code
        # Since we know the tool is defined in _setup_handlers
        
        # Mock check - the list_pages tool should not have offset
        # We'll verify this by checking the actual server code was updated
        source = inspect.getsource(server._setup_handlers)
        
        # Simple text check for the updated schema
        assert '"offset"' not in source  # offset should not be in the schema
        assert 'List all pages with pagination' not in source  # description should be updated
    
    async def test_handle_search_response_format(self):
        """Test search response formatting."""
        server = WikiJSMCPServer()
        mock_client = Mock(spec=WikiJSClient)
        
        search_results = [
            {
                "id": 1,
                "path": "docs/api",
                "title": "API Documentation",
                "description": "REST API reference",
                "updatedAt": "2024-01-01T00:00:00Z",
                "createdAt": "2023-12-01T00:00:00Z"
            }
        ]
        
        mock_client.search_pages = AsyncMock(return_value=search_results)
        
        result = await server._handle_wiki_search(
            mock_client, 
            {"query": "api", "limit": 10}
        )
        
        assert "Found 1 pages for query 'api'" in result
        assert "**API Documentation**" in result
        assert "Path: docs/api" in result
        assert "Description: REST API reference" in result
    
    async def test_error_handling_compatibility(self):
        """Test error handling for Wiki.js specific errors."""
        server = WikiJSMCPServer()
        mock_client = Mock(spec=WikiJSClient)
        
        # Simulate GraphQL validation error
        mock_client.list_pages = AsyncMock(
            side_effect=Exception("GraphQL query failed: Unknown argument")
        )
        
        # The _handle_wiki_list_pages will raise the exception
        # In real usage, this would be caught in handle_call_tool
        with pytest.raises(Exception, match="GraphQL query failed"):
            await server._handle_wiki_list_pages(mock_client, {"limit": 10})