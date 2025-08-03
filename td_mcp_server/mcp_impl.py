"""
MCP server implementation using FastMCP for Treasure Data API.
This module provides a FastMCP server for Treasure Data API.
"""

import os
import re
import tarfile
import tempfile
from pathlib import Path
from typing import Any

import requests
from mcp.server.fastmcp import FastMCP

from . import (
    diagnostic_tools,
    execution_tools,
    exploration_tools,
    search_tools,
    url_tools,
)
from .api import TreasureDataClient

# Constants
DEFAULT_LIMIT = 30
DEFAULT_ENDPOINT = "api.treasuredata.com"
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
MAX_READ_SIZE = 10 * 1024 * 1024  # 10MB
TEMP_DIR_PERMISSIONS = 0o700

# Initialize FastMCP server
mcp = FastMCP("treasure-data")


def _validate_project_id(project_id: str) -> bool:
    """Validate project ID to prevent path traversal attacks."""
    if not project_id:
        return False
    # Only allow alphanumeric characters, hyphens, and underscores
    if not re.match(r"^[a-zA-Z0-9_-]+$", project_id):
        return False
    # Prevent path traversal patterns
    if ".." in project_id or "/" in project_id or "\\" in project_id:
        return False
    return True


def _validate_file_path(file_path: str) -> bool:
    """Validate file path to prevent path traversal attacks."""
    if not file_path:
        return False
    # Normalize path and check for traversal attempts
    normalized = os.path.normpath(file_path)
    # Prevent absolute paths and traversal
    if normalized.startswith("/") or normalized.startswith("\\") or ".." in normalized:
        return False
    return True


def _validate_archive_path(archive_path: str) -> bool:
    """Validate archive path to ensure it's in allowed temporary directories."""
    if not archive_path:
        return False

    # Normalize the path to prevent tricks
    normalized_path = os.path.normpath(archive_path)

    # Allow paths in temp directories or test paths
    temp_prefix = tempfile.gettempdir()
    allowed_prefixes = [temp_prefix, "/tmp"]

    if not any(normalized_path.startswith(prefix) for prefix in allowed_prefixes):
        return False

    # Prevent path traversal
    if ".." in normalized_path:
        return False

    if not archive_path.endswith(".tar.gz"):
        return False
    return True


def _safe_extract_member(member, extract_path: str) -> bool:
    """Safely extract a tar member, preventing path traversal and other attacks."""
    # Normalize the member name
    member_path = os.path.normpath(member.name)

    # Prevent absolute paths
    if member_path.startswith("/") or member_path.startswith("\\"):
        return False

    # Prevent path traversal
    if ".." in member_path:
        return False

    # Check final extracted path
    final_path = os.path.join(extract_path, member_path)
    if not final_path.startswith(extract_path):
        return False

    # Check file size (prevent zip bombs)
    if hasattr(member, "size") and member.size > MAX_FILE_SIZE:
        return False

    return True


def _format_error_response(error_msg: str) -> dict[str, str]:
    """Format error response without exposing sensitive information."""
    return {"error": error_msg}


def _get_api_credentials() -> tuple[str | None, str, str | None]:
    """Get API credentials from environment variables.

    Returns:
        Tuple of (api_key, endpoint, workflow_endpoint)
    """
    api_key = os.environ.get("TD_API_KEY")
    endpoint = os.environ.get("TD_ENDPOINT", DEFAULT_ENDPOINT)
    workflow_endpoint = os.environ.get("TD_WORKFLOW_ENDPOINT")
    return api_key, endpoint, workflow_endpoint


def _create_client(
    include_workflow: bool = False,
) -> TreasureDataClient | dict[str, str]:
    """Create TreasureDataClient with environment credentials.

    Args:
        include_workflow: Whether to include workflow endpoint

    Returns:
        TreasureDataClient instance or error dict if API key missing
    """
    api_key, endpoint, workflow_endpoint = _get_api_credentials()

    if not api_key:
        return _format_error_response("TD_API_KEY environment variable is not set")

    kwargs = {"api_key": api_key, "endpoint": endpoint}
    if include_workflow and workflow_endpoint:
        kwargs["workflow_endpoint"] = workflow_endpoint

    return TreasureDataClient(**kwargs)


