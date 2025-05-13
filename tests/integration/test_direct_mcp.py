"""
Integration tests for the MCP implementation by directly calling MCP functions.

These tests verify that the MCP server functions can correctly handle requests
and return appropriate responses without launching a subprocess.
"""

import os
import asyncio
import pytest
import pytest_asyncio
from unittest.mock import patch, MagicMock

from td_mcp_server.api import Database, Table
from td_mcp_server.mcp_impl import td_list_databases, td_get_database, td_list_tables


class TestDirectMCPIntegration:
    """Integration tests that call MCP functions directly without a client."""

    def setup_method(self):
        """Set up test environment before each test."""
        # Set up mock data
        self.mock_databases = [
            Database(
                name="db1",
                created_at="2023-01-01 00:00:00 UTC",
                updated_at="2023-01-01 00:00:00 UTC",
                count=3,
                organization=None,
                permission="administrator",
                delete_protected=False
            ),
            Database(
                name="db2",
                created_at="2023-01-02 00:00:00 UTC",
                updated_at="2023-01-02 00:00:00 UTC",
                count=5,
                organization=None,
                permission="administrator",
                delete_protected=True
            ),
        ]
        self.mock_tables = [
            Table(
                id=1234,
                name="table1",
                estimated_storage_size=10000,
                counter_updated_at="2023-01-01T00:00:00Z",
                last_log_timestamp="2023-01-01T00:00:00Z",
                delete_protected=False,
                created_at="2023-01-01 00:00:00 UTC",
                updated_at="2023-01-01 00:00:00 UTC",
                type="log",
                include_v=True,
                count=100,
                table_schema="[[\"id\",\"string\"],[\"name\",\"string\"]]",
                expire_days=None
            ),
            Table(
                id=5678,
                name="table2",
                estimated_storage_size=20000,
                counter_updated_at="2023-01-02T00:00:00Z",
                last_log_timestamp="2023-01-02T00:00:00Z",
                delete_protected=True,
                created_at="2023-01-02 00:00:00 UTC",
                updated_at="2023-01-02 00:00:00 UTC",
                type="log",
                include_v=True,
                count=200,
                table_schema="[[\"id\",\"string\"],[\"value\",\"integer\"]]",
                expire_days=30
            )
        ]
        
        # Test environment
        self.test_api_key = "test_api_key"
        self.test_endpoint = "api.example.com"
    
    # Environment fixture with test API key and endpoint
    @pytest.fixture
    def mcp_env(self):
        """Set up environment variables for MCP functions."""
        with patch.dict(os.environ, {
            "TD_API_KEY": self.test_api_key,
            "TD_ENDPOINT": self.test_endpoint
        }):
            yield
    
    @pytest.mark.asyncio
    @patch('td_mcp_server.mcp_impl.TreasureDataClient')
    async def test_list_databases_integration(self, mock_client_class, mcp_env):
        """Test listing databases through direct MCP function call."""
        # Setup the mock client
        mock_client = mock_client_class.return_value
        mock_client.get_databases.return_value = self.mock_databases
        
        # Default parameters
        result = await td_list_databases()
        assert "databases" in result
        assert result["databases"] == ["db1", "db2"]
        
        # With verbose=True
        result = await td_list_databases(verbose=True)
        assert "databases" in result
        assert len(result["databases"]) == 2
        assert result["databases"][0]["name"] == "db1"
        
        # With pagination
        result = await td_list_databases(limit=10, offset=0)
        assert "databases" in result
        
        # With all_results=True
        result = await td_list_databases(all_results=True)
        assert "databases" in result
    
    @pytest.mark.asyncio
    @patch('td_mcp_server.mcp_impl.TreasureDataClient')
    async def test_get_database_integration(self, mock_client_class, mcp_env):
        """Test getting a specific database through direct MCP function call."""
        # Setup the mock client
        mock_client = mock_client_class.return_value
        mock_client.get_database.side_effect = lambda db_name: (
            self.mock_databases[0] if db_name == "db1" else None
        )
        
        # Success case
        result = await td_get_database(database_name="db1")
        assert "name" in result
        assert result["name"] == "db1"
        
        # Not found case
        result = await td_get_database(database_name="nonexistent")
        assert "error" in result
        assert "not found" in result["error"]
    
    @pytest.mark.asyncio
    @patch('td_mcp_server.mcp_impl.TreasureDataClient')
    async def test_list_tables_integration(self, mock_client_class, mcp_env):
        """Test listing tables through direct MCP function call."""
        # Setup the mock client
        mock_client = mock_client_class.return_value
        mock_client.get_database.side_effect = lambda db_name: (
            self.mock_databases[0] if db_name == "db1" else None
        )
        mock_client.get_tables.return_value = self.mock_tables
        
        # Default parameters
        result = await td_list_tables(database_name="db1")
        assert "database" in result
        assert "tables" in result
        assert result["database"] == "db1"
        assert result["tables"] == ["table1", "table2"]
        
        # With verbose=True
        result = await td_list_tables(database_name="db1", verbose=True)
        assert "database" in result
        assert "tables" in result
        assert result["tables"][0]["name"] == "table1"
        
        # With pagination
        result = await td_list_tables(database_name="db1", limit=10, offset=0)
        assert "tables" in result
        
        # Database not found
        result = await td_list_tables(database_name="nonexistent")
        assert "error" in result
        assert "not found" in result["error"]


# We focus on the direct function calling approach which works reliably
# and doesn't require complex setup of FastMCP internals