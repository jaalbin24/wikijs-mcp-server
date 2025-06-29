"""Command-line interface for WikiJS MCP Server."""

import sys


def main():
    """Main CLI entry point."""
    print("The encryption feature has been removed from WikiJS MCP Server.")
    print("Please create a plain .env file with your WikiJS configuration:")
    print("")
    print("WIKIJS_URL=https://your-wiki-instance.com")
    print("WIKIJS_API_KEY=your-api-key")
    print("WIKIJS_GRAPHQL_ENDPOINT=/graphql")
    print("DEBUG=false")
    return 0


if __name__ == "__main__":
    sys.exit(main())