@mcp.tool()
async def td_list_databases(
    verbose: bool = False,
    limit: int = DEFAULT_LIMIT,
    offset: int = 0,
    all_results: bool = False,
) -> dict[str, Any]:
    """List available databases to find data sources and check access.

    Shows all databases you can access. Returns just names for quick overview,
    or set verbose=True for details like table count and permissions.

    Common scenarios:
    - Discover what databases are available in your account
    - Check permissions on specific databases
    - Get database list for documentation or auditing

    Use pagination (limit/offset) for large lists or all_results=True for everything.
    """
    client = _create_client()
    if isinstance(client, dict):
        return client

    try:
        databases = client.get_databases(
            limit=limit, offset=offset, all_results=all_results
        )

        if verbose:
            # Return full database details
            return {"databases": [db.model_dump() for db in databases]}
        else:
            # Return only database names
            return {"databases": [db.name for db in databases]}
    except (ValueError, requests.RequestException) as e:
        return _format_error_response(f"Failed to retrieve databases: {str(e)}")
    except Exception as e:
        return _format_error_response(
            f"Unexpected error while retrieving databases: {str(e)}"
        )


@mcp.tool()
async def td_get_database(database_name: str) -> dict[str, Any]:
    """Get specific database details like table count, permissions, and metadata.

    Shows detailed information about a named database. Use when you need to check
    database properties, understand access permissions, or get table statistics.

    Common scenarios:
    - Verify database exists before running queries
    - Check permission level (administrator, read-only, etc.)
    - Get table count and creation/update timestamps
    - Audit database properties for documentation

    Returns creation time, table count, permissions, and protection status.
    """
    # Input validation
    if not database_name or not database_name.strip():
        return _format_error_response("Database name cannot be empty")

    client = _create_client()
    if isinstance(client, dict):
        return client

    try:
        database = client.get_database(database_name)
        if database:
            return {"database": database.model_dump()}
        else:
            return _format_error_response(f"Database '{database_name}' not found")
    except (ValueError, requests.RequestException) as e:
        return _format_error_response(
            f"Failed to retrieve database '{database_name}': {str(e)}"
        )
    except Exception as e:
        return _format_error_response(
            f"Unexpected error while retrieving database '{database_name}': {str(e)}"
        )


@mcp.tool()
async def td_list_tables(
    database_name: str,
    verbose: bool = False,
    limit: int = DEFAULT_LIMIT,
    offset: int = 0,
    all_results: bool = False,
) -> dict[str, Any]:
    """List tables in a database to explore data structure and find datasets.

    Shows all tables within a specific database. Returns table names for quick
    scanning, or set verbose=True for schemas, sizes, and record counts.

    Common scenarios:
    - Explore available data in a database
    - Find specific tables by scanning names
    - Check table schemas before writing queries
    - Audit table sizes and record counts
    - Verify table exists before querying

    Supports pagination (limit/offset) or all_results=True for complete list.
    """
    # Input validation
    if not database_name or not database_name.strip():
        return _format_error_response("Database name cannot be empty")

    client = _create_client()
    if isinstance(client, dict):
        return client

    try:
        # First, verify that the database exists
        database = client.get_database(database_name)
        if not database:
            return _format_error_response(f"Database '{database_name}' not found")

        # Get tables for the database
        tables = client.get_tables(
            database_name, limit=limit, offset=offset, all_results=all_results
        )

        if verbose:
            # Return full table details
            return {
                "database": database_name,
                "tables": [table.model_dump() for table in tables],
            }
        else:
            # Return only table names
            return {
                "database": database_name,
                "tables": [table.name for table in tables],
            }
    except (ValueError, requests.RequestException) as e:
        return _format_error_response(
            f"Failed to retrieve tables from database '{database_name}': {str(e)}"
        )
    except Exception as e:
        return _format_error_response(
            f"Unexpected error while retrieving tables from database "
            f"'{database_name}': {str(e)}"
        )


