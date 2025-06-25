# WikiJS MCP Server

A Model Context Protocol (MCP) server for integrating with Wiki.js instances, enabling Claude to read and update documentation.

## Features

- **Search Pages**: Find pages by title or content
- **Read Pages**: Get full page content by path or ID
- **List Pages**: Browse all pages with pagination
- **Page Tree**: View wiki structure as a tree
- **Create Pages**: Add new documentation pages
- **Update Pages**: Modify existing page content
- **Authentication**: Secure API key-based access

## Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd wikijs-mcp
```

2. Install dependencies:
```bash
pip install -e .
```

3. Configure environment:
```bash
cp .env.example .env
# Edit .env with your Wiki.js details
```

## Configuration

Create a `.env` file with your Wiki.js configuration:

```env
WIKIJS_URL=https://your-wiki.example.com
WIKIJS_API_KEY=your_api_key_here
WIKIJS_GRAPHQL_ENDPOINT=/graphql  # Optional, defaults to /graphql
DEBUG=false  # Optional, enables debug logging
```

### Getting Wiki.js API Key

1. Log into your Wiki.js admin panel
2. Go to **Administration** → **API Access**
3. Enable the API if not already enabled
4. Click **New API Key**
5. Set appropriate permissions for your use case
6. Add the key to your `.env` file

## Usage

### 🐳 Docker (Recommended)

#### Quick Start with Docker

1. **Create your `.env` file** in the `config/` directory with your WikiJS settings

2. **Start the server:**
```bash
docker compose up -d wikijs-mcp-server
```

3. **View logs:**
```bash
docker compose logs -f wikijs-mcp-server
```

#### Docker Management Commands

```bash
# Start server in background
docker compose up -d wikijs-mcp-server

# Access interactive shell
docker-compose run --rm wikijs-mcp-server bash

# Stop server
docker compose down
```

#### Docker with Claude Code

Add to your Claude Code MCP configuration:

```json
{
  "mcpServers": {
    "wikijs": {
      "command": "docker",
      "args": ["exec", "-i", "wikijs-mcp-server", "python3", "-m", "wikijs_mcp.server"],
      "env": {
        "DOCKER_CONTAINER": "wikijs-mcp-server"
      }
    }
  }
}
```

### Standalone Server

Run the server directly:
```bash
python -m wikijs_mcp.server
```

### With Claude Code (Native)

Add to your Claude Code MCP configuration:

```json
{
  "mcpServers": {
    "wikijs": {
      "command": "python3",
      "args": ["-m", "wikijs_mcp.server"],
      "cwd": "/path/to/wikijs-mcp"
    }
  }
}
```

## Available Tools

### `wiki_search`
Search for pages by title or content.
- **Parameters**: `query` (string), `limit` (optional integer)

### `wiki_get_page`
Get a specific page by path or ID.
- **Parameters**: `path` (string) OR `id` (integer)

### `wiki_list_pages`
List all pages with pagination.
- **Parameters**: `limit` (optional integer), `offset` (optional integer)

### `wiki_get_tree`
Get wiki page tree structure.
- **Parameters**: `parent_path` (optional string)

### `wiki_create_page`
Create a new wiki page.
- **Parameters**: `path` (string), `title` (string), `content` (string), `description` (optional), `tags` (optional array)

### `wiki_update_page`
Update an existing wiki page.
- **Parameters**: `id` (integer), `content` (string), `title` (optional), `description` (optional), `tags` (optional array)

## Example Usage with Claude

```
# Search for documentation
"Search for pages about authentication"

# Read a specific page
"Get the content of the page at path 'docs/api/authentication'"

# Update documentation
"Update page ID 123 with improved authentication examples"

# Create new documentation
"Create a new page at 'docs/troubleshooting/common-issues' with troubleshooting guide"
```

## Development

### Setup Development Environment

Install development dependencies:
```bash
pip install -e ".[dev]"
```

### Testing

The project has comprehensive test coverage with pytest:

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=wikijs_mcp --cov-report=html

# Run specific test categories
pytest -m unit          # Unit tests only
pytest -m integration   # Integration tests only

# Run tests in parallel (faster)
pytest -n auto
```

### Test Categories

- **Unit tests** (`-m unit`): Fast, isolated component tests
- **Integration tests** (`-m integration`): Full MCP server functionality tests  
- **Network tests** (`-m network`): Tests requiring network access (skipped by default)

### Code Quality

Format code:
```bash
black wikijs_mcp/ tests/
```

Type checking:
```bash
mypy wikijs_mcp/
```

Security scanning:
```bash
bandit -r wikijs_mcp/
safety check
```

### Docker Testing

Test the Docker build:
```bash
docker compose build
docker-compose run --rm wikijs-mcp-server bash
```

### CI/CD

The project uses GitHub Actions for:
- ✅ **Multi-Python testing** (3.8-3.12)
- ✅ **Code quality checks** (black, mypy)
- ✅ **Security scanning** (bandit, safety)
- ✅ **Docker build testing**
- ✅ **Coverage reporting** (Codecov)

## Requirements

- Python 3.8+
- Wiki.js 2.2+ (for API access)
- Valid Wiki.js API key with appropriate permissions

## License

MIT License