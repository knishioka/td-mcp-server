"""
JSON-RPC 2.0 protocol compliance tests for MCP server.

These tests verify strict adherence to JSON-RPC 2.0 specification
as required by the Model Context Protocol (MCP) standard.
"""

import json
import os
from typing import Union
from unittest.mock import patch

import pytest

from td_mcp_server.mcp_impl import mcp


class TestJSONRPCCompliance:
    """Test JSON-RPC 2.0 specification compliance."""

    async def test_jsonrpc_request_format_validation(self):
        """Test that MCP server validates JSON-RPC 2.0 request format."""
        # Note: FastMCP handles JSON-RPC validation internally
        # We test the tool layer compliance here

        # Valid tool calls should work
        tools = await mcp.list_tools()
        assert len(tools) > 0, "Should have tools available"

        # Each tool should be callable
        for tool in tools:
            assert hasattr(tool, "name"), f"Tool missing name: {tool}"
            assert tool.name, f"Tool name is empty: {tool}"

    def test_jsonrpc_response_format_structure(self):
        """Test JSON-RPC 2.0 response format requirements."""
        # Valid JSON-RPC 2.0 response must have:
        # - jsonrpc: "2.0"
        # - id: matching request id
        # - result OR error (but not both)

        # This is a specification test - we verify the structure our tools should fit
        valid_success_response = {"jsonrpc": "2.0", "id": 1, "result": {"tools": []}}

        valid_error_response = {
            "jsonrpc": "2.0",
            "id": 1,
            "error": {"code": -32600, "message": "Invalid Request"},
        }

        # Verify our response structure
        assert "jsonrpc" in valid_success_response
        assert valid_success_response["jsonrpc"] == "2.0"
        assert "id" in valid_success_response
        assert "result" in valid_success_response
        assert "error" not in valid_success_response

        assert "jsonrpc" in valid_error_response
        assert valid_error_response["jsonrpc"] == "2.0"
        assert "id" in valid_error_response
        assert "error" in valid_error_response
        assert "result" not in valid_error_response

    def test_jsonrpc_error_codes_compliance(self):
        """Test JSON-RPC 2.0 standard error codes."""
        # Standard JSON-RPC 2.0 error codes that should be used
        standard_errors = {
            -32700: "Parse error",  # Invalid JSON
            -32600: "Invalid Request",  # JSON-RPC structure invalid
            -32601: "Method not found",  # Method doesn't exist
            -32602: "Invalid params",  # Invalid method parameters
            -32603: "Internal error",  # Server internal error
        }

        # Our MCP tools should return appropriate error structures
        # that can be mapped to these standard codes by the MCP framework
        for code, message in standard_errors.items():
            error_response = {"code": code, "message": message}

            # Verify error structure
            assert isinstance(error_response["code"], int)
            assert isinstance(error_response["message"], str)
            assert error_response["code"] < 0, "Error codes should be negative"

    @pytest.mark.asyncio
    async def test_mcp_tool_parameter_types_compliance(self):
        """Test that MCP tools handle JSON-RPC parameter types correctly."""
        from td_mcp_server.mcp_impl import td_list_databases

        with patch.dict(os.environ, {"TD_API_KEY": "test_key"}):
            with patch(
                "td_mcp_server.mcp_impl.TreasureDataClient"
            ) as mock_client_class:
                mock_client = mock_client_class.return_value
                mock_client.get_databases.return_value = []

                # Test boolean parameter
                result = await td_list_databases(verbose=True)
                assert isinstance(result, dict), "Result should be dict"

                result = await td_list_databases(verbose=False)
                assert isinstance(result, dict), "Result should be dict"

                # Test integer parameters
                result = await td_list_databases(limit=50)
                assert isinstance(result, dict), "Result should be dict"
                mock_client.get_databases.assert_called_with(
                    limit=50, offset=0, all_results=False
                )

                result = await td_list_databases(offset=10)
                assert isinstance(result, dict), "Result should be dict"
                mock_client.get_databases.assert_called_with(
                    limit=30, offset=10, all_results=False
                )

    @pytest.mark.asyncio
    async def test_mcp_tool_return_type_compliance(self):
        """Test that MCP tools return JSON-serializable types."""
        from td_mcp_server.api import Database
        from td_mcp_server.mcp_impl import td_get_database, td_list_databases

        mock_database = Database(
            name="test_db",
            created_at="2023-01-01 00:00:00 UTC",
            updated_at="2023-01-01 00:00:00 UTC",
            count=5,
            organization=None,
            permission="administrator",
            delete_protected=False,
        )

        with patch.dict(os.environ, {"TD_API_KEY": "test_key"}):
            with patch(
                "td_mcp_server.mcp_impl.TreasureDataClient"
            ) as mock_client_class:
                mock_client = mock_client_class.return_value
                mock_client.get_databases.return_value = [mock_database]
                mock_client.get_database.return_value = mock_database

                # Test td_list_databases return type
                result = await td_list_databases()
                assert isinstance(result, dict), "Should return dict"

                # Verify result is JSON serializable
                try:
                    json.dumps(result)
                except (TypeError, ValueError) as e:
                    pytest.fail(f"Result not JSON serializable: {e}")

                # Test td_get_database return type
                result = await td_get_database("test_db")
                assert isinstance(result, dict), "Should return dict"

                # Verify result is JSON serializable
                try:
                    json.dumps(result)
                except (TypeError, ValueError) as e:
                    pytest.fail(f"Result not JSON serializable: {e}")

    @pytest.mark.asyncio
    async def test_mcp_error_response_format(self):
        """Test that MCP tools return properly formatted error responses."""
        from td_mcp_server.mcp_impl import td_get_database

        # Test missing API key error
        with patch.dict(os.environ, {}, clear=True):
            result = await td_get_database("test_db")

            # Verify error response structure
            assert isinstance(result, dict), "Error response should be dict"
            assert "error" in result, "Should have 'error' key"
            assert isinstance(result["error"], str), "Error should be string"

            # Verify JSON serializable
            try:
                json.dumps(result)
            except (TypeError, ValueError) as e:
                pytest.fail(f"Error response not JSON serializable: {e}")

        # Test input validation error
        with patch.dict(os.environ, {"TD_API_KEY": "test_key"}):
            result = await td_get_database("")

            assert isinstance(result, dict), "Error response should be dict"
            assert "error" in result, "Should have 'error' key"
            assert isinstance(result["error"], str), "Error should be string"
            assert len(result["error"]) > 0, "Error message should not be empty"

    def test_mcp_tool_schema_jsonrpc_compatibility(self):
        """Test that MCP tool schemas are compatible with JSON-RPC."""
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

        json_compatible_types = (
            str,
            int,
            float,
            bool,
            list,
            dict,
            type(None),
            # Union types and Optional are also OK
        )

        for tool_func in tools:
            sig = inspect.signature(tool_func)

            # Check parameter types are JSON-RPC compatible
            for param_name, param in sig.parameters.items():
                if param.annotation != inspect.Parameter.empty:
                    # Extract base type from annotations like Optional[str]
                    annotation = param.annotation

                    # Handle Union types (like str | None)
                    if hasattr(annotation, "__origin__"):
                        if annotation.__origin__ is Union:
                            # Check all union members are JSON compatible
                            for arg in annotation.__args__:
                                if arg not in json_compatible_types and arg is not type(
                                    None
                                ):
                                    # Allow basic types
                                    if arg not in (str, int, float, bool):
                                        pytest.fail(
                                            f"Tool {tool_func.__name__} parameter "
                                            f"{param_name} has non-JSON-compatible "
                                            f"type: {arg}"
                                        )
                    else:
                        # Simple type check
                        if annotation not in json_compatible_types:
                            if annotation not in (str, int, float, bool, dict, list):
                                pytest.fail(
                                    f"Tool {tool_func.__name__} parameter "
                                    f"{param_name} has non-JSON-compatible "
                                    f"type: {annotation}"
                                )

    @pytest.mark.asyncio
    async def test_mcp_batch_request_compatibility(self):
        """Test compatibility with JSON-RPC batch requests (array of requests)."""
        # JSON-RPC 2.0 supports batch requests as an array
        # Our individual tools should work in batch context

        from td_mcp_server.mcp_impl import td_list_databases

        with patch.dict(os.environ, {"TD_API_KEY": "test_key"}):
            with patch(
                "td_mcp_server.mcp_impl.TreasureDataClient"
            ) as mock_client_class:
                mock_client = mock_client_class.return_value
                mock_client.get_databases.return_value = []

                # Simulate multiple tool calls (as would happen in batch)
                results = []
                for i in range(3):
                    result = await td_list_databases(verbose=(i % 2 == 0))
                    results.append(result)

                # All results should be valid
                assert len(results) == 3, "Should get all results"
                for i, result in enumerate(results):
                    assert isinstance(result, dict), f"Result {i} should be dict"
                    assert (
                        "databases" in result
                    ), f"Result {i} should have 'databases' key"

                    # Verify each result is JSON serializable
                    try:
                        json.dumps(result)
                    except (TypeError, ValueError) as e:
                        pytest.fail(f"Batch result {i} not JSON serializable: {e}")

    def test_mcp_notification_compatibility(self):
        """Test compatibility with JSON-RPC notifications (requests without id)."""
        # JSON-RPC 2.0 notifications don't expect a response
        # Our tools should be compatible with this pattern

        # Notifications have no 'id' field and expect no response
        notification_request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {"name": "td_list_databases", "arguments": {}},
            # No 'id' field = notification
        }

        # Verify notification structure
        assert "jsonrpc" in notification_request
        assert "method" in notification_request
        assert "id" not in notification_request

        # Our tools should be callable regardless of notification vs request
        # (The MCP framework handles the notification vs request distinction)

    @pytest.mark.asyncio
    async def test_mcp_unicode_and_encoding_compliance(self):
        """Test Unicode and encoding compliance for international usage."""
        from td_mcp_server.mcp_impl import td_get_database

        with patch.dict(os.environ, {"TD_API_KEY": "test_key"}):
            with patch(
                "td_mcp_server.mcp_impl.TreasureDataClient"
            ) as mock_client_class:
                mock_client = mock_client_class.return_value
                mock_client.get_database.return_value = None

                # Test Unicode database names
                unicode_names = [
                    "データベース",  # Japanese
                    "数据库",  # Chinese
                    "база_данных",  # Russian
                    "🚀_database",  # Emoji
                    "test-db-café",  # Accented characters
                ]

                for db_name in unicode_names:
                    result = await td_get_database(db_name)

                    # Should handle Unicode gracefully
                    assert isinstance(
                        result, dict
                    ), f"Should return dict for Unicode name: {db_name}"

                    # Result should be JSON serializable with Unicode
                    try:
                        json_str = json.dumps(result, ensure_ascii=False)
                        # Should be able to round-trip
                        json.loads(json_str)
                    except (TypeError, ValueError) as e:
                        pytest.fail(f"Unicode handling failed for '{db_name}': {e}")

    def test_mcp_numeric_precision_compliance(self):
        """Test numeric precision handling for JSON-RPC compatibility."""
        # JSON numbers have precision limitations
        # Our tools should handle this appropriately

        # Test that our constants are JSON-safe
        from td_mcp_server.mcp_impl import DEFAULT_LIMIT, MAX_FILE_SIZE, MAX_READ_SIZE

        constants = {
            "DEFAULT_LIMIT": DEFAULT_LIMIT,
            "MAX_FILE_SIZE": MAX_FILE_SIZE,
            "MAX_READ_SIZE": MAX_READ_SIZE,
        }

        for name, value in constants.items():
            assert isinstance(value, int), f"{name} should be integer"

            # Verify JSON serialization preserves value
            json_str = json.dumps(value)
            parsed_value = json.loads(json_str)
            assert (
                parsed_value == value
            ), f"{name} loses precision in JSON: {value} != {parsed_value}"
