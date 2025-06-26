"""WikiJS HTTP Server implementation."""

import asyncio
import logging
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn
from .client import WikiJSClient
from .config import WikiJSConfig

logger = logging.getLogger(__name__)


# Pydantic models for request/response
class SearchRequest(BaseModel):
    query: str = Field(description="Search query for finding pages")
    limit: int = Field(default=10, description="Maximum number of results")

class GetPageRequest(BaseModel):
    path: Optional[str] = Field(default=None, description="Page path")
    id: Optional[int] = Field(default=None, description="Page ID")

class ListPagesRequest(BaseModel):
    limit: int = Field(default=50, description="Number of pages to return")

class GetTreeRequest(BaseModel):
    parent_path: str = Field(default="", description="Parent path to get tree from")

class CreatePageRequest(BaseModel):
    path: str = Field(description="Page path")
    title: str = Field(description="Page title")
    content: str = Field(description="Page content in markdown")
    description: str = Field(default="", description="Page description")
    tags: List[str] = Field(default=[], description="Page tags")

class UpdatePageRequest(BaseModel):
    id: int = Field(description="Page ID to update")
    content: str = Field(description="New page content in markdown")
    title: Optional[str] = Field(default=None, description="New page title")
    description: Optional[str] = Field(default=None, description="New page description")
    tags: Optional[List[str]] = Field(default=None, description="New page tags")

class WikiJSHTTPServer:
    """HTTP Server for Wiki.js integration."""
    
    def __init__(self):
        self.app = FastAPI(
            title="WikiJS HTTP Server",
            description="HTTP API for Wiki.js integration",
            version="0.1.0"
        )
        self.config = WikiJSConfig.load_config()
        self._setup_middleware()
        self._setup_routes()

    def _setup_middleware(self):
        """Setup CORS and other middleware."""
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=self.config.cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    
    def _setup_routes(self):
        """Setup FastAPI routes."""
        
        @self.app.post("/search")
        async def search_pages(request: SearchRequest):
            """Search for pages in the Wiki.js instance."""
            try:
                async with WikiJSClient(self.config) as client:
                    results = await client.search_pages(request.query, request.limit)
                    
                    if not results:
                        return {"message": f"No pages found for query: {request.query}", "results": []}
                    
                    return {
                        "message": f"Found {len(results)} pages for query '{request.query}'",
                        "results": results
                    }
            except Exception as e:
                logger.error(f"Search failed: {str(e)}")
                raise HTTPException(status_code=500, detail=str(e))
    
        @self.app.post("/page")
        async def get_page(request: GetPageRequest):
            """Get a specific wiki page by path or ID."""
            try:
                # Validate that exactly one of path or id is provided
                has_path = request.path is not None
                has_id = request.id is not None
                
                if not has_path and not has_id:
                    raise HTTPException(status_code=400, detail="Either 'path' or 'id' parameter is required")
                if has_path and has_id:
                    raise HTTPException(status_code=400, detail="Cannot specify both 'path' and 'id' parameters - use only one")
                
                async with WikiJSClient(self.config) as client:
                    if has_path:
                        page = await client.get_page_by_path(request.path)
                    else:
                        page = await client.get_page_by_id(request.id)
                    
                    if not page:
                        raise HTTPException(status_code=404, detail="Page not found")
                    
                    return {"page": page}
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Get page failed: {str(e)}")
                raise HTTPException(status_code=500, detail=str(e))
    
        @self.app.post("/pages")
        async def list_pages(request: ListPagesRequest = ListPagesRequest()):
            """List all pages."""
            try:
                async with WikiJSClient(self.config) as client:
                    pages = await client.list_pages(request.limit)
                    
                    if not pages:
                        return {"message": "No pages found", "pages": []}
                    
                    return {
                        "message": f"Found {len(pages)} pages (limit: {request.limit})",
                        "pages": pages
                    }
            except Exception as e:
                logger.error(f"List pages failed: {str(e)}")
                raise HTTPException(status_code=500, detail=str(e))
    
        @self.app.post("/tree")
        async def get_tree(request: GetTreeRequest = GetTreeRequest()):
            """Get wiki page tree structure."""
            try:
                async with WikiJSClient(self.config) as client:
                    tree = await client.get_page_tree(request.parent_path)
                    
                    if not tree:
                        return {"message": "No pages found in tree", "tree": []}
                    
                    return {
                        "message": f"Wiki page tree from '{request.parent_path or 'root'}'",
                        "tree": tree
                    }
            except Exception as e:
                logger.error(f"Get tree failed: {str(e)}")
                raise HTTPException(status_code=500, detail=str(e))
    
        @self.app.post("/page/create")
        async def create_page(request: CreatePageRequest):
            """Create a new wiki page."""
            try:
                async with WikiJSClient(self.config) as client:
                    result = await client.create_page(
                        path=request.path,
                        title=request.title,
                        content=request.content,
                        description=request.description,
                        tags=request.tags
                    )
                    
                    return {
                        "message": "Successfully created page",
                        "result": result
                    }
            except Exception as e:
                logger.error(f"Create page failed: {str(e)}")
                raise HTTPException(status_code=500, detail=str(e))
    
        @self.app.post("/page/update")
        async def update_page(request: UpdatePageRequest):
            """Update an existing wiki page."""
            try:
                async with WikiJSClient(self.config) as client:
                    result = await client.update_page(
                        page_id=request.id,
                        content=request.content,
                        title=request.title,
                        description=request.description,
                        tags=request.tags
                    )
                    
                    return {
                        "message": "Successfully updated page",
                        "result": result
                    }
            except Exception as e:
                logger.error(f"Update page failed: {str(e)}")
                raise HTTPException(status_code=500, detail=str(e))
    
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint."""
            return {"status": "healthy", "service": "wikijs-http-server"}
        
        @self.app.get("/tools")
        async def list_tools():
            """List available API endpoints."""
            return {
                "endpoints": [
                    {
                        "name": "search",
                        "method": "POST",
                        "path": "/search",
                        "description": "Search for pages in the Wiki.js instance"
                    },
                    {
                        "name": "get_page",
                        "method": "POST",
                        "path": "/page",
                        "description": "Get a specific wiki page by path or ID"
                    },
                    {
                        "name": "list_pages",
                        "method": "POST",
                        "path": "/pages",
                        "description": "List all pages"
                    },
                    {
                        "name": "get_tree",
                        "method": "POST",
                        "path": "/tree",
                        "description": "Get wiki page tree structure"
                    },
                    {
                        "name": "create_page",
                        "method": "POST",
                        "path": "/page/create",
                        "description": "Create a new wiki page"
                    },
                    {
                        "name": "update_page",
                        "method": "POST",
                        "path": "/page/update",
                        "description": "Update an existing wiki page"
                    }
                ]
            }
        
    def get_app(self) -> FastAPI:
        """Get the FastAPI application instance."""
        return self.app
    
    async def run(self, host: Optional[str] = None, port: Optional[int] = None):
        """Run the HTTP server."""
        try:
            self.config.validate_config()
            
            # Use config values if not provided as parameters
            host = host or self.config.http_host
            port = port or self.config.http_port
            
            logger.info(f"Starting WikiJS HTTP Server for {self.config.url}")
            logger.info(f"Server running on http://{host}:{port}")
            
            config = uvicorn.Config(
                app=self.app,
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
    logging.basicConfig(level=logging.INFO)
    server = WikiJSHTTPServer()
    
    # Run HTTP server (uses config values)
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())