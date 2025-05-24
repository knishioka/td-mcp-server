"""
Integration tests for MCP protocol compliance.

These tests verify that the MCP server correctly implements the Model Context Protocol
specification, including JSON-RPC format, tools/list, tools/call, and error handling.
"""

import asyncio
import os
import subprocess
import time
from pathlib import Path
from unittest.mock import patch

import pytest

from td_mcp_server.mcp_impl import mcp


class TestMCPProtocolCompliance:
    """Test MCP protocol compliance according to specification."""

    async def test_mcp_tools_list_protocol(self):
        """Test tools/list method returns proper MCP protocol response."""
        # Get tools using FastMCP's list_tools method
        tools = await mcp.list_tools()

        # Verify we have the expected number of tools
        assert len(tools) == 8, f"Expected 8 tools, got {len(tools)}"

        # Verify each tool has required MCP protocol fields
        expected_tools = [
            "td_list_databases",
            "td_get_database",
            "td_list_tables",
            "td_list_projects",
            "td_get_project",
            "td_download_project_archive",
            "td_list_project_files",
            "td_read_project_file",
        ]

        tool_names = [tool.name for tool in tools]
        assert set(tool_names) == set(
            expected_tools
        ), f"Tool names mismatch: {tool_names}"

        # Verify each tool has required MCP protocol structure
        for tool in tools:
            # Required fields according to MCP spec
            assert hasattr(tool, "name"), f"Tool missing 'name' field: {tool}"
            assert hasattr(
                tool, "description"
            ), f"Tool missing 'description' field: {tool}"
            assert tool.name, f"Tool name is empty: {tool}"
            assert tool.description, f"Tool description is empty: {tool}"

            # Verify tool names match expected pattern
            assert tool.name in expected_tools, f"Unexpected tool name: {tool.name}"

            # Verify description is meaningful (not empty or placeholder)
            assert (
                len(tool.description) > 10
            ), f"Tool description too short: {tool.description}"
            assert (
                "TODO" not in tool.description.upper()
            ), f"Tool has placeholder description: {tool.description}"

    @pytest.mark.asyncio
    @patch("td_mcp_server.mcp_impl.TreasureDataClient")
    async def test_mcp_tool_call_protocol_simple(self, mock_client_class):
        """Test tools/call protocol with simple tool (td_list_databases)."""
        from td_mcp_server.api import Database
        from td_mcp_server.mcp_impl import td_list_databases

        # Setup mock data
        mock_databases = [
            Database(
                name="test_db1",
                created_at="2023-01-01 00:00:00 UTC",
                updated_at="2023-01-01 00:00:00 UTC",
                count=5,
                organization=None,
                permission="administrator",
                delete_protected=False,
            ),
            Database(
                name="test_db2",
                created_at="2023-01-02 00:00:00 UTC",
                updated_at="2023-01-02 00:00:00 UTC",
                count=10,
                organization=None,
                permission="administrator",
                delete_protected=True,
            ),
        ]

        # Setup mock client
        mock_client = mock_client_class.return_value
        mock_client.get_databases.return_value = mock_databases

        # Test with environment variables
        with patch.dict(
            os.environ, {"TD_API_KEY": "test_key", "TD_ENDPOINT": "api.example.com"}
        ):
            # Test default parameters (non-verbose)
            result = await td_list_databases()

            # Verify MCP protocol compliance for tool response
            assert isinstance(
                result, dict
            ), f"Tool should return dict, got {type(result)}"
            assert "databases" in result, f"Missing 'databases' key in result: {result}"
            assert isinstance(
                result["databases"], list
            ), f"'databases' should be list, got {type(result['databases'])}"
            assert result["databases"] == [
                "test_db1",
                "test_db2",
            ], f"Unexpected database names: {result['databases']}"

            # Test verbose mode
            result_verbose = await td_list_databases(verbose=True)
            assert isinstance(result_verbose, dict), "Verbose result should be dict"
            assert (
                "databases" in result_verbose
            ), "Missing 'databases' key in verbose result"
            assert isinstance(
                result_verbose["databases"], list
            ), "Verbose 'databases' should be list"
            assert (
                len(result_verbose["databases"]) == 2
            ), "Should have 2 databases in verbose mode"

            # Verify verbose mode returns full database objects
            for db in result_verbose["databases"]:
                assert isinstance(db, dict), "Each database should be a dict"
                assert "name" in db, "Database object missing 'name' field"
                assert "count" in db, "Database object missing 'count' field"
                assert "permission" in db, "Database object missing 'permission' field"

    @pytest.mark.asyncio
    @patch("td_mcp_server.mcp_impl.TreasureDataClient")
    async def test_mcp_tool_call_protocol_with_parameters(self, mock_client_class):
        """Test tools/call protocol with parameters (td_list_tables)."""
        from td_mcp_server.api import Database, Table
        from td_mcp_server.mcp_impl import td_list_tables

        # Setup mock data
        mock_database = Database(
            name="test_db",
            created_at="2023-01-01 00:00:00 UTC",
            updated_at="2023-01-01 00:00:00 UTC",
            count=2,
            organization=None,
            permission="administrator",
            delete_protected=False,
        )

        mock_tables = [
            Table(
                id=1,
                name="table1",
                estimated_storage_size=1000,
                counter_updated_at="2023-01-01T00:00:00Z",
                last_log_timestamp="2023-01-01T00:00:00Z",
                delete_protected=False,
                created_at="2023-01-01 00:00:00 UTC",
                updated_at="2023-01-01 00:00:00 UTC",
                type="log",
                include_v=True,
                count=100,
                table_schema='[["id","string"]]',
                expire_days=None,
            ),
            Table(
                id=2,
                name="table2",
                estimated_storage_size=2000,
                counter_updated_at="2023-01-02T00:00:00Z",
                last_log_timestamp="2023-01-02T00:00:00Z",
                delete_protected=True,
                created_at="2023-01-02 00:00:00 UTC",
                updated_at="2023-01-02 00:00:00 UTC",
                type="log",
                include_v=True,
                count=200,
                table_schema='[["id","string"],["value","integer"]]',
                expire_days=30,
            ),
        ]

        # Setup mock client
        mock_client = mock_client_class.return_value
        mock_client.get_database.return_value = mock_database
        mock_client.get_tables.return_value = mock_tables

        # Test with environment variables
        with patch.dict(
            os.environ, {"TD_API_KEY": "test_key", "TD_ENDPOINT": "api.example.com"}
        ):
            # Test required parameter
            result = await td_list_tables(database_name="test_db")

            # Verify MCP protocol compliance
            assert isinstance(result, dict), "Result should be dict"
            assert "database" in result, "Missing 'database' key"
            assert "tables" in result, "Missing 'tables' key"
            assert result["database"] == "test_db", "Database name should match input"
            assert isinstance(result["tables"], list), "'tables' should be list"
            assert result["tables"] == [
                "table1",
                "table2",
            ], "Table names should match mock data"

            # Test with pagination parameters
            result_paginated = await td_list_tables(
                database_name="test_db", limit=10, offset=5, verbose=True
            )

            # Verify pagination parameters are handled
            assert isinstance(result_paginated, dict), "Paginated result should be dict"
            assert "tables" in result_paginated, "Paginated result missing 'tables'"
            mock_client.get_tables.assert_called_with(
                "test_db", limit=10, offset=5, all_results=False
            )

    @pytest.mark.asyncio
    async def test_mcp_error_handling_protocol(self):
        """Test MCP protocol error handling compliance."""
        from td_mcp_server.mcp_impl import td_get_database

        # Test missing API key
        with patch.dict(os.environ, {}, clear=True):
            result = await td_get_database(database_name="test_db")

            # Verify error response format
            assert isinstance(result, dict), "Error response should be dict"
            assert "error" in result, "Error response missing 'error' key"
            assert isinstance(result["error"], str), "Error message should be string"
            assert (
                "TD_API_KEY" in result["error"]
            ), "Error should mention missing API key"
            assert (
                "environment variable" in result["error"]
            ), "Error should mention environment variable"

        # Test invalid input
        with patch.dict(os.environ, {"TD_API_KEY": "test_key"}):
            result = await td_get_database(database_name="")

            # Verify input validation error
            assert isinstance(result, dict), "Validation error should be dict"
            assert "error" in result, "Validation error missing 'error' key"
            assert (
                "cannot be empty" in result["error"]
            ), "Should validate empty database name"

    @pytest.mark.asyncio
    @patch("td_mcp_server.mcp_impl.TreasureDataClient")
    async def test_mcp_tool_parameter_validation(self, mock_client_class):
        """Test MCP tool parameter validation and type handling."""
        from td_mcp_server.mcp_impl import td_list_databases

        # Setup mock
        mock_client = mock_client_class.return_value
        mock_client.get_databases.return_value = []

        with patch.dict(os.environ, {"TD_API_KEY": "test_key"}):
            # Test default parameters
            result = await td_list_databases()
            mock_client.get_databases.assert_called_with(
                limit=30, offset=0, all_results=False
            )

            # Test explicit parameters with correct types
            result = await td_list_databases(
                verbose=True, limit=50, offset=10, all_results=True
            )
            mock_client.get_databases.assert_called_with(
                limit=50, offset=10, all_results=True
            )

            # Verify boolean parameter handling
            assert isinstance(
                result, dict
            ), "Result should be dict even with all parameters"

    def test_mcp_server_tool_schema_compliance(self):
        """Test that MCP tools have proper schema definitions."""
        # This test verifies that FastMCP can introspect our tools properly
        import inspect

        from td_mcp_server.mcp_impl import (
            td_download_project_archive,
            td_get_database,
            td_get_project,
            td_list_databases,
            td_list_project_files,
            td_list_projects,
            td_list_tables,
            td_read_project_file,
        )

        tools = [
            td_list_databases,
            td_get_database,
            td_list_tables,
            td_list_projects,
            td_get_project,
            td_download_project_archive,
            td_list_project_files,
            td_read_project_file,
        ]

        for tool_func in tools:
            # Verify function has proper signature
            sig = inspect.signature(tool_func)

            # Verify function is async
            assert asyncio.iscoroutinefunction(
                tool_func
            ), f"{tool_func.__name__} should be async"

            # Verify function has docstring
            assert tool_func.__doc__, f"{tool_func.__name__} missing docstring"
            assert (
                len(tool_func.__doc__.strip()) > 20
            ), f"{tool_func.__name__} docstring too short"

            # Verify function has type annotations
            for param_name, param in sig.parameters.items():
                if param_name != "return":
                    assert param.annotation != inspect.Parameter.empty, (
                        f"{tool_func.__name__} parameter '{param_name}' "
                        "missing type annotation"
                    )

            # Verify return type annotation
            assert (
                sig.return_annotation != inspect.Parameter.empty
            ), f"{tool_func.__name__} missing return type annotation"

    @pytest.mark.asyncio
    async def test_mcp_concurrent_tool_calls(self):
        """Test MCP server handles concurrent tool calls properly."""
        from td_mcp_server.mcp_impl import td_list_databases

        with patch.dict(os.environ, {"TD_API_KEY": "test_key"}):
            with patch(
                "td_mcp_server.mcp_impl.TreasureDataClient"
            ) as mock_client_class:
                mock_client = mock_client_class.return_value
                mock_client.get_databases.return_value = []

                # Run multiple concurrent tool calls
                tasks = [
                    td_list_databases(verbose=False),
                    td_list_databases(verbose=True),
                    td_list_databases(limit=10),
                    td_list_databases(all_results=True),
                ]

                results = await asyncio.gather(*tasks)

                # Verify all calls completed successfully
                assert len(results) == 4, "All concurrent calls should complete"
                for result in results:
                    assert isinstance(result, dict), "Each result should be dict"
                    assert (
                        "databases" in result
                    ), "Each result should have 'databases' key"


