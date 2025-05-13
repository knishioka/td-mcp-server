"""
Command-line interface for Treasure Data API.
This module provides simple command-line access to the Treasure Data API client.
"""

import os
import sys
import json
import argparse
from typing import Optional, List, Dict, Any
from .api import TreasureDataClient, Database, Table


def list_databases(api_key: Optional[str] = None, endpoint: str = "api.treasuredata.com", 
                   format_output: str = "table", verbose: bool = False,
                   limit: int = 30, offset: int = 0, all_results: bool = False) -> None:
    """
    List databases in your Treasure Data account with pagination support.
    
    Args:
        api_key: Treasure Data API key (if not provided, uses TD_API_KEY env var)
        endpoint: API endpoint to use
        format_output: Output format (table or json)
        verbose: If True, show all database details; if False, show only names
        limit: Maximum number of databases to retrieve (defaults to 30)
        offset: Index to start retrieving from (defaults to 0)
        all_results: If True, retrieves all databases ignoring limit and offset
    """
    try:
        client = TreasureDataClient(api_key=api_key, endpoint=endpoint)
        databases = client.get_databases(limit=limit, offset=offset, all_results=all_results)
        
        if format_output == "json":
            # Output as JSON
            if verbose:
                db_list = [db.model_dump() for db in databases]
            else:
                db_list = [db.name for db in databases]
            print(json.dumps(db_list, indent=2))
        else:
            # Output as table
            if not databases:
                print("No databases found.")
                return
                
            if verbose:
                # Format as a detailed table
                headers = ["Name", "Tables", "Created", "Updated", "Permission", "Protected"]
                
                # Print headers
                print(" | ".join(headers))
                print("-" * (sum(len(h) for h in headers) + len(headers) * 3 - 2))
                
                # Print each row
                for db in databases:
                    row = [
                        db.name,
                        str(db.count),
                        db.created_at,
                        db.updated_at,
                        db.permission,
                        "Yes" if db.delete_protected else "No"
                    ]
                    print(" | ".join(row))
            else:
                # Only show database names
                for db in databases:
                    print(db.name)
    
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)


def get_database(database_name: str, api_key: Optional[str] = None, 
                 endpoint: str = "api.treasuredata.com", format_output: str = "json") -> None:
    """
    Get information about a specific database.
    
    Args:
        database_name: Name of the database to retrieve
        api_key: Treasure Data API key (if not provided, uses TD_API_KEY env var)
        endpoint: API endpoint to use
        format_output: Output format (table or json)
    """
    try:
        client = TreasureDataClient(api_key=api_key, endpoint=endpoint)
        database = client.get_database(database_name)
        
        if not database:
            print(f"Database '{database_name}' not found.", file=sys.stderr)
            sys.exit(1)
            
        if format_output == "json":
            # Output as JSON
            print(json.dumps(database.model_dump(), indent=2))
        else:
            # Output as a simple table of key-value pairs
            for key, value in database.model_dump().items():
                print(f"{key.replace('_', ' ').title()}: {value}")
    
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)


def list_tables(database_name: str, api_key: Optional[str] = None, 
                endpoint: str = "api.treasuredata.com", format_output: str = "table", 
                verbose: bool = False, limit: int = 30, offset: int = 0, all_results: bool = False) -> None:
    """
    List tables in a specific database with pagination support.
    
    Args:
        database_name: Name of the database to retrieve tables from
        api_key: Treasure Data API key (if not provided, uses TD_API_KEY env var)
        endpoint: API endpoint to use
        format_output: Output format (table or json)
        verbose: If True, show all table details; if False, show only names
        limit: Maximum number of tables to retrieve (defaults to 30)
        offset: Index to start retrieving from (defaults to 0)
        all_results: If True, retrieves all tables ignoring limit and offset
    """
    try:
        client = TreasureDataClient(api_key=api_key, endpoint=endpoint)
        tables = client.get_tables(database_name, limit=limit, offset=offset, all_results=all_results)
        
        if format_output == "json":
            # Output as JSON
            if verbose:
                table_list = [table.model_dump() for table in tables]
            else:
                table_list = [table.name for table in tables]
            print(json.dumps(table_list, indent=2))
        else:
            # Output as table
            if not tables:
                print(f"No tables found in database '{database_name}'.", file=sys.stderr)
                return
                
            if verbose:
                # Format as a detailed table
                headers = ["Name", "Type", "Count", "Size (bytes)", "Created", "Updated", "Protected"]
                
                # Print headers
                print(" | ".join(headers))
                print("-" * (sum(len(h) for h in headers) + len(headers) * 3 - 2))
                
                # Print each row
                for table in tables:
                    row = [
                        table.name,
                        table.type,
                        str(table.count),
                        str(table.estimated_storage_size),
                        table.created_at,
                        table.updated_at,
                        "Yes" if table.delete_protected else "No"
                    ]
                    print(" | ".join(row))
            else:
                # Only show table names
                for table in tables:
                    print(table.name)
    
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)


