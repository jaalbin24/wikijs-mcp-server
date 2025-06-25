"""Tests for encryption utilities."""

import os
import pytest
from unittest.mock import patch, mock_open
from wikijs_mcp.crypto import EnvEncryption


@pytest.mark.unit
@pytest.mark.crypto
class TestEnvEncryption:
    """Test cases for EnvEncryption class."""
    
    def test_init(self, temp_dir):
        """Test EnvEncryption initialization."""
        env_path = os.path.join(temp_dir, ".env")
        encryption = EnvEncryption(env_path)
        
        assert encryption.env_path == env_path
        assert encryption.encrypted_path == f"{env_path}.encrypted"
    
    def test_derive_key_consistent(self, encryption_instance):
        """Test that key derivation is consistent with same password and salt."""
        password = "test-password"
        salt = b"test-salt-16byte"
        
        key1 = encryption_instance._derive_key(password, salt)
        key2 = encryption_instance._derive_key(password, salt)
        
        assert key1 == key2
        assert len(key1) == 44  # Base64 encoded 32-byte key
    
    def test_derive_key_different_salts(self, encryption_instance):
        """Test that different salts produce different keys."""
        password = "test-password"
        salt1 = b"salt1-16-bytes!!"
        salt2 = b"salt2-16-bytes!!"
        
        key1 = encryption_instance._derive_key(password, salt1)
        key2 = encryption_instance._derive_key(password, salt2)
        
        assert key1 != key2
    
    def test_encrypt_env_file_success(self, temp_env_file, mock_getpass):
        """Test successful encryption of env file."""
        encryption = EnvEncryption(temp_env_file)
        
        with patch('builtins.input', return_value='y'):  # Delete original
            result = encryption.encrypt_env_file("test-password")
        
        assert result is True
        assert os.path.exists(encryption.encrypted_path)
        assert not os.path.exists(temp_env_file)  # Original deleted
    
    def test_encrypt_env_file_keep_original(self, temp_env_file, mock_getpass):
        """Test encryption while keeping original file."""
        encryption = EnvEncryption(temp_env_file)
        
        with patch('builtins.input', return_value='n'):  # Keep original
            result = encryption.encrypt_env_file("test-password")
        
        assert result is True
        assert os.path.exists(encryption.encrypted_path)
        assert os.path.exists(temp_env_file)  # Original kept
    
    def test_encrypt_env_file_no_file(self, encryption_instance):
        """Test encryption when env file doesn't exist."""
        result = encryption_instance.encrypt_env_file("test-password")
        
        assert result is False
    
    def test_decrypt_env_file_success(self, temp_env_file, sample_env_content):
        """Test successful decryption of env file."""
        encryption = EnvEncryption(temp_env_file)
        
        # First encrypt the file
        encryption.encrypt_env_file("test-password")
        os.remove(temp_env_file)  # Remove original
        
        # Then decrypt it
        result = encryption.decrypt_env_file("test-password")
        
        assert result is True
        assert os.path.exists(temp_env_file)
        
        # Verify content
        with open(temp_env_file, 'r') as f:
            content = f.read()
        assert "WIKIJS_URL=https://test-wiki.example.com" in content
    
    def test_decrypt_env_file_wrong_password(self, temp_env_file):
        """Test decryption with wrong password."""
        encryption = EnvEncryption(temp_env_file)
        
        # Encrypt with one password
        encryption.encrypt_env_file("correct-password")
        os.remove(temp_env_file)
        
        # Try to decrypt with wrong password
        result = encryption.decrypt_env_file("wrong-password")
        
        assert result is False
        assert not os.path.exists(temp_env_file)
    
    def test_decrypt_env_file_no_encrypted_file(self, encryption_instance):
        """Test decryption when encrypted file doesn't exist."""
        result = encryption_instance.decrypt_env_file("test-password")
        
        assert result is False
    
    def test_decrypt_temp_file(self, temp_env_file):
        """Test temporary decryption."""
        encryption = EnvEncryption(temp_env_file)
        
        # Encrypt the file
        encryption.encrypt_env_file("test-password")
        os.remove(temp_env_file)
        
        # Decrypt temporarily
        result = encryption.decrypt_env_file("test-password", temp_decrypt=True)
        
        assert result is True
        assert os.path.exists(f"{temp_env_file}.tmp")
        assert not os.path.exists(temp_env_file)
    
    @patch('os.system')
    def test_edit_env_file_success(self, mock_system, temp_env_file, mock_getpass):
        """Test successful editing of encrypted env file."""
        mock_system.return_value = 0  # Success exit code
        encryption = EnvEncryption(temp_env_file)
        
        # Encrypt the file first
        encryption.encrypt_env_file("test-password")
        
        result = encryption.edit_env_file("nano")
        
        assert result is True
        mock_system.assert_called_once()
    
    @patch('os.system')
    def test_edit_env_file_editor_failure(self, mock_system, temp_env_file, mock_getpass):
        """Test editing when editor fails."""
        mock_system.return_value = 1  # Failure exit code
        encryption = EnvEncryption(temp_env_file)
        
        # Encrypt the file first
        encryption.encrypt_env_file("test-password")
        
        result = encryption.edit_env_file("nano")
        
        assert result is False
    
    def test_edit_env_file_no_encrypted_file(self, encryption_instance):
        """Test editing when no encrypted file exists."""
        result = encryption_instance.edit_env_file()
        
        assert result is False
    
    def test_status_no_files(self, encryption_instance, capsys):
        """Test status when no files exist."""
        encryption_instance.status()
        
        captured = capsys.readouterr()
        assert "❌ not found" in captured.out
    
    def test_status_encrypted_file_exists(self, temp_env_file, capsys):
        """Test status when encrypted file exists."""
        encryption = EnvEncryption(temp_env_file)
        
        # Create encrypted file
        encryption.encrypt_env_file("test-password")
        
        encryption.status()
        
        captured = capsys.readouterr()
        assert "✅ exists" in captured.out
    
    def test_status_both_files_exist(self, temp_env_file, capsys):
        """Test status when both files exist."""
        encryption = EnvEncryption(temp_env_file)
        
        # Create encrypted file but keep original
        with patch('builtins.input', return_value='n'):
            encryption.encrypt_env_file("test-password")
        
        encryption.status()
        
        captured = capsys.readouterr()
        assert "⚠️  Warning: Both encrypted and unencrypted files exist!" in captured.out
    
    def test_has_encrypted_env_true(self, temp_env_file):
        """Test has_encrypted_env when encrypted file exists."""
        encryption = EnvEncryption(temp_env_file)
        
        # Create encrypted file
        encryption.encrypt_env_file("test-password")
        
        assert encryption.has_encrypted_env() is True
    
    def test_has_encrypted_env_false(self, encryption_instance):
        """Test has_encrypted_env when encrypted file doesn't exist."""
        assert encryption_instance.has_encrypted_env() is False
    
    @pytest.mark.parametrize("password,confirm,expected", [
        ("pass123", "pass123", True),  # Matching passwords
        ("pass123", "different", False),  # Non-matching passwords
    ])
    def test_encrypt_password_confirmation(self, temp_env_file, password, confirm, expected):
        """Test password confirmation during encryption."""
        encryption = EnvEncryption(temp_env_file)
        
        with patch('getpass.getpass', side_effect=[password, confirm]), \
             patch('builtins.input', return_value='y'):
            
            result = encryption.encrypt_env_file()
            assert result is expected
    
    def test_encrypt_decrypt_roundtrip(self, temp_env_file, sample_env_content):
        """Test full encrypt-decrypt roundtrip preserves content."""
        encryption = EnvEncryption(temp_env_file)
        password = "test-password-123"
        
        # Read original content
        with open(temp_env_file, 'r') as f:
            original_content = f.read()
        
        # Encrypt
        assert encryption.encrypt_env_file(password) is True
        
        # Remove original
        os.remove(temp_env_file)
        
        # Decrypt
        assert encryption.decrypt_env_file(password) is True
        
        # Verify content is preserved
        with open(temp_env_file, 'r') as f:
            decrypted_content = f.read()
        
        assert decrypted_content == original_content