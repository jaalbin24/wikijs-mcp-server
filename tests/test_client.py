"""Tests for WikiJS GraphQL client."""

import pytest
from unittest.mock import Mock, AsyncMock
import httpx
from wikijs_mcp.client import WikiJSClient
from wikijs_mcp.config import WikiJSConfig


@pytest.mark.unit
class TestWikiJSClient:
    """Test cases for WikiJSClient class."""
    
    def test_init(self, mock_wiki_config):
        """Test WikiJSClient initialization."""
        client = WikiJSClient(mock_wiki_config)
        
        assert client.config == mock_wiki_config
        assert isinstance(client.client, httpx.AsyncClient)
    
    async def test_context_manager(self, mock_wiki_config):
        """Test WikiJSClient as async context manager."""
        async with WikiJSClient(mock_wiki_config) as client:
            assert isinstance(client, WikiJSClient)
    
    async def test_execute_query_success(self, mock_wiki_config, sample_graphql_response):
        """Test successful GraphQL query execution."""
        client = WikiJSClient(mock_wiki_config)
        
        # Mock the HTTP response
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = sample_graphql_response
        
        client.client.post = AsyncMock(return_value=mock_response)
        
        result = await client._execute_query("query { test }")
        
        assert result == sample_graphql_response["data"]
        client.client.post.assert_called_once()
    
    async def test_execute_query_with_variables(self, mock_wiki_config, sample_graphql_response):
        """Test GraphQL query execution with variables."""
        client = WikiJSClient(mock_wiki_config)
        
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = sample_graphql_response
        
        client.client.post = AsyncMock(return_value=mock_response)
        
        variables = {"query": "test", "limit": 10}
        await client._execute_query("query { test }", variables)
        
        # Verify the payload includes variables
        call_args = client.client.post.call_args
        payload = call_args[1]["json"]
        assert payload["variables"] == variables
    
    async def test_execute_query_graphql_errors(self, mock_wiki_config):
        """Test GraphQL query with GraphQL errors."""
        client = WikiJSClient(mock_wiki_config)
        
        error_response = {
            "errors": [{"message": "Invalid query"}],
            "data": None
        }
        
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = error_response
        
        client.client.post = AsyncMock(return_value=mock_response)
        
        with pytest.raises(Exception, match="GraphQL query failed"):
            await client._execute_query("invalid query")
    
    async def test_execute_query_http_error(self, mock_wiki_config):
        """Test GraphQL query with HTTP error."""
        client = WikiJSClient(mock_wiki_config)
        
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        
        http_error = httpx.HTTPStatusError(
            "401 Unauthorized", 
            request=Mock(), 
            response=mock_response
        )
        
        client.client.post = AsyncMock(side_effect=http_error)
        
        with pytest.raises(Exception, match="API request failed: 401"):
            await client._execute_query("query { test }")
    
    async def test_search_pages_success(self, mock_wiki_config):
        """Test successful page search."""
        client = WikiJSClient(mock_wiki_config)
        
        search_response = {
            "pages": {
                "search": {
                    "results": [
                        {
                            "id": 1,
                            "path": "docs/test",
                            "title": "Test Page",
                            "description": "Test description",
                            "updatedAt": "2024-01-01T00:00:00Z",
                            "createdAt": "2024-01-01T00:00:00Z"
                        }
                    ]
                }
            }
        }
        
        client._execute_query = AsyncMock(return_value=search_response)
        
        results = await client.search_pages("test query", 5)
        
        assert len(results) == 1
        assert results[0]["title"] == "Test Page"
        
        # Verify correct query and variables were used
        call_args = client._execute_query.call_args
        assert "SearchPages" in call_args[0][0]
        assert call_args[0][1] == {"query": "test query", "limit": 5}
    
    async def test_search_pages_no_results(self, mock_wiki_config):
        """Test page search with no results."""
        client = WikiJSClient(mock_wiki_config)
        
        empty_response = {"pages": {"search": {"results": []}}}
        client._execute_query = AsyncMock(return_value=empty_response)
        
        results = await client.search_pages("nonexistent")
        
        assert results == []
    
    async def test_get_page_by_path_success(self, mock_wiki_config, sample_page_data):
        """Test successful get page by path."""
        client = WikiJSClient(mock_wiki_config)
        
        page_response = {"pages": {"single": sample_page_data}}
        client._execute_query = AsyncMock(return_value=page_response)
        
        result = await client.get_page_by_path("docs/test-page")
        
        assert result == sample_page_data
        assert result["title"] == "Test Page"
        
        # Verify correct query was used
        call_args = client._execute_query.call_args
        assert "GetPageByPath" in call_args[0][0]
        assert call_args[0][1] == {"path": "docs/test-page"}
    
    async def test_get_page_by_path_not_found(self, mock_wiki_config):
        """Test get page by path when page not found."""
        client = WikiJSClient(mock_wiki_config)
        
        not_found_response = {"pages": {"single": None}}
        client._execute_query = AsyncMock(return_value=not_found_response)
        
        result = await client.get_page_by_path("nonexistent")
        
        assert result is None
    
    async def test_get_page_by_id_success(self, mock_wiki_config, sample_page_data):
        """Test successful get page by ID."""
        client = WikiJSClient(mock_wiki_config)
        
        page_response = {"pages": {"single": sample_page_data}}
        client._execute_query = AsyncMock(return_value=page_response)
        
        result = await client.get_page_by_id(123)
        
        assert result == sample_page_data
        
        # Verify correct query was used
        call_args = client._execute_query.call_args
        assert "GetPageById" in call_args[0][0]
        assert call_args[0][1] == {"id": 123}
    
    async def test_list_pages_success(self, mock_wiki_config):
        """Test successful list pages."""
        client = WikiJSClient(mock_wiki_config)
        
        pages_response = {
            "pages": {
                "list": [
                    {
                        "id": 1,
                        "path": "docs/page1",
                        "title": "Page 1",
                        "description": "First page",
                        "updatedAt": "2024-01-01T00:00:00Z",
                        "createdAt": "2024-01-01T00:00:00Z",
                        "locale": "en"
                    }
                ]
            }
        }
        
        client._execute_query = AsyncMock(return_value=pages_response)
        
        result = await client.list_pages(25)
        
        assert len(result) == 1
        assert result[0]["title"] == "Page 1"
        
        # Verify correct parameters
        call_args = client._execute_query.call_args
        assert call_args[0][1] == {"limit": 25}
    
    async def test_get_page_tree_success(self, mock_wiki_config):
        """Test successful get page tree."""
        client = WikiJSClient(mock_wiki_config)
        
        tree_response = {
            "pages": {
                "tree": [
                    {
                        "id": 1,
                        "path": "docs",
                        "title": "Documentation",
                        "isFolder": True,
                        "parent": "",
                        "pageId": None,
                        "locale": "en"
                    }
                ]
            }
        }
        
        client._execute_query = AsyncMock(return_value=tree_response)
        
        result = await client.get_page_tree("docs", "PATH")
        
        assert len(result) == 1
        assert result[0]["isFolder"] is True
        
        # Verify correct parameters
        call_args = client._execute_query.call_args
        assert call_args[0][1] == {"parent": "docs", "mode": "PATH"}
    
    async def test_create_page_success(self, mock_wiki_config):
        """Test successful page creation."""
        client = WikiJSClient(mock_wiki_config)
        
        create_response = {
            "pages": {
                "create": {
                    "responseResult": {
                        "succeeded": True,
                        "errorCode": None,
                        "slug": "new-page",
                        "message": "Page created successfully"
                    },
                    "page": {
                        "id": 123,
                        "path": "docs/new-page",
                        "title": "New Page"
                    }
                }
            }
        }
        
        client._execute_query = AsyncMock(return_value=create_response)
        
        result = await client.create_page(
            path="docs/new-page",
            title="New Page",
            content="# New Page\n\nContent here",
            description="A new page",
            tags=["test", "new"]
        )
        
        assert result["page"]["id"] == 123
        assert result["responseResult"]["succeeded"] is True
        
        # Verify correct parameters
        call_args = client._execute_query.call_args
        variables = call_args[0][1]
        assert variables["path"] == "docs/new-page"
        assert variables["title"] == "New Page"
        assert variables["tags"] == ["test", "new"]
    
    async def test_create_page_failure(self, mock_wiki_config):
        """Test page creation failure."""
        client = WikiJSClient(mock_wiki_config)
        
        failed_response = {
            "pages": {
                "create": {
                    "responseResult": {
                        "succeeded": False,
                        "errorCode": "PAGE_CREATION_FAILED",
                        "message": "Page creation failed"
                    }
                }
            }
        }
        
        client._execute_query = AsyncMock(return_value=failed_response)
        
        with pytest.raises(Exception, match="Failed to create page"):
            await client.create_page("docs/fail", "Fail", "content")
    
    async def test_update_page_success(self, mock_wiki_config):
        """Test successful page update."""
        client = WikiJSClient(mock_wiki_config)
        
        update_response = {
            "pages": {
                "update": {
                    "responseResult": {
                        "succeeded": True,
                        "errorCode": None,
                        "message": "Page updated successfully"
                    },
                    "page": {
                        "id": 123,
                        "path": "docs/updated-page",
                        "title": "Updated Page",
                        "updatedAt": "2024-01-01T12:00:00Z"
                    }
                }
            }
        }
        
        client._execute_query = AsyncMock(return_value=update_response)
        
        result = await client.update_page(
            page_id=123,
            content="# Updated Content",
            title="Updated Page",
            tags=["updated"]
        )
        
        assert result["page"]["id"] == 123
        assert result["responseResult"]["succeeded"] is True
        
        # Verify correct parameters
        call_args = client._execute_query.call_args
        variables = call_args[0][1]
        assert variables["id"] == 123
        assert variables["content"] == "# Updated Content"
        assert variables["title"] == "Updated Page"
        assert variables["tags"] == ["updated"]
    
    async def test_update_page_failure(self, mock_wiki_config):
        """Test page update failure."""
        client = WikiJSClient(mock_wiki_config)
        
        failed_response = {
            "pages": {
                "update": {
                    "responseResult": {
                        "succeeded": False,
                        "errorCode": "PAGE_UPDATE_FAILED",
                        "message": "Page update failed"
                    }
                }
            }
        }
        
        client._execute_query = AsyncMock(return_value=failed_response)
        
        with pytest.raises(Exception, match="Failed to update page"):
            await client.update_page(123, "new content")
    
    async def test_delete_page_success(self, mock_wiki_config):
        """Test successful page deletion."""
        client = WikiJSClient(mock_wiki_config)
        
        delete_response = {
            "pages": {
                "delete": {
                    "responseResult": {
                        "succeeded": True,
                        "errorCode": None,
                        "message": "Page deleted successfully"
                    }
                }
            }
        }
        
        client._execute_query = AsyncMock(return_value=delete_response)
        
        result = await client.delete_page(123)
        
        assert result["responseResult"]["succeeded"] is True
        
        # Verify correct parameters
        call_args = client._execute_query.call_args
        assert call_args[0][1] == {"id": 123}
    
    async def test_delete_page_failure(self, mock_wiki_config):
        """Test page deletion failure."""
        client = WikiJSClient(mock_wiki_config)
        
        failed_response = {
            "pages": {
                "delete": {
                    "responseResult": {
                        "succeeded": False,
                        "errorCode": "PAGE_DELETE_FAILED",
                        "message": "Page deletion failed"
                    }
                }
            }
        }
        
        client._execute_query = AsyncMock(return_value=failed_response)
        
        with pytest.raises(Exception, match="Failed to delete page"):
            await client.delete_page(123)
    
    @pytest.mark.parametrize("method,args", [
        ("search_pages", ["test"]),
        ("get_page_by_path", ["docs/test"]),
        ("get_page_by_id", [123]),
        ("list_pages", []),
        ("get_page_tree", []),
    ])
    async def test_methods_handle_missing_data(self, mock_wiki_config, method, args):
        """Test that methods handle missing data gracefully."""
        client = WikiJSClient(mock_wiki_config)
        
        # Empty response
        client._execute_query = AsyncMock(return_value={})
        
        result = await getattr(client, method)(*args)
        
        # Should return empty list or None without raising
        assert result in ([], None)