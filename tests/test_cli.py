"""Tests for CLI functionality."""

import pytest
from unittest.mock import patch, Mock
from wikijs_mcp.cli import main, setup_encrypted_env
from wikijs_mcp.crypto import EnvEncryption


@pytest.mark.unit
class TestCLI:
    """Test cases for CLI functionality."""
    
    @patch('sys.argv', ['wikijs-env'])
    @patch('argparse.ArgumentParser.print_help')
    def test_main_no_command(self, mock_print_help):
        """Test main with no command shows help."""
        result = main()
        
        assert result == 1
        mock_print_help.assert_called_once()
    
    @patch('sys.argv', ['wikijs-env', 'encrypt'])
    @patch('wikijs_mcp.cli.EnvEncryption')
    def test_main_encrypt_success(self, mock_encryption_class):
        """Test main encrypt command success."""
        mock_encryption = Mock()
        mock_encryption.encrypt_env_file.return_value = True
        mock_encryption_class.return_value = mock_encryption
        
        result = main()
        
        assert result == 0
        mock_encryption.encrypt_env_file.assert_called_with(None)
    
    @patch('sys.argv', ['wikijs-env', 'encrypt', '--password', 'test123'])
    @patch('wikijs_mcp.cli.EnvEncryption')
    def test_main_encrypt_with_password(self, mock_encryption_class):
        """Test main encrypt command with password."""
        mock_encryption = Mock()
        mock_encryption.encrypt_env_file.return_value = True
        mock_encryption_class.return_value = mock_encryption
        
        result = main()
        
        assert result == 0
        mock_encryption.encrypt_env_file.assert_called_with('test123')
    
    @patch('sys.argv', ['wikijs-env', 'encrypt'])
    @patch('wikijs_mcp.cli.EnvEncryption')
    def test_main_encrypt_failure(self, mock_encryption_class):
        """Test main encrypt command failure."""
        mock_encryption = Mock()
        mock_encryption.encrypt_env_file.return_value = False
        mock_encryption_class.return_value = mock_encryption
        
        result = main()
        
        assert result == 1
    
    @patch('sys.argv', ['wikijs-env', 'decrypt'])
    @patch('wikijs_mcp.cli.EnvEncryption')
    def test_main_decrypt_success(self, mock_encryption_class):
        """Test main decrypt command success."""
        mock_encryption = Mock()
        mock_encryption.decrypt_env_file.return_value = True
        mock_encryption_class.return_value = mock_encryption
        
        result = main()
        
        assert result == 0
        mock_encryption.decrypt_env_file.assert_called_with(None, False)
    
    @patch('sys.argv', ['wikijs-env', 'decrypt', '--temp'])
    @patch('wikijs_mcp.cli.EnvEncryption')
    def test_main_decrypt_temp(self, mock_encryption_class):
        """Test main decrypt command with temp flag."""
        mock_encryption = Mock()
        mock_encryption.decrypt_env_file.return_value = True
        mock_encryption_class.return_value = mock_encryption
        
        result = main()
        
        assert result == 0
        mock_encryption.decrypt_env_file.assert_called_with(None, True)
    
    @patch('sys.argv', ['wikijs-env', 'edit', '--editor', 'vim'])
    @patch('wikijs_mcp.cli.EnvEncryption')
    def test_main_edit_success(self, mock_encryption_class):
        """Test main edit command success."""
        mock_encryption = Mock()
        mock_encryption.edit_env_file.return_value = True
        mock_encryption_class.return_value = mock_encryption
        
        result = main()
        
        assert result == 0
        mock_encryption.edit_env_file.assert_called_with('vim')
    
    @patch('sys.argv', ['wikijs-env', 'status'])
    @patch('wikijs_mcp.cli.EnvEncryption')
    def test_main_status(self, mock_encryption_class):
        """Test main status command."""
        mock_encryption = Mock()
        mock_encryption_class.return_value = mock_encryption
        
        result = main()
        
        assert result == 0
        mock_encryption.status.assert_called_once()
    
    @patch('sys.argv', ['wikijs-env', 'setup'])
    @patch('wikijs_mcp.cli.setup_encrypted_env')
    def test_main_setup_success(self, mock_setup):
        """Test main setup command success."""
        mock_setup.return_value = 0
        
        result = main()
        
        assert result == 0
        mock_setup.assert_called_once()
    
    @patch('sys.argv', ['wikijs-env', 'unknown'])
    def test_main_unknown_command(self):
        """Test main with unknown command."""
        result = main()
        
        assert result == 1
    
    @patch('sys.argv', ['wikijs-env', '--env-file', 'custom.env', 'status'])
    @patch('wikijs_mcp.cli.EnvEncryption')
    def test_main_custom_env_file(self, mock_encryption_class):
        """Test main with custom env file."""
        mock_encryption = Mock()
        mock_encryption_class.return_value = mock_encryption
        
        result = main()
        
        assert result == 0
        mock_encryption_class.assert_called_with('custom.env')


