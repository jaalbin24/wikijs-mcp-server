"""Wiki.js GraphQL API client."""

import logging
from typing import Any, Dict, List, Optional
import httpx
from .config import WikiJSConfig

logger = logging.getLogger(__name__)


class WikiJSClient:
    """Client for interacting with Wiki.js GraphQL API."""
    
    def __init__(self, config: WikiJSConfig):
        self.config = config
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    async def _execute_query(self, query: str, variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute a GraphQL query against the Wiki.js API."""
        payload = {"query": query}
        if variables:
            payload["variables"] = variables
        
        try:
            response = await self.client.post(
                self.config.graphql_url,
                json=payload,
                headers=self.config.headers
            )
            response.raise_for_status()
            result = response.json()
            
            if "errors" in result:
                logger.error(f"GraphQL errors: {result['errors']}")
                raise Exception(f"GraphQL query failed: {result['errors']}")
            
            return result.get("data", {})
        
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error {e.response.status_code}: {e.response.text}")
            raise Exception(f"API request failed: {e.response.status_code}")
        except Exception as e:
            logger.error(f"Request failed: {str(e)}")
            raise
    
    async def search_pages(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for pages by title or content."""
        graphql_query = """
        query SearchPages($query: String!, $limit: Int!) {
            pages {
                search(query: $query, limit: $limit) {
                    results {
                        id
                        path
                        title
                        description
                        updatedAt
                        createdAt
                    }
                }
            }
        }
        """
        
        result = await self._execute_query(graphql_query, {"query": query, "limit": limit})
        return result.get("pages", {}).get("search", {}).get("results", [])
    
    async def get_page_by_path(self, path: str) -> Optional[Dict[str, Any]]:
        """Get a page by its path."""
        graphql_query = """
        query GetPageByPath($path: String!) {
            pages {
                single(path: $path) {
                    id
                    path
                    title
                    description
                    content
                    contentType
                    createdAt
                    updatedAt
                    author {
                        name
                        email
                    }
                    editor
                    locale
                    tags {
                        tag
                    }
                }
            }
        }
        """
        
        result = await self._execute_query(graphql_query, {"path": path})
        return result.get("pages", {}).get("single")
    
    async def get_page_by_id(self, page_id: int) -> Optional[Dict[str, Any]]:
        """Get a page by its ID."""
        graphql_query = """
        query GetPageById($id: Int!) {
            pages {
                single(id: $id) {
                    id
                    path
                    title
                    description
                    content
                    contentType
                    createdAt
                    updatedAt
                    author {
                        name
                        email
                    }
                    editor
                    locale
                    tags {
                        tag
                    }
                }
            }
        }
        """
        
        result = await self._execute_query(graphql_query, {"id": page_id})
        return result.get("pages", {}).get("single")
    
    async def list_pages(self, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """List all pages with pagination."""
        graphql_query = """
        query ListPages($limit: Int!, $offset: Int!) {
            pages {
                list(limit: $limit, offset: $offset) {
                    id
                    path
                    title
                    description
                    updatedAt
                    createdAt
                    author {
                        name
                    }
                    locale
                }
            }
        }
        """
        
        result = await self._execute_query(graphql_query, {"limit": limit, "offset": offset})
        return result.get("pages", {}).get("list", [])
    
    async def get_page_tree(self, parent_path: str = "", mode: str = "PATH") -> List[Dict[str, Any]]:
        """Get page tree structure."""
        graphql_query = """
        query GetPageTree($parent: String!, $mode: PageTreeMode!) {
            pages {
                tree(parent: $parent, mode: $mode) {
                    id
                    path
                    title
                    isFolder
                    parent
                    pageId
                    locale
                }
            }
        }
        """
        
        result = await self._execute_query(graphql_query, {"parent": parent_path, "mode": mode})
        return result.get("pages", {}).get("tree", [])
    
    async def create_page(
        self,
        path: str,
        title: str,
        content: str,
        description: str = "",
        editor: str = "markdown",
        locale: str = "en",
        tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Create a new page."""
        graphql_query = """
        mutation CreatePage(
            $path: String!,
            $title: String!,
            $content: String!,
            $description: String!,
            $editor: String!,
            $locale: String!,
            $tags: [String]
        ) {
            pages {
                create(
                    path: $path,
                    title: $title,
                    content: $content,
                    description: $description,
                    editor: $editor,
                    locale: $locale,
                    tags: $tags
                ) {
                    responseResult {
                        succeeded
                        errorCode
                        slug
                        message
                    }
                    page {
                        id
                        path
                        title
                    }
                }
            }
        }
        """
        
        variables = {
            "path": path,
            "title": title,
            "content": content,
            "description": description,
            "editor": editor,
            "locale": locale,
            "tags": tags or []
        }
        
        result = await self._execute_query(graphql_query, variables)
        create_result = result.get("pages", {}).get("create", {})
        
        response = create_result.get("responseResult", {})
        if not response.get("succeeded"):
            raise Exception(f"Failed to create page: {response.get('message', 'Unknown error')}")
        
        return create_result
    
    async def update_page(
        self,
        page_id: int,
        content: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Update an existing page."""
        graphql_query = """
        mutation UpdatePage(
            $id: Int!,
            $content: String!,
            $title: String,
            $description: String,
            $tags: [String]
        ) {
            pages {
                update(
                    id: $id,
                    content: $content,
                    title: $title,
                    description: $description,
                    tags: $tags
                ) {
                    responseResult {
                        succeeded
                        errorCode
                        message
                    }
                    page {
                        id
                        path
                        title
                        updatedAt
                    }
                }
            }
        }
        """
        
        variables = {
            "id": page_id,
            "content": content
        }
        if title is not None:
            variables["title"] = title
        if description is not None:
            variables["description"] = description
        if tags is not None:
            variables["tags"] = tags
        
        result = await self._execute_query(graphql_query, variables)
        update_result = result.get("pages", {}).get("update", {})
        
        response = update_result.get("responseResult", {})
        if not response.get("succeeded"):
            raise Exception(f"Failed to update page: {response.get('message', 'Unknown error')}")
        
        return update_result
    
    async def delete_page(self, page_id: int) -> Dict[str, Any]:
        """Delete a page."""
        graphql_query = """
        mutation DeletePage($id: Int!) {
            pages {
                delete(id: $id) {
                    responseResult {
                        succeeded
                        errorCode
                        message
                    }
                }
            }
        }
        """
        
        result = await self._execute_query(graphql_query, {"id": page_id})
        delete_result = result.get("pages", {}).get("delete", {})
        
        response = delete_result.get("responseResult", {})
        if not response.get("succeeded"):
            raise Exception(f"Failed to delete page: {response.get('message', 'Unknown error')}")
        
        return delete_result