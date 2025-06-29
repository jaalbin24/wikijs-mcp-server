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
        """Search for pages by title or content. Uses correct schema parameters."""
        # Try GraphQL search with required path and locale parameters
        try:
            graphql_query = """
            query SearchPages($query: String!, $path: String, $locale: String) {
                pages {
                    search(query: $query, path: $path, locale: $locale) {
                        results {
                            id
                            title
                            description
                            path
                            locale
                        }
                        totalHits
                    }
                }
            }
            """
            
            # Use empty path to search all paths, default locale
            variables = {
                "query": query,
                "path": "",  # Search all paths
                "locale": "en"  # Default locale
            }
            
            result = await self._execute_query(graphql_query, variables)
            results = result.get("pages", {}).get("search", {}).get("results", [])
            return results[:limit]  # Apply limit manually
        except Exception:
            # Fallback: Filter pages from list_pages
            all_pages = await self.list_pages(limit=1000)
            query_lower = query.lower()
            filtered_pages = []
            
            for page in all_pages:
                if (query_lower in page.get('title', '').lower() or 
                    query_lower in page.get('description', '').lower() or
                    query_lower in page.get('path', '').lower()):
                    # Transform to match PageSearchResult schema (remove extra fields)
                    search_result = {
                        'id': str(page.get('id', '')),  # Convert to string to match schema
                        'title': page.get('title', ''),
                        'description': page.get('description', ''),
                        'path': page.get('path', ''),
                        'locale': page.get('locale', 'en')
                    }
                    filtered_pages.append(search_result)
                    if len(filtered_pages) >= limit:
                        break
            
            return filtered_pages
    
    async def get_page_by_path(self, path: str, locale: str = "en") -> Optional[Dict[str, Any]]:
        """Get a page by its path using the singleByPath query."""
        graphql_query = """
        query GetPageByPath($path: String!, $locale: String!) {
            pages {
                singleByPath(path: $path, locale: $locale) {
                    id
                    path
                    title
                    description
                    content
                    contentType
                    isPublished
                    isPrivate
                    createdAt
                    updatedAt
                    editor
                    locale
                    authorId
                    authorName
                    authorEmail
                    creatorId
                    creatorName
                    creatorEmail
                    tags {
                        id
                        tag
                        title
                    }
                }
            }
        }
        """
        
        result = await self._execute_query(graphql_query, {"path": path, "locale": locale})
        return result.get("pages", {}).get("singleByPath")
    
    async def get_page_by_id(self, page_id: int) -> Optional[Dict[str, Any]]:
        """Get a page by its ID using the single query."""
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
                    isPublished
                    isPrivate
                    createdAt
                    updatedAt
                    editor
                    locale
                    authorId
                    authorName
                    authorEmail
                    creatorId
                    creatorName
                    creatorEmail
                    tags {
                        id
                        tag
                        title
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
        query ListPages($limit: Int!) {
            pages {
                list(limit: $limit) {
                    id
                    path
                    title
                    description
                    updatedAt
                    createdAt
                    locale
                }
            }
        }
        """
        
        result = await self._execute_query(graphql_query, {"limit": limit})
        return result.get("pages", {}).get("list", [])
    
    async def get_page_tree(self, parent_path: str = "", mode: str = "ALL", locale: str = "en", parent_id: int = None) -> List[Dict[str, Any]]:
        """Get page tree structure using the correct schema."""
        graphql_query = """
        query GetPageTree($path: String, $parent: Int, $mode: PageTreeMode!, $locale: String!, $includeAncestors: Boolean) {
            pages {
                tree(path: $path, parent: $parent, mode: $mode, locale: $locale, includeAncestors: $includeAncestors) {
                    id
                    path
                    depth
                    title
                    isPrivate
                    isFolder
                    privateNS
                    parent
                    pageId
                    locale
                }
            }
        }
        """
        
        variables = {
            "path": parent_path if parent_path else None,
            "parent": parent_id,
            "mode": mode,  # ALL, FOLDERS, or PAGES
            "locale": locale,
            "includeAncestors": False
        }
        
        result = await self._execute_query(graphql_query, variables)
        return result.get("pages", {}).get("tree", [])
    
    async def create_page(
        self,
        path: str,
        title: str,
        content: str,
        description: str = "",
        editor: str = "markdown",
        locale: str = "en",
        tags: Optional[List[str]] = None,
        is_published: bool = True,
        is_private: bool = False
    ) -> Dict[str, Any]:
        """Create a new page using the correct schema."""
        graphql_query = """
        mutation CreatePage(
            $content: String!,
            $description: String!,
            $editor: String!,
            $isPublished: Boolean!,
            $isPrivate: Boolean!,
            $locale: String!,
            $path: String!,
            $tags: [String]!,
            $title: String!
        ) {
            pages {
                create(
                    content: $content,
                    description: $description,
                    editor: $editor,
                    isPublished: $isPublished,
                    isPrivate: $isPrivate,
                    locale: $locale,
                    path: $path,
                    tags: $tags,
                    title: $title
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
            "content": content,
            "description": description,
            "editor": editor,
            "isPublished": is_published,
            "isPrivate": is_private,
            "locale": locale,
            "path": path,
            "tags": tags or [],
            "title": title
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
        content: Optional[str] = None,
        title: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        editor: Optional[str] = None,
        is_private: Optional[bool] = None,
        is_published: Optional[bool] = None,
        locale: Optional[str] = None,
        path: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update an existing page. Retrieves current page data and merges with updates."""
        
        # First, get the current page to ensure we have all required fields
        current_page = await self.get_page_by_id(page_id)
        if not current_page:
            raise Exception(f"Page with ID {page_id} not found")
        
        # Merge current values with provided updates
        update_data = {
            "id": page_id,
            "content": content if content is not None else current_page.get("content", ""),
            "title": title if title is not None else current_page.get("title", ""),
            "description": description if description is not None else current_page.get("description", ""),
            "editor": editor if editor is not None else current_page.get("editor", "markdown"),
            "isPrivate": is_private if is_private is not None else current_page.get("isPrivate", False),
            "isPublished": is_published if is_published is not None else current_page.get("isPublished", True),
            "locale": locale if locale is not None else current_page.get("locale", "en"),
            "path": path if path is not None else current_page.get("path", ""),
            "tags": tags if tags is not None else []
        }
        
        graphql_query = """
        mutation UpdatePage(
            $id: Int!,
            $content: String,
            $description: String,
            $editor: String,
            $isPrivate: Boolean,
            $isPublished: Boolean,
            $locale: String,
            $path: String,
            $tags: [String],
            $title: String
        ) {
            pages {
                update(
                    id: $id,
                    content: $content,
                    description: $description,
                    editor: $editor,
                    isPrivate: $isPrivate,
                    isPublished: $isPublished,
                    locale: $locale,
                    path: $path,
                    tags: $tags,
                    title: $title
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
        
        result = await self._execute_query(graphql_query, update_data)
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
    
    async def move_page(self, page_id: int, destination_path: str, destination_locale: str = "en") -> Dict[str, Any]:
        """Move a page to a new path and/or locale."""
        graphql_query = """
        mutation MovePage($id: Int!, $destinationPath: String!, $destinationLocale: String!) {
            pages {
                move(id: $id, destinationPath: $destinationPath, destinationLocale: $destinationLocale) {
                    responseResult {
                        succeeded
                        errorCode
                        message
                    }
                }
            }
        }
        """
        
        variables = {
            "id": page_id,
            "destinationPath": destination_path,
            "destinationLocale": destination_locale
        }
        
        result = await self._execute_query(graphql_query, variables)
        move_result = result.get("pages", {}).get("move", {})
        
        response = move_result.get("responseResult", {})
        if not response.get("succeeded"):
            raise Exception(f"Failed to move page: {response.get('message', 'Unknown error')}")
        
        return move_result