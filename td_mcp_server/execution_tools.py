"""
Workflow execution tools for Treasure Data MCP Server.
Provides tools for monitoring and analyzing workflow executions.
"""

from collections.abc import Callable
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    pass

# These will be injected from mcp_impl.py to avoid circular import
mcp: Any = None
_create_client: Callable[..., Any] = None  # type: ignore[assignment]
_format_error_response: Callable[[str], dict[str, Any]] = None  # type: ignore[assignment]


def register_execution_tools(mcp_instance, create_client_func, format_error_func):
    """Register execution tools with the provided MCP instance."""
    global mcp, _create_client, _format_error_response
    mcp = mcp_instance
    _create_client = create_client_func
    _format_error_response = format_error_func

    # Register all tools
    mcp.tool()(td_get_session)
    mcp.tool()(td_list_sessions)
    mcp.tool()(td_get_attempt)
    mcp.tool()(td_get_attempt_tasks)
    mcp.tool()(td_analyze_execution)


async def td_get_session(session_id: str) -> dict[str, Any]:
    """Get workflow session details by ID to check execution status and timing.

    A session is a scheduled workflow run. Use when you have a session ID and need
    to check if it ran successfully, when it was scheduled, or get attempt details.

    Common scenarios:
    - Verify if a scheduled workflow executed at the expected time
    - Get the attempt ID to investigate execution details
    - Check overall success/failure status

    Returns session info with workflow name, schedule time, and latest attempt status.
    """
    if not session_id or not session_id.strip():
        return _format_error_response("Session ID cannot be empty")

    client = _create_client(include_workflow=True)
    if isinstance(client, dict):
        return client

    try:
        session = client.get_session(session_id)

        if session:
            result = {
                "type": "session",
                "session": {
                    "id": session.id,
                    "project": session.project,
                    "workflow": session.workflow,
                    "session_uuid": session.session_uuid,
                    "session_time": session.session_time,
                    "last_attempt": {
                        "id": session.last_attempt.id,
                        "done": session.last_attempt.done,
                        "success": session.last_attempt.success,
                        "status": session.last_attempt.status,
                        "created_at": session.last_attempt.created_at,
                        "finished_at": session.last_attempt.finished_at,
                    },
                },
            }
            return result
        else:
            return _format_error_response(f"Session with ID '{session_id}' not found")

    except Exception as e:
        return _format_error_response(f"Failed to get session: {str(e)}")


async def td_list_sessions(
    workflow_id: str | None = None, count: int = 20
) -> dict[str, Any]:
    """List recent workflow executions to monitor status and find failures.

    Shows recent scheduled runs (sessions) with their execution status. Filter by
    workflow ID to see history of a specific workflow, or leave empty for all.

    Common scenarios:
    - Check which workflows ran recently and their status
    - Find failed executions that need investigation
    - Monitor execution patterns for a specific workflow
    - Get session IDs for detailed analysis

    Returns list with workflow names, execution times, and success/failure status.
    """
    client = _create_client(include_workflow=True)
    if isinstance(client, dict):
        return client

    try:
        sessions = client.get_sessions(workflow_id=workflow_id, last=count)

        session_list = []
        for session in sessions:
            session_info = {
                "id": session.id,
                "workflow": session.workflow["name"],
                "project": session.project["name"],
                "session_time": session.session_time,
                "status": session.last_attempt.status,
                "success": session.last_attempt.success,
            }

            # Add duration if available
            if session.last_attempt.created_at and session.last_attempt.finished_at:
                session_info["created_at"] = session.last_attempt.created_at
                session_info["finished_at"] = session.last_attempt.finished_at

            session_list.append(session_info)

        result = {
            "sessions": session_list,
            "count": len(session_list),
        }

        if workflow_id:
            result["filtered_by_workflow"] = workflow_id

        return result

    except Exception as e:
        return _format_error_response(f"Failed to list sessions: {str(e)}")


