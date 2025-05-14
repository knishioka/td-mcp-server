#!/usr/bin/env python3
"""
Standalone MCP server script for Treasure Data API.
This module is designed to be run directly with the MCP CLI using:
    mcp run /path/to/td_mcp_server/server.py

For Claude Desktop integration, use:
    mcp install server.py -v TD_API_KEY=your-api-key -v TD_ENDPOINT=api.treasuredata.com
"""

import os
import sys
import tarfile
import tempfile
import traceback
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

from td_mcp_server.api import TreasureDataClient

# Initialize FastMCP server
mcp = FastMCP("treasure-data")


@mcp.tool()
async def td_list_databases(
    verbose: bool = False, limit: int = 30, offset: int = 0, all_results: bool = False
) -> dict[str, Any]:
    """Get databases in your Treasure Data account with pagination support.

    Args:
        verbose: If True, return full details; if False, return only names (default)
        limit: Maximum number of databases to retrieve (defaults to 30)
        offset: Index to start retrieving from (defaults to 0)
        all_results: If True, retrieves all databases ignoring limit and offset
    """
    api_key = os.environ.get("TD_API_KEY")
    endpoint = os.environ.get("TD_ENDPOINT", "api.treasuredata.com")

    if not api_key:
        return {"error": "TD_API_KEY environment variable is not set"}

    try:
        client = TreasureDataClient(api_key=api_key, endpoint=endpoint)
        databases = client.get_databases(
            limit=limit, offset=offset, all_results=all_results
        )

        if verbose:
            # Return full database details
            return {"databases": [db.model_dump() for db in databases]}
        else:
            # Return only database names
            return {"databases": [db.name for db in databases]}
    except Exception as e:
        return {"error": str(e), "traceback": traceback.format_exc()}


@mcp.tool()
async def td_get_database(database_name: str) -> dict[str, Any]:
    """Get information about a specific database.

    Args:
        database_name: The name of the database to retrieve information for
    """
    api_key = os.environ.get("TD_API_KEY")
    endpoint = os.environ.get("TD_ENDPOINT", "api.treasuredata.com")

    if not api_key:
        return {"error": "TD_API_KEY environment variable is not set"}

    try:
        client = TreasureDataClient(api_key=api_key, endpoint=endpoint)
        database = client.get_database(database_name)
        if database:
            return database.model_dump()
        else:
            return {"error": f"Database '{database_name}' not found"}
    except Exception as e:
        return {"error": str(e), "traceback": traceback.format_exc()}


@mcp.tool()
async def td_list_tables(
    database_name: str,
    verbose: bool = False,
    limit: int = 30,
    offset: int = 0,
    all_results: bool = False,
) -> dict[str, Any]:
    """Get tables in a specific Treasure Data database with pagination support.

    Args:
        database_name: The name of the database to retrieve tables from
        verbose: If True, return full details; if False, return only names (default)
        limit: Maximum number of tables to retrieve (defaults to 30)
        offset: Index to start retrieving from (defaults to 0)
        all_results: If True, retrieves all tables ignoring limit and offset
    """
    api_key = os.environ.get("TD_API_KEY")
    endpoint = os.environ.get("TD_ENDPOINT", "api.treasuredata.com")

    if not api_key:
        return {"error": "TD_API_KEY environment variable is not set"}

    try:
        client = TreasureDataClient(api_key=api_key, endpoint=endpoint)

        # First, verify that the database exists
        database = client.get_database(database_name)
        if not database:
            return {"error": f"Database '{database_name}' not found"}

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
    except Exception as e:
        return {"error": str(e), "traceback": traceback.format_exc()}


@mcp.tool()
async def td_list_projects(
    verbose: bool = False,
    limit: int = 30,
    offset: int = 0,
    all_results: bool = False,
    include_system: bool = False,
) -> dict[str, Any]:
    """Get workflow projects in your Treasure Data account with pagination support.

    Workflow projects in Treasure Data are containers for data workflows that include
    SQL queries and Digdag (.dig) files. These projects define data processing pipelines
    and scheduled tasks that execute on the Treasure Data platform.

    Args:
        verbose: If True, return full details; if False, return only names (default)
        limit: Maximum number of projects to retrieve (defaults to 30)
        offset: Index to start retrieving from (defaults to 0)
        all_results: If True, retrieves all projects ignoring limit and offset
        include_system: If True, include system-generated projects (with "sys" metadata)
    """
    api_key = os.environ.get("TD_API_KEY")
    endpoint = os.environ.get("TD_ENDPOINT", "api.treasuredata.com")
    workflow_endpoint = os.environ.get("TD_WORKFLOW_ENDPOINT")

    if not api_key:
        return {"error": "TD_API_KEY environment variable is not set"}

    try:
        client = TreasureDataClient(
            api_key=api_key, endpoint=endpoint, workflow_endpoint=workflow_endpoint
        )

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
    except Exception as e:
        return {"error": str(e), "traceback": traceback.format_exc()}


