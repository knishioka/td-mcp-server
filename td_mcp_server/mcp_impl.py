"""
MCP server implementation using FastMCP for Treasure Data API.
This module provides a FastMCP server for Treasure Data API.
"""

import os
import sys
import traceback
from typing import Dict, Any, Optional

from mcp.server.fastmcp import FastMCP

from .api import TreasureDataClient, Database


# Initialize FastMCP server
mcp = FastMCP("treasure-data")


@mcp.tool()
async def td_list_databases() -> Dict[str, Any]:
    """Get all databases in your Treasure Data account.
    """
    api_key = os.environ.get("TD_API_KEY")
    endpoint = os.environ.get("TD_ENDPOINT", "api.treasuredata.com")
    
    if not api_key:
        return {
            "error": "TD_API_KEY environment variable is not set"
        }
    
    try:
        client = TreasureDataClient(api_key=api_key, endpoint=endpoint)
        databases = client.get_databases()
        return {
            "databases": [db.model_dump() for db in databases]
        }
    except Exception as e:
        return {
            "error": str(e),
            "traceback": traceback.format_exc()
        }


@mcp.tool()
async def td_get_database(database_name: str) -> Dict[str, Any]:
    """Get information about a specific database.
    
    Args:
        database_name: The name of the database to retrieve information for
    """
    api_key = os.environ.get("TD_API_KEY")
    endpoint = os.environ.get("TD_ENDPOINT", "api.treasuredata.com")
    
    if not api_key:
        return {
            "error": "TD_API_KEY environment variable is not set"
        }
    
    try:
        client = TreasureDataClient(api_key=api_key, endpoint=endpoint)
        database = client.get_database(database_name)
        if database:
            return database.model_dump()
        else:
            return {
                "error": f"Database '{database_name}' not found."
            }
    except Exception as e:
        return {
            "error": str(e),
            "traceback": traceback.format_exc()
        }


if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio')