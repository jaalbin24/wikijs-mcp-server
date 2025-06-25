"""Tests for MCP server functionality."""

import asyncio
import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from mcp.types import Tool, TextContent
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
        assert server.client is None
        mock_load_config.assert_called_once()
    
    
    @patch('wikijs_mcp.server.WikiJSConfig.load_config')
    async def test_run_with_valid_config(self, mock_load_config, mock_wiki_config):
        """Test running server with valid configuration."""
        mock_load_config.return_value = mock_wiki_config
        server = WikiJSMCPServer()
        
        with patch.object(server.server, 'run', new_callable=AsyncMock) as mock_run:
            await server.run()
            mock_run.assert_called_once()
    
    @patch('wikijs_mcp.server.WikiJSConfig.load_config')
    async def test_run_with_invalid_config(self, mock_load_config):
        """Test running server with invalid configuration."""
        invalid_config = Mock()
        invalid_config.validate_config.side_effect = ValueError("Invalid config")
        mock_load_config.return_value = invalid_config
        
        server = WikiJSMCPServer()
        
        with pytest.raises(ValueError, match="Invalid config"):
            await server.run()
    
    
