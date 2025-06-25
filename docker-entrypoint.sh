#!/bin/bash
set -e

# WikiJS MCP Server Docker Entrypoint Script

# Set default config path
export CONFIG_DIR="/app/config"
export ENV_FILE="$CONFIG_DIR/.env"

# Ensure config directory exists
mkdir -p "$CONFIG_DIR"

# Change to config directory for relative paths
cd "$CONFIG_DIR"

# Function to print colored output
print_info() {
    echo -e "\033[1;34m[INFO]\033[0m $1"
}

print_success() {
    echo -e "\033[1;32m[SUCCESS]\033[0m $1"
}

print_error() {
    echo -e "\033[1;31m[ERROR]\033[0m $1"
}

print_warning() {
    echo -e "\033[1;33m[WARNING]\033[0m $1"
}

# Main command handling
case "$1" in
    "server")
        print_info "Starting WikiJS MCP Server..."
        
        # Check if encrypted config exists
        if [ -f "$ENV_FILE.encrypted" ]; then
            print_success "Found encrypted configuration"
        elif [ -f "$ENV_FILE" ]; then
            print_warning "Found unencrypted configuration"
            echo "Consider encrypting it with: docker-compose run --rm wikijs-mcp-server encrypt"
        else
            print_error "No configuration found!"
            echo "Run setup with: docker-compose run --rm wikijs-mcp-server setup"
            exit 1
        fi
        
        # Start the server
        cd /app
        exec python3 -m wikijs_mcp.server
        ;;
    
    "setup")
        print_info "Setting up WikiJS MCP Server configuration..."
        cd /app
        exec python3 -m wikijs_mcp.cli setup --env-file "$ENV_FILE"
        ;;
    
    "encrypt")
        print_info "Encrypting configuration..."
        cd /app
        exec python3 -m wikijs_mcp.cli encrypt --env-file "$ENV_FILE"
        ;;
    
    "decrypt")
        print_info "Decrypting configuration..."
        cd /app
        exec python3 -m wikijs_mcp.cli decrypt --env-file "$ENV_FILE"
        ;;
    
    "edit")
        print_info "Editing encrypted configuration..."
        cd /app
        exec python3 -m wikijs_mcp.cli edit --env-file "$ENV_FILE"
        ;;
    
    "status")
        print_info "Checking configuration status..."
        cd /app
        exec python3 -m wikijs_mcp.cli status --env-file "$ENV_FILE"
        ;;
    
    "bash")
        print_info "Starting interactive bash shell..."
        exec /bin/bash
        ;;
    
    "sh")
        print_info "Starting interactive shell..."
        exec /bin/sh
        ;;
    
    *)
        print_error "Unknown command: $1"
        echo ""
        echo "Available commands:"
        echo "  server   - Start the MCP server (default)"
        echo "  setup    - Interactive configuration setup"
        echo "  encrypt  - Encrypt existing .env file"
        echo "  decrypt  - Decrypt .env.encrypted file"
        echo "  edit     - Edit encrypted configuration"
        echo "  status   - Show configuration status"
        echo "  bash     - Interactive bash shell"
        echo "  sh       - Interactive shell"
        echo ""
        echo "Examples:"
        echo "  docker-compose run --rm wikijs-mcp-server setup"
        echo "  docker-compose run --rm wikijs-mcp-server encrypt"
        echo "  docker-compose up wikijs-mcp-server"
        exit 1
        ;;
esac