@mcp.tool()
async def td_list_projects(
    verbose: bool = False,
    limit: int = DEFAULT_LIMIT,
    offset: int = 0,
    all_results: bool = False,
    include_system: bool = False,
) -> dict[str, Any]:
    """List workflow projects to find data pipelines and scheduled jobs.

    Shows all workflow projects containing Digdag workflows, SQL queries, and
    Python scripts. Returns names/IDs for navigation or verbose=True for details.

    Common scenarios:
    - Discover available data processing workflows
    - Find specific project by browsing names
    - Get project IDs for detailed exploration
    - Audit workflow projects in the account
    - List user projects (exclude system with include_system=False)

    Projects contain .dig files defining scheduled data pipelines.
    """
    client = _create_client(include_workflow=True)
    if isinstance(client, dict):
        return client

    try:
        projects = client.get_projects(
            limit=limit, offset=offset, all_results=all_results
        )

        # Filter out system projects (those with "sys" metadata)
        if not include_system:
            projects = [
                p for p in projects if not any(meta.key == "sys" for meta in p.metadata)
            ]

        if verbose:
            # Return full project details
            return {"projects": [project.model_dump() for project in projects]}
        else:
            # Return only project names and ids
            return {
                "projects": [
                    {"id": project.id, "name": project.name} for project in projects
                ]
            }
    except (ValueError, requests.RequestException) as e:
        return _format_error_response(f"Failed to retrieve projects: {str(e)}")
    except Exception as e:
        return _format_error_response(
            f"Unexpected error while retrieving projects: {str(e)}"
        )


@mcp.tool()
async def td_get_project(project_id: str) -> dict[str, Any]:
    """Get workflow project details by ID to check metadata and revision.

    Retrieves project information including creation time, last update, and
    revision hash. Use after finding project ID from td_list_projects.

    Common scenarios:
    - Get project metadata before downloading archive
    - Check when project was last updated
    - Verify project exists by ID
    - Get revision for version tracking

    Note: Use numeric project ID (e.g., "123456") not project name.
    For project contents, use td_download_project_archive.
    """
    # Input validation - prevent path traversal
    if not _validate_project_id(project_id):
        return _format_error_response("Invalid project ID format")

    client = _create_client(include_workflow=True)
    if isinstance(client, dict):
        return client

    try:
        project = client.get_project(project_id)
        if project:
            return {"project": project.model_dump()}
        else:
            return _format_error_response(f"Project with ID '{project_id}' not found")
    except (ValueError, requests.RequestException) as e:
        return _format_error_response(
            f"Failed to retrieve project '{project_id}': {str(e)}"
        )
    except Exception as e:
        return _format_error_response(
            f"Unexpected error while retrieving project '{project_id}': {str(e)}"
        )


@mcp.tool()
async def td_download_project_archive(project_id: str) -> dict[str, Any]:
    """Download a project's archive (tar.gz) and return information about the download.

    This tool downloads the complete archive of a Treasure Data workflow project,
    which contains all SQL queries, Digdag (.dig) files, Python scripts, and other
    resources. The file is temporarily stored on the server.

    Args:
        project_id: The ID of the workflow project to download
    """
    # Input validation - prevent path traversal
    if not _validate_project_id(project_id):
        return _format_error_response("Invalid project ID format")

    client = _create_client(include_workflow=True)
    if isinstance(client, dict):
        return client

    try:
        # Create temporary directory with secure permissions
        temp_dir = tempfile.mkdtemp(prefix="td_project_")
        os.chmod(temp_dir, TEMP_DIR_PERMISSIONS)
        # Use sanitized project_id for filename
        safe_filename = re.sub(r"[^a-zA-Z0-9_-]", "_", project_id)
        output_path = os.path.join(temp_dir, f"project_{safe_filename}.tar.gz")

        # Check that project exists before attempting download
        project = client.get_project(project_id)
        if not project:
            return {"error": f"Project with ID '{project_id}' not found"}

        # Download the archive
        success = client.download_project_archive(project_id, output_path)

        if not success:
            return {"error": f"Failed to download archive for project '{project_id}'"}

        return {
            "success": True,
            "project_id": project_id,
            "project_name": project.name,
            "archive_path": output_path,
            "temp_dir": temp_dir,
            "message": f"Successfully downloaded archive for project '{project.name}'",
        }
    except (ValueError, requests.RequestException, OSError) as e:
        return _format_error_response(f"Failed to download project archive: {str(e)}")
    except Exception as e:
        return _format_error_response(
            f"Unexpected error while downloading project archive: {str(e)}"
        )