class TestMCPServerIntegration:
    """Test MCP server integration at the process level."""

    def test_server_startup_with_valid_api_key(self):
        """Test that server.py starts up properly with valid environment."""
        env = os.environ.copy()
        env["TD_API_KEY"] = "test_key"
        env["TD_ENDPOINT"] = "api.example.com"

        # Start server process
        process = subprocess.Popen(
            ["uv", "run", "td_mcp_server/server.py"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            cwd=Path(__file__).parent.parent.parent,
            text=True,
        )

        try:
            # Give server time to start
            time.sleep(1)

            # Check if process is still running (didn't crash on startup)
            poll_result = process.poll()
            if poll_result is not None:
                # Process exited, check stderr for errors
                _, stderr = process.communicate()
                pytest.fail(
                    f"Server process exited with code {poll_result}. Stderr: {stderr}"
                )

            # Server is running successfully
            assert process.poll() is None, "Server should be running"

        finally:
            # Clean up
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()

    def test_server_exit_without_api_key(self):
        """Test that server.py exits properly when API key is missing."""
        env = os.environ.copy()
        # Remove TD_API_KEY if it exists
        env.pop("TD_API_KEY", None)

        # Start server process
        process = subprocess.Popen(
            ["uv", "run", "td_mcp_server/server.py"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            cwd=Path(__file__).parent.parent.parent,
            text=True,
        )

        try:
            # Wait for process to exit
            return_code = process.wait(timeout=10)

            # Should exit with error code (1)
            assert (
                return_code == 1
            ), f"Server should exit with code 1, got {return_code}"

        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
            pytest.fail("Server should have exited quickly without API key")

    def test_server_import_resolution(self):
        """Test that server.py resolves imports correctly in different contexts."""
        # This test verifies the import fallback mechanism works

        # Test 1: Run as module (should use relative imports)
        env = os.environ.copy()
        env["TD_API_KEY"] = "test_key"

        process = subprocess.Popen(
            ["uv", "run", "python", "-m", "td_mcp_server.server"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            cwd=Path(__file__).parent.parent.parent,
            text=True,
        )

        try:
            time.sleep(1)
            # Should not crash due to import errors
            poll_result = process.poll()
            if poll_result is not None:
                _, stderr = process.communicate()
                # Check if it's an import error
                if "ImportError" in stderr or "ModuleNotFoundError" in stderr:
                    pytest.fail(f"Import error when running as module: {stderr}")

        finally:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
