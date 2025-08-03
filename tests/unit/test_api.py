"""
Unit tests for the Treasure Data API client.
"""

import pytest
import requests
import responses

from td_mcp_server.api import Database, Project, Table, TreasureDataClient


class TestTreasureDataClient:
    """Tests for the TreasureDataClient class."""

    def setup_method(self):
        """Set up test environment before each test."""
        self.api_key = "test_api_key"
        self.endpoint = "api.treasuredata.com"
        self.client = TreasureDataClient(api_key=self.api_key, endpoint=self.endpoint)
        self.mock_databases = [
            {
                "name": "db1",
                "created_at": "2023-01-01 00:00:00 UTC",
                "updated_at": "2023-01-01 00:00:00 UTC",
                "count": 3,
                "organization": None,
                "permission": "administrator",
                "delete_protected": False,
            },
            {
                "name": "db2",
                "created_at": "2023-01-02 00:00:00 UTC",
                "updated_at": "2023-01-02 00:00:00 UTC",
                "count": 5,
                "organization": None,
                "permission": "administrator",
                "delete_protected": True,
            },
            {
                "name": "db3",
                "created_at": "2023-01-03 00:00:00 UTC",
                "updated_at": "2023-01-03 00:00:00 UTC",
                "count": 0,
                "organization": None,
                "permission": "administrator",
                "delete_protected": False,
            },
        ]
        self.mock_tables = [
            {
                "id": 1234,
                "name": "table1",
                "estimated_storage_size": 10000,
                "counter_updated_at": "2023-01-01T00:00:00Z",
                "last_log_timestamp": "2023-01-01T00:00:00Z",
                "delete_protected": False,
                "created_at": "2023-01-01 00:00:00 UTC",
                "updated_at": "2023-01-01 00:00:00 UTC",
                "type": "log",
                "include_v": True,
                "count": 100,
                "schema": '[["id","string"],["name","string"]]',
                "expire_days": None,
            },
            {
                "id": 5678,
                "name": "table2",
                "estimated_storage_size": 20000,
                "counter_updated_at": "2023-01-02T00:00:00Z",
                "last_log_timestamp": "2023-01-02T00:00:00Z",
                "delete_protected": True,
                "created_at": "2023-01-02 00:00:00 UTC",
                "updated_at": "2023-01-02 00:00:00 UTC",
                "type": "log",
                "include_v": True,
                "count": 200,
                "schema": '[["id","string"],["value","integer"]]',
                "expire_days": 30,
            },
        ]
        self.mock_projects = [
            {
                "id": "123456",
                "name": "demo_content_affinity",
                "revision": "abcdef1234567890abcdef1234567890",
                "createdAt": "2022-01-01T00:00:00Z",
                "updatedAt": "2022-01-02T00:00:00Z",
                "deletedAt": None,
                "archiveType": "s3",
                "archiveMd5": "abcdefghijklmnopqrstuvwx==",
                "metadata": [],
            },
            {
                "id": "789012",
                "name": "cdp_audience_123456",
                "revision": "abcdef1234567890abcdef1234567890",
                "createdAt": "2022-01-01T00:00:00Z",
                "updatedAt": "2023-01-01T00:00:00Z",
                "deletedAt": None,
                "archiveType": "s3",
                "archiveMd5": "zyxwvutsrqponmlkjihgfed==",
                "metadata": [
                    {"key": "pbp", "value": "cdp_audience"},
                    {"key": "pbp", "value": "cdp_audience_123456"},
                    {"key": "sys", "value": "cdp_audience"},
                ],
            },
        ]

    def test_init(self):
        """Test client initialization."""
        assert self.client.api_key == self.api_key
        assert self.client.endpoint == self.endpoint
        assert self.client.base_url == f"https://{self.endpoint}/v3"
        assert self.client.headers["Authorization"] == f"TD1 {self.api_key}"
        assert self.client.headers["Content-Type"] == "application/json"

    def test_init_from_env(self, monkeypatch):
        """Test client initialization from environment variable."""
        monkeypatch.setenv("TD_API_KEY", "env_api_key")
        client = TreasureDataClient()
        assert client.api_key == "env_api_key"
        assert client.endpoint == "api.treasuredata.com"  # default endpoint

    def test_init_missing_api_key(self, monkeypatch):
        """Test client initialization with missing API key."""
        monkeypatch.delenv("TD_API_KEY", raising=False)
        with pytest.raises(ValueError, match="API key must be provided"):
            TreasureDataClient()

    @responses.activate
    def test_get_databases(self):
        """Test get_databases method."""
        # Mock the API response
        responses.add(
            responses.GET,
            f"https://{self.endpoint}/v3/database/list",
            json={"databases": self.mock_databases},
            status=200,
        )

        # Call the method
        databases = self.client.get_databases()

        # Verify the results
        assert len(databases) == 3
        assert isinstance(databases[0], Database)
        assert databases[0].name == "db1"
        assert databases[1].name == "db2"
        assert databases[2].name == "db3"
        assert databases[0].count == 3
        assert databases[1].delete_protected is True

    @responses.activate
    def test_get_databases_with_pagination(self):
        """Test get_databases method with pagination."""
        # Mock the API response
        responses.add(
            responses.GET,
            f"https://{self.endpoint}/v3/database/list",
            json={"databases": self.mock_databases},
            status=200,
        )

        # Test with limit and offset
        databases = self.client.get_databases(limit=2, offset=1)
        assert len(databases) == 2
        assert databases[0].name == "db2"
        assert databases[1].name == "db3"

        # Test with all_results=True
        databases = self.client.get_databases(all_results=True)
        assert len(databases) == 3

        # Test with small limit
        databases = self.client.get_databases(limit=1)
        assert len(databases) == 1
        assert databases[0].name == "db1"

    @responses.activate
    def test_get_database(self):
        """Test get_database method."""
        # Mock the API response
        responses.add(
            responses.GET,
            f"https://{self.endpoint}/v3/database/list",
            json={"databases": self.mock_databases},
            status=200,
        )

        # Test existing database
        database = self.client.get_database("db2")
        assert database is not None
        assert database.name == "db2"
        assert database.count == 5
        assert database.delete_protected is True

        # Test non-existing database
        database = self.client.get_database("nonexistent")
        assert database is None

    @responses.activate
    def test_get_tables(self):
        """Test get_tables method."""
        database_name = "test_db"

        # Mock the API response
        responses.add(
            responses.GET,
            f"https://{self.endpoint}/v3/table/list/{database_name}",
            json={"tables": self.mock_tables},
            status=200,
        )

        # Call the method
        tables = self.client.get_tables(database_name)

        # Verify the results
        assert len(tables) == 2
        assert isinstance(tables[0], Table)
        assert tables[0].name == "table1"
        assert tables[1].name == "table2"
        assert tables[0].count == 100
        assert tables[1].expire_days == 30

    @responses.activate
    def test_get_tables_with_pagination(self):
        """Test get_tables method with pagination."""
        database_name = "test_db"

        # Mock the API response
        responses.add(
            responses.GET,
            f"https://{self.endpoint}/v3/table/list/{database_name}",
            json={"tables": self.mock_tables},
            status=200,
        )

        # Test with limit and offset
        tables = self.client.get_tables(database_name, limit=1, offset=1)
        assert len(tables) == 1
        assert tables[0].name == "table2"

        # Test with all_results=True
        tables = self.client.get_tables(database_name, all_results=True)
        assert len(tables) == 2

        # Test with large limit
        tables = self.client.get_tables(database_name, limit=10)
        assert len(tables) == 2

    @responses.activate
    def test_make_request_error(self):
        """Test error handling in _make_request method."""
        # Mock an error response
        responses.add(
            responses.GET,
            f"https://{self.endpoint}/v3/error",
            json={"error": "Something went wrong"},
            status=500,
        )

        # Verify that exception is raised
        with pytest.raises(requests.exceptions.HTTPError):
            self.client._make_request("GET", "error")

    @responses.activate
    def test_get_projects(self):
        """Test get_projects method."""
        # Mock the API response
        workflow_endpoint = "api-workflow.treasuredata.com"
        responses.add(
            responses.GET,
            f"https://{workflow_endpoint}/api/projects",
            json={"projects": self.mock_projects},
            status=200,
        )

        # Call the method
        projects = self.client.get_projects()

        # Verify the results
        assert len(projects) == 2
        assert isinstance(projects[0], Project)
        assert projects[0].id == "123456"
        assert projects[0].name == "demo_content_affinity"
        assert projects[1].id == "789012"
        assert projects[1].name == "cdp_audience_123456"
        assert len(projects[1].metadata) == 3
        assert projects[1].metadata[0].key == "pbp"
        assert projects[1].metadata[0].value == "cdp_audience"

    @responses.activate
    def test_get_projects_with_pagination(self):
        """Test get_projects method with pagination."""
        # Mock the API response
        workflow_endpoint = "api-workflow.treasuredata.com"
        responses.add(
            responses.GET,
            f"https://{workflow_endpoint}/api/projects",
            json={"projects": self.mock_projects},
            status=200,
        )

        # Test with limit and offset
        projects = self.client.get_projects(limit=1, offset=1)
        assert len(projects) == 1
        assert projects[0].id == "789012"
        assert projects[0].name == "cdp_audience_123456"

        # Test with all_results=True
        projects = self.client.get_projects(all_results=True)
        assert len(projects) == 2

        # Test with large limit
        projects = self.client.get_projects(limit=10)
        assert len(projects) == 2

    def test_workflow_endpoint_derivation(self):
        """Test workflow endpoint derivation based on API endpoint."""
        # Test US region standard pattern
        client = TreasureDataClient(
            api_key=self.api_key, endpoint="api.treasuredata.com"
        )
        assert client.workflow_endpoint == "api-workflow.treasuredata.com"

        # Test Japan region pattern
        client = TreasureDataClient(
            api_key=self.api_key, endpoint="api.treasuredata.co.jp"
        )
        assert client.workflow_endpoint == "api-workflow.treasuredata.co.jp"

        # Test with non-standard region
        client = TreasureDataClient(
            api_key=self.api_key, endpoint="api.treasuredata.eu"
        )
        assert client.workflow_endpoint == "api-workflow.treasuredata.eu"

        # Test with different domain structure (non-standard input)
        client = TreasureDataClient(
            api_key=self.api_key, endpoint="treasuredata-api.com"
        )
        # Should still perform the replacement
        assert client.workflow_endpoint == "treasuredata-api-workflow.com"

        # Test custom endpoint
        custom_endpoint = "custom-workflow.example.com"
        client = TreasureDataClient(
            api_key=self.api_key,
            endpoint="api.example.com",
            workflow_endpoint=custom_endpoint,
        )
        assert client.workflow_endpoint == custom_endpoint

    @responses.activate
    def test_get_project(self):
        """Test get_project method."""
        project_id = "123456"
        workflow_endpoint = "api-workflow.treasuredata.com"

        # Mock the API response
        responses.add(
            responses.GET,
            f"https://{workflow_endpoint}/api/projects/{project_id}",
            json={
                "id": project_id,
                "name": "demo_content_affinity",
                "revision": "abcdef1234567890abcdef1234567890",
                "createdAt": "2022-01-01T00:00:00Z",
                "updatedAt": "2022-01-02T00:00:00Z",
                "deletedAt": None,
                "archiveType": "s3",
                "archiveMd5": "abcdefghijklmnopqrstuvwx==",
                "metadata": [
                    {"key": "category", "value": "machine-learning"},
                    {"key": "version", "value": "1.0.0"},
                ],
            },
            status=200,
        )

        # Call the method
        project = self.client.get_project(project_id)

        # Verify the results
        assert project is not None
        assert project.id == project_id
        assert project.name == "demo_content_affinity"
        assert project.revision == "abcdef1234567890abcdef1234567890"
        assert project.created_at == "2022-01-01T00:00:00Z"
        assert project.updated_at == "2022-01-02T00:00:00Z"
        assert len(project.metadata) == 2
        assert project.metadata[0].key == "category"
        assert project.metadata[0].value == "machine-learning"

    @responses.activate
    def test_get_project_not_found(self):
        """Test get_project method when project is not found."""
        project_id = "nonexistent"
        workflow_endpoint = "api-workflow.treasuredata.com"

        # Mock the API response with 404 status code
        responses.add(
            responses.GET,
            f"https://{workflow_endpoint}/api/projects/{project_id}",
            json={"error": "Project not found"},
            status=404,
        )

        # Call the method - should return None for 404
        project = self.client.get_project(project_id)

        # Verify the result
        assert project is None

    @responses.activate
    def test_download_project_archive(self, tmp_path):
        """Test download_project_archive method."""
        project_id = "123456"
        workflow_endpoint = "api-workflow.treasuredata.com"

        # Create a temporary file to save the archive
        output_path = tmp_path / f"project_{project_id}.tar.gz"

        # Mock archive data - creating a simple tar.gz file
        mock_archive_data = b"mock tar.gz content"

        # Mock the API response
        responses.add(
            responses.GET,
            f"https://{workflow_endpoint}/api/projects/{project_id}/archive",
            body=mock_archive_data,
            status=200,
        )

        # Call the method
        success = self.client.download_project_archive(project_id, str(output_path))

        # Verify the result
        assert success is True
        assert output_path.exists()

        # Check content of the downloaded file
        with open(output_path, "rb") as f:
            content = f.read()
            assert content == mock_archive_data

    @responses.activate
    def test_download_project_archive_not_found(self, tmp_path):
        """Test download_project_archive method when project is not found."""
        project_id = "nonexistent"
        workflow_endpoint = "api-workflow.treasuredata.com"

        # Create a temporary file to save the archive
        output_path = tmp_path / f"project_{project_id}.tar.gz"

        # Mock the API response with 404 status code
        responses.add(
            responses.GET,
            f"https://{workflow_endpoint}/api/projects/{project_id}/archive",
            json={"error": "Project not found"},
            status=404,
        )

        # Call the method - should return False for 404
        success = self.client.download_project_archive(project_id, str(output_path))

        # Verify the result
        assert success is False
        assert not output_path.exists()

    @responses.activate
    def test_get_workflow_by_id(self):
        """Test get_workflow_by_id method."""
        workflow_id = "12345678"
        workflow_endpoint = "api-workflow.treasuredata.com"

        # Mock the API response
        mock_response = {
            "id": workflow_id,
            "name": "test_workflow",
            "project": {
                "id": "123456",
                "name": "test_project",
            },
            "revision": "abcdef1234567890abcdef1234567890",
            "timezone": "UTC",
            "config": {
                "+task1": {
                    "td>": {
                        "database": "test_db",
                        "engine": "presto",
                    }
                }
            },
        }

        responses.add(
            responses.GET,
            f"https://{workflow_endpoint}/api/workflows/{workflow_id}",
            json=mock_response,
            status=200,
        )

        # Call the method
        workflow = self.client.get_workflow_by_id(workflow_id)

        # Verify the result
        assert workflow is not None
        assert workflow.id == workflow_id
        assert workflow.name == "test_workflow"
        assert workflow.project.id == "123456"
        assert workflow.project.name == "test_project"
        assert workflow.timezone == "UTC"
        assert workflow.revision == "abcdef1234567890abcdef1234567890"

    @responses.activate
    def test_get_workflow_by_id_not_found(self):
        """Test get_workflow_by_id method when workflow is not found."""
        workflow_id = "nonexistent"
        workflow_endpoint = "api-workflow.treasuredata.com"

        # Mock the API response with 404 status code
        responses.add(
            responses.GET,
            f"https://{workflow_endpoint}/api/workflows/{workflow_id}",
            json={"message": "Resource does not exist: workflow id=nonexistent"},
            status=404,
        )

        # Call the method - should return None for 404
        workflow = self.client.get_workflow_by_id(workflow_id)

        # Verify the result
        assert workflow is None

    @responses.activate
    def test_get_workflows_with_pagination(self):
        """Test get_workflows method with pagination."""
        workflow_endpoint = "api-workflow.treasuredata.com"

        # Mock workflow data for page 1
        mock_workflows_page1 = [
            {
                "id": "123",
                "name": "workflow1",
                "project": {
                    "id": "1",
                    "name": "project1",
                    "updatedAt": "2023-01-01T00:00:00Z",
                },
                "revision": "abc123",
                "timezone": "UTC",
                "config": {},
                "schedule": None,
                "latestSessions": [],
            },
            {
                "id": "456",
                "name": "workflow2",
                "project": {
                    "id": "2",
                    "name": "project2",
                    "updatedAt": "2023-01-02T00:00:00Z",
                },
                "revision": "def456",
                "timezone": "Asia/Tokyo",
                "config": {},
                "schedule": {"cron": "0 0 * * *"},
                "latestSessions": [],
            },
        ]

        # Mock the API response for page 1
        responses.add(
            responses.GET,
            f"https://{workflow_endpoint}/api/console/workflows",
            json={"workflows": mock_workflows_page1},
            status=200,
            match=[
                responses.matchers.query_param_matcher(
                    {
                        "count": "2",
                        "page": "1",
                        "order": "asc",
                        "sessions": "5",
                        "output": "simple",
                        "project_type": "user",
                    }
                )
            ],
        )

        # Call the method with specific page
        workflows = self.client.get_workflows(count=2, page=1)

        # Verify the result
        assert len(workflows) == 2
        assert workflows[0].id == "123"
        assert workflows[0].name == "workflow1"
        assert workflows[1].id == "456"
        assert workflows[1].name == "workflow2"

    @responses.activate
    def test_get_session(self):
        """Test get_session method."""
        session_id = "123456789"
        workflow_endpoint = "api-workflow.treasuredata.com"

        # Mock the API response
        mock_response = {
            "id": session_id,
            "project": {"id": "123456", "name": "test_project"},
            "workflow": {"name": "test_workflow", "id": "12345678"},
            "sessionUuid": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
            "sessionTime": "2025-08-03T03:00:00+00:00",
            "lastAttempt": {
                "id": "987654321",
                "retryAttemptName": None,
                "done": True,
                "success": True,
                "cancelRequested": False,
                "params": {},
                "createdAt": "2025-08-03T03:00:00Z",
                "finishedAt": "2025-08-03T03:05:30Z",
                "status": "success",
            },
        }

        responses.add(
            responses.GET,
            f"https://{workflow_endpoint}/api/sessions/{session_id}",
            json=mock_response,
            status=200,
        )

        # Call the method
        session = self.client.get_session(session_id)

        # Verify the result
        assert session is not None
        assert session.id == session_id
        assert session.project["name"] == "test_project"
        assert session.workflow["name"] == "test_workflow"
        assert session.session_time == "2025-08-03T03:00:00+00:00"
        assert session.last_attempt.success is True

    @responses.activate
    def test_get_sessions(self):
        """Test get_sessions method."""
        workflow_endpoint = "api-workflow.treasuredata.com"

        # Mock the API response
        mock_response = {
            "sessions": [
                {
                    "id": "123456789",
                    "project": {"id": "123456", "name": "test_project"},
                    "workflow": {"name": "test_workflow", "id": "12345678"},
                    "sessionUuid": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                    "sessionTime": "2025-08-03T03:00:00+00:00",
                    "lastAttempt": {
                        "id": "987654321",
                        "retryAttemptName": None,
                        "done": True,
                        "success": True,
                        "cancelRequested": False,
                        "params": {},
                        "createdAt": "2025-08-03T03:00:00Z",
                        "finishedAt": "2025-08-03T03:05:30Z",
                        "status": "success",
                    },
                }
            ]
        }

        responses.add(
            responses.GET,
            f"https://{workflow_endpoint}/api/sessions",
            json=mock_response,
            status=200,
            match=[responses.matchers.query_param_matcher({"last": "20"})],
        )

        # Call the method
        sessions = self.client.get_sessions()

        # Verify the result
        assert len(sessions) == 1
        assert sessions[0].id == "123456789"
        assert sessions[0].project["name"] == "test_project"

    @responses.activate
    def test_get_attempt(self):
        """Test get_attempt method."""
        attempt_id = "987654321"
        workflow_endpoint = "api-workflow.treasuredata.com"

        # Mock the API response
        mock_response = {
            "id": attempt_id,
            "index": 1,
            "project": {"id": "123456", "name": "test_project"},
            "workflow": {"name": "test_workflow", "id": "12345678"},
            "sessionId": "123456789",
            "sessionUuid": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
            "sessionTime": "2025-08-03T03:00:00+00:00",
            "retryAttemptName": None,
            "done": True,
            "success": True,
            "cancelRequested": False,
            "params": {},
            "createdAt": "2025-08-03T03:00:00Z",
            "finishedAt": "2025-08-03T03:05:30Z",
            "status": "success",
        }

        responses.add(
            responses.GET,
            f"https://{workflow_endpoint}/api/attempts/{attempt_id}",
            json=mock_response,
            status=200,
        )

        # Call the method
        attempt = self.client.get_attempt(attempt_id)

        # Verify the result
        assert attempt is not None
        assert attempt.id == attempt_id
        assert attempt.index == 1
        assert attempt.session_id == "123456789"
        assert attempt.success is True

    @responses.activate
    def test_get_attempt_tasks(self):
        """Test get_attempt_tasks method."""
        attempt_id = "987654321"
        workflow_endpoint = "api-workflow.treasuredata.com"

        # Mock the API response
        mock_response = {
            "tasks": [
                {
                    "id": "1234567890",
                    "fullName": "+main_workflow",
                    "parentId": None,
                    "config": {},
                    "upstreams": [],
                    "state": "success",
                    "cancelRequested": False,
                    "exportParams": {},
                    "storeParams": {},
                    "stateParams": {},
                    "updatedAt": "2025-08-03T03:05:30Z",
                    "retryAt": None,
                    "startedAt": "2025-08-03T03:00:00Z",
                    "error": {},
                    "isGroup": True,
                },
                {
                    "id": "1234567891",
                    "fullName": "+main_workflow+extract_data",
                    "parentId": "1234567890",
                    "config": {
                        "td>": {
                            "query": "SELECT * FROM test_table",
                            "database": "test_db",
                        }
                    },
                    "upstreams": [],
                    "state": "success",
                    "cancelRequested": False,
                    "exportParams": {},
                    "storeParams": {},
                    "stateParams": {},
                    "updatedAt": "2025-08-03T03:02:15Z",
                    "retryAt": None,
                    "startedAt": "2025-08-03T03:00:01Z",
                    "error": {},
                    "isGroup": False,
                },
            ]
        }

        responses.add(
            responses.GET,
            f"https://{workflow_endpoint}/api/attempts/{attempt_id}/tasks",
            json=mock_response,
            status=200,
        )

        # Call the method
        tasks = self.client.get_attempt_tasks(attempt_id)

        # Verify the result
        assert len(tasks) == 2
        assert tasks[0].id == "1234567890"
        assert tasks[0].full_name == "+main_workflow"
        assert tasks[0].is_group is True
        assert tasks[1].id == "1234567891"
        assert tasks[1].full_name == "+main_workflow+extract_data"
        assert tasks[1].parent_id == "1234567890"
