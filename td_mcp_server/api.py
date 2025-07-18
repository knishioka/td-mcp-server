"""
Treasure Data API client module.

This module provides a client for interacting with the Treasure Data API,
with functions to retrieve database listings and other information.
"""

import os
from typing import Any

import requests
from pydantic import BaseModel, Field


class Database(BaseModel):
    """Model representing a Treasure Data database."""

    name: str
    created_at: str
    updated_at: str
    count: int
    organization: str | None = None
    permission: str
    delete_protected: bool


class Table(BaseModel):
    """Model representing a Treasure Data table."""

    id: int
    name: str
    estimated_storage_size: int
    counter_updated_at: str
    last_log_timestamp: str | None = None
    delete_protected: bool
    created_at: str
    updated_at: str
    type: str
    include_v: bool
    count: int
    table_schema: str | None = Field(None, alias="schema")
    expire_days: int | None = None


class Metadata(BaseModel):
    """Model representing workflow project metadata."""

    key: str
    value: str


class ProjectInfo(BaseModel):
    """Minimal project information included in workflow responses."""

    id: str
    name: str
    updated_at: str = Field(..., alias="updatedAt")
    last_editor: dict[str, Any] | None = Field(None, alias="lastEditor")


class SessionAttempt(BaseModel):
    """Model representing a workflow session attempt."""

    id: str
    retry_attempt_name: str | None = Field(None, alias="retryAttemptName")
    done: bool
    success: bool
    cancel_requested: bool = Field(..., alias="cancelRequested")
    params: dict[str, Any] = {}
    created_at: str = Field(..., alias="createdAt")
    finished_at: str | None = Field(None, alias="finishedAt")
    status: str


class Session(BaseModel):
    """Model representing a workflow session."""

    id: str
    project: dict[str, Any]
    workflow: dict[str, Any]
    session_uuid: str = Field(..., alias="sessionUuid")
    session_time: str = Field(..., alias="sessionTime")
    last_attempt: SessionAttempt = Field(..., alias="lastAttempt")


class Workflow(BaseModel):
    """
    Model representing a Treasure Data workflow.

    A workflow in Treasure Data is a set of tasks defined in a Digdag file (.dig)
    that specifies data processing steps, their dependencies, and execution order.
    Workflows are contained within projects and can be scheduled or run manually.
    """

    id: str
    name: str
    project: ProjectInfo
    revision: str
    timezone: str
    config: dict[str, Any] = {}
    schedule: dict[str, Any] | None = None
    latest_sessions: list[Session] = Field(default_factory=list, alias="latestSessions")


class Project(BaseModel):
    """
    Model representing a Treasure Data workflow project.

    In Treasure Data, a workflow project is a container for workflow definitions,
    which typically include SQL queries and Digdag files (.dig) that define
    the workflow execution steps and dependencies. These workflows are used
    for data processing, analytics pipelines, and scheduled jobs.
    """

    id: str
    name: str
    revision: str
    created_at: str = Field(..., alias="createdAt")
    updated_at: str = Field(..., alias="updatedAt")
    deleted_at: str | None = Field(None, alias="deletedAt")
    archive_type: str = Field(..., alias="archiveType")
    archive_md5: str = Field(..., alias="archiveMd5")
    metadata: list[Metadata] = []


