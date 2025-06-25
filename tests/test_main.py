"""Tests for main entry points."""

import pytest
from unittest.mock import patch, AsyncMock, Mock, MagicMock
import asyncio


class TestMainFunctions:
    """Test cases for main entry points."""
    
    @patch('mcp.server.stdio.stdio_server')
    @patch('wikijs_mcp.server.logging.basicConfig')
    @patch('wikijs_mcp.server.WikiJSMCPServer')
    async def test_server_main(self, mock_server_class, mock_logging, mock_stdio_server):
        """Test the server main() function."""
        # Mock server instance
        mock_server_instance = Mock()
        mock_server_instance.server = Mock()
        mock_server_instance.server.run = AsyncMock()
        mock_server_instance.server.create_initialization_options = Mock(return_value={})
        mock_server_class.return_value = mock_server_instance
        
        # Mock stdio streams
        mock_read_stream = Mock()
        mock_write_stream = Mock()
        mock_stdio_context = AsyncMock()
        mock_stdio_context.__aenter__ = AsyncMock(return_value=(mock_read_stream, mock_write_stream))
        mock_stdio_context.__aexit__ = AsyncMock()
        mock_stdio_server.return_value = mock_stdio_context
        
        # Import and run main
        from wikijs_mcp.server import main
        await main()
        
        # Verify calls
        mock_logging.assert_called_once()
        mock_server_class.assert_called_once()
        mock_stdio_server.assert_called_once()
        mock_server_instance.server.run.assert_called_once_with(
            mock_read_stream,
            mock_write_stream,
            {}
        )