def main_list_db():
    """Entry point for the list-db command."""
    parser = argparse.ArgumentParser(description="List databases in your Treasure Data account")
    parser.add_argument("--api-key", help="Treasure Data API key (if not provided, uses TD_API_KEY env var)")
    parser.add_argument("--endpoint", default="api.treasuredata.com", 
                      help="API endpoint (default: api.treasuredata.com for US, use api.treasuredata.co.jp for Japan)")
    parser.add_argument("--format", dest="format_output", choices=["table", "json"], default="table", 
                      help="Output format (table or json)")
    parser.add_argument("--verbose", "-v", action="store_true", 
                      help="Show detailed information about databases (default: show only names)")
    parser.add_argument("--limit", type=int, default=30,
                      help="Maximum number of databases to retrieve (default: 30)")
    parser.add_argument("--offset", type=int, default=0,
                      help="Index to start retrieving from (default: 0)")
    parser.add_argument("--all", action="store_true", dest="all_results",
                      help="Retrieve all databases ignoring limit and offset")
    
    args = parser.parse_args()
    list_databases(api_key=args.api_key, endpoint=args.endpoint, format_output=args.format_output, 
                 verbose=args.verbose, limit=args.limit, offset=args.offset, all_results=args.all_results)


def main_get_db():
    """Entry point for the get-db command."""
    parser = argparse.ArgumentParser(description="Get information about a specific database")
    parser.add_argument("database_name", help="Name of the database to retrieve")
    parser.add_argument("--api-key", help="Treasure Data API key (if not provided, uses TD_API_KEY env var)")
    parser.add_argument("--endpoint", default="api.treasuredata.com", 
                      help="API endpoint (default: api.treasuredata.com for US, use api.treasuredata.co.jp for Japan)")
    parser.add_argument("--format", dest="format_output", choices=["table", "json"], default="json", 
                      help="Output format (table or json)")
    
    args = parser.parse_args()
    get_database(database_name=args.database_name, api_key=args.api_key, 
                 endpoint=args.endpoint, format_output=args.format_output)


def main_list_tables():
    """Entry point for the list-tables command."""
    parser = argparse.ArgumentParser(description="List tables in a specific database")
    parser.add_argument("database_name", help="Name of the database to retrieve tables from")
    parser.add_argument("--api-key", help="Treasure Data API key (if not provided, uses TD_API_KEY env var)")
    parser.add_argument("--endpoint", default="api.treasuredata.com", 
                      help="API endpoint (default: api.treasuredata.com for US, use api.treasuredata.co.jp for Japan)")
    parser.add_argument("--format", dest="format_output", choices=["table", "json"], default="table", 
                      help="Output format (table or json)")
    parser.add_argument("--verbose", "-v", action="store_true", 
                      help="Show detailed information about tables (default: show only names)")
    parser.add_argument("--limit", type=int, default=30,
                      help="Maximum number of tables to retrieve (default: 30)")
    parser.add_argument("--offset", type=int, default=0,
                      help="Index to start retrieving from (default: 0)")
    parser.add_argument("--all", action="store_true", dest="all_results",
                      help="Retrieve all tables ignoring limit and offset")
    
    args = parser.parse_args()
    list_tables(database_name=args.database_name, api_key=args.api_key, endpoint=args.endpoint, 
                format_output=args.format_output, verbose=args.verbose, limit=args.limit, 
                offset=args.offset, all_results=args.all_results)


def main_td_mcp():
    """Entry point for the td-mcp command to start MCP server using FastMCP."""
    parser = argparse.ArgumentParser(description="Start Treasure Data MCP server")
    parser.add_argument("--api-key", help="Treasure Data API key (if not provided, uses TD_API_KEY env var)")
    parser.add_argument("--endpoint", default="api.treasuredata.com", 
                      help="API endpoint (default: api.treasuredata.com for US, use api.treasuredata.co.jp for Japan)")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    # Set environment variables for the MCP implementation
    if args.api_key:
        os.environ["TD_API_KEY"] = args.api_key
    
    if args.endpoint:
        os.environ["TD_ENDPOINT"] = args.endpoint
    
    # Import here to avoid circular imports
    from .mcp_impl import mcp
    
    api_key = args.api_key or os.environ.get("TD_API_KEY")
    endpoint = args.endpoint
    
    print("Starting Treasure Data MCP Server with FastMCP...", file=sys.stderr)
    print(f"API Endpoint: {endpoint}", file=sys.stderr)
    
    if not api_key:
        print("ERROR: TD_API_KEY environment variable is not set and --api-key not provided", file=sys.stderr)
        print("Please set your API key using: export TD_API_KEY='your-api-key'", file=sys.stderr)
        sys.exit(1)
        
    print("Initializing FastMCP server...", file=sys.stderr)
    
    try:
        # Run the FastMCP server with stdio transport
        print("Waiting for MCP requests...", file=sys.stderr)
        mcp.run(transport='stdio')
    except Exception as e:
        print(f"ERROR: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    # This is just for testing - the entry points will be defined in pyproject.toml
    if len(sys.argv) > 1 and sys.argv[1] == "list":
        main_list_db()
    elif len(sys.argv) > 1 and sys.argv[1] == "get":
        sys.argv.pop(1)  # Remove the 'get' arg so argparse works correctly
        main_get_db()
    else:
        print("Usage: python -m td_mcp_server.cli_api [list|get] [args...]", file=sys.stderr)
        sys.exit(1)