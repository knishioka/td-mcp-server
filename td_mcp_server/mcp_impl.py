"""
MCP server implementation using FastMCP for Treasure Data API.
This module provides a FastMCP server for Treasure Data API.
"""

import os
import sys
import traceback
from typing import Dict, Any, Optional, List

from mcp.server.fastmcp import FastMCP

from .api import TreasureDataClient, Database, Table


# Initialize FastMCP server
mcp = FastMCP("treasure-data")


@mcp.tool()
async def td_list_databases(verbose: bool = False, limit: int = 30, offset: int = 0, all_results: bool = False) -> Dict[str, Any]:
    """Get databases in your Treasure Data account with pagination support.
    
    Args:
        verbose: If True, return full database details; if False, return only database names (default)
        limit: Maximum number of databases to retrieve (defaults to 30)
        offset: Index to start retrieving from (defaults to 0)
        all_results: If True, retrieves all databases ignoring limit and offset
    """
    api_key = os.environ.get("TD_API_KEY")
    endpoint = os.environ.get("TD_ENDPOINT", "api.treasuredata.com")
    
    if not api_key:
        return {
            "error": "TD_API_KEY environment variable is not set"
        }
    
    try:
        client = TreasureDataClient(api_key=api_key, endpoint=endpoint)
        databases = client.get_databases(limit=limit, offset=offset, all_results=all_results)
        
        if verbose:
            # Return full database details
            return {
                "databases": [db.model_dump() for db in databases]
            }
        else:
            # Return only database names
            return {
                "databases": [db.name for db in databases]
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


@mcp.tool()
async def td_list_tables(database_name: str, verbose: bool = False, limit: int = 30, offset: int = 0, all_results: bool = False) -> Dict[str, Any]:
    """Get tables in a specific Treasure Data database with pagination support.
    
    Args:
        database_name: The name of the database to retrieve tables from
        verbose: If True, return full table details; if False, return only table names (default)
        limit: Maximum number of tables to retrieve (defaults to 30)
        offset: Index to start retrieving from (defaults to 0)
        all_results: If True, retrieves all tables ignoring limit and offset
    """
    api_key = os.environ.get("TD_API_KEY")
    endpoint = os.environ.get("TD_ENDPOINT", "api.treasuredata.com")
    
    if not api_key:
        return {
            "error": "TD_API_KEY environment variable is not set"
        }
    
    try:
        client = TreasureDataClient(api_key=api_key, endpoint=endpoint)
        
        # First, verify that the database exists
        database = client.get_database(database_name)
        if not database:
            return {
                "error": f"Database '{database_name}' not found."
            }
        
        # Get tables for the database
        tables = client.get_tables(database_name, limit=limit, offset=offset, all_results=all_results)
        
        if verbose:
            # Return full table details
            return {
                "database": database_name,
                "tables": [table.model_dump() for table in tables]
            }
        else:
            # Return only table names
            return {
                "database": database_name,
                "tables": [table.name for table in tables]
            }
    except Exception as e:
        return {
            "error": str(e),
            "traceback": traceback.format_exc()
        }


if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio')