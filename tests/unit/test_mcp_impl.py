"""
Unit tests for the MCP implementation.
"""

import os
import json
import pytest
from unittest.mock import patch, MagicMock, AsyncMock

from td_mcp_server.api import Database, Table
from td_mcp_server.mcp_impl import td_list_databases, td_get_database, td_list_tables


class TestMCPImplementation:
    """Tests for the MCP implementation functions."""

    def setup_method(self):
        """Set up test environment before each test."""
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
                schema="[[\"id\",\"string\"],[\"name\",\"string\"]]",
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
                schema="[[\"id\",\"string\"],[\"value\",\"integer\"]]",
                expire_days=30
            )
        ]

    @pytest.mark.asyncio
    @patch('td_mcp_server.mcp_impl.TreasureDataClient')
    @patch.dict(os.environ, {"TD_API_KEY": "test_key", "TD_ENDPOINT": "api.example.com"})
    async def test_td_list_databases_default(self, mock_client_class):
        """Test td_list_databases with default parameters."""
        # Setup the mock
        mock_client = mock_client_class.return_value
        mock_client.get_databases.return_value = self.mock_databases

        # Call the MCP function
        result = await td_list_databases()

        # Verify the result
        assert "databases" in result
        assert result["databases"] == ["db1", "db2"]
        assert mock_client.get_databases.called
        mock_client.get_databases.assert_called_with(limit=30, offset=0, all_results=False)

    @pytest.mark.asyncio
    @patch('td_mcp_server.mcp_impl.TreasureDataClient')
    @patch.dict(os.environ, {"TD_API_KEY": "test_key", "TD_ENDPOINT": "api.example.com"})
    async def test_td_list_databases_verbose(self, mock_client_class):
        """Test td_list_databases with verbose=True."""
        # Setup the mock
        mock_client = mock_client_class.return_value
        mock_client.get_databases.return_value = self.mock_databases

        # Call the MCP function
        result = await td_list_databases(verbose=True)

        # Verify the result
        assert "databases" in result
        assert len(result["databases"]) == 2
        assert result["databases"][0]["name"] == "db1"
        assert result["databases"][1]["name"] == "db2"
        assert result["databases"][0]["count"] == 3
        assert result["databases"][1]["count"] == 5
        assert mock_client.get_databases.called

    @pytest.mark.asyncio
    @patch('td_mcp_server.mcp_impl.TreasureDataClient')
    @patch.dict(os.environ, {"TD_API_KEY": "test_key", "TD_ENDPOINT": "api.example.com"})
    async def test_td_list_databases_pagination(self, mock_client_class):
        """Test td_list_databases with pagination parameters."""
        # Setup the mock
        mock_client = mock_client_class.return_value
        mock_client.get_databases.return_value = self.mock_databases

        # Call the MCP function
        await td_list_databases(limit=10, offset=5, all_results=False)

        # Verify the function calls
        mock_client.get_databases.assert_called_with(limit=10, offset=5, all_results=False)

    @pytest.mark.asyncio
    @patch('td_mcp_server.mcp_impl.TreasureDataClient')
    @patch.dict(os.environ, {"TD_API_KEY": "test_key", "TD_ENDPOINT": "api.example.com"})
    async def test_td_list_databases_all_results(self, mock_client_class):
        """Test td_list_databases with all_results=True."""
        # Setup the mock
        mock_client = mock_client_class.return_value
        mock_client.get_databases.return_value = self.mock_databases

        # Call the MCP function
        await td_list_databases(all_results=True)

        # Verify the function calls
        mock_client.get_databases.assert_called_with(limit=30, offset=0, all_results=True)

    @pytest.mark.asyncio
    @patch('td_mcp_server.mcp_impl.TreasureDataClient')
    @patch.dict(os.environ, {"TD_API_KEY": "test_key", "TD_ENDPOINT": "api.example.com"})
    async def test_td_list_databases_no_api_key(self, mock_client_class):
        """Test td_list_databases with no API key."""
        # Remove the API key from the environment
        with patch.dict(os.environ, {"TD_API_KEY": "", "TD_ENDPOINT": "api.example.com"}):
            # Call the MCP function
            result = await td_list_databases()

            # Verify the result contains an error message
            assert "error" in result
            assert "TD_API_KEY environment variable is not set" in result["error"]
            assert not mock_client_class.called

    @pytest.mark.asyncio
    @patch('td_mcp_server.mcp_impl.TreasureDataClient')
    @patch.dict(os.environ, {"TD_API_KEY": "test_key", "TD_ENDPOINT": "api.example.com"})
    async def test_td_get_database(self, mock_client_class):
        """Test td_get_database function."""
        # Setup the mock
        mock_client = mock_client_class.return_value
        mock_client.get_database.return_value = self.mock_databases[0]

        # Call the MCP function
        result = await td_get_database(database_name="db1")

        # Verify the result
        assert result["name"] == "db1"
        assert result["count"] == 3
        assert mock_client.get_database.called
        mock_client.get_database.assert_called_with("db1")

    @pytest.mark.asyncio
    @patch('td_mcp_server.mcp_impl.TreasureDataClient')
    @patch.dict(os.environ, {"TD_API_KEY": "test_key", "TD_ENDPOINT": "api.example.com"})
    async def test_td_get_database_not_found(self, mock_client_class):
        """Test td_get_database when database is not found."""
        # Setup the mock
        mock_client = mock_client_class.return_value
        mock_client.get_database.return_value = None

        # Call the MCP function
        result = await td_get_database(database_name="nonexistent")

        # Verify the result
        assert "error" in result
        assert "Database 'nonexistent' not found." in result["error"]
        assert mock_client.get_database.called

    @pytest.mark.asyncio
    @patch('td_mcp_server.mcp_impl.TreasureDataClient')
    @patch.dict(os.environ, {"TD_API_KEY": "test_key", "TD_ENDPOINT": "api.example.com"})
    async def test_td_list_tables_default(self, mock_client_class):
        """Test td_list_tables with default parameters."""
        # Setup the mock
        mock_client = mock_client_class.return_value
        mock_client.get_database.return_value = self.mock_databases[0]
        mock_client.get_tables.return_value = self.mock_tables

        # Call the MCP function
        result = await td_list_tables(database_name="db1")

        # Verify the result
        assert "database" in result
        assert "tables" in result
        assert result["database"] == "db1"
        assert result["tables"] == ["table1", "table2"]
        assert mock_client.get_tables.called
        mock_client.get_tables.assert_called_with("db1", limit=30, offset=0, all_results=False)

    @pytest.mark.asyncio
    @patch('td_mcp_server.mcp_impl.TreasureDataClient')
    @patch.dict(os.environ, {"TD_API_KEY": "test_key", "TD_ENDPOINT": "api.example.com"})
    async def test_td_list_tables_verbose(self, mock_client_class):
        """Test td_list_tables with verbose=True."""
        # Setup the mock
        mock_client = mock_client_class.return_value
        mock_client.get_database.return_value = self.mock_databases[0]
        mock_client.get_tables.return_value = self.mock_tables

        # Call the MCP function
        result = await td_list_tables(database_name="db1", verbose=True)

        # Verify the result
        assert "database" in result
        assert "tables" in result
        assert result["database"] == "db1"
        assert len(result["tables"]) == 2
        assert result["tables"][0]["name"] == "table1"
        assert result["tables"][1]["name"] == "table2"
        assert result["tables"][0]["count"] == 100
        assert result["tables"][1]["count"] == 200
        assert mock_client.get_tables.called

    @pytest.mark.asyncio
    @patch('td_mcp_server.mcp_impl.TreasureDataClient')
    @patch.dict(os.environ, {"TD_API_KEY": "test_key", "TD_ENDPOINT": "api.example.com"})
    async def test_td_list_tables_pagination(self, mock_client_class):
        """Test td_list_tables with pagination parameters."""
        # Setup the mock
        mock_client = mock_client_class.return_value
        mock_client.get_database.return_value = self.mock_databases[0]
        mock_client.get_tables.return_value = self.mock_tables

        # Call the MCP function
        await td_list_tables(database_name="db1", limit=10, offset=5, all_results=False)

        # Verify the function calls
        mock_client.get_tables.assert_called_with("db1", limit=10, offset=5, all_results=False)

    @pytest.mark.asyncio
    @patch('td_mcp_server.mcp_impl.TreasureDataClient')
    @patch.dict(os.environ, {"TD_API_KEY": "test_key", "TD_ENDPOINT": "api.example.com"})
    async def test_td_list_tables_all_results(self, mock_client_class):
        """Test td_list_tables with all_results=True."""
        # Setup the mock
        mock_client = mock_client_class.return_value
        mock_client.get_database.return_value = self.mock_databases[0]
        mock_client.get_tables.return_value = self.mock_tables

        # Call the MCP function
        await td_list_tables(database_name="db1", all_results=True)

        # Verify the function calls
        mock_client.get_tables.assert_called_with("db1", limit=30, offset=0, all_results=True)

    @pytest.mark.asyncio
    @patch('td_mcp_server.mcp_impl.TreasureDataClient')
    @patch.dict(os.environ, {"TD_API_KEY": "test_key", "TD_ENDPOINT": "api.example.com"})
    async def test_td_list_tables_database_not_found(self, mock_client_class):
        """Test td_list_tables when database is not found."""
        # Setup the mock
        mock_client = mock_client_class.return_value
        mock_client.get_database.return_value = None

        # Call the MCP function
        result = await td_list_tables(database_name="nonexistent")

        # Verify the result
        assert "error" in result
        assert "Database 'nonexistent' not found." in result["error"]
        assert not mock_client.get_tables.called