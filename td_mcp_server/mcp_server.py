"""
MCP (Model Context Protocol) server implementation for Treasure Data API.
"""

import json
import os
import sys
import traceback
from typing import Dict, Any, List, Optional

from .api import TreasureDataClient, Database


class MCPServer:
    """Model Context Protocol server for Treasure Data API."""
    
    def __init__(self, api_key: Optional[str] = None, endpoint: str = "api.treasuredata.com"):
        """
        Initialize the MCP server.
        
        Args:
            api_key: Treasure Data API key. If not provided, will look for TD_API_KEY environment variable.
            endpoint: API endpoint to use. Defaults to US region.
        """
        self.client = TreasureDataClient(api_key=api_key, endpoint=endpoint)
        
        # Define MCP tools
        self.tools = {
            "td_list_databases": {
                "description": "List all databases in your Treasure Data account",
                "parameters": {},
                "handler": self.td_list_databases
            },
            "td_get_database": {
                "description": "Get information about a specific database",
                "parameters": {
                    "database_name": {
                        "type": "string",
                        "description": "The name of the database to retrieve information for"
                    }
                },
                "handler": self.td_get_database
            }
        }
    
    def td_list_databases(self, **kwargs) -> Dict[str, Any]:
        """
        MCP handler for listing databases.
        
        Returns:
            A dictionary with database information
        """
        try:
            databases = self.client.get_databases()
            return {
                "databases": [db.model_dump() for db in databases]
            }
        except Exception as e:
            return {
                "error": str(e),
                "traceback": traceback.format_exc()
            }
    
    def td_get_database(self, database_name: str) -> Dict[str, Any]:
        """
        MCP handler for retrieving a specific database.
        
        Args:
            database_name: The name of the database to retrieve
            
        Returns:
            A dictionary with database information or error details
        """
        try:
            database = self.client.get_database(database_name)
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
    
    def handle_mcp_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle an MCP request.
        
        Args:
            request: The MCP request dictionary
            
        Returns:
            The MCP response dictionary
        """
        try:
            tool_name = request.get("tool_name")
            if not tool_name:
                return {
                    "error": "Missing tool_name in request"
                }
            
            if tool_name not in self.tools:
                return {
                    "error": f"Unknown tool: {tool_name}"
                }
            
            # Get the tool handler and parameters
            tool = self.tools[tool_name]
            handler = tool["handler"]
            parameters = request.get("parameters", {})
            
            # Call the handler with the provided parameters
            result = handler(**parameters)
            return result
            
        except Exception as e:
            return {
                "error": str(e),
                "traceback": traceback.format_exc()
            }
    
    def serve(self):
        """Start the MCP server and handle requests from stdin/stdout."""
        for line in sys.stdin:
            try:
                # Parse the JSON request
                request = json.loads(line)
                
                # Handle the request
                if request.get("type") == "discover":
                    # Return tool descriptions
                    tools = {}
                    for name, tool in self.tools.items():
                        tools[name] = {
                            "description": tool["description"],
                            "parameters": tool["parameters"]
                        }
                    
                    response = {
                        "tools": tools
                    }
                elif request.get("type") == "execute":
                    # Execute a tool
                    response = self.handle_mcp_request(request)
                else:
                    response = {
                        "error": f"Unknown request type: {request.get('type')}"
                    }
                
                # Send the response
                print(json.dumps(response), flush=True)
                
            except json.JSONDecodeError:
                print(json.dumps({"error": "Invalid JSON request"}), flush=True)
            except Exception as e:
                print(json.dumps({
                    "error": str(e),
                    "traceback": traceback.format_exc()
                }), flush=True)


def main():
    """Start the MCP server."""
    api_key = os.environ.get("TD_API_KEY")
    endpoint = os.environ.get("TD_ENDPOINT", "api.treasuredata.com")
    
    server = MCPServer(api_key=api_key, endpoint=endpoint)
    server.serve()


if __name__ == "__main__":
    main()