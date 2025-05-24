#!/usr/bin/env python3
"""
Standalone MCP server script for Treasure Data API.
This module is designed to be run directly with the MCP CLI using:
    mcp run /path/to/td_mcp_server/server.py

For Claude Desktop integration, use:
    mcp install server.py -v TD_API_KEY=your-api-key -v TD_ENDPOINT=api.treasuredata.com
"""

import os
import sys

from .mcp_impl import mcp

if __name__ == "__main__":
    # Check for API key
    api_key = os.environ.get("TD_API_KEY")
    endpoint = os.environ.get("TD_ENDPOINT", "api.treasuredata.com")

    if not api_key:
        sys.exit(1)

    # Run the FastMCP server
    try:
        mcp.run(transport="stdio")
    except Exception:
        sys.exit(1)
