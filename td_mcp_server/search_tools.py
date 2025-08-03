"""
Search tools for Treasure Data MCP Server.
Provides efficient name-based search for projects and workflows.
"""

from collections.abc import Callable
from typing import Any

# These will be injected from mcp_impl.py to avoid circular import
mcp: Any | None = None
_create_client: Callable[..., Any] | None = None
_format_error_response: Callable[[str], dict[str, Any]] | None = None
_validate_project_id: Callable[[str], bool] | None = None


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
    mcp.tool()(td_smart_search)


async def td_find_project(
    search_term: str,
    exact_match: bool = False,
) -> dict[str, Any]:
    """Find project by name when you don't know the exact ID.

    Searches all projects and returns matches. Useful when you know project
    name but need the ID for other operations like downloading archives.

    Common scenarios:
    - User mentions project name, need to find ID
    - Looking for projects containing specific keywords
    - Getting project ID before using td_download_project_archive
    - Finding multiple projects with similar names

    Use exact_match=True for precise name matching, False for fuzzy search.
    Returns project IDs, names, and metadata for all matches.
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
    """Find workflows by name to get IDs and check execution status.

    Essential for locating specific workflows when you know the name.
    Returns workflow IDs, project info, and latest execution status.

    Common scenarios:
    - User mentions workflow name, need to find details
    - Looking for failing workflows with specific names
    - Finding workflows within a specific project
    - Getting workflow ID before detailed analysis
    - Checking if a named workflow is running/failed

    Filters: project_name (optional), status ('success', 'error', 'running').
    Use exact_match=True for precise names, False for partial matches.
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
    """Get full project details using exact name instead of ID.

    Convenient shortcut when you know the exact project name.
    Combines find + get operations for immediate detailed results.

    Common scenarios:
    - User provides exact project name, need full details
    - Quick project metadata lookup by name
    - Avoiding two-step process (find ID then get details)
    - Getting revision/timestamps for known project

    Requires exact name match. For fuzzy search use td_find_project.
    Returns same details as td_get_project but using name lookup.
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


async def td_smart_search(
    query: str,
    search_scope: str = "all",
    search_mode: str = "fuzzy",
    active_only: bool = True,
    min_relevance: float = 0.7,
) -> dict[str, Any]:
    """Universal search across Treasure Data - best for broad queries.

    One-stop search for projects, workflows, and tables with smart ranking.
    Use when unsure what resource type you're looking for or need comprehensive results.

    Common scenarios:
    - "Find anything related to customer analytics"
    - Discovering resources around a topic/keyword
    - Broad exploration of available data assets
    - Finding resources when type is unknown
    - Cross-resource impact analysis

    Search modes:
    - exact: Precise string matching only
    - fuzzy: Partial matches and substrings (default)
    - semantic: Word-based matching for concepts

    Scopes: "all", "projects", "workflows", "tables"
    Returns ranked results with relevance scores (0-1).
    """
    if not query or not query.strip():
        return _format_error_response("Search query cannot be empty")

    if search_scope not in ["projects", "workflows", "tables", "all"]:
        return _format_error_response("Invalid search scope")

    if search_mode not in ["exact", "fuzzy", "semantic"]:
        return _format_error_response("Invalid search mode")

    client = _create_client(include_workflow=True)
    if isinstance(client, dict):
        return client

    results: dict[str, Any] = {
        "query": query,
        "search_scope": search_scope,
        "search_mode": search_mode,
        "results": [],
        "total_found": 0,
    }

    try:
        # Helper function to calculate relevance score
        def calculate_relevance(text: str, query: str, exact: bool = False) -> float:
            text_lower = text.lower()
            query_lower = query.lower()

            if exact:
                return 1.0 if query_lower == text_lower else 0.0

            # Exact match gets highest score
            if query_lower == text_lower:
                return 1.0

            # Substring match
            if query_lower in text_lower:
                # Score based on position and length ratio
                position_score = 1.0 - (text_lower.index(query_lower) / len(text_lower))
                length_score = len(query_lower) / len(text_lower)
                return (position_score + length_score) / 2

            # Fuzzy matching for semantic mode
            if search_mode == "semantic":
                # Simple word-based matching
                query_words = set(query_lower.split())
                text_words = set(text_lower.split())
                if query_words:
                    overlap = len(query_words & text_words) / len(query_words)
                    return overlap * 0.8  # Slightly lower score for word matches

            return 0.0

        # Search projects
        if search_scope in ["projects", "all"]:
            try:
                projects = client.get_projects(limit=200, all_results=True)
                for project in projects:
                    relevance = calculate_relevance(
                        project.name, query, exact=(search_mode == "exact")
                    )

                    if relevance >= min_relevance:
                        results["results"].append(
                            {
                                "type": "project",
                                "relevance": round(relevance, 3),
                                "resource": {
                                    "id": project.id,
                                    "name": project.name,
                                    "created_at": project.created_at,
                                    "updated_at": project.updated_at,
                                },
                                "match_context": f"Project name: {project.name}",
                            }
                        )
            except Exception:
                # Log error but continue with other searches
                pass

        # Search workflows
        if search_scope in ["workflows", "all"]:
            try:
                workflows = client.get_workflows(count=1000, all_results=True)
                for workflow in workflows:
                    # Check workflow name
                    workflow_relevance = calculate_relevance(
                        workflow.name, query, exact=(search_mode == "exact")
                    )

                    # Also check project name for better context
                    project_relevance = calculate_relevance(
                        workflow.project.name, query, exact=(search_mode == "exact")
                    )

                    # Take the higher relevance
                    relevance = max(workflow_relevance, project_relevance * 0.7)

                    if relevance >= min_relevance:
                        # Get latest status
                        latest_status = "no_runs"
                        if workflow.latest_sessions:
                            latest_status = workflow.latest_sessions[
                                0
                            ].last_attempt.status

                        results["results"].append(
                            {
                                "type": "workflow",
                                "relevance": round(relevance, 3),
                                "resource": {
                                    "id": workflow.id,
                                    "name": workflow.name,
                                    "project": workflow.project.name,
                                    "scheduled": workflow.schedule is not None,
                                    "latest_status": latest_status,
                                },
                                "match_context": (
                                    f"Workflow: {workflow.name} "
                                    f"in project: {workflow.project.name}"
                                ),
                            }
                        )
            except Exception:
                # Log error but continue
                pass

        # Search tables
        if search_scope in ["tables", "all"]:
            try:
                # Get all databases first
                databases = client.get_databases(all_results=True)

                for database in databases[:10]:  # Limit to avoid too many API calls
                    try:
                        tables = client.get_tables(database.name, all_results=True)
                        for table in tables:
                            # Check table name
                            table_relevance = calculate_relevance(
                                table.name, query, exact=(search_mode == "exact")
                            )

                            # Also consider database name
                            db_relevance = calculate_relevance(
                                database.name, query, exact=(search_mode == "exact")
                            )

                            relevance = max(table_relevance, db_relevance * 0.5)

                            if relevance >= min_relevance:
                                results["results"].append(
                                    {
                                        "type": "table",
                                        "relevance": round(relevance, 3),
                                        "resource": {
                                            "name": table.name,
                                            "database": database.name,
                                            "full_name": (
                                                f"{database.name}.{table.name}"
                                            ),
                                            "type": table.type,
                                            "count": table.count,
                                        },
                                        "match_context": (
                                            f"Table: {table.name} "
                                            f"in database: {database.name}"
                                        ),
                                    }
                                )
                    except Exception:
                        # Skip databases with access issues
                        continue
            except Exception:
                # Log error but continue
                pass

        # Sort results by relevance
        results["results"].sort(key=lambda x: x["relevance"], reverse=True)
        results["total_found"] = len(results["results"])

        # Add search suggestions if few results
        if results["total_found"] < 5 and search_mode == "exact":
            results[
                "suggestion"
            ] = "Try using fuzzy or semantic search mode for more results"

        # Limit results to prevent token overflow
        if len(results["results"]) > 50:
            results["results"] = results["results"][:50]
            results["truncated"] = True
            results[
                "truncated_message"
            ] = f"Showing top 50 of {results['total_found']} results"

        return results

    except Exception as e:
        return _format_error_response(f"Search failed: {str(e)}")
