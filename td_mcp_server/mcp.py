"""
MCP server entry point for Treasure Data API.
This module provides a simple entry point for 'uv run mcp' to work.
"""

import os
from .mcp_server import MCPServer


def main():
    """
    Entry point for the MCP server.
    This function is called when running 'uv run mcp' or 'python -m mcp'.
    """
    api_key = os.environ.get("TD_API_KEY")
    endpoint = os.environ.get("TD_ENDPOINT", "api.treasuredata.com")
    
    print("Starting Treasure Data MCP Server...")
    print(f"API Endpoint: {endpoint}")
    
    if not api_key:
        print("ERROR: TD_API_KEY environment variable is not set")
        print("Please set your API key using: export TD_API_KEY='your-api-key'")
        return 1
        
    print("Waiting for MCP requests...")
    
    try:
        server = MCPServer(api_key=api_key, endpoint=endpoint)
        server.serve()
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return 1
        
    return 0


if __name__ == "__main__":
    main()