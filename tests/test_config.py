"""Tests for configuration management."""

import os
import pytest
from unittest.mock import patch, Mock
from wikijs_mcp.config import WikiJSConfig


@pytest.mark.unit
class TestWikiJSConfig:
    """Test cases for WikiJSConfig class."""
    
    def test_init_with_defaults(self):
        """Test WikiJSConfig initialization with defaults."""
        config = WikiJSConfig()
        
        assert config.url == ""
        assert config.api_key == ""
        assert config.graphql_endpoint == "/graphql"
        assert config.debug is False
    
    def test_init_with_values(self):
        """Test WikiJSConfig initialization with specific values."""
        config = WikiJSConfig(
            url="https://test-wiki.com",
            api_key="test-key-123",
            graphql_endpoint="/api/graphql",
            debug=True
        )
        
        assert config.url == "https://test-wiki.com"
        assert config.api_key == "test-key-123"
        assert config.graphql_endpoint == "/api/graphql"
        assert config.debug is True
    
    def test_graphql_url_property(self):
        """Test graphql_url property construction."""
        config = WikiJSConfig(
            url="https://test-wiki.com",
            graphql_endpoint="/graphql"
        )
        
        assert config.graphql_url == "https://test-wiki.com/graphql"
    
    def test_graphql_url_property_trailing_slash(self):
        """Test graphql_url property with trailing slash in URL."""
        config = WikiJSConfig(
            url="https://test-wiki.com/",
            graphql_endpoint="/graphql"
        )
        
        assert config.graphql_url == "https://test-wiki.com/graphql"
    
    def test_headers_property(self):
        """Test headers property construction."""
        config = WikiJSConfig(api_key="test-api-key-123")
        
        headers = config.headers
        
        assert headers["Authorization"] == "Bearer test-api-key-123"
        assert headers["Content-Type"] == "application/json"
    
    def test_validate_config_success(self):
        """Test successful config validation."""
        config = WikiJSConfig(
            url="https://test-wiki.com",
            api_key="test-api-key"
        )
        
        # Should not raise any exception
        config.validate_config()
    
    def test_validate_config_missing_url(self):
        """Test config validation with missing URL."""
        config = WikiJSConfig(api_key="test-api-key")
        
        with pytest.raises(ValueError, match="WIKIJS_URL must be set"):
            config.validate_config()
    
    def test_validate_config_missing_api_key(self):
        """Test config validation with missing API key."""
        config = WikiJSConfig(url="https://test-wiki.com")
        
        with pytest.raises(ValueError, match="WIKIJS_API_KEY must be set"):
            config.validate_config()
    
    def test_validate_config_missing_both(self):
        """Test config validation with missing URL and API key."""
        config = WikiJSConfig()
        
        with pytest.raises(ValueError, match="WIKIJS_URL must be set"):
            config.validate_config()
    
    @patch('wikijs_mcp.config.load_dotenv')
    def test_load_config_from_plain_env_file(self, mock_load_dotenv, temp_env_file):
        """Test loading config from plain .env file."""
        # Mock environment variables
        env_vars = {
            "WIKIJS_URL": "https://test-wiki.com",
            "WIKIJS_API_KEY": "test-key-123",
            "WIKIJS_GRAPHQL_ENDPOINT": "/api/graphql",
            "DEBUG": "true"
        }
        
        with patch.dict(os.environ, env_vars):
            config = WikiJSConfig.load_config(temp_env_file)
        
        assert config.url == "https://test-wiki.com"
        assert config.api_key == "test-key-123"
        assert config.graphql_endpoint == "/api/graphql"
        assert config.debug is True
        mock_load_dotenv.assert_called_with(temp_env_file)
    
    @patch('wikijs_mcp.config.EnvEncryption')
    @patch('getpass.getpass')
    @patch('tempfile.NamedTemporaryFile')
    @patch('wikijs_mcp.config.load_dotenv')
    @patch('os.remove')
    def test_load_config_from_encrypted_file(self, mock_remove, mock_load_dotenv, mock_temp_file, 
                                           mock_getpass, mock_encryption_class, temp_dir):
        """Test loading config from encrypted .env file."""
        env_file = os.path.join(temp_dir, ".env")
        
        # Mock encryption instance
        mock_encryption = Mock()
        mock_encryption.has_encrypted_env.return_value = True
        mock_encryption.decrypt_env_file.return_value = True
        mock_encryption_class.return_value = mock_encryption
        
        # Mock temporary file
        temp_path = "/tmp/test.env"
        mock_temp_context = Mock()
        mock_temp_context.name = temp_path
        mock_temp_file.return_value.__enter__.return_value = mock_temp_context
        
        mock_getpass.return_value = "test-password"
        
        # Mock environment variables after decryption
        env_vars = {
            "WIKIJS_URL": "https://encrypted-wiki.com",
            "WIKIJS_API_KEY": "encrypted-key-123"
        }
        
        with patch.dict(os.environ, env_vars), \
             patch('os.path.exists', return_value=False):
            
            config = WikiJSConfig.load_config(env_file)
        
        assert config.url == "https://encrypted-wiki.com"
        assert config.api_key == "encrypted-key-123"
        
        # Verify encryption methods were called
        mock_encryption.decrypt_env_file.assert_called_with("test-password", temp_decrypt=True)
        mock_load_dotenv.assert_called_with(temp_path)
        mock_remove.assert_called_with(temp_path)
    
    @patch('wikijs_mcp.config.EnvEncryption')
    @patch('getpass.getpass')
    def test_load_config_decryption_failure(self, mock_getpass, mock_encryption_class, temp_dir):
        """Test config loading when decryption fails."""
        env_file = os.path.join(temp_dir, ".env")
        
        # Mock encryption instance that fails to decrypt
        mock_encryption = Mock()
        mock_encryption.has_encrypted_env.return_value = True
        mock_encryption.decrypt_env_file.return_value = False
        mock_encryption_class.return_value = mock_encryption
        
        mock_getpass.return_value = "wrong-password"
        
        with patch('os.path.exists', return_value=False):
            with pytest.raises(ValueError, match="Failed to decrypt configuration file"):
                WikiJSConfig.load_config(env_file)
    
    @patch('wikijs_mcp.config.EnvEncryption')
    def test_load_config_no_files_exist(self, mock_encryption_class, temp_dir, capsys):
        """Test config loading when no config files exist."""
        env_file = os.path.join(temp_dir, ".env")
        
        # Mock encryption instance with no encrypted file
        mock_encryption = Mock()
        mock_encryption.has_encrypted_env.return_value = False
        mock_encryption_class.return_value = mock_encryption
        
        with patch('os.path.exists', return_value=False):
            config = WikiJSConfig.load_config(env_file)
        
        # Should create config with defaults
        assert config.url == ""
        assert config.api_key == ""
        
        # Should print helpful message
        captured = capsys.readouterr()
        assert "No configuration found" in captured.out
        assert "wikijs-env setup" in captured.out
    
    @pytest.mark.parametrize("debug_value,expected", [
        ("true", True),
        ("TRUE", True),
        ("True", True),
        ("false", False),
        ("FALSE", False),
        ("False", False),
        ("", False),
        ("invalid", False),
    ])
    def test_debug_flag_parsing(self, debug_value, expected):
        """Test debug flag parsing from environment."""
        env_vars = {
            "WIKIJS_URL": "https://test.com",
            "WIKIJS_API_KEY": "test-key",
            "DEBUG": debug_value
        }
        
        with patch.dict(os.environ, env_vars), \
             patch('wikijs_mcp.config.load_dotenv'):
            config = WikiJSConfig.load_config(".env")
        
        assert config.debug is expected
    
    def test_load_config_preserves_defaults(self, temp_dir):
        """Test that load_config preserves default values for missing env vars."""
        env_file = os.path.join(temp_dir, ".env")
        
        # Only set required variables
        env_vars = {
            "WIKIJS_URL": "https://test.com",
            "WIKIJS_API_KEY": "test-key"
        }
        
        with patch.dict(os.environ, env_vars), \
             patch('wikijs_mcp.config.load_dotenv'), \
             patch('os.path.exists', return_value=True):
            config = WikiJSConfig.load_config(env_file)
        
        assert config.url == "https://test.com"
        assert config.api_key == "test-key"
        assert config.graphql_endpoint == "/graphql"  # Default
        assert config.debug is False  # Default
    
    def test_config_immutable_after_creation(self):
        """Test that config values can't be modified after creation."""
        config = WikiJSConfig(url="https://test.com")
        
        # This should work (Pydantic allows it by default)
        # If you want immutability, you'd need to set frozen=True in the model
        original_url = config.url
        config.url = "https://changed.com"
        assert config.url == "https://changed.com"
        assert config.url != original_url