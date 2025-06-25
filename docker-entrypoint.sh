#!/bin/bash
set -e

# WikiJS MCP Server Docker Entrypoint Script

# Set default config path
export ENV_FILE="/app/.env"

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
        
        # Check if config exists
        if [ -f "$ENV_FILE" ]; then
            print_success "Found configuration file"
        else
            print_error "No configuration found!"
            echo "Please create a .env file in the project root with your WikiJS settings."
            exit 1
        fi
        
        # Start the server
        cd /app
        exec python3 -m wikijs_mcp.server
        ;;
    
    "bash")
        print_info "Starting interactive bash shell..."
        exec /bin/bash
        ;;
    
    "sh")
        print_info "Starting interactive shell..."
        exec /bin/sh
        ;;
    
    "test")
        print_info "Running tests..."
        cd /app
        exec python3 -m pytest tests/
        ;;
    
    "lint")
        print_info "Running code formatting check..."
        cd /app
        exec black --check --diff wikijs_mcp/ tests/
        ;;
    
    "format")
        print_info "Formatting code with black..."
        cd /app
        exec black wikijs_mcp/ tests/
        ;;
    
    "typecheck")
        print_info "Running type checking..."
        cd /app
        exec mypy wikijs_mcp/ --ignore-missing-imports --no-strict-optional
        ;;
    
    "security")
        print_info "Running security scan..."
        cd /app
        exec bandit -r wikijs_mcp/
        ;;
    
    "ci-check")
        print_info "Running full CI checks..."
        cd /app
        echo "=== Code Formatting ==="
        black --check --diff wikijs_mcp/ tests/ || exit 1
        echo "=== Type Checking ==="
        mypy wikijs_mcp/ --ignore-missing-imports --no-strict-optional || exit 1
        echo "=== Security Scan ==="
        bandit -r wikijs_mcp/ || exit 1
        echo "=== Tests ==="
        python3 -m pytest tests/ || exit 1
        print_success "All CI checks passed!"
        ;;
    
    *)
        # If the command is not one of our predefined commands,
        # execute it directly (allows for python3, etc.)
        if command -v "$1" > /dev/null 2>&1; then
            cd /app
            exec "$@"
        else
            print_error "Unknown command: $1"
            echo ""
            echo "Available commands:"
            echo "  server    - Start the MCP server (default)"
            echo "  test      - Run test suite"
            echo "  lint      - Check code formatting"
            echo "  format    - Format code with black"
            echo "  typecheck - Run type checking"
            echo "  security  - Run security scan"
            echo "  ci-check  - Run all CI checks"
            echo "  bash      - Interactive bash shell"
            echo "  sh        - Interactive shell"
            echo ""
            echo "Examples:"
            echo "  docker compose up wikijs-mcp-server"
            echo "  docker compose run --rm wikijs-mcp-server test"
            exit 1
        fi
        ;;
esac