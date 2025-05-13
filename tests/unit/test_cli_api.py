"""
Unit tests for the CLI commands.
"""

import json
import pytest
from unittest.mock import patch, MagicMock
import sys
from io import StringIO

from td_mcp_server.api import Database, Table
from td_mcp_server.cli_api import (
    list_databases, 
    get_database, 
    list_tables,
    main_list_databases,
    main_get_database,
    main_list_tables
)


class TestCliApi:
    """Tests for the CLI API functions."""

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

    @patch('td_mcp_server.cli_api.TreasureDataClient')
    def test_list_databases_default(self, mock_client_class):
        """Test list_databases with default parameters."""
        # Setup the mock
        mock_client = mock_client_class.return_value
        mock_client.get_databases.return_value = self.mock_databases

        # Capture stdout
        stdout = StringIO()
        sys.stdout = stdout

        # Call the function
        list_databases(api_key="test_key", endpoint="api.example.com")

        # Reset stdout
        sys.stdout = sys.__stdout__
        output = stdout.getvalue().strip()

        # Verify the output
        assert "db1" in output
        assert "db2" in output
        assert mock_client.get_databases.called
        mock_client.get_databases.assert_called_with(limit=30, offset=0, all_results=False)

    @patch('td_mcp_server.cli_api.TreasureDataClient')
    def test_list_databases_verbose(self, mock_client_class):
        """Test list_databases with verbose=True."""
        # Setup the mock
        mock_client = mock_client_class.return_value
        mock_client.get_databases.return_value = self.mock_databases

        # Capture stdout
        stdout = StringIO()
        sys.stdout = stdout

        # Call the function
        list_databases(api_key="test_key", endpoint="api.example.com", verbose=True)

        # Reset stdout
        sys.stdout = sys.__stdout__
        output = stdout.getvalue().strip()

        # Verify the output
        assert "Name" in output
        assert "Tables" in output
        assert "Created" in output
        assert "Updated" in output
        assert "Permission" in output
        assert "Protected" in output
        assert "db1" in output
        assert "db2" in output
        assert "3" in output  # table count
        assert "5" in output  # table count
        assert "Yes" in output  # delete_protected for db2
        assert mock_client.get_databases.called

    @patch('td_mcp_server.cli_api.TreasureDataClient')
    def test_list_databases_json(self, mock_client_class):
        """Test list_databases with json format."""
        # Setup the mock
        mock_client = mock_client_class.return_value
        mock_client.get_databases.return_value = self.mock_databases

        # Capture stdout
        stdout = StringIO()
        sys.stdout = stdout

        # Call the function
        list_databases(api_key="test_key", endpoint="api.example.com", format_output="json")

        # Reset stdout
        sys.stdout = sys.__stdout__
        output = stdout.getvalue().strip()

        # Verify the output
        assert json.loads(output) == ["db1", "db2"]
        assert mock_client.get_databases.called

    @patch('td_mcp_server.cli_api.TreasureDataClient')
    def test_list_databases_json_verbose(self, mock_client_class):
        """Test list_databases with json format and verbose=True."""
        # Setup the mock
        mock_client = mock_client_class.return_value
        mock_client.get_databases.return_value = self.mock_databases

        # Capture stdout
        stdout = StringIO()
        sys.stdout = stdout

        # Call the function
        list_databases(api_key="test_key", endpoint="api.example.com", format_output="json", verbose=True)

        # Reset stdout
        sys.stdout = sys.__stdout__
        output = stdout.getvalue().strip()

        # Verify the output
        db_list = json.loads(output)
        assert len(db_list) == 2
        assert db_list[0]["name"] == "db1"
        assert db_list[1]["name"] == "db2"
        assert db_list[0]["count"] == 3
        assert db_list[1]["count"] == 5
        assert mock_client.get_databases.called

    @patch('td_mcp_server.cli_api.TreasureDataClient')
    def test_list_databases_pagination(self, mock_client_class):
        """Test list_databases with pagination parameters."""
        # Setup the mock
        mock_client = mock_client_class.return_value
        mock_client.get_databases.return_value = self.mock_databases

        # Call the function with pagination
        list_databases(api_key="test_key", limit=10, offset=5, all_results=False)

        # Verify that pagination parameters were passed correctly
        mock_client.get_databases.assert_called_with(limit=10, offset=5, all_results=False)

    @patch('td_mcp_server.cli_api.TreasureDataClient')
    def test_list_databases_all_results(self, mock_client_class):
        """Test list_databases with all_results=True."""
        # Setup the mock
        mock_client = mock_client_class.return_value
        mock_client.get_databases.return_value = self.mock_databases

        # Call the function with all_results
        list_databases(api_key="test_key", all_results=True)

        # Verify that all_results was passed correctly
        mock_client.get_databases.assert_called_with(limit=30, offset=0, all_results=True)

    @patch('td_mcp_server.cli_api.TreasureDataClient')
    def test_get_database(self, mock_client_class):
        """Test get_database function."""
        # Setup the mock
        mock_client = mock_client_class.return_value
        mock_client.get_database.return_value = self.mock_databases[0]

        # Capture stdout
        stdout = StringIO()
        sys.stdout = stdout

        # Call the function
        get_database(database_name="db1", api_key="test_key")

        # Reset stdout
        sys.stdout = sys.__stdout__
        output = stdout.getvalue().strip()

        # Verify the output is JSON by default
        db_info = json.loads(output)
        assert db_info["name"] == "db1"
        assert db_info["count"] == 3
        assert mock_client.get_database.called
        mock_client.get_database.assert_called_with("db1")

    @patch('td_mcp_server.cli_api.TreasureDataClient')
    def test_get_database_table_format(self, mock_client_class):
        """Test get_database function with table format."""
        # Setup the mock
        mock_client = mock_client_class.return_value
        mock_client.get_database.return_value = self.mock_databases[0]

        # Capture stdout
        stdout = StringIO()
        sys.stdout = stdout

        # Call the function
        get_database(database_name="db1", api_key="test_key", format_output="table")

        # Reset stdout
        sys.stdout = sys.__stdout__
        output = stdout.getvalue().strip()

        # Verify the output in table format
        assert "Name: db1" in output
        assert "Count: 3" in output
        assert "Delete Protected: False" in output
        assert mock_client.get_database.called

    @patch('td_mcp_server.cli_api.TreasureDataClient')
    def test_get_database_not_found(self, mock_client_class):
        """Test get_database when database is not found."""
        # Setup the mock
        mock_client = mock_client_class.return_value
        mock_client.get_database.return_value = None

        # Capture stderr
        stderr = StringIO()
        sys.stderr = stderr

        # Call the function and expect exit
        with pytest.raises(SystemExit):
            get_database(database_name="nonexistent", api_key="test_key")

        # Reset stderr
        sys.stderr = sys.__stderr__
        output = stderr.getvalue().strip()

        # Verify the error message
        assert "Database 'nonexistent' not found." in output
        assert mock_client.get_database.called

    @patch('td_mcp_server.cli_api.TreasureDataClient')
    def test_list_tables_default(self, mock_client_class):
        """Test list_tables with default parameters."""
        # Setup the mock
        mock_client = mock_client_class.return_value
        mock_client.get_tables.return_value = self.mock_tables

        # Capture stdout
        stdout = StringIO()
        sys.stdout = stdout

        # Call the function
        list_tables(database_name="test_db", api_key="test_key")

        # Reset stdout
        sys.stdout = sys.__stdout__
        output = stdout.getvalue().strip()

        # Verify the output
        assert "table1" in output
        assert "table2" in output
        assert mock_client.get_tables.called
        mock_client.get_tables.assert_called_with("test_db", limit=30, offset=0, all_results=False)

    @patch('td_mcp_server.cli_api.TreasureDataClient')
    def test_list_tables_verbose(self, mock_client_class):
        """Test list_tables with verbose=True."""
        # Setup the mock
        mock_client = mock_client_class.return_value
        mock_client.get_tables.return_value = self.mock_tables

        # Capture stdout
        stdout = StringIO()
        sys.stdout = stdout

        # Call the function
        list_tables(database_name="test_db", api_key="test_key", verbose=True)

        # Reset stdout
        sys.stdout = sys.__stdout__
        output = stdout.getvalue().strip()

        # Verify the output
        assert "Name" in output
        assert "Type" in output
        assert "Count" in output
        assert "Size (bytes)" in output
        assert "Created" in output
        assert "Updated" in output
        assert "Protected" in output
        assert "table1" in output
        assert "table2" in output
        assert "10000" in output  # estimated_storage_size
        assert "20000" in output  # estimated_storage_size
        assert "100" in output  # count
        assert "200" in output  # count
        assert mock_client.get_tables.called

    @patch('td_mcp_server.cli_api.TreasureDataClient')
    def test_list_tables_json(self, mock_client_class):
        """Test list_tables with json format."""
        # Setup the mock
        mock_client = mock_client_class.return_value
        mock_client.get_tables.return_value = self.mock_tables

        # Capture stdout
        stdout = StringIO()
        sys.stdout = stdout

        # Call the function
        list_tables(database_name="test_db", api_key="test_key", format_output="json")

        # Reset stdout
        sys.stdout = sys.__stdout__
        output = stdout.getvalue().strip()

        # Verify the output
        assert json.loads(output) == ["table1", "table2"]
        assert mock_client.get_tables.called

    @patch('td_mcp_server.cli_api.TreasureDataClient')
    def test_list_tables_pagination(self, mock_client_class):
        """Test list_tables with pagination parameters."""
        # Setup the mock
        mock_client = mock_client_class.return_value
        mock_client.get_tables.return_value = self.mock_tables

        # Call the function with pagination
        list_tables(database_name="test_db", api_key="test_key", limit=10, offset=5, all_results=False)

        # Verify that pagination parameters were passed correctly
        mock_client.get_tables.assert_called_with("test_db", limit=10, offset=5, all_results=False)

    @patch('td_mcp_server.cli_api.list_databases')
    @patch('td_mcp_server.cli_api.argparse.ArgumentParser.parse_args')
    def test_main_list_databases(self, mock_parse_args, mock_list_databases):
        """Test main_list_databases function."""
        # Setup mock args
        mock_args = MagicMock()
        mock_args.api_key = "test_key"
        mock_args.endpoint = "api.example.com"
        mock_args.format_output = "table"
        mock_args.verbose = False
        mock_args.limit = 20
        mock_args.offset = 10
        mock_args.all_results = True
        mock_parse_args.return_value = mock_args

        # Call the function
        main_list_databases()

        # Verify the function calls
        mock_list_databases.assert_called_with(
            api_key="test_key", 
            endpoint="api.example.com", 
            format_output="table", 
            verbose=False,
            limit=20,
            offset=10,
            all_results=True
        )

    @patch('td_mcp_server.cli_api.get_database')
    @patch('td_mcp_server.cli_api.argparse.ArgumentParser.parse_args')
    def test_main_get_database(self, mock_parse_args, mock_get_database):
        """Test main_get_database function."""
        # Setup mock args
        mock_args = MagicMock()
        mock_args.database_name = "test_db"
        mock_args.api_key = "test_key"
        mock_args.endpoint = "api.example.com"
        mock_args.format_output = "json"
        mock_parse_args.return_value = mock_args

        # Call the function
        main_get_database()

        # Verify the function calls
        mock_get_database.assert_called_with(
            database_name="test_db",
            api_key="test_key",
            endpoint="api.example.com",
            format_output="json"
        )

    @patch('td_mcp_server.cli_api.list_tables')
    @patch('td_mcp_server.cli_api.argparse.ArgumentParser.parse_args')
    def test_main_list_tables(self, mock_parse_args, mock_list_tables):
        """Test main_list_tables function."""
        # Setup mock args
        mock_args = MagicMock()
        mock_args.database_name = "test_db"
        mock_args.api_key = "test_key"
        mock_args.endpoint = "api.example.com"
        mock_args.format_output = "table"
        mock_args.verbose = True
        mock_args.limit = 15
        mock_args.offset = 5
        mock_args.all_results = False
        mock_parse_args.return_value = mock_args

        # Call the function
        main_list_tables()

        # Verify the function calls
        mock_list_tables.assert_called_with(
            database_name="test_db",
            api_key="test_key",
            endpoint="api.example.com",
            format_output="table",
            verbose=True,
            limit=15,
            offset=5,
            all_results=False
        )