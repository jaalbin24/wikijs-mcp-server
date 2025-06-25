"""Integration tests for WikiJS MCP Server."""

import pytest
from unittest.mock import patch, AsyncMock, Mock
from wikijs_mcp.server import WikiJSMCPServer


@pytest.mark.integration
class TestServerIntegration:
    """Integration tests for the MCP server."""
    
    @patch('wikijs_mcp.server.WikiJSConfig.load_config')
    def test_server_initialization_creates_handlers(self, mock_load_config, mock_wiki_config):
        """Test that server initialization creates all necessary handlers."""
        mock_load_config.return_value = mock_wiki_config
        
        server = WikiJSMCPServer()
        
        # The server should have these attributes after initialization
        assert server.server is not None
        assert server.config == mock_wiki_config
        assert server.client is None
        
        # The server name should be set
        assert server.server.name == "wikijs-mcp-server"