"""WikiJS MCP Server implementation over HTTP."""

import asyncio
import logging
from typing import Any, Dict, List, Optional
from mcp.server import FastMCP
from mcp.types import TextContent
from .client import WikiJSClient
from .config import WikiJSConfig

logger = logging.getLogger(__name__)


class WikiJSMCPServer:
    """MCP Server for Wiki.js integration over HTTP."""
    
    def __init__(self):
        self.config = WikiJSConfig.load_config()
        self.app = FastMCP(
            name="wikijs-mcp-server",
            instructions="A Model Context Protocol server for Wiki.js integration"
        )
        self._setup_tools()
    
    def _setup_tools(self):
        """Setup MCP tools."""
        
        @self.app.tool(description="Search for pages in the Wiki.js instance")
        async def wiki_search(query: str, limit: int = 10) -> str:
            """Search for pages in Wiki.js.
            
            Args:
                query: Search query for finding pages
                limit: Maximum number of results (default: 10)
            """
            async with WikiJSClient(self.config) as client:
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
        
        @self.app.tool(description="Get a specific wiki page by path or ID")
        async def wiki_get_page(path: Optional[str] = None, id: Optional[int] = None) -> str:
            """Get a specific wiki page by path or ID.
            
            Args:
                path: Page path (e.g., 'docs/getting-started'). Use either path OR id, not both.
                id: Page ID. Use either path OR id, not both.
            """
            # Validate that exactly one of path or id is provided
            has_path = path is not None
            has_id = id is not None
            
            if not has_path and not has_id:
                raise ValueError("Either 'path' or 'id' parameter is required")
            if has_path and has_id:
                raise ValueError("Cannot specify both 'path' and 'id' parameters - use only one")
            
            async with WikiJSClient(self.config) as client:
                if has_path:
                    page = await client.get_page_by_path(path)
                else:
                    page = await client.get_page_by_id(id)
                
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
        
        @self.app.tool(description="List all pages")
        async def wiki_list_pages(limit: int = 50) -> str:
            """List all pages.
            
            Args:
                limit: Number of pages to return (default: 50)
            """
            async with WikiJSClient(self.config) as client:
                pages = await client.list_pages(limit)
                
                if not pages:
                    return "No pages found"
                
                response = f"Found {len(pages)} pages (limit: {limit}):\n\n"
                for page in pages:
                    response += f"**{page['title']}**\n"
                    response += f"Path: {page['path']} (ID: {page['id']})\n"
                    if page.get('description'):
                        response += f"Description: {page['description']}\n"
                    response += f"Updated: {page['updatedAt']}\n\n"
                
                return response
        
        @self.app.tool(description="Get wiki page tree structure")
        async def wiki_get_tree(parent_path: str = "") -> str:
            """Get wiki page tree structure.
            
            Args:
                parent_path: Parent path to get tree from (default: root)
            """
            async with WikiJSClient(self.config) as client:
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
        
        @self.app.tool(description="Create a new wiki page")
        async def wiki_create_page(
            path: str, 
            title: str, 
            content: str, 
            description: str = "", 
            tags: List[str] = None
        ) -> str:
            """Create a new wiki page.
            
            Args:
                path: Page path (e.g., 'docs/new-feature')
                title: Page title
                content: Page content in markdown
                description: Page description (optional)
                tags: Page tags (optional)
            """
            if tags is None:
                tags = []
                
            async with WikiJSClient(self.config) as client:
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
        
        @self.app.tool(description="Update an existing wiki page")
        async def wiki_update_page(
            id: int, 
            content: str, 
            title: Optional[str] = None, 
            description: Optional[str] = None, 
            tags: Optional[List[str]] = None
        ) -> str:
            """Update an existing wiki page.
            
            Args:
                id: Page ID to update
                content: New page content in markdown
                title: New page title (optional)
                description: New page description (optional)
                tags: New page tags (optional)
            """
            async with WikiJSClient(self.config) as client:
                result = await client.update_page(
                    page_id=id,
                    content=content,
                    title=title,
                    description=description,
                    tags=tags
                )
                
                page_info = result.get("page", {})
                response = f"✅ Successfully updated page:\n\n"
                response += f"**Title:** {page_info.get('title', 'Unknown')}\n"
                response += f"**Path:** {page_info.get('path', 'Unknown')}\n"
                response += f"**ID:** {page_info.get('id', id)}\n"
                response += f"**Updated:** {page_info.get('updatedAt', 'Just now')}\n"
                
                return response
    
    def get_streamable_http_app(self):
        """Get the FastMCP StreamableHTTP app for HTTP transport."""
        return self.app.streamable_http_app()
    
    async def run_stdio(self):
        """Run the MCP server over stdio (for local use)."""
        try:
            self.config.validate_config()
            logger.info(f"Starting WikiJS MCP Server (stdio) for {self.config.url}")
            await self.app.run_stdio_async()
        except Exception as e:
            logger.error(f"Server failed to start: {str(e)}")
            raise
    
    async def run_http(self, host: str = None, port: int = None):
        """Run the MCP server over HTTP transport."""
        try:
            self.config.validate_config()
            
            # Use config values if not provided
            host = host or self.config.http_host
            port = port or self.config.http_port
            
            logger.info(f"Starting WikiJS MCP Server (HTTP) for {self.config.url}")
            logger.info(f"Server running on http://{host}:{port}")
            
            # Get the StreamableHTTP app and run it with uvicorn
            import uvicorn
            app = self.get_streamable_http_app()
            
            config = uvicorn.Config(
                app=app,
                host=host,
                port=port,
                log_level="info"
            )
            server = uvicorn.Server(config)
            await server.serve()
        except Exception as e:
            logger.error(f"Server failed to start: {str(e)}")
            raise


async def main():
    """Main entry point."""
    import os
    import sys
    
    logging.basicConfig(level=logging.INFO)
    server = WikiJSMCPServer()
    
    # Check if we should run over HTTP or stdio
    transport = os.getenv("MCP_TRANSPORT", "http").lower()
    
    # Allow command line override
    if len(sys.argv) > 1:
        if sys.argv[1] == "--stdio":
            transport = "stdio"
        elif sys.argv[1] == "--http":
            transport = "http"
        elif sys.argv[1] == "--help":
            print("WikiJS MCP Server")
            print("Usage:")
            print("  python -m wikijs_mcp.server [--stdio|--http]")
            print("  python -m wikijs_mcp.server --help")
            print("")
            print("Environment variables:")
            print("  MCP_TRANSPORT=stdio|http  (default: http)")
            print("")
            print("For Claude Code:")
            print("  - Use --http or MCP_TRANSPORT=http")
            print("  - Server will run on http://localhost:8000/mcp")
            print("  - Configure Claude Code to connect to HTTP MCP server")
            return
    
    if transport == "stdio":
        # Run over stdio (for legacy MCP client compatibility)
        print("Starting MCP server over stdio...")
        await server.run_stdio()
    else:
        # Run over HTTP (default, for Claude Code and network access)
        print("Starting MCP server over HTTP...")
        print("Claude Code can connect to: http://localhost:8000/mcp")
        await server.run_http()


if __name__ == "__main__":
    asyncio.run(main())