async def td_get_attempt(attempt_id: str) -> dict[str, Any]:
    """Get workflow attempt details to investigate specific execution instance.

    An attempt is one execution try of a scheduled session. Use when you have an
    attempt ID from error logs or td_get_session and need execution details.

    Common scenarios:
    - Investigate why a workflow execution failed
    - Check how long the execution took
    - See if this was a retry after previous failure
    - Get execution parameters for debugging

    Returns attempt status, timing, retry info, and safe execution parameters.
    """
    if not attempt_id or not attempt_id.strip():
        return _format_error_response("Attempt ID cannot be empty")

    client = _create_client(include_workflow=True)
    if isinstance(client, dict):
        return client

    try:
        attempt = client.get_attempt(attempt_id)

        if attempt:
            result = {
                "type": "attempt",
                "attempt": {
                    "id": attempt.id,
                    "index": attempt.index,
                    "project": attempt.project,
                    "workflow": attempt.workflow,
                    "session_id": attempt.session_id,
                    "session_time": attempt.session_time,
                    "retry_attempt_name": attempt.retry_attempt_name,
                    "done": attempt.done,
                    "success": attempt.success,
                    "status": attempt.status,
                    "created_at": attempt.created_at,
                    "finished_at": attempt.finished_at,
                },
            }

            # Add duration if finished
            if attempt.created_at and attempt.finished_at:
                try:
                    from datetime import datetime

                    created = datetime.fromisoformat(
                        attempt.created_at.replace("Z", "+00:00")
                    )
                    finished = datetime.fromisoformat(
                        attempt.finished_at.replace("Z", "+00:00")
                    )
                    duration = finished - created
                    result["attempt"]["duration_seconds"] = duration.total_seconds()
                except Exception:
                    pass  # Ignore date parsing errors

            # Add non-sensitive parameters
            if attempt.params:
                # Filter out sensitive parameters
                safe_params = {
                    k: v
                    for k, v in attempt.params.items()
                    if not any(
                        sensitive in k.lower()
                        for sensitive in ["email", "ip", "user_id", "token", "key"]
                    )
                }
                if safe_params:
                    result["attempt"]["params"] = safe_params

            return result
        else:
            return _format_error_response(f"Attempt with ID '{attempt_id}' not found")

    except Exception as e:
        return _format_error_response(f"Failed to get attempt: {str(e)}")


async def td_get_attempt_tasks(attempt_id: str) -> dict[str, Any]:
    """Get task breakdown to find which step failed or is slow in workflow.

    Shows all individual tasks (steps) within a workflow execution with their
    status, timing, and dependencies. Essential for debugging failed workflows.

    Common scenarios:
    - Find exactly which task/query failed in a complex workflow
    - Identify slow-running tasks causing delays
    - Understand task execution order and dependencies
    - Debug data processing issues at task level

    Returns task list with names, states, timing, and failure details.
    """
    if not attempt_id or not attempt_id.strip():
        return _format_error_response("Attempt ID cannot be empty")

    client = _create_client(include_workflow=True)
    if isinstance(client, dict):
        return client

    try:
        tasks = client.get_attempt_tasks(attempt_id)

        # Process tasks to create hierarchy and statistics
        task_list = []
        task_stats = {
            "total": len(tasks),
            "success": 0,
            "failed": 0,
            "running": 0,
            "blocked": 0,
            "other": 0,
        }

        for task in tasks:
            task_info = {
                "id": task.id,
                "name": task.full_name,
                "state": task.state,
                "is_group": task.is_group,
            }

            # Add parent info for hierarchy
            if task.parent_id:
                task_info["parent_id"] = task.parent_id

            # Add timing info
            if task.started_at:
                task_info["started_at"] = task.started_at
            if task.updated_at:
                task_info["updated_at"] = task.updated_at

            # Add dependencies
            if task.upstreams:
                task_info["depends_on"] = task.upstreams

            # Add non-sensitive config
            if task.config:
                # Extract key task type info
                if "td>" in task.config:
                    task_info["type"] = "td_query"
                    if "database" in task.config["td>"]:
                        task_info["database"] = task.config["td>"]["database"]
                elif "py>" in task.config:
                    task_info["type"] = "python"
                elif "sh>" in task.config:
                    task_info["type"] = "shell"
                else:
                    task_info["type"] = "other"

            # Add error info if failed
            if task.error and task.state in ["failed", "error"]:
                task_info["error"] = task.error

            # Update statistics
            if task.state == "success":
                task_stats["success"] += 1
            elif task.state in ["failed", "error"]:
                task_stats["failed"] += 1
            elif task.state == "running":
                task_stats["running"] += 1
            elif task.state == "blocked":
                task_stats["blocked"] += 1
            else:
                task_stats["other"] += 1

            task_list.append(task_info)

        return {
            "attempt_id": attempt_id,
            "tasks": task_list,
            "statistics": task_stats,
        }

    except Exception as e:
        return _format_error_response(f"Failed to get attempt tasks: {str(e)}")


