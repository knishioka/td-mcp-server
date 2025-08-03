"""
URL analysis tools for Treasure Data MCP Server.
Helps users investigate from console URLs.
"""

import re
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    pass

# These will be injected from mcp_impl.py to avoid circular import
mcp: Any = None
_create_client: Callable[..., Any] = None  # type: ignore[assignment]
_format_error_response: Callable[[str], dict[str, Any]] = None  # type: ignore[assignment]


def register_url_tools(mcp_instance, create_client_func, format_error_func):
    """Register URL tools with the provided MCP instance."""
    global mcp, _create_client, _format_error_response
    mcp = mcp_instance
    _create_client = create_client_func
    _format_error_response = format_error_func

    # Register all tools
    mcp.tool()(td_analyze_url)
    mcp.tool()(td_get_workflow)


async def td_analyze_url(url: str) -> dict[str, Any]:
    """Analyze any Treasure Data console URL to get resource details.

    Smart URL parser that extracts IDs and fetches information. Use when someone
    shares a console link in Slack, email, or documentation.

    Common scenarios:
    - Someone shares workflow URL during incident investigation
    - Documentation contains console links to resources
    - Error message includes console URL reference
    - Quick lookup from browser URL copy/paste

    Supported formats:
    - Workflow: https://console.../app/workflows/12345678/info
    - Project: https://console.../app/projects/123456
    - Job: https://console.../app/jobs/123456

    Automatically detects type and returns full resource information.
    """
    if not url or not url.strip():
        return _format_error_response("URL cannot be empty")

    # Parse workflow URL
    workflow_match = re.search(r"/app/workflows/(\d+)", url)
    if workflow_match:
        workflow_id = workflow_match.group(1)
        return await td_get_workflow(workflow_id)

    # Parse project URL
    project_match = re.search(r"/app/projects/(\d+)", url)
    if project_match:
        project_id = project_match.group(1)
        client = _create_client(include_workflow=True)
        if isinstance(client, dict):
            return client

        try:
            project = client.get_project(project_id)
            if project:
                return {"type": "project", "project": project.model_dump()}
            else:
                return _format_error_response(
                    f"Project with ID '{project_id}' not found"
                )
        except Exception as e:
            return _format_error_response(f"Failed to get project: {str(e)}")

    # Parse job URL
    job_match = re.search(r"/app/jobs/(\d+)", url)
    if job_match:
        job_id = job_match.group(1)
        return {
            "type": "job",
            "job_id": job_id,
            "message": "Job information retrieval not yet implemented",
        }

    return _format_error_response(
        "Unrecognized URL format. Supported: /app/workflows/ID, /app/projects/ID"
    )


async def td_get_workflow(workflow_id: str) -> dict[str, Any]:
    """Get workflow details using numeric ID - essential for console URLs.

    Direct workflow lookup when you have the ID. Handles large workflow IDs
    that exceed pagination limits. Returns project info and execution history.

    Common scenarios:
    - Extracting ID from console URL (../workflows/12345678/info)
    - Looking up workflow from error logs containing ID
    - Getting project context for a known workflow ID
    - Checking execution status by workflow ID

    Returns workflow name, project details, schedule, and recent runs.
    Includes console URL for quick browser access.
    """
    if not workflow_id or not workflow_id.strip():
        return _format_error_response("Workflow ID cannot be empty")

    # Validate workflow ID format
    if not re.match(r"^\d+$", workflow_id):
        return _format_error_response("Invalid workflow ID format. Must be numeric.")

    client = _create_client(include_workflow=True)
    if isinstance(client, dict):
        return client

    try:
        # First try the direct API endpoint
        workflow = client.get_workflow_by_id(workflow_id)

        if workflow:
            # Found the workflow via direct API
            result: dict[str, Any] = {
                "type": "workflow",
                "workflow": {
                    "id": workflow.id,
                    "name": workflow.name,
                    "project": {
                        "id": workflow.project.id,
                        "name": workflow.project.name,
                    },
                    "timezone": workflow.timezone,
                    "scheduled": workflow.schedule is not None,
                },
            }

            # Add schedule info if available
            if workflow.schedule:
                result["workflow"]["schedule"] = workflow.schedule

            # Add latest session info if available
            # Note: Direct API might not include session info
            if workflow.latest_sessions:
                latest_sessions = []
                for session in workflow.latest_sessions[:5]:  # Last 5 sessions
                    latest_sessions.append(
                        {
                            "session_time": session.session_time,
                            "status": session.last_attempt.status,
                            "success": session.last_attempt.success,
                        }
                    )
                result["workflow"]["latest_sessions"] = latest_sessions

            # Construct console URL
            result[
                "console_url"
            ] = f"https://console.treasuredata.com/app/workflows/{workflow_id}/info"

            return result

        # If not found via direct API, fall back to searching through all workflows
        # This might be needed for workflows accessible via console API only
        workflows = client.get_workflows(count=1000, all_results=True)

        for workflow in workflows:
            if workflow.id == workflow_id:
                # Found the workflow
                result = {
                    "type": "workflow",
                    "workflow": {
                        "id": workflow.id,
                        "name": workflow.name,
                        "project": {
                            "id": workflow.project.id,
                            "name": workflow.project.name,
                        },
                        "timezone": workflow.timezone,
                        "scheduled": workflow.schedule is not None,
                    },
                }

                # Add schedule info if available
                if workflow.schedule:
                    result["workflow"]["schedule"] = workflow.schedule

                # Add latest session info if available
                if workflow.latest_sessions:
                    latest_sessions = []
                    for session in workflow.latest_sessions[:5]:  # Last 5 sessions
                        latest_sessions.append(
                            {
                                "session_time": session.session_time,
                                "status": session.last_attempt.status,
                                "success": session.last_attempt.success,
                            }
                        )
                    result["workflow"]["latest_sessions"] = latest_sessions

                # Construct console URL
                result[
                    "console_url"
                ] = f"https://console.treasuredata.com/app/workflows/{workflow_id}/info"

                return result

        return _format_error_response(f"Workflow with ID '{workflow_id}' not found")

    except Exception as e:
        return _format_error_response(f"Failed to get workflow: {str(e)}")
