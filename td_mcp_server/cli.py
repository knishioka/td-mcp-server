"""
Command-line interface for Treasure Data API tools.
"""

import os
import json
import sys
from typing import Optional
import click
from .api import TreasureDataClient
from .mcp_server import MCPServer


@click.group()
@click.option("--api-key", envvar="TD_API_KEY", help="Treasure Data API key")
@click.option(
    "--endpoint", 
    default="api.treasuredata.com", 
    help="API endpoint (default: api.treasuredata.com for US, use api.treasuredata.co.jp for Japan)"
)
@click.option("--mcp-server", is_flag=True, help="Run as an MCP server")
@click.pass_context
def cli(ctx, api_key: Optional[str], endpoint: str, mcp_server: bool):
    """Treasure Data API command-line interface."""
    # Check if we should run as an MCP server
    if mcp_server:
        server = MCPServer(api_key=api_key, endpoint=endpoint)
        server.serve()
        sys.exit(0)
        
    # Otherwise, create client and store in the context for subcommands
    ctx.ensure_object(dict)
    ctx.obj["client"] = TreasureDataClient(api_key=api_key, endpoint=endpoint)


@cli.command("list-databases")
@click.option("--format", "output_format", type=click.Choice(["table", "json"]), default="table", help="Output format")
@click.pass_context
def list_databases(ctx, output_format: str):
    """List all databases in your Treasure Data account."""
    client = ctx.obj["client"]
    
    try:
        databases = client.get_databases()
        
        if output_format == "json":
            # Output as JSON
            db_list = [db.model_dump() for db in databases]
            click.echo(json.dumps(db_list, indent=2))
        else:
            # Output as table
            if not databases:
                click.echo("No databases found.")
                return
                
            # Format as a table
            headers = ["Name", "Tables", "Created", "Updated", "Permission", "Protected"]
            
            # Print headers
            click.echo(" | ".join(headers))
            click.echo("-" * (sum(len(h) for h in headers) + len(headers) * 3 - 2))
            
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
                click.echo(" | ".join(row))
    
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        ctx.exit(1)


@cli.command("get-database")
@click.argument("database_name")
@click.option("--format", "output_format", type=click.Choice(["table", "json"]), default="json", help="Output format")
@click.pass_context
def get_database(ctx, database_name: str, output_format: str):
    """Get information about a specific database."""
    client = ctx.obj["client"]
    
    try:
        database = client.get_database(database_name)
        
        if not database:
            click.echo(f"Database '{database_name}' not found.", err=True)
            ctx.exit(1)
            
        if output_format == "json":
            # Output as JSON
            click.echo(json.dumps(database.model_dump(), indent=2))
        else:
            # Output as a simple table of key-value pairs
            for key, value in database.model_dump().items():
                click.echo(f"{key.replace('_', ' ').title()}: {value}")
    
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        ctx.exit(1)


def main():
    """Entry point for the CLI."""
    cli(obj={})


if __name__ == "__main__":
    main()