async def td_analyze_execution(url_or_id: str) -> dict[str, Any]:
    """Analyze workflow execution from console URL or ID - best for debugging.

    Smart analysis tool that accepts URLs from error alerts or IDs. Automatically
    detects type and provides comprehensive execution analysis with recommendations.

    Accepts:
    - Console URLs (e.g., https://console.../app/sessions/123456)
    - Session IDs (e.g., 123456789)
    - Attempt IDs (e.g., 987654321)

    Common scenarios:
    - Someone shares a workflow URL in Slack during incident
    - Quick analysis when you only have an ID from logs
    - One-stop debugging for any execution issue

    Returns analysis with failures, slow tasks, and actionable recommendations.
    """
    if not url_or_id or not url_or_id.strip():
        return _format_error_response("URL or ID cannot be empty")

    import re

    # Try to extract IDs from URLs
    session_id = None
    attempt_id = None

    # Check for session URL
    session_match = re.search(r"/sessions/(\d+)", url_or_id)
    if session_match:
        session_id = session_match.group(1)
    # Check for attempt URL
    attempt_match = re.search(r"/attempts/(\d+)", url_or_id)
    if attempt_match:
        attempt_id = attempt_match.group(1)
    # If no URL pattern, assume it's a direct ID
    elif url_or_id.isdigit():
        # Try to determine if it's a session or attempt by checking both
        session_id = url_or_id  # Will try session first

    client = _create_client(include_workflow=True)
    if isinstance(client, dict):
        return client

    try:
        analysis = {"input": url_or_id}

        # Try session first
        if session_id:
            session = client.get_session(session_id)
            if session:
                analysis["type"] = "session"
                analysis["session"] = {
                    "id": session.id,
                    "workflow": session.workflow["name"],
                    "project": session.project["name"],
                    "session_time": session.session_time,
                    "status": session.last_attempt.status,
                    "success": session.last_attempt.success,
                }

                # Get attempt details
                attempt_id = session.last_attempt.id
                analysis["latest_attempt_id"] = attempt_id

        # If not a session or if we have an attempt ID, try attempt
        if attempt_id and "type" not in analysis:
            attempt = client.get_attempt(attempt_id)
            if attempt:
                analysis["type"] = "attempt"
                analysis["attempt"] = {
                    "id": attempt.id,
                    "workflow": attempt.workflow["name"],
                    "project": attempt.project["name"],
                    "session_time": attempt.session_time,
                    "status": attempt.status,
                    "success": attempt.success,
                }
                attempt_id = attempt.id

        # If we found something, get tasks for detailed analysis
        if attempt_id:
            tasks = client.get_attempt_tasks(attempt_id)

            # Analyze task execution
            failed_tasks = []
            long_running_tasks = []
            task_tree = {}

            for task in tasks:
                # Build task tree
                if task.parent_id:
                    if task.parent_id not in task_tree:
                        task_tree[task.parent_id] = []
                    task_tree[task.parent_id].append(task.full_name)

                # Track failures
                if task.state in ["failed", "error"]:
                    failed_tasks.append(
                        {
                            "name": task.full_name,
                            "state": task.state,
                            "error": task.error if task.error else "No error details",
                        }
                    )

                # Track long-running tasks
                if task.started_at and task.updated_at:
                    try:
                        from datetime import datetime

                        started = datetime.fromisoformat(
                            task.started_at.replace("Z", "+00:00")
                        )
                        updated = datetime.fromisoformat(
                            task.updated_at.replace("Z", "+00:00")
                        )
                        duration = (updated - started).total_seconds()
                        if duration > 300:  # Tasks longer than 5 minutes
                            long_running_tasks.append(
                                {
                                    "name": task.full_name,
                                    "duration_seconds": duration,
                                }
                            )
                    except Exception:
                        pass

            analysis["task_analysis"] = {
                "total_tasks": len(tasks),
                "failed_tasks": failed_tasks,
                "long_running_tasks": sorted(
                    long_running_tasks,
                    key=lambda x: x["duration_seconds"],
                    reverse=True,
                )[:5],  # Top 5 longest
            }

            # Add recommendations
            recommendations = []
            if failed_tasks:
                recommendations.append(
                    f"Found {len(failed_tasks)} failed task(s). "
                    "Check error details above."
                )
            if long_running_tasks:
                recommendations.append(
                    f"Found {len(long_running_tasks)} task(s) running longer than "
                    "5 minutes. Consider optimization."
                )
            if not analysis.get("session", {}).get("success", True):
                recommendations.append(
                    "Workflow failed. Use td_get_attempt_tasks for detailed "
                    "task breakdown."
                )

            if recommendations:
                analysis["recommendations"] = recommendations

            return analysis
        else:
            return _format_error_response(
                f"Could not find session or attempt with identifier: {url_or_id}"
            )

    except Exception as e:
        return _format_error_response(f"Failed to analyze execution: {str(e)}")