@mcp.tool()
async def td_get_project(project_id: str) -> dict[str, Any]:
    """Get detailed information about a specific workflow project.
    Note: This method provides basic project metadata. For detailed project contents
    including SQL queries and workflow definitions, use td_download_project_archive
    followed by td_list_project_files and td_read_project_file to examine the files.

    Retrieves comprehensive details about a Treasure Data workflow project.
    These projects contain SQL queries and Digdag (.dig) workflow definition files
    that orchestrate data processing tasks. Workflows are used for scheduled jobs,
    ETL processes, and data transformation pipelines within Treasure Data.

    Args:
        project_id: The ID of the workflow project to retrieve information for
    """
    api_key = os.environ.get("TD_API_KEY")
    endpoint = os.environ.get("TD_ENDPOINT", "api.treasuredata.com")
    workflow_endpoint = os.environ.get("TD_WORKFLOW_ENDPOINT")

    if not api_key:
        return {"error": "TD_API_KEY environment variable is not set"}

    try:
        client = TreasureDataClient(
            api_key=api_key, endpoint=endpoint, workflow_endpoint=workflow_endpoint
        )
        project = client.get_project(project_id)
        if project:
            return project.model_dump()
        else:
            return {"error": f"Project with ID '{project_id}' not found"}
    except Exception as e:
        return {"error": str(e), "traceback": traceback.format_exc()}


@mcp.tool()
async def td_download_project_archive(project_id: str) -> dict[str, Any]:
    """Download a project's archive (tar.gz) and return information about the download.

    This tool downloads the complete archive of a Treasure Data workflow project,
    which contains all SQL queries, Digdag (.dig) files, Python scripts, and other
    resources. The file is temporarily stored on the server.

    Args:
        project_id: The ID of the workflow project to download
    """
    api_key = os.environ.get("TD_API_KEY")
    endpoint = os.environ.get("TD_ENDPOINT", "api.treasuredata.com")
    workflow_endpoint = os.environ.get("TD_WORKFLOW_ENDPOINT")

    if not api_key:
        return {"error": "TD_API_KEY environment variable is not set"}

    try:
        # Create temporary directory for storing the archive
        temp_dir = tempfile.mkdtemp(prefix="td_project_")
        output_path = os.path.join(temp_dir, f"project_{project_id}.tar.gz")

        client = TreasureDataClient(
            api_key=api_key, endpoint=endpoint, workflow_endpoint=workflow_endpoint
        )

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
    except Exception as e:
        return {"error": str(e), "traceback": traceback.format_exc()}


@mcp.tool()
async def td_list_project_files(archive_path: str) -> dict[str, Any]:
    """List all files contained in a project archive.

    This tool extracts and lists the content of a previously downloaded
    project archive, showing all files and directories within the project.

    Args:
        archive_path: The path to the downloaded project archive (.tar.gz file)
    """
    try:
        if not os.path.exists(archive_path):
            return {"error": f"Archive file not found at path: {archive_path}"}

        file_list = []

        with tarfile.open(archive_path, "r:gz") as tar:
            for member in tar.getmembers():
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
    except Exception as e:
        return {"error": str(e), "traceback": traceback.format_exc()}


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
    try:
        if not os.path.exists(archive_path):
            return {"error": f"Archive file not found at path: {archive_path}"}

        try:
            with tarfile.open(archive_path, "r:gz") as tar:
                try:
                    file_info = tar.getmember(file_path)

                    # Don't try to read directories
                    if file_info.isdir():
                        return {"error": f"Cannot read directory contents: {file_path}"}

                    # Extract and read the file
                    f = tar.extractfile(file_info)
                    if f is None:
                        return {"error": f"Failed to extract file: {file_path}"}

                    content = f.read().decode("utf-8")

                    extension = Path(file_path).suffix.lower()

                    return {
                        "success": True,
                        "file_path": file_path,
                        "content": content,
                        "size": file_info.size,
                        "extension": extension,
                    }
                except KeyError:
                    return {"error": f"File not found in archive: {file_path}"}
        except tarfile.ReadError:
            return {"error": f"Invalid or corrupted archive file: {archive_path}"}
    except Exception as e:
        return {"error": str(e), "traceback": traceback.format_exc()}


if __name__ == "__main__":
    # Check for API key
    api_key = os.environ.get("TD_API_KEY")
    endpoint = os.environ.get("TD_ENDPOINT", "api.treasuredata.com")

    if not api_key:
        sys.exit(1)

    # Run the FastMCP server
    try:
        mcp.run(transport="stdio")
    except Exception:
        sys.exit(1)
