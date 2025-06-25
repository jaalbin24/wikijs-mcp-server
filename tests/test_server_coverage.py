"""Additional tests to improve server coverage."""

import pytest
from unittest.mock import patch, AsyncMock, Mock, MagicMock
from wikijs_mcp.server import WikiJSMCPServer


class TestServerCoverage:
    """Additional test cases to improve server coverage."""
    
    @patch('wikijs_mcp.server.WikiJSConfig.load_config')
    def test_server_attributes(self, mock_load_config, mock_wiki_config):
        """Test server instance attributes."""
        mock_load_config.return_value = mock_wiki_config
        
        server = WikiJSMCPServer()
        
        # Check attributes
        assert server.server.name == "wikijs-mcp-server"
        assert server.config == mock_wiki_config
        assert server.client is None
    
    @patch('wikijs_mcp.server.WikiJSConfig.load_config')
    def test_init_calls_setup_handlers(self, mock_load_config, mock_wiki_config):
        """Test that __init__ calls _setup_handlers."""
        mock_load_config.return_value = mock_wiki_config
        
        with patch.object(WikiJSMCPServer, '_setup_handlers') as mock_setup:
            server = WikiJSMCPServer()
            mock_setup.assert_called_once()
    
    @patch('wikijs_mcp.server.WikiJSConfig.load_config')
    @patch('wikijs_mcp.server.Server')
    def test_server_creation(self, mock_server_class, mock_load_config, mock_wiki_config):
        """Test server creation with mocked Server class."""
        mock_load_config.return_value = mock_wiki_config
        mock_server_instance = Mock()
        mock_server_class.return_value = mock_server_instance
        
        server = WikiJSMCPServer()
        
        mock_server_class.assert_called_once_with("wikijs-mcp-server")
        assert server.server == mock_server_instance