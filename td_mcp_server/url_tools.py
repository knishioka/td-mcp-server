"""
URL analysis tools for Treasure Data MCP Server.
Helps users investigate from console URLs.
"""

import re
from typing import Any

# These will be injected from mcp_impl.py to avoid circular import
mcp = None
_create_client = None
_format_error_response = None


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
    """Extract and retrieve information from a Treasure Data console URL.

    Use this when you have a console URL and need to get details about the resource.
    Automatically detects the resource type (workflow, project, job) from the URL.

    Supported URL formats:
    - Workflow: https://console.us01.treasuredata.com/app/workflows/12345678/info
    - Project: https://console.us01.treasuredata.com/app/projects/123456
    - Job: https://console.us01.treasuredata.com/app/jobs/123456

    Returns complete information about the resource including project details.
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
    """Get workflow details by numeric ID (e.g., from console URL).

    Use this when you have a workflow ID and need its details including project info.
    Returns workflow name, project name/ID, schedule, and recent execution history.

    Example: For URL .../workflows/12345678/info, use workflow_id="12345678"

    Returns:
        - Workflow name and configuration
        - Project name and ID (can be used with td_get_project)
        - Latest execution status and history
        - Console URL for easy access
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
        # Get workflows and search for the specific ID
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
