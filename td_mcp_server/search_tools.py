"""
Search tools for Treasure Data MCP Server.
Provides efficient name-based search for projects and workflows.
"""

from typing import Any

# These will be injected from mcp_impl.py to avoid circular import
mcp = None
_create_client = None
_format_error_response = None
_validate_project_id = None


def register_mcp_tools(
    mcp_instance, create_client_func, format_error_func, validate_project_func
):
    """Register MCP tools with the provided MCP instance."""
    global mcp, _create_client, _format_error_response, _validate_project_id
    mcp = mcp_instance
    _create_client = create_client_func
    _format_error_response = format_error_func
    _validate_project_id = validate_project_func

    # Register all tools
    mcp.tool()(td_find_project)
    mcp.tool()(td_find_workflow)
    mcp.tool()(td_get_project_by_name)


async def td_find_project(
    search_term: str,
    exact_match: bool = False,
) -> dict[str, Any]:
    """Find project by name or partial name match.

    Searches through all projects efficiently and returns matching results.
    Use exact_match=True for exact name matching.

    Args:
        search_term: Project name or partial name to search for
        exact_match: If True, only return exact matches (default: False)

    Returns:
        Dict with found projects including their IDs and metadata
    """
    if not search_term or not search_term.strip():
        return _format_error_response("Search term cannot be empty")

    client = _create_client(include_workflow=True)
    if isinstance(client, dict):
        return client

    try:
        # First, try to get projects directly (up to 200)
        projects = client.get_projects(limit=200, all_results=True)

        found_projects = []
        search_lower = search_term.lower()

        for project in projects:
            project_name = project.name.lower()

            if exact_match:
                if project_name == search_lower:
                    found_projects.append(project)
            else:
                if search_lower in project_name:
                    found_projects.append(project)

        if found_projects:
            return {
                "found": True,
                "count": len(found_projects),
                "projects": [
                    {
                        "id": p.id,
                        "name": p.name,
                        "created_at": p.created_at,
                        "updated_at": p.updated_at,
                    }
                    for p in found_projects
                ],
            }

        # If not found in projects, search through workflows
        workflows = client.get_workflows(count=1000, all_results=True)

        project_map = {}
        for workflow in workflows:
            project_name = workflow.project.name
            project_id = workflow.project.id

            if exact_match:
                if project_name.lower() == search_lower:
                    if project_id not in project_map:
                        project_map[project_id] = {
                            "id": project_id,
                            "name": project_name,
                            "workflow_count": 0,
                        }
                    project_map[project_id]["workflow_count"] += 1
            else:
                if search_lower in project_name.lower():
                    if project_id not in project_map:
                        project_map[project_id] = {
                            "id": project_id,
                            "name": project_name,
                            "workflow_count": 0,
                        }
                    project_map[project_id]["workflow_count"] += 1

        if project_map:
            # Get full project details for found projects
            projects_with_details = []
            for project_id, project_info in project_map.items():
                try:
                    project = client.get_project(project_id)
                    if project:
                        projects_with_details.append(
                            {
                                "id": project.id,
                                "name": project.name,
                                "created_at": project.created_at,
                                "updated_at": project.updated_at,
                                "workflow_count": project_info["workflow_count"],
                            }
                        )
                except Exception:
                    # Fallback to basic info
                    projects_with_details.append(project_info)

            return {
                "found": True,
                "count": len(projects_with_details),
                "projects": projects_with_details,
                "source": "workflows",
            }

        return {
            "found": False,
            "count": 0,
            "message": f"No projects found matching '{search_term}'",
        }

    except Exception as e:
        return _format_error_response(f"Failed to search projects: {str(e)}")


async def td_find_workflow(
    search_term: str,
    project_name: str | None = None,
    exact_match: bool = False,
    status_filter: str | None = None,
) -> dict[str, Any]:
    """Find workflows by name or partial name match.

    Searches through workflows efficiently with optional project and status filters.

    Args:
        search_term: Workflow name or partial name to search for
        project_name: Optional project name to filter by
        exact_match: If True, only return exact matches (default: False)
        status_filter: Filter by status ('success', 'error', 'running', None)

    Returns:
        Dict with found workflows including their project info and status
    """
    if not search_term or not search_term.strip():
        return _format_error_response("Search term cannot be empty")

    client = _create_client(include_workflow=True)
    if isinstance(client, dict):
        return client

    try:
        # Get workflows (up to 1000)
        workflows = client.get_workflows(count=1000, all_results=True)

        found_workflows = []
        search_lower = search_term.lower()
        project_lower = project_name.lower() if project_name else None

        for workflow in workflows:
            workflow_name = workflow.name.lower()
            workflow_project = workflow.project.name.lower()

            # Check workflow name match
            name_match = False
            if exact_match:
                name_match = workflow_name == search_lower
            else:
                name_match = search_lower in workflow_name

            if not name_match:
                continue

            # Check project filter if specified
            if project_lower:
                if project_lower not in workflow_project:
                    continue

            # Check status filter if specified
            if status_filter:
                if workflow.latest_sessions:
                    last_status = workflow.latest_sessions[0].last_attempt.status
                    if last_status != status_filter:
                        continue
                else:
                    # No sessions means no status, skip if filtering by status
                    continue

            # Prepare workflow info
            workflow_info = {
                "id": workflow.id,
                "name": workflow.name,
                "project": {
                    "id": workflow.project.id,
                    "name": workflow.project.name,
                },
                "timezone": workflow.timezone,
                "scheduled": workflow.schedule is not None,
            }

            # Add latest status if available
            if workflow.latest_sessions:
                latest = workflow.latest_sessions[0]
                workflow_info["latest_session"] = {
                    "session_time": latest.session_time,
                    "status": latest.last_attempt.status,
                    "success": latest.last_attempt.success,
                }
            else:
                workflow_info["latest_session"] = None

            found_workflows.append(workflow_info)

        if found_workflows:
            return {
                "found": True,
                "count": len(found_workflows),
                "workflows": found_workflows,
            }

        message = f"No workflows found matching '{search_term}'"
        if project_name:
            message += f" in project '{project_name}'"
        if status_filter:
            message += f" with status '{status_filter}'"

        return {"found": False, "count": 0, "message": message}

    except Exception as e:
        return _format_error_response(f"Failed to search workflows: {str(e)}")


async def td_get_project_by_name(
    project_name: str,
) -> dict[str, Any]:
    """Get project details by exact name match.

    Finds a project by name and returns its full details.
    This is more convenient than finding the ID first.

    Args:
        project_name: Exact project name

    Returns:
        Project details if found, error otherwise
    """
    if not project_name or not project_name.strip():
        return _format_error_response("Project name cannot be empty")

    # Use find_project with exact match
    search_result = await td_find_project(project_name, exact_match=True)

    if search_result.get("found") and search_result.get("projects"):
        project = search_result["projects"][0]

        # Get full details using td_get_project
        client = _create_client(include_workflow=True)
        if isinstance(client, dict):
            return client

        try:
            full_project = client.get_project(project["id"])
            if full_project:
                return {"project": full_project.model_dump()}
            else:
                return _format_error_response(
                    f"Could not retrieve details for project '{project_name}'"
                )
        except Exception as e:
            return _format_error_response(f"Failed to get project details: {str(e)}")

    return _format_error_response(f"Project '{project_name}' not found")