@mcp.tool()
async def td_list_project_files(archive_path: str) -> dict[str, Any]:
    """List all files contained in a project archive.

    This tool extracts and lists the content of a previously downloaded
    project archive, showing all files and directories within the project.

    Args:
        archive_path: The path to the downloaded project archive (.tar.gz file)
    """
    # Input validation - prevent path traversal
    if not _validate_archive_path(archive_path):
        return _format_error_response("Invalid archive path")

    try:
        if not os.path.exists(archive_path):
            return _format_error_response("Archive file not found")

        file_list = []

        with tarfile.open(archive_path, "r:gz") as tar:
            for member in tar.getmembers():
                # Security check for each member
                if not _safe_extract_member(member, "/tmp/validation"):
                    continue  # Skip unsafe members

                file_info = {
                    "name": member.name,
                    "type": "directory" if member.isdir() else "file",
                    "size": member.size,
                }

                # Add extension information for files
                if not member.isdir():
                    ext = Path(member.name).suffix.lower()
                    file_info["extension"] = ext

                    # Identify file types based on extension
                    if ext == ".dig":
                        file_info["file_type"] = "Digdag workflow"
                    elif ext == ".sql":
                        file_info["file_type"] = "SQL query"
                    elif ext == ".py":
                        file_info["file_type"] = "Python script"
                    elif ext in [".yml", ".yaml"]:
                        file_info["file_type"] = "YAML configuration"
                    else:
                        file_info["file_type"] = "Other"

                file_list.append(file_info)

        # Sort files: directories first, then by name
        file_list.sort(key=lambda x: (0 if x["type"] == "directory" else 1, x["name"]))

        return {
            "success": True,
            "archive_path": archive_path,
            "file_count": len(file_list),
            "files": file_list,
        }
    except (OSError, tarfile.ReadError) as e:
        return _format_error_response(f"Failed to list project files: {str(e)}")
    except Exception as e:
        return _format_error_response(
            f"Unexpected error while listing project files: {str(e)}"
        )


@mcp.tool()
async def td_read_project_file(archive_path: str, file_path: str) -> dict[str, Any]:
    """Read the contents of a specific file from a project archive.

    This tool extracts and reads a specific file from a project archive,
    returning its contents. This allows examining SQL queries, workflow
    definitions, and other files without fully extracting the archive.

    Args:
        archive_path: The path to the downloaded project archive (.tar.gz file)
        file_path: The path of the file within the archive to read
    """
    # Input validation - prevent path traversal
    if not _validate_archive_path(archive_path):
        return _format_error_response("Invalid archive path")

    if not _validate_file_path(file_path):
        return _format_error_response("Invalid file path")

    try:
        if not os.path.exists(archive_path):
            return _format_error_response("Archive file not found")

        try:
            with tarfile.open(archive_path, "r:gz") as tar:
                try:
                    file_info = tar.getmember(file_path)

                    # Security check for the member
                    if not _safe_extract_member(file_info, "/tmp/validation"):
                        return _format_error_response(
                            "File access denied for security reasons"
                        )

                    # Don't try to read directories
                    if file_info.isdir():
                        return _format_error_response("Cannot read directory contents")

                    # Extract and read the file
                    f = tar.extractfile(file_info)
                    if f is None:
                        return _format_error_response("Failed to extract file")

                    # Read with size limit
                    if file_info.size > MAX_READ_SIZE:
                        return _format_error_response("File too large to read")

                    content_bytes = f.read()

                    # Try to decode as text
                    try:
                        content = content_bytes.decode("utf-8")
                    except UnicodeDecodeError:
                        try:
                            content = content_bytes.decode("latin-1")
                        except UnicodeDecodeError:
                            return _format_error_response(
                                "File is not readable as text"
                            )

                    extension = Path(file_path).suffix.lower()

                    return {
                        "success": True,
                        "file_path": file_path,
                        "content": content,
                        "size": file_info.size,
                        "extension": extension,
                    }
                except KeyError:
                    return _format_error_response("File not found in archive")
        except tarfile.ReadError:
            return _format_error_response("Invalid or corrupted archive file")
    except (OSError, UnicodeDecodeError) as e:
        return _format_error_response(f"Failed to read file: {str(e)}")
    except Exception as e:
        return _format_error_response(f"Unexpected error while reading file: {str(e)}")