class TreasureDataClient:
    """Client for interacting with the Treasure Data API."""

    def __init__(
        self,
        api_key: str | None = None,
        endpoint: str = "api.treasuredata.com",
        api_version: str = "v3",
        workflow_endpoint: str | None = None,
    ):
        """
        Initialize a new Treasure Data API client.

        Args:
            api_key: The API key to use for authentication.
                     If not provided, will look for TD_API_KEY environment variable.
            endpoint: The API endpoint to use. Defaults to the US region.
            api_version: The API version to use. Defaults to v3.
            workflow_endpoint: The workflow API endpoint to use.
                             Defaults based on the provided endpoint.
        """
        self.api_key = api_key or os.environ.get("TD_API_KEY")
        if not self.api_key:
            raise ValueError(
                "API key must be provided via parameter or TD_API_KEY env var"
            )

        self.endpoint = endpoint
        self.api_version = api_version
        self.base_url = f"https://{endpoint}/{api_version}"

        # Derive workflow endpoint based on the API endpoint if not provided
        if workflow_endpoint is None:
            # Simply replace "api" with "api-workflow" in the endpoint
            self.workflow_endpoint = endpoint.replace("api.", "api-workflow.")
        else:
            self.workflow_endpoint = workflow_endpoint

        self.workflow_base_url = f"https://{self.workflow_endpoint}/api"

        self.headers = {
            "Authorization": f"TD1 {self.api_key}",
            "Content-Type": "application/json",
        }

    def _make_request(
        self, method: str, path: str, base_url: str | None = None, **kwargs
    ) -> dict[str, Any]:
        """
        Make a request to the Treasure Data API.

        Args:
            method: The HTTP method to use (GET, POST, etc.)
            path: The API path to request
            base_url: Optional base URL to use instead of the default
            **kwargs: Additional arguments to pass to requests

        Returns:
            The JSON response from the API

        Raises:
            requests.HTTPError: If the API returns an error response
        """
        if base_url is None:
            base_url = self.base_url

        url = f"{base_url}/{path}"
        response = requests.request(
            method=method, url=url, headers=self.headers, **kwargs
        )
        response.raise_for_status()
        return response.json()

    def get_databases(
        self, limit: int = 30, offset: int = 0, all_results: bool = False
    ) -> list[Database]:
        """
        Retrieve a list of databases with pagination support.

        Args:
            limit: Maximum number of databases to retrieve (defaults to 30)
            offset: Index to start retrieving from (defaults to 0)
            all_results: If True, retrieves all databases ignoring limit and offset

        Returns:
            A list of Database objects

        Raises:
            requests.HTTPError: If the API returns an error response
        """
        response = self._make_request("GET", "database/list")
        all_databases = [Database(**db) for db in response.get("databases", [])]

        if all_results:
            return all_databases
        else:
            end_index = (
                offset + limit
                if offset + limit <= len(all_databases)
                else len(all_databases)
            )
            return all_databases[offset:end_index]

    def get_database(self, database_name: str) -> Database | None:
        """
        Retrieve information about a specific database.

        Args:
            database_name: The name of the database to retrieve

        Returns:
            A Database object if found, None otherwise

        Raises:
            requests.HTTPError: If the API returns an error response
        """
        databases = self.get_databases(all_results=True)
        for db in databases:
            if db.name == database_name:
                return db
        return None

    def get_tables(
        self,
        database_name: str,
        limit: int = 30,
        offset: int = 0,
        all_results: bool = False,
    ) -> list[Table]:
        """
        Retrieve a list of tables in a specific database with pagination support.

        Args:
            database_name: The name of the database to retrieve tables from
            limit: Maximum number of tables to retrieve (defaults to 30)
            offset: Index to start retrieving from (defaults to 0)
            all_results: If True, retrieves all tables ignoring limit and offset

        Returns:
            A list of Table objects

        Raises:
            requests.HTTPError: If the API returns an error response
        """
        response = self._make_request("GET", f"table/list/{database_name}")
        all_tables = [Table(**table) for table in response.get("tables", [])]

        if all_results:
            return all_tables
        else:
            end_index = (
                offset + limit if offset + limit <= len(all_tables) else len(all_tables)
            )
            return all_tables[offset:end_index]

    def get_projects(
        self,
        limit: int = 30,
        offset: int = 0,
        all_results: bool = False,
    ) -> list[Project]:
        """
        Retrieve a list of workflow projects with pagination support.

        Workflow projects in Treasure Data contain workflow definitions used for
        data processing and analytics. Each project typically includes SQL queries
        and Digdag (.dig) files that define workflow execution steps and dependencies.
        These workflows are executed on the Treasure Data platform for scheduled
        data pipelines, ETL processes, and other automation tasks.

        Note: The API uses 'count' parameter for limiting results, but this method
        provides limit/offset interface for consistency with other methods.

        Args:
            limit: Maximum number of projects to retrieve (defaults to 30)
            offset: Index to start retrieving from (defaults to 0)
            all_results: If True, retrieves all projects ignoring limit and offset

        Returns:
            A list of Project objects representing workflow projects

        Raises:
            requests.HTTPError: If the API returns an error response
        """
        # The projects API uses 'count' parameter, not limit/offset
        # Request more data if offset is specified
        count = 100 if all_results else offset + limit

        params = {"count": count}
        response = self._make_request(
            "GET", "projects", base_url=self.workflow_base_url, params=params
        )
        all_projects = [Project(**project) for project in response.get("projects", [])]

        if all_results:
            return all_projects
        else:
            # Apply offset and limit on the client side
            end_index = min(offset + limit, len(all_projects))
            return all_projects[offset:end_index]

    def get_project(self, project_id: str) -> Project | None:
        """
        Retrieve detailed information about a specific workflow project.

        This method retrieves a specific Treasure Data workflow project by its ID.
        Workflow projects contain SQL queries and Digdag (.dig) files
        that define data processing pipelines. These projects are used for scheduling
        and executing data workflows, ETL processes, and machine learning tasks
        on Treasure Data.

        Args:
            project_id: The ID of the workflow project to retrieve

        Returns:
            A Project object representing the workflow project if found, None otherwise

        Raises:
            requests.HTTPError: If the API returns an error response (except 404)
        """
        url = f"{self.workflow_base_url}/projects/{project_id}"

        try:
            response = requests.get(url, headers=self.headers)

            # Return None for 404 (project not found)
            if response.status_code == 404:
                return None

            # Raise for other error status codes
            response.raise_for_status()

            return Project(**response.json())
        except requests.RequestException as e:
            # Re-raise if it's not a 404 error
            if not isinstance(e, requests.HTTPError) or (
                hasattr(e, "response") and e.response.status_code != 404
            ):
                raise
            return None

    def download_project_archive(self, project_id: str, output_path: str) -> bool:
        """
        Download a project's archive as a tar.gz file.

        This method downloads the complete archive of a workflow project, including all
        SQL queries, Digdag workflow files, Python scripts, and other resources. The
        archive is saved as a tar.gz file at the specified output path.

        Args:
            project_id: The ID of the workflow project to download
            output_path: The file path where the archive will be saved

        Returns:
            True if the download was successful, False otherwise

        Raises:
            requests.HTTPError: If the API returns an error response (except 404)
            IOError: If there's an issue writing to the output file
        """
        url = f"{self.workflow_base_url}/projects/{project_id}/archive"

        try:
            response = requests.get(url, headers=self.headers, stream=True)

            # Handle 404 specifically before raising other status codes
            if response.status_code == 404:
                return False

            # Raise for other error status codes
            response.raise_for_status()

            with open(output_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            return True
        except (OSError, requests.RequestException) as e:
            # Re-raise if it's not a 404 error
            if not isinstance(e, requests.HTTPError) or (
                hasattr(e, "response") and e.response.status_code != 404
            ):
                raise
            return False

    def get_workflows(
        self,
        count: int = 100,
        all_results: bool = False,
    ) -> list[Workflow]:
        """
        Retrieve a list of workflows across all projects.

        This method retrieves workflows from the Treasure Data workflow console API.
        Workflows are the actual executable units that contain tasks defined in
        Digdag files (.dig). Each workflow belongs to a project and can have
        multiple sessions (execution instances).

        Args:
            count: Maximum number of workflows to retrieve (defaults to 100)
            all_results: If True, retrieves all workflows up to count limit

        Returns:
            A list of Workflow objects

        Raises:
            requests.HTTPError: If the API returns an error response
        """
        # Use the console workflows endpoint as discovered
        params = {
            "count": count,
            "order": "asc",
            "sessions": 5,  # Include last 5 sessions for each workflow
            "output": "simple",
            "project_type": "user",
        }

        # Build console URL using the workflow endpoint
        # The console API is available at the same endpoint as the workflow API
        response = requests.get(
            f"{self.workflow_base_url}/console/workflows",
            headers=self.headers,
            params=params,
        )
        response.raise_for_status()

        data = response.json()
        workflows = [Workflow(**workflow) for workflow in data.get("workflows", [])]

        if all_results:
            return workflows
        else:
            # Return up to count workflows
            return workflows[:count]
