"""Tests for server handler methods."""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from mcp.types import Tool, TextContent
from wikijs_mcp.server import WikiJSMCPServer


class TestServerHandlers:
    """Test cases for server handler methods."""
    
    @patch('wikijs_mcp.server.WikiJSConfig.load_config')
    def test_setup_handlers_registers_decorators(self, mock_load_config, mock_wiki_config):
        """Test that _setup_handlers registers the correct decorators."""
        mock_load_config.return_value = mock_wiki_config
        
        server = WikiJSMCPServer()
        
        # Check that decorators were used (they modify the server object)
        assert hasattr(server.server, 'list_tools')
        assert hasattr(server.server, 'call_tool')
    
    @patch('wikijs_mcp.server.WikiJSConfig.load_config') 
    @patch('wikijs_mcp.server.logger')
    async def test_run_logs_startup(self, mock_logger, mock_load_config, mock_wiki_config):
        """Test that run() logs startup information."""
        mock_load_config.return_value = mock_wiki_config
        server = WikiJSMCPServer()
        
        with patch.object(server.server, 'run', new_callable=AsyncMock) as mock_run:
            await server.run()
            
            mock_logger.info.assert_called_once()
            assert "Starting WikiJS MCP Server" in mock_logger.info.call_args[0][0]
            assert mock_wiki_config.url in mock_logger.info.call_args[0][0]
    
    @patch('wikijs_mcp.server.WikiJSConfig.load_config')
    @patch('wikijs_mcp.server.logger')
    async def test_run_logs_error_on_failure(self, mock_logger, mock_load_config, mock_wiki_config):
        """Test that run() logs errors on failure."""
        mock_load_config.return_value = mock_wiki_config
        server = WikiJSMCPServer()
        
        error_msg = "Connection failed"
        with patch.object(server.server, 'run', new_callable=AsyncMock) as mock_run:
            mock_run.side_effect = Exception(error_msg)
            
            with pytest.raises(Exception):
                await server.run()
            
            mock_logger.error.assert_called_once()
            assert "Server failed to start" in mock_logger.error.call_args[0][0]
            assert error_msg in mock_logger.error.call_args[0][0]