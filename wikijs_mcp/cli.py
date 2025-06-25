"""Command-line interface for WikiJS MCP Server encryption utilities."""

import sys
import argparse
from .crypto import EnvEncryption


def main():
    """Main CLI entry point for encryption utilities."""
    parser = argparse.ArgumentParser(
        description="WikiJS MCP Server - Environment Encryption Utilities",
        prog="wikijs-env"
    )
    
    parser.add_argument(
        "--env-file",
        default=".env",
        help="Path to .env file (default: .env)"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Encrypt command
    encrypt_parser = subparsers.add_parser("encrypt", help="Encrypt .env file")
    encrypt_parser.add_argument(
        "--password",
        help="Password for encryption (will prompt if not provided)"
    )
    
    # Decrypt command
    decrypt_parser = subparsers.add_parser("decrypt", help="Decrypt .env file")
    decrypt_parser.add_argument(
        "--password",
        help="Password for decryption (will prompt if not provided)"
    )
    decrypt_parser.add_argument(
        "--temp",
        action="store_true",
        help="Decrypt to temporary file"
    )
    
    # Edit command
    edit_parser = subparsers.add_parser("edit", help="Edit encrypted .env file")
    edit_parser.add_argument(
        "--editor",
        help="Editor to use (default: $EDITOR or nano)"
    )
    
    # Status command
    subparsers.add_parser("status", help="Show .env file status")
    
    # Setup command for initial configuration
    subparsers.add_parser("setup", help="Setup encrypted .env file")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    encryption = EnvEncryption(args.env_file)
    
    if args.command == "encrypt":
        success = encryption.encrypt_env_file(args.password)
        return 0 if success else 1
    
    elif args.command == "decrypt":
        success = encryption.decrypt_env_file(args.password, args.temp)
        return 0 if success else 1
    
    elif args.command == "edit":
        success = encryption.edit_env_file(args.editor)
        return 0 if success else 1
    
    elif args.command == "status":
        encryption.status()
        return 0
    
    elif args.command == "setup":
        return setup_encrypted_env(encryption)
    
    else:
        print(f"Unknown command: {args.command}")
        return 1


def setup_encrypted_env(encryption: EnvEncryption) -> int:
    """Interactive setup for encrypted .env file."""
    import os
    
    print("🔐 WikiJS MCP Server Environment Setup")
    print("=====================================")
    
    # Check current state
    has_env = os.path.exists(encryption.env_path)
    has_encrypted = encryption.has_encrypted_env()
    
    if has_encrypted:
        print(f"✅ Encrypted environment file already exists at {encryption.encrypted_path}")
        edit = input("Would you like to edit it? (y/N): ").lower().strip()
        if edit == 'y':
            return 0 if encryption.edit_env_file() else 1
        return 0
    
    if has_env:
        print(f"📄 Found existing {encryption.env_path}")
        encrypt = input("Would you like to encrypt it? (Y/n): ").lower().strip()
        if encrypt != 'n':
            return 0 if encryption.encrypt_env_file() else 1
        return 0
    
    # Create new .env file
    print(f"📝 Creating new {encryption.env_path} file...")
    print("Please provide your Wiki.js configuration:")
    
    wikijs_url = input("Wiki.js URL (e.g., https://wiki-prod.kriib.com): ").strip()
    if not wikijs_url:
        print("Error: Wiki.js URL is required")
        return 1
    
    wikijs_api_key = input("Wiki.js API Key: ").strip()
    if not wikijs_api_key:
        print("Error: API Key is required")
        return 1
    
    graphql_endpoint = input("GraphQL endpoint [/graphql]: ").strip() or "/graphql"
    debug = input("Enable debug logging? (y/N): ").lower().strip() == 'y'
    
    # Create .env file
    env_content = f"""# Wiki.js Configuration
WIKIJS_URL={wikijs_url}
WIKIJS_API_KEY={wikijs_api_key}
WIKIJS_GRAPHQL_ENDPOINT={graphql_endpoint}
DEBUG={str(debug).lower()}
"""
    
    try:
        with open(encryption.env_path, 'w') as f:
            f.write(env_content)
        print(f"✅ Created {encryption.env_path}")
        
        # Encrypt immediately
        print("🔒 Encrypting configuration file...")
        success = encryption.encrypt_env_file()
        return 0 if success else 1
        
    except Exception as e:
        print(f"Error creating .env file: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())