@mcp.tool()
async def td_list_workflows(
    verbose: bool = False,
    count: int = 50,
    include_system: bool = False,
    status_filter: str | None = None,
    search: str | None = None,
) -> dict[str, Any]:
    """List all workflows to monitor executions and find failed jobs.

    Shows workflows across all projects with their latest execution status.
    Essential for monitoring data pipeline health and finding issues.

    Common scenarios:
    - Check which workflows are failing (status_filter="error")
    - Monitor currently running workflows (status_filter="running")
    - Find workflows by name (use search parameter)
    - Get overview of all scheduled jobs
    - Audit workflow execution patterns

    Filter options: status ('success', 'error', 'running'), search by name.
    Set verbose=True for execution history. Limit count to avoid token issues.
    """
    client = _create_client(include_workflow=True)
    if isinstance(client, dict):
        return client

    try:
        workflows = client.get_workflows(count=min(count, 12000), all_results=True)

        # Filter out system workflows if requested
        if not include_system:
            workflows = [
                w
                for w in workflows
                if not any(
                    meta.key == "sys"
                    for meta in w.project.model_dump().get("metadata", [])
                )
            ]

        # Filter by status if requested
        if status_filter:
            filtered_workflows = []
            for workflow in workflows:
                if workflow.latest_sessions:
                    last_status = workflow.latest_sessions[0].last_attempt.status
                    if last_status == status_filter:
                        filtered_workflows.append(workflow)
            workflows = filtered_workflows

        # Filter by search term if requested
        if search:
            search_lower = search.lower()
            filtered_workflows = []
            for workflow in workflows:
                workflow_name = workflow.name.lower()
                project_name = workflow.project.name.lower()
                if search_lower in workflow_name or search_lower in project_name:
                    filtered_workflows.append(workflow)
            workflows = filtered_workflows

        if verbose:
            # Return full workflow details including sessions
            return {
                "workflows": [
                    {
                        "id": w.id,
                        "name": w.name,
                        "project": {
                            "id": w.project.id,
                            "name": w.project.name,
                        },
                        "timezone": w.timezone,
                        "schedule": w.schedule,
                        "latest_sessions": [
                            {
                                "session_time": s.session_time,
                                "status": s.last_attempt.status,
                                "success": s.last_attempt.success,
                                "duration": None,  # Would need date parsing
                            }
                            for s in w.latest_sessions[:3]  # Show last 3 sessions
                        ],
                    }
                    for w in workflows
                ]
            }
        else:
            # Return summary information
            return {
                "workflows": [
                    {
                        "id": w.id,
                        "name": w.name,
                        "project": w.project.name,
                        "last_status": (
                            w.latest_sessions[0].last_attempt.status
                            if w.latest_sessions
                            else "no_runs"
                        ),
                        "scheduled": w.schedule is not None,
                    }
                    for w in workflows
                ],
                "total_count": len(workflows),
            }
    except (ValueError, requests.RequestException) as e:
        return _format_error_response(f"Failed to retrieve workflows: {str(e)}")
    except Exception as e:
        return _format_error_response(
            f"Unexpected error while retrieving workflows: {str(e)}"
        )


# Register search and URL tools
search_tools.register_mcp_tools(
    mcp, _create_client, _format_error_response, _validate_project_id
)
url_tools.register_url_tools(mcp, _create_client, _format_error_response)

# Register new exploration and diagnostic tools
exploration_tools.register_exploration_tools(
    mcp,
    _create_client,
    _format_error_response,
    _validate_project_id,
    _safe_extract_member,
)
diagnostic_tools.register_diagnostic_tools(mcp, _create_client, _format_error_response)

# Register workflow execution tools
execution_tools.register_execution_tools(mcp, _create_client, _format_error_response)

if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport="stdio")
