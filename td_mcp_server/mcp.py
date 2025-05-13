"""
MCP server entry point for Treasure Data API using FastMCP.
This module provides a simple entry point for 'uv run mcp' to work with FastMCP.
"""

import os
import sys
from .mcp_impl import mcp


def main():
    """
    Entry point for the MCP server using FastMCP.
    This function is called when running 'uv run mcp' or 'python -m mcp'.
    """
    api_key = os.environ.get("TD_API_KEY")
    endpoint = os.environ.get("TD_ENDPOINT", "api.treasuredata.com")
    
    print("Starting Treasure Data MCP Server with FastMCP...", file=sys.stderr)
    print(f"API Endpoint: {endpoint}", file=sys.stderr)
    
    if not api_key:
        print("ERROR: TD_API_KEY environment variable is not set", file=sys.stderr)
        print("Please set your API key using: export TD_API_KEY='your-api-key'", file=sys.stderr)
        return 1
        
    print("Initializing FastMCP server...", file=sys.stderr)
    
    try:
        # Run the FastMCP server with stdio transport
        print("Waiting for MCP requests...", file=sys.stderr)
        mcp.run(transport='stdio')
    except Exception as e:
        print(f"ERROR: {str(e)}", file=sys.stderr)
        return 1
        
    return 0


if __name__ == "__main__":
    main()