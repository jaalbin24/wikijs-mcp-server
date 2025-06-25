"""Configuration management for WikiJS MCP Server."""

import os
import getpass
import tempfile
from typing import Optional
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from .crypto import EnvEncryption


class WikiJSConfig(BaseModel):
    """Configuration for Wiki.js connection."""
    
    url: str = Field(default="")
    api_key: str = Field(default="")
    graphql_endpoint: str = Field(default="/graphql")
    debug: bool = Field(default=False)
    
    @classmethod
    def load_config(cls, env_file: str = ".env") -> "WikiJSConfig":
        """Load configuration from .env file (encrypted or plain)."""
        encryption = EnvEncryption(env_file)
        
        # Try to load from regular .env first
        if os.path.exists(env_file):
            load_dotenv(env_file)
        elif encryption.has_encrypted_env():
            # Load from encrypted file
            password = getpass.getpass("Enter password to decrypt configuration: ")
            
            # Create temporary file for decryption
            with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as temp_file:
                temp_path = temp_file.name
            
            try:
                # Temporarily decrypt to temp file
                original_path = encryption.env_path
                encryption.env_path = temp_path
                
                if not encryption.decrypt_env_file(password, temp_decrypt=True):
                    raise ValueError("Failed to decrypt configuration file")
                
                # Load from temp file
                load_dotenv(temp_path)
                
            finally:
                # Clean up temp file
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                encryption.env_path = original_path
        else:
            # No configuration found
            print("No configuration found. Run 'wikijs-env setup' to create encrypted config.")
        
        return cls(
            url=os.getenv("WIKIJS_URL", ""),
            api_key=os.getenv("WIKIJS_API_KEY", ""),
            graphql_endpoint=os.getenv("WIKIJS_GRAPHQL_ENDPOINT", "/graphql"),
            debug=os.getenv("DEBUG", "false").lower() == "true"
        )
    
    @property
    def graphql_url(self) -> str:
        """Get the full GraphQL endpoint URL."""
        return f"{self.url.rstrip('/')}{self.graphql_endpoint}"
    
    @property
    def headers(self) -> dict[str, str]:
        """Get authentication headers for API requests."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
    
    def validate_config(self) -> None:
        """Validate that required configuration is present."""
        if not self.url:
            raise ValueError("WIKIJS_URL must be set. Run 'wikijs-env setup' to configure.")
        if not self.api_key:
            raise ValueError("WIKIJS_API_KEY must be set. Run 'wikijs-env setup' to configure.")