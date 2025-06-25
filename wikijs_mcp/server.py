"""WikiJS MCP Server implementation."""

import asyncio
import logging
from typing import Any, Dict, List
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.types import Resource, Tool, TextContent, ImageContent, EmbeddedResource
from .client import WikiJSClient
from .config import WikiJSConfig

logger = logging.getLogger(__name__)


class WikiJSMCPServer:
    """MCP Server for Wiki.js integration."""
    
    def __init__(self):
        self.server = Server("wikijs-mcp-server")
        self.config = WikiJSConfig.load_config()
        self.client: WikiJSClient = None
        self._setup_handlers()
    
    async def _handle_wiki_search(self, client: WikiJSClient, arguments: Dict[str, Any]) -> str:
        """Handle wiki search requests."""
        query = arguments["query"]
        limit = arguments.get("limit", 10)
        results = await client.search_pages(query, limit)
        
        if not results:
            return f"No pages found for query: {query}"
        
        response = f"Found {len(results)} pages for query '{query}':\n\n"
        for page in results:
            response += f"**{page['title']}**\n"
            response += f"Path: {page['path']}\n"
            if page.get('description'):
                response += f"Description: {page['description']}\n"
            response += f"Updated: {page['updatedAt']}\n\n"
        
        return response
    
    async def _handle_wiki_get_page(self, client: WikiJSClient, arguments: Dict[str, Any]) -> str:
        """Handle get page requests."""
        if "path" in arguments:
            page = await client.get_page_by_path(arguments["path"])
        else:
            page = await client.get_page_by_id(arguments["id"])
        
        if not page:
            return "Page not found"
        
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
        
        return response
    
    async def _handle_wiki_list_pages(self, client: WikiJSClient, arguments: Dict[str, Any]) -> str:
        """Handle list pages requests."""
        limit = arguments.get("limit", 50)
        offset = arguments.get("offset", 0)
        pages = await client.list_pages(limit, offset)
        
        if not pages:
            return "No pages found"
        
        response = f"Found {len(pages)} pages (offset: {offset}, limit: {limit}):\n\n"
        for page in pages:
            response += f"**{page['title']}**\n"
            response += f"Path: {page['path']} (ID: {page['id']})\n"
            if page.get('description'):
                response += f"Description: {page['description']}\n"
            if page.get('author'):
                response += f"Author: {page['author'].get('name', 'Unknown')}\n"
            response += f"Updated: {page['updatedAt']}\n\n"
        
        return response
    
    async def _handle_wiki_get_tree(self, client: WikiJSClient, arguments: Dict[str, Any]) -> str:
        """Handle get tree requests."""
        parent_path = arguments.get("parent_path", "")
        tree = await client.get_page_tree(parent_path)
        
        if not tree:
            return "No pages found in tree"
        
        response = f"Wiki page tree from '{parent_path or 'root'}':\n\n"
        for item in tree:
            indent = "  " * item.get('depth', 0)
            if item.get('isFolder'):
                response += f"{indent}📁 {item['title']}/\n"
            else:
                response += f"{indent}📄 {item['title']} ({item['path']})\n"
        
        return response
    
    async def _handle_wiki_create_page(self, client: WikiJSClient, arguments: Dict[str, Any]) -> str:
        """Handle create page requests."""
        path = arguments["path"]
        title = arguments["title"]
        content = arguments["content"]
        description = arguments.get("description", "")
        tags = arguments.get("tags", [])
        
        result = await client.create_page(
            path=path,
            title=title,
            content=content,
            description=description,
            tags=tags
        )
        
        page_info = result.get("page", {})
        response = f"✅ Successfully created page:\n\n"
        response += f"**Title:** {page_info.get('title', title)}\n"
        response += f"**Path:** {page_info.get('path', path)}\n"
        response += f"**ID:** {page_info.get('id', 'Unknown')}\n"
        
        return response
    
    async def _handle_wiki_update_page(self, client: WikiJSClient, arguments: Dict[str, Any]) -> str:
        """Handle update page requests."""
        page_id = arguments["id"]
        content = arguments["content"]
        title = arguments.get("title")
        description = arguments.get("description")
        tags = arguments.get("tags")
        
        result = await client.update_page(
            page_id=page_id,
            content=content,
            title=title,
            description=description,
            tags=tags
        )
        
        page_info = result.get("page", {})
        response = f"✅ Successfully updated page:\n\n"
        response += f"**Title:** {page_info.get('title', 'Unknown')}\n"
        response += f"**Path:** {page_info.get('path', 'Unknown')}\n"
        response += f"**ID:** {page_info.get('id', page_id)}\n"
        response += f"**Updated:** {page_info.get('updatedAt', 'Just now')}\n"
        
        return response
    
    def _setup_handlers(self):
        """Setup MCP server handlers."""
        
        @self.server.list_tools()
        async def handle_list_tools() -> List[Tool]:
            """List available tools."""
            return [
                Tool(
                    name="wiki_search",
                    description="Search for pages in the Wiki.js instance",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Search query for finding pages"
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Maximum number of results (default: 10)",
                                "default": 10
                            }
                        },
                        "required": ["query"]
                    }
                ),
                Tool(
                    name="wiki_get_page",
                    description="Get a specific wiki page by path or ID",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "Page path (e.g., 'docs/getting-started')"
                            },
                            "id": {
                                "type": "integer",
                                "description": "Page ID"
                            }
                        },
                        "oneOf": [
                            {"required": ["path"]},
                            {"required": ["id"]}
                        ]
                    }
                ),
                Tool(
                    name="wiki_list_pages",
                    description="List all pages with pagination",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "limit": {
                                "type": "integer",
                                "description": "Number of pages to return (default: 50)",
                                "default": 50
                            },
                            "offset": {
                                "type": "integer",
                                "description": "Number of pages to skip (default: 0)",
                                "default": 0
                            }
                        }
                    }
                ),
                Tool(
                    name="wiki_get_tree",
                    description="Get wiki page tree structure",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "parent_path": {
                                "type": "string",
                                "description": "Parent path to get tree from (default: root)",
                                "default": ""
                            }
                        }
                    }
                ),
                Tool(
                    name="wiki_create_page",
                    description="Create a new wiki page",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "Page path (e.g., 'docs/new-feature')"
                            },
                            "title": {
                                "type": "string",
                                "description": "Page title"
                            },
                            "content": {
                                "type": "string",
                                "description": "Page content in markdown"
                            },
                            "description": {
                                "type": "string",
                                "description": "Page description (optional)",
                                "default": ""
                            },
                            "tags": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Page tags (optional)"
                            }
                        },
                        "required": ["path", "title", "content"]
                    }
                ),
                Tool(
                    name="wiki_update_page",
                    description="Update an existing wiki page",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "id": {
                                "type": "integer",
                                "description": "Page ID to update"
                            },
                            "content": {
                                "type": "string",
                                "description": "New page content in markdown"
                            },
                            "title": {
                                "type": "string",
                                "description": "New page title (optional)"
                            },
                            "description": {
                                "type": "string",
                                "description": "New page description (optional)"
                            },
                            "tags": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "New page tags (optional)"
                            }
                        },
                        "required": ["id", "content"]
                    }
                )
            ]
        
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            """Handle tool calls."""
            try:
                async with WikiJSClient(self.config) as client:
                    if name == "wiki_search":
                        response = await self._handle_wiki_search(client, arguments)
                        return [TextContent(type="text", text=response)]
                    
                    elif name == "wiki_get_page":
                        response = await self._handle_wiki_get_page(client, arguments)
                        return [TextContent(type="text", text=response)]
                    
                    elif name == "wiki_list_pages":
                        response = await self._handle_wiki_list_pages(client, arguments)
                        return [TextContent(type="text", text=response)]
                    
                    elif name == "wiki_get_tree":
                        response = await self._handle_wiki_get_tree(client, arguments)
                        return [TextContent(type="text", text=response)]
                    
                    elif name == "wiki_create_page":
                        response = await self._handle_wiki_create_page(client, arguments)
                        return [TextContent(type="text", text=response)]
                    
                    elif name == "wiki_update_page":
                        response = await self._handle_wiki_update_page(client, arguments)
                        return [TextContent(type="text", text=response)]
                    
                    else:
                        response = f"Unknown tool: {name}"
                        return [TextContent(type="text", text=response)]
            
            except Exception as e:
                logger.error(f"Tool call failed: {str(e)}")
                return [TextContent(type="text", text=f"Error: {str(e)}")]
    
    async def run(self):
        """Run the MCP server."""
        try:
            self.config.validate_config()
            logger.info(f"Starting WikiJS MCP Server for {self.config.url}")
            await self.server.run()
        except Exception as e:
            logger.error(f"Server failed to start: {str(e)}")
            raise


async def main():
    """Main entry point."""
    from mcp.server.stdio import stdio_server
    
    logging.basicConfig(level=logging.INFO)
    server = WikiJSMCPServer()
    
    # MCP servers run via stdio
    async with stdio_server() as (read_stream, write_stream):
        await server.server.run(
            read_stream, 
            write_stream, 
            server.server.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())