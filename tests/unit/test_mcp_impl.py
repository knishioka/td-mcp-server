"""
Unit tests for the MCP implementation.
"""

import os
from unittest.mock import MagicMock, patch

import pytest

from td_mcp_server.api import Database, Metadata, Project, Table
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
                delete_protected=False,
            ),
            Database(
                name="db2",
                created_at="2023-01-02 00:00:00 UTC",
                updated_at="2023-01-02 00:00:00 UTC",
                count=5,
                organization=None,
                permission="administrator",
                delete_protected=True,
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
                schema='[["id","string"],["name","string"]]',
                expire_days=None,
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
                schema='[["id","string"],["value","integer"]]',
                expire_days=30,
            ),
        ]
        self.mock_projects = [
            Project(
                id="123456",
                name="demo_content_affinity",
                revision="abcdef1234567890abcdef1234567890",
                createdAt="2022-01-01T00:00:00Z",
                updatedAt="2022-01-02T00:00:00Z",
                deletedAt=None,
                archiveType="s3",
                archiveMd5="abcdefghijklmnopqrstuvwx==",
                metadata=[],
            ),
            Project(
                id="789012",
                name="cdp_audience_123456",
                revision="abcdef1234567890abcdef1234567890",
                createdAt="2022-01-01T00:00:00Z",
                updatedAt="2023-01-01T00:00:00Z",
                deletedAt=None,
                archiveType="s3",
                archiveMd5="zyxwvutsrqponmlkjihgfed==",
                metadata=[
                    Metadata(key="pbp", value="cdp_audience"),
                    Metadata(key="pbp", value="cdp_audience_123456"),
                    Metadata(key="sys", value="cdp_audience"),
                ],
            ),
        ]

    @pytest.mark.asyncio
    @patch("td_mcp_server.mcp_impl.TreasureDataClient")
    @patch.dict(
        os.environ, {"TD_API_KEY": "test_key", "TD_ENDPOINT": "api.example.com"}
    )
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
        mock_client.get_databases.assert_called_with(
            limit=30, offset=0, all_results=False
        )

    @pytest.mark.asyncio
    @patch("td_mcp_server.mcp_impl.TreasureDataClient")
    @patch.dict(
        os.environ, {"TD_API_KEY": "test_key", "TD_ENDPOINT": "api.example.com"}
    )
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
    @patch("td_mcp_server.mcp_impl.TreasureDataClient")
    @patch.dict(
        os.environ, {"TD_API_KEY": "test_key", "TD_ENDPOINT": "api.example.com"}
    )
    async def test_td_list_databases_pagination(self, mock_client_class):
        """Test td_list_databases with pagination parameters."""
        # Setup the mock
        mock_client = mock_client_class.return_value
        mock_client.get_databases.return_value = self.mock_databases

        # Call the MCP function
        await td_list_databases(limit=10, offset=5, all_results=False)

        # Verify the function calls
        mock_client.get_databases.assert_called_with(
            limit=10, offset=5, all_results=False
        )

    @pytest.mark.asyncio
    @patch("td_mcp_server.mcp_impl.TreasureDataClient")
    @patch.dict(
        os.environ, {"TD_API_KEY": "test_key", "TD_ENDPOINT": "api.example.com"}
    )
    async def test_td_list_databases_all_results(self, mock_client_class):
        """Test td_list_databases with all_results=True."""
        # Setup the mock
        mock_client = mock_client_class.return_value
        mock_client.get_databases.return_value = self.mock_databases

        # Call the MCP function
        await td_list_databases(all_results=True)

        # Verify the function calls
        mock_client.get_databases.assert_called_with(
            limit=30, offset=0, all_results=True
        )

    @pytest.mark.asyncio
    @patch("td_mcp_server.mcp_impl.TreasureDataClient")
    @patch.dict(
        os.environ, {"TD_API_KEY": "test_key", "TD_ENDPOINT": "api.example.com"}
    )
    async def test_td_list_databases_no_api_key(self, mock_client_class):
        """Test td_list_databases with no API key."""
        # Remove the API key from the environment
        with patch.dict(
            os.environ, {"TD_API_KEY": "", "TD_ENDPOINT": "api.example.com"}
        ):
            # Call the MCP function
            result = await td_list_databases()

            # Verify the result contains an error message
            assert "error" in result
            assert "TD_API_KEY environment variable is not set" in result["error"]
            assert not mock_client_class.called

    @pytest.mark.asyncio
    @patch("td_mcp_server.mcp_impl.TreasureDataClient")
    @patch.dict(
        os.environ, {"TD_API_KEY": "test_key", "TD_ENDPOINT": "api.example.com"}
    )
    async def test_td_get_database(self, mock_client_class):
        """Test td_get_database function."""
        # Setup the mock
        mock_client = mock_client_class.return_value
        mock_client.get_database.return_value = self.mock_databases[0]

        # Call the MCP function
        result = await td_get_database(database_name="db1")

        # Verify the result
        assert "database" in result
        assert result["database"]["name"] == "db1"
        assert result["database"]["count"] == 3
        assert mock_client.get_database.called
        mock_client.get_database.assert_called_with("db1")

    @pytest.mark.asyncio
    @patch("td_mcp_server.mcp_impl.TreasureDataClient")
    @patch.dict(
        os.environ, {"TD_API_KEY": "test_key", "TD_ENDPOINT": "api.example.com"}
    )
    async def test_td_get_database_not_found(self, mock_client_class):
        """Test td_get_database when database is not found."""
        # Setup the mock
        mock_client = mock_client_class.return_value
        mock_client.get_database.return_value = None

        # Call the MCP function
        result = await td_get_database(database_name="nonexistent")

        # Verify the result
        assert "error" in result
        assert "Database 'nonexistent' not found" in result["error"]
        assert mock_client.get_database.called

    @pytest.mark.asyncio
    @patch("td_mcp_server.mcp_impl.TreasureDataClient")
    @patch.dict(
        os.environ, {"TD_API_KEY": "test_key", "TD_ENDPOINT": "api.example.com"}
    )
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
        mock_client.get_tables.assert_called_with(
            "db1", limit=30, offset=0, all_results=False
        )

    @pytest.mark.asyncio
    @patch("td_mcp_server.mcp_impl.TreasureDataClient")
    @patch.dict(
        os.environ, {"TD_API_KEY": "test_key", "TD_ENDPOINT": "api.example.com"}
    )
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
    @patch("td_mcp_server.mcp_impl.TreasureDataClient")
    @patch.dict(
        os.environ, {"TD_API_KEY": "test_key", "TD_ENDPOINT": "api.example.com"}
    )
    async def test_td_list_tables_pagination(self, mock_client_class):
        """Test td_list_tables with pagination parameters."""
        # Setup the mock
        mock_client = mock_client_class.return_value
        mock_client.get_database.return_value = self.mock_databases[0]
        mock_client.get_tables.return_value = self.mock_tables

        # Call the MCP function
        await td_list_tables(database_name="db1", limit=10, offset=5, all_results=False)

        # Verify the function calls
        mock_client.get_tables.assert_called_with(
            "db1", limit=10, offset=5, all_results=False
        )

    @pytest.mark.asyncio
    @patch("td_mcp_server.mcp_impl.TreasureDataClient")
    @patch.dict(
        os.environ, {"TD_API_KEY": "test_key", "TD_ENDPOINT": "api.example.com"}
    )
    async def test_td_list_tables_all_results(self, mock_client_class):
        """Test td_list_tables with all_results=True."""
        # Setup the mock
        mock_client = mock_client_class.return_value
        mock_client.get_database.return_value = self.mock_databases[0]
        mock_client.get_tables.return_value = self.mock_tables

        # Call the MCP function
        await td_list_tables(database_name="db1", all_results=True)

        # Verify the function calls
        mock_client.get_tables.assert_called_with(
            "db1", limit=30, offset=0, all_results=True
        )

    @pytest.mark.asyncio
    @patch("td_mcp_server.mcp_impl.TreasureDataClient")
    @patch.dict(
        os.environ, {"TD_API_KEY": "test_key", "TD_ENDPOINT": "api.example.com"}
    )
    async def test_td_list_tables_database_not_found(self, mock_client_class):
        """Test td_list_tables when database is not found."""
        # Setup the mock
        mock_client = mock_client_class.return_value
        mock_client.get_database.return_value = None

        # Call the MCP function
        result = await td_list_tables(database_name="nonexistent")

        # Verify the result
        assert "error" in result
        assert "Database 'nonexistent' not found" in result["error"]
        assert not mock_client.get_tables.called

    @pytest.mark.asyncio
    @patch("td_mcp_server.mcp_impl.TreasureDataClient")
    @patch.dict(
        os.environ, {"TD_API_KEY": "test_key", "TD_ENDPOINT": "api.example.com"}
    )
    async def test_td_list_projects_default(self, mock_client_class):
        """Test td_list_projects with default parameters."""
        # Setup the mock
        mock_client = mock_client_class.return_value
        mock_client.get_projects.return_value = self.mock_projects

        # Call the MCP function
        result = await td_list_projects()

        # Verify the result
        assert "projects" in result
        # Only the non-system project should be included (default behavior)
        assert len(result["projects"]) == 1
        assert result["projects"][0]["id"] == "123456"
        assert result["projects"][0]["name"] == "demo_content_affinity"
        assert mock_client.get_projects.called
        mock_client.get_projects.assert_called_with(
            limit=30, offset=0, all_results=False
        )

    @pytest.mark.asyncio
    @patch("td_mcp_server.mcp_impl.TreasureDataClient")
    @patch.dict(
        os.environ, {"TD_API_KEY": "test_key", "TD_ENDPOINT": "api.example.com"}
    )
    async def test_td_list_projects_verbose(self, mock_client_class):
        """Test td_list_projects with verbose=True."""
        # Setup the mock
        mock_client = mock_client_class.return_value
        mock_client.get_projects.return_value = self.mock_projects

        # Call the MCP function
        result = await td_list_projects(verbose=True)

        # Verify the result
        assert "projects" in result
        # Only the non-system project should be included (default behavior)
        assert len(result["projects"]) == 1
        # Check detailed fields in the project
        assert result["projects"][0]["id"] == "123456"
        assert result["projects"][0]["name"] == "demo_content_affinity"
        assert result["projects"][0]["revision"] == "abcdef1234567890abcdef1234567890"
        assert result["projects"][0]["created_at"] == "2022-01-01T00:00:00Z"
        assert result["projects"][0]["metadata"] == []
        # The second project (with "sys" metadata) should be excluded
        for project in result["projects"]:
            assert project["id"] != "789012"
        assert mock_client.get_projects.called

    @pytest.mark.asyncio
    @patch("td_mcp_server.mcp_impl.TreasureDataClient")
    @patch.dict(
        os.environ, {"TD_API_KEY": "test_key", "TD_ENDPOINT": "api.example.com"}
    )
    async def test_td_list_projects_pagination(self, mock_client_class):
        """Test td_list_projects with pagination parameters."""
        # Setup the mock
        mock_client = mock_client_class.return_value
        mock_client.get_projects.return_value = self.mock_projects

        # Call the MCP function
        await td_list_projects(limit=10, offset=5, all_results=False)

        # Verify the function calls
        mock_client.get_projects.assert_called_with(
            limit=10, offset=5, all_results=False
        )

    @pytest.mark.asyncio
    @patch("td_mcp_server.mcp_impl.TreasureDataClient")
    @patch.dict(
        os.environ, {"TD_API_KEY": "test_key", "TD_ENDPOINT": "api.example.com"}
    )
    async def test_td_list_projects_all_results(self, mock_client_class):
        """Test td_list_projects with all_results=True."""
        # Setup the mock
        mock_client = mock_client_class.return_value
        mock_client.get_projects.return_value = self.mock_projects

        # Call the MCP function
        await td_list_projects(all_results=True)

        # Verify the function calls
        mock_client.get_projects.assert_called_with(
            limit=30, offset=0, all_results=True
        )

    @pytest.mark.asyncio
    @patch("td_mcp_server.mcp_impl.TreasureDataClient")
    @patch.dict(
        os.environ, {"TD_API_KEY": "test_key", "TD_ENDPOINT": "api.example.com"}
    )
    async def test_td_list_projects_exclude_system(self, mock_client_class):
        """Test td_list_projects with system project filtering (default behavior)."""
        # Setup the mock
        mock_client = mock_client_class.return_value
        mock_client.get_projects.return_value = self.mock_projects

        # Call the MCP function (default is include_system=False)
        result = await td_list_projects()

        # Verify the result
        assert "projects" in result
        # Only the first project should be included (the one without "sys" metadata)
        assert len(result["projects"]) == 1
        assert result["projects"][0]["id"] == "123456"
        assert result["projects"][0]["name"] == "demo_content_affinity"

        # The second project (with "sys" metadata) should be excluded
        for project in result["projects"]:
            assert project["id"] != "789012"

        assert mock_client.get_projects.called
        mock_client.get_projects.assert_called_with(
            limit=30, offset=0, all_results=False
        )

    @pytest.mark.asyncio
    @patch("td_mcp_server.mcp_impl.TreasureDataClient")
    @patch.dict(
        os.environ, {"TD_API_KEY": "test_key", "TD_ENDPOINT": "api.example.com"}
    )
    async def test_td_list_projects_include_system(self, mock_client_class):
        """Test td_list_projects with include_system=True."""
        # Setup the mock
        mock_client = mock_client_class.return_value
        mock_client.get_projects.return_value = self.mock_projects

        # Call the MCP function with include_system=True
        result = await td_list_projects(include_system=True)

        # Verify the result
        assert "projects" in result
        # Both projects should be included
        assert len(result["projects"]) == 2

        # Check that both projects are in the result
        project_ids = [p["id"] for p in result["projects"]]
        assert "123456" in project_ids
        assert "789012" in project_ids

        assert mock_client.get_projects.called
        mock_client.get_projects.assert_called_with(
            limit=30, offset=0, all_results=False
        )

    @pytest.mark.asyncio
    @patch("td_mcp_server.mcp_impl.TreasureDataClient")
    @patch.dict(os.environ, {"TD_API_KEY": "", "TD_ENDPOINT": "api.example.com"})
    async def test_td_list_projects_no_api_key(self, mock_client_class):
        """Test td_list_projects with no API key."""
        # Call the MCP function
        result = await td_list_projects()

        # Verify the result contains an error message
        assert "error" in result
        assert "TD_API_KEY environment variable is not set" in result["error"]
        assert not mock_client_class.called

    @pytest.mark.asyncio
    @patch("td_mcp_server.mcp_impl.TreasureDataClient")
    @patch.dict(
        os.environ, {"TD_API_KEY": "test_key", "TD_ENDPOINT": "api.example.com"}
    )
    async def test_td_get_project(self, mock_client_class):
        """Test td_get_project function."""
        # Setup the mock
        mock_client = mock_client_class.return_value
        mock_client.get_project.return_value = self.mock_projects[0]

        # Call the MCP function
        result = await td_get_project(project_id="123456")

        # Verify the result
        assert "project" in result
        assert result["project"]["id"] == "123456"
        assert result["project"]["name"] == "demo_content_affinity"
        assert mock_client.get_project.called
        mock_client.get_project.assert_called_with("123456")

    @pytest.mark.asyncio
    @patch("td_mcp_server.mcp_impl.TreasureDataClient")
    @patch.dict(
        os.environ, {"TD_API_KEY": "test_key", "TD_ENDPOINT": "api.example.com"}
    )
    async def test_td_get_project_not_found(self, mock_client_class):
        """Test td_get_project when project is not found."""
        # Setup the mock
        mock_client = mock_client_class.return_value
        mock_client.get_project.return_value = None

        # Call the MCP function
        result = await td_get_project(project_id="nonexistent")

        # Verify the result
        assert "error" in result
        assert "Project with ID 'nonexistent' not found" in result["error"]
        assert mock_client.get_project.called

    @pytest.mark.asyncio
    @patch("td_mcp_server.mcp_impl.TreasureDataClient")
    @patch("td_mcp_server.mcp_impl.tempfile.mkdtemp")
    @patch("td_mcp_server.mcp_impl.os.chmod")
    @patch.dict(
        os.environ, {"TD_API_KEY": "test_key", "TD_ENDPOINT": "api.example.com"}
    )
    async def test_td_download_project_archive(
        self, mock_chmod, mock_mkdtemp, mock_client_class
    ):
        """Test td_download_project_archive with successful download."""
        # Setup mocks
        mock_temp_dir = "/tmp/td_project_123"
        mock_mkdtemp.return_value = mock_temp_dir

        mock_client = mock_client_class.return_value
        mock_client.get_project.return_value = self.mock_projects[0]
        mock_client.download_project_archive.return_value = True

        # Call the MCP function
        result = await td_download_project_archive(project_id="123456")

        # Verify the result
        assert "success" in result
        assert result["success"] is True
        assert result["project_id"] == "123456"
        assert result["project_name"] == "demo_content_affinity"
        assert result["temp_dir"] == mock_temp_dir
        expected_path = os.path.join(mock_temp_dir, "project_123456.tar.gz")
        assert result["archive_path"] == expected_path

        # Verify API client calls
        mock_client.get_project.assert_called_with("123456")
        output_path = os.path.join(mock_temp_dir, "project_123456.tar.gz")
        mock_client.download_project_archive.assert_called_with("123456", output_path)

    @pytest.mark.asyncio
    @patch("td_mcp_server.mcp_impl.TreasureDataClient")
    @patch("td_mcp_server.mcp_impl.tempfile.mkdtemp")
    @patch("td_mcp_server.mcp_impl.os.chmod")
    @patch.dict(
        os.environ, {"TD_API_KEY": "test_key", "TD_ENDPOINT": "api.example.com"}
    )
    async def test_td_download_project_archive_not_found(
        self, mock_chmod, mock_mkdtemp, mock_client_class
    ):
        """Test td_download_project_archive when project is not found."""
        # Setup mocks
        mock_temp_dir = "/tmp/td_project_456"
        mock_mkdtemp.return_value = mock_temp_dir

        mock_client = mock_client_class.return_value
        mock_client.get_project.return_value = None

        # Call the MCP function
        result = await td_download_project_archive(project_id="nonexistent")

        # Verify the result
        assert "error" in result
        assert "Project with ID 'nonexistent' not found" in result["error"]

        # Verify that download was not attempted
        assert not mock_client.download_project_archive.called

    @pytest.mark.asyncio
    @patch("td_mcp_server.mcp_impl.TreasureDataClient")
    @patch("td_mcp_server.mcp_impl.tempfile.mkdtemp")
    @patch("td_mcp_server.mcp_impl.os.chmod")
    @patch.dict(
        os.environ, {"TD_API_KEY": "test_key", "TD_ENDPOINT": "api.example.com"}
    )
    async def test_td_download_project_archive_download_failed(
        self, mock_chmod, mock_mkdtemp, mock_client_class
    ):
        """Test td_download_project_archive when download fails."""
        # Setup mocks
        mock_temp_dir = "/tmp/td_project_789"
        mock_mkdtemp.return_value = mock_temp_dir

        mock_client = mock_client_class.return_value
        mock_client.get_project.return_value = self.mock_projects[0]
        mock_client.download_project_archive.return_value = False

        # Call the MCP function
        result = await td_download_project_archive(project_id="123456")

        # Verify the result
        assert "error" in result
        assert "Failed to download archive for project '123456'" in result["error"]

    @pytest.mark.asyncio
    @patch("td_mcp_server.mcp_impl.os.path.exists")
    @patch("td_mcp_server.mcp_impl.tarfile.open")
    async def test_td_list_project_files(self, mock_tarfile_open, mock_path_exists):
        """Test td_list_project_files successfully listing files."""
        # Setup mocks
        mock_path_exists.return_value = True

        # Create mock tarfile members
        mock_file1 = MagicMock()
        mock_file1.name = "workflow.dig"
        mock_file1.isdir.return_value = False
        mock_file1.size = 1024

        mock_file2 = MagicMock()
        mock_file2.name = "queries/daily_count.sql"
        mock_file2.isdir.return_value = False
        mock_file2.size = 2048

        mock_dir = MagicMock()
        mock_dir.name = "queries"
        mock_dir.isdir.return_value = True
        mock_dir.size = 0

        mock_python = MagicMock()
        mock_python.name = "scripts/process_data.py"
        mock_python.isdir.return_value = False
        mock_python.size = 3072

        # Setup mock tarfile
        mock_tar = MagicMock()
        mock_tar.getmembers.return_value = [
            mock_file1,
            mock_file2,
            mock_dir,
            mock_python,
        ]
        mock_tarfile_open.return_value.__enter__.return_value = mock_tar

        # Call the MCP function
        result = await td_list_project_files(archive_path="/tmp/project_123456.tar.gz")

        # Verify the result
        assert result["success"] is True
        assert result["archive_path"] == "/tmp/project_123456.tar.gz"
        assert result["file_count"] == 4

        # Find each file type and verify its attributes
        directory_found = False
        workflow_found = False
        sql_found = False
        python_found = False

        for file_info in result["files"]:
            if file_info["type"] == "directory" and file_info["name"] == "queries":
                directory_found = True
            elif file_info["name"] == "workflow.dig":
                workflow_found = True
                assert file_info["extension"] == ".dig"
                assert file_info["file_type"] == "Digdag workflow"
            elif file_info["name"] == "queries/daily_count.sql":
                sql_found = True
                assert file_info["extension"] == ".sql"
                assert file_info["file_type"] == "SQL query"
            elif file_info["name"] == "scripts/process_data.py":
                python_found = True
                assert file_info["extension"] == ".py"
                assert file_info["file_type"] == "Python script"

        assert directory_found, "Directory not found in results"
        assert workflow_found, "Workflow file not found in results"
        assert sql_found, "SQL file not found in results"
        assert python_found, "Python file not found in results"

    @pytest.mark.asyncio
    @patch("td_mcp_server.mcp_impl.os.path.exists")
    async def test_td_list_project_files_not_found(self, mock_path_exists):
        """Test td_list_project_files when archive file not found."""
        # Setup mock
        mock_path_exists.return_value = False

        # Call the MCP function
        result = await td_list_project_files(archive_path="/tmp/nonexistent.tar.gz")

        # Verify the result
        assert "error" in result
        assert "Archive file not found" in result["error"]

    @pytest.mark.asyncio
    @patch("td_mcp_server.mcp_impl.os.path.exists")
    @patch("td_mcp_server.mcp_impl.tarfile.open")
    async def test_td_read_project_file(self, mock_tarfile_open, mock_path_exists):
        """Test td_read_project_file reading a file successfully."""
        # Setup mocks
        mock_path_exists.return_value = True

        # Create mock tarfile member
        mock_file = MagicMock()
        mock_file.isdir.return_value = False
        mock_file.size = 1024

        # Setup mock tar file
        mock_tar = MagicMock()
        mock_tar.getmember.return_value = mock_file

        # Setup mock file content
        mock_extracted_file = MagicMock()
        mock_extracted_file.read.return_value = (
            b"SELECT COUNT(*) FROM events WHERE "
            b"td_time_range(time, '2023-01-01', '2023-01-31', 'JST')"
        )
        mock_tar.extractfile.return_value = mock_extracted_file

        mock_tarfile_open.return_value.__enter__.return_value = mock_tar

        # Call the MCP function
        result = await td_read_project_file(
            archive_path="/tmp/project_123456.tar.gz",
            file_path="queries/monthly_count.sql",
        )

        # Verify the result
        assert result["success"] is True
        assert result["file_path"] == "queries/monthly_count.sql"
        assert result["extension"] == ".sql"
        assert result["size"] == 1024
        assert "SELECT COUNT(*) FROM events" in result["content"]

        # Verify tar operations
        mock_tar.getmember.assert_called_with("queries/monthly_count.sql")
        mock_tar.extractfile.assert_called_with(mock_file)

    @pytest.mark.asyncio
    @patch("td_mcp_server.mcp_impl.os.path.exists")
    async def test_td_read_project_file_archive_not_found(self, mock_path_exists):
        """Test td_read_project_file when archive not found."""
        # Setup mock
        mock_path_exists.return_value = False

        # Call the MCP function
        result = await td_read_project_file(
            archive_path="/tmp/nonexistent.tar.gz", file_path="workflow.dig"
        )

        # Verify the result
        assert "error" in result
        assert "Archive file not found" in result["error"]

    @pytest.mark.asyncio
    @patch("td_mcp_server.mcp_impl.os.path.exists")
    @patch("td_mcp_server.mcp_impl.tarfile.open")
    async def test_td_read_project_file_not_found(
        self, mock_tarfile_open, mock_path_exists
    ):
        """Test td_read_project_file when file not in archive."""
        # Setup mocks
        mock_path_exists.return_value = True

        # Setup mock tar file
        mock_tar = MagicMock()
        mock_tar.getmember.side_effect = KeyError("File not found in archive")
        mock_tarfile_open.return_value.__enter__.return_value = mock_tar

        # Call the MCP function
        result = await td_read_project_file(
            archive_path="/tmp/project_123456.tar.gz", file_path="nonexistent.sql"
        )

        # Verify the result
        assert "error" in result
        assert "File not found in archive" in result["error"]

    @pytest.mark.asyncio
    @patch("td_mcp_server.mcp_impl.os.path.exists")
    @patch("td_mcp_server.mcp_impl.tarfile.open")
    async def test_td_read_project_file_is_directory(
        self, mock_tarfile_open, mock_path_exists
    ):
        """Test td_read_project_file when path is a directory."""
        # Setup mocks
        mock_path_exists.return_value = True

        # Create mock tarfile member (directory)
        mock_dir = MagicMock()
        mock_dir.isdir.return_value = True
        mock_dir.name = "queries"
        mock_dir.size = 0

        # Setup mock tar file
        mock_tar = MagicMock()
        mock_tar.getmember.return_value = mock_dir
        mock_tarfile_open.return_value.__enter__.return_value = mock_tar

        # Call the MCP function
        result = await td_read_project_file(
            archive_path="/tmp/project_123456.tar.gz", file_path="queries"
        )

        # Verify the result
        assert "error" in result
        assert "Cannot read directory contents" in result["error"]
