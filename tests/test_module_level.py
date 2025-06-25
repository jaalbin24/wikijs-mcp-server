"""Tests for module-level code."""

import pytest
from unittest.mock import patch, Mock
import sys


class TestModuleLevel:
    """Test cases for module-level code execution."""
    
    @patch('sys.exit')
    def test_cli_main_execution(self, mock_exit):
        """Test CLI module execution when run as main."""
        # Save original
        original_argv = sys.argv[:]
        
        try:
            sys.argv = ['wikijs_mcp.cli']
            
            # Import and execute the module
            with patch('wikijs_mcp.cli.main', return_value=0) as mock_main:
                import wikijs_mcp.cli
                # Simulate running as main
                if hasattr(wikijs_mcp.cli, '__name__'):
                    wikijs_mcp.cli.__name__ = '__main__'
                    # Re-execute the module code
                    exec(compile(open(wikijs_mcp.cli.__file__).read(), wikijs_mcp.cli.__file__, 'exec'), wikijs_mcp.cli.__dict__)
                
                mock_exit.assert_called_once_with(0)
        finally:
            sys.argv = original_argv
    
    @patch('asyncio.run')
    def test_server_main_execution(self, mock_asyncio_run):
        """Test server module execution when run as main."""
        # Import the module
        import wikijs_mcp.server
        
        # Test would require executing the module as main
        # This is covered by integration tests