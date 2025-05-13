"""
Treasure Data API client module.

This module provides a client for interacting with the Treasure Data API,
with functions to retrieve database listings and other information.
"""

import os
from typing import Dict, List, Optional, Union, Any
import requests
from pydantic import BaseModel


class Database(BaseModel):
    """Model representing a Treasure Data database."""
    name: str
    created_at: str
    updated_at: str
    count: int
    organization: Optional[str] = None
    permission: str
    delete_protected: bool


class TreasureDataClient:
    """Client for interacting with the Treasure Data API."""
    
    def __init__(
        self, 
        api_key: Optional[str] = None, 
        endpoint: str = "api.treasuredata.com",
        api_version: str = "v3"
    ):
        """
        Initialize a new Treasure Data API client.
        
        Args:
            api_key: The API key to use for authentication. 
                     If not provided, will look for TD_API_KEY environment variable.
            endpoint: The API endpoint to use. Defaults to the US region.
            api_version: The API version to use. Defaults to v3.
        """
        self.api_key = api_key or os.environ.get("TD_API_KEY")
        if not self.api_key:
            raise ValueError(
                "API key must be provided either as a parameter or via TD_API_KEY environment variable"
            )
            
        self.endpoint = endpoint
        self.api_version = api_version
        self.base_url = f"https://{endpoint}/{api_version}"
        self.headers = {
            "Authorization": f"TD1 {self.api_key}",
            "Content-Type": "application/json",
        }
    
    def _make_request(self, method: str, path: str, **kwargs) -> Dict[str, Any]:
        """
        Make a request to the Treasure Data API.
        
        Args:
            method: The HTTP method to use (GET, POST, etc.)
            path: The API path to request
            **kwargs: Additional arguments to pass to requests
            
        Returns:
            The JSON response from the API
            
        Raises:
            requests.HTTPError: If the API returns an error response
        """
        url = f"{self.base_url}/{path}"
        response = requests.request(
            method=method,
            url=url,
            headers=self.headers,
            **kwargs
        )
        response.raise_for_status()
        return response.json()
    
    def get_databases(self) -> List[Database]:
        """
        Retrieve a list of all databases.
        
        Returns:
            A list of Database objects
            
        Raises:
            requests.HTTPError: If the API returns an error response
        """
        response = self._make_request("GET", "database/list")
        return [Database(**db) for db in response.get("databases", [])]
    
    def get_database(self, database_name: str) -> Optional[Database]:
        """
        Retrieve information about a specific database.
        
        Args:
            database_name: The name of the database to retrieve
            
        Returns:
            A Database object if found, None otherwise
            
        Raises:
            requests.HTTPError: If the API returns an error response
        """
        databases = self.get_databases()
        for db in databases:
            if db.name == database_name:
                return db
        return None