@pytest.mark.unit
class TestSetupEncryptedEnv:
    """Test cases for setup_encrypted_env function."""
    
    def test_setup_with_existing_encrypted_file(self, temp_dir, capsys):
        """Test setup when encrypted file already exists."""
        encryption = EnvEncryption(f"{temp_dir}/.env")
        
        with patch.object(encryption, 'has_encrypted_env', return_value=True), \
             patch('builtins.input', return_value='n'):
            
            result = setup_encrypted_env(encryption)
        
        assert result == 0
        captured = capsys.readouterr()
        assert "already exists" in captured.out
    
    def test_setup_edit_existing_encrypted_file(self, temp_dir):
        """Test setup to edit existing encrypted file."""
        encryption = EnvEncryption(f"{temp_dir}/.env")
        
        with patch.object(encryption, 'has_encrypted_env', return_value=True), \
             patch.object(encryption, 'edit_env_file', return_value=True), \
             patch('builtins.input', return_value='y'):
            
            result = setup_encrypted_env(encryption)
        
        assert result == 0
        encryption.edit_env_file.assert_called_once()
    
    def test_setup_encrypt_existing_env_file(self, temp_env_file):
        """Test setup to encrypt existing .env file."""
        encryption = EnvEncryption(temp_env_file)
        
        with patch.object(encryption, 'has_encrypted_env', return_value=False), \
             patch.object(encryption, 'encrypt_env_file', return_value=True), \
             patch('os.path.exists', return_value=True), \
             patch('builtins.input', return_value='y'):
            
            result = setup_encrypted_env(encryption)
        
        assert result == 0
        encryption.encrypt_env_file.assert_called_once()
    
    def test_setup_keep_existing_env_file(self, temp_env_file):
        """Test setup choosing to keep existing .env file."""
        encryption = EnvEncryption(temp_env_file)
        
        with patch.object(encryption, 'has_encrypted_env', return_value=False), \
             patch('os.path.exists', return_value=True), \
             patch('builtins.input', return_value='n'):
            
            result = setup_encrypted_env(encryption)
        
        assert result == 0
    
    @patch('builtins.input')
    def test_setup_create_new_env_file_success(self, mock_input, temp_dir):
        """Test setup creating new .env file successfully."""
        env_path = f"{temp_dir}/.env"
        encryption = EnvEncryption(env_path)
        
        # Mock user inputs
        mock_input.side_effect = [
            'https://test-wiki.com',  # URL
            'test-api-key-123',       # API key
            '/graphql',               # GraphQL endpoint
            'y'                       # Enable debug
        ]
        
        with patch.object(encryption, 'has_encrypted_env', return_value=False), \
             patch.object(encryption, 'encrypt_env_file', return_value=True), \
             patch('os.path.exists', return_value=False):
            
            result = setup_encrypted_env(encryption)
        
        assert result == 0
        
        # Verify .env file was created with correct content
        with open(env_path, 'r') as f:
            content = f.read()
        
        assert 'WIKIJS_URL=https://test-wiki.com' in content
        assert 'WIKIJS_API_KEY=test-api-key-123' in content
        assert 'WIKIJS_GRAPHQL_ENDPOINT=/graphql' in content
        assert 'DEBUG=true' in content
        
        encryption.encrypt_env_file.assert_called_once()
    
    @patch('builtins.input')
    def test_setup_create_new_env_file_missing_url(self, mock_input, temp_dir, capsys):
        """Test setup with missing URL."""
        encryption = EnvEncryption(f"{temp_dir}/.env")
        
        mock_input.side_effect = ['']  # Empty URL
        
        with patch.object(encryption, 'has_encrypted_env', return_value=False), \
             patch('os.path.exists', return_value=False):
            
            result = setup_encrypted_env(encryption)
        
        assert result == 1
        captured = capsys.readouterr()
        assert "Wiki.js URL is required" in captured.out
    
    @patch('builtins.input')
    def test_setup_create_new_env_file_missing_api_key(self, mock_input, temp_dir, capsys):
        """Test setup with missing API key."""
        encryption = EnvEncryption(f"{temp_dir}/.env")
        
        mock_input.side_effect = [
            'https://test-wiki.com',  # URL
            ''                        # Empty API key
        ]
        
        with patch.object(encryption, 'has_encrypted_env', return_value=False), \
             patch('os.path.exists', return_value=False):
            
            result = setup_encrypted_env(encryption)
        
        assert result == 1
        captured = capsys.readouterr()
        assert "API Key is required" in captured.out
    
    @patch('builtins.input')
    def test_setup_create_new_env_file_with_defaults(self, mock_input, temp_dir):
        """Test setup creating new .env file with default values."""
        env_path = f"{temp_dir}/.env"
        encryption = EnvEncryption(env_path)
        
        mock_input.side_effect = [
            'https://test-wiki.com',  # URL
            'test-api-key-123',       # API key
            '',                       # Use default GraphQL endpoint
            'n'                       # Don't enable debug
        ]
        
        with patch.object(encryption, 'has_encrypted_env', return_value=False), \
             patch.object(encryption, 'encrypt_env_file', return_value=True), \
             patch('os.path.exists', return_value=False):
            
            result = setup_encrypted_env(encryption)
        
        assert result == 0
        
        # Verify defaults were used
        with open(env_path, 'r') as f:
            content = f.read()
        
        assert 'WIKIJS_GRAPHQL_ENDPOINT=/graphql' in content  # Default
        assert 'DEBUG=false' in content  # Default
    
    @patch('builtins.input')
    def test_setup_create_new_env_file_write_error(self, mock_input, temp_dir, capsys):
        """Test setup when .env file creation fails."""
        encryption = EnvEncryption(f"{temp_dir}/.env")
        
        mock_input.side_effect = [
            'https://test-wiki.com',
            'test-api-key-123',
            '/graphql',
            'n'
        ]
        
        with patch.object(encryption, 'has_encrypted_env', return_value=False), \
             patch('os.path.exists', return_value=False), \
             patch('builtins.open', side_effect=PermissionError("Permission denied")):
            
            result = setup_encrypted_env(encryption)
        
        assert result == 1
        captured = capsys.readouterr()
        assert "Error creating .env file" in captured.out
    
    @patch('builtins.input')
    def test_setup_encryption_failure(self, mock_input, temp_dir, capsys):
        """Test setup when encryption fails."""
        env_path = f"{temp_dir}/.env"
        encryption = EnvEncryption(env_path)
        
        mock_input.side_effect = [
            'https://test-wiki.com',
            'test-api-key-123',
            '/graphql',
            'n'
        ]
        
        with patch.object(encryption, 'has_encrypted_env', return_value=False), \
             patch.object(encryption, 'encrypt_env_file', return_value=False), \
             patch('os.path.exists', return_value=False):
            
            result = setup_encrypted_env(encryption)
        
        assert result == 1