"""Encryption utilities for protecting sensitive configuration files."""

import os
import base64
import getpass
from typing import Optional
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.fernet import Fernet


class EnvEncryption:
    """Handle password-based encryption/decryption of .env files."""
    
    def __init__(self, env_path: str = ".env"):
        self.env_path = env_path
        self.encrypted_path = f"{env_path}.encrypted"
    
    def _derive_key(self, password: str, salt: bytes) -> bytes:
        """Derive encryption key from password using PBKDF2."""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key
    
    def encrypt_env_file(self, password: Optional[str] = None) -> bool:
        """Encrypt the .env file with a password."""
        if not os.path.exists(self.env_path):
            print(f"Error: {self.env_path} not found")
            return False
        
        if password is None:
            password = getpass.getpass("Enter password to encrypt .env file: ")
            confirm = getpass.getpass("Confirm password: ")
            if password != confirm:
                print("Error: Passwords don't match")
                return False
        
        try:
            # Generate random salt
            salt = os.urandom(16)
            
            # Derive key from password
            key = self._derive_key(password, salt)
            fernet = Fernet(key)
            
            # Read and encrypt the .env file
            with open(self.env_path, 'rb') as file:
                env_data = file.read()
            
            encrypted_data = fernet.encrypt(env_data)
            
            # Save encrypted file with salt prepended
            with open(self.encrypted_path, 'wb') as file:
                file.write(salt + encrypted_data)
            
            print(f"✅ Encrypted {self.env_path} → {self.encrypted_path}")
            
            # Ask if user wants to delete original
            delete = input(f"Delete original {self.env_path}? (y/N): ").lower().strip()
            if delete == 'y':
                os.remove(self.env_path)
                print(f"🗑️  Deleted {self.env_path}")
            
            return True
            
        except Exception as e:
            print(f"Error encrypting file: {str(e)}")
            return False
    
    def decrypt_env_file(self, password: Optional[str] = None, temp_decrypt: bool = False) -> bool:
        """Decrypt the .env file with a password."""
        if not os.path.exists(self.encrypted_path):
            print(f"Error: {self.encrypted_path} not found")
            return False
        
        if password is None:
            password = getpass.getpass("Enter password to decrypt .env file: ")
        
        try:
            # Read encrypted file
            with open(self.encrypted_path, 'rb') as file:
                encrypted_content = file.read()
            
            # Extract salt and encrypted data
            salt = encrypted_content[:16]
            encrypted_data = encrypted_content[16:]
            
            # Derive key and decrypt
            key = self._derive_key(password, salt)
            fernet = Fernet(key)
            
            decrypted_data = fernet.decrypt(encrypted_data)
            
            # Write decrypted content
            output_path = self.env_path if not temp_decrypt else f"{self.env_path}.tmp"
            with open(output_path, 'wb') as file:
                file.write(decrypted_data)
            
            if temp_decrypt:
                print(f"✅ Temporarily decrypted to {output_path}")
            else:
                print(f"✅ Decrypted {self.encrypted_path} → {self.env_path}")
            
            return True
            
        except Exception as e:
            print(f"Error decrypting file: {str(e)}")
            print("Check your password and try again")
            return False
    
    def edit_env_file(self, editor: Optional[str] = None) -> bool:
        """Decrypt, edit, and re-encrypt the .env file."""
        if not os.path.exists(self.encrypted_path):
            print(f"Error: {self.encrypted_path} not found")
            print("Create .env file first, then encrypt it")
            return False
        
        password = getpass.getpass("Enter password to edit .env file: ")
        
        # Decrypt temporarily
        if not self.decrypt_env_file(password, temp_decrypt=True):
            return False
        
        temp_file = f"{self.env_path}.tmp"
        
        try:
            # Open editor
            if editor is None:
                editor = os.environ.get('EDITOR', 'nano')
            
            print(f"Opening {temp_file} with {editor}...")
            print("Save and close the editor when done.")
            
            exit_code = os.system(f"{editor} {temp_file}")
            
            if exit_code != 0:
                print(f"Editor exited with code {exit_code}")
                os.remove(temp_file)
                return False
            
            # Check if file was modified
            if not os.path.exists(temp_file):
                print("Error: Temporary file was deleted")
                return False
            
            # Re-encrypt with same password
            original_path = self.env_path
            self.env_path = temp_file
            
            # Generate new salt for re-encryption
            salt = os.urandom(16)
            key = self._derive_key(password, salt)
            fernet = Fernet(key)
            
            with open(temp_file, 'rb') as file:
                env_data = file.read()
            
            encrypted_data = fernet.encrypt(env_data)
            
            with open(self.encrypted_path, 'wb') as file:
                file.write(salt + encrypted_data)
            
            # Clean up
            os.remove(temp_file)
            self.env_path = original_path
            
            print(f"✅ Updated and re-encrypted {self.encrypted_path}")
            return True
            
        except Exception as e:
            print(f"Error editing file: {str(e)}")
            # Clean up temp file
            if os.path.exists(temp_file):
                os.remove(temp_file)
            return False
    
    def status(self) -> None:
        """Show status of .env files."""
        print("Environment file status:")
        print(f"  📄 {self.env_path}: {'✅ exists' if os.path.exists(self.env_path) else '❌ not found'}")
        print(f"  🔒 {self.encrypted_path}: {'✅ exists' if os.path.exists(self.encrypted_path) else '❌ not found'}")
        
        if os.path.exists(self.env_path) and os.path.exists(self.encrypted_path):
            print("\n⚠️  Warning: Both encrypted and unencrypted files exist!")
            print("   Consider deleting the unencrypted .env file for security.")
    
    def has_encrypted_env(self) -> bool:
        """Check if encrypted .env file exists."""
        return os.path.exists(self.encrypted_path)