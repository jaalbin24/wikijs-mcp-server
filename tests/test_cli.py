"""Tests for CLI module."""

import pytest
from unittest.mock import patch
from wikijs_mcp.cli import main


class TestCLI:
    """Test cases for CLI functionality."""
    
    def test_main_prints_instructions(self, capsys):
        """Test that main() prints the correct instructions."""
        result = main()
        
        captured = capsys.readouterr()
        
        assert result == 0
        assert "The encryption feature has been removed" in captured.out
        assert "WIKIJS_URL=https://your-wiki-instance.com" in captured.out
        assert "WIKIJS_API_KEY=your-api-key" in captured.out
        assert "WIKIJS_GRAPHQL_ENDPOINT=/graphql" in captured.out
        assert "DEBUG=false" in captured.out
    
    def test_main_returns_zero(self):
        """Test that main() returns 0 indicating success."""
        result = main()
        assert result == 0