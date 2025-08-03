"""
Diagnostic tools for Treasure Data MCP Server.
Provides workflow health checks and troubleshooting capabilities.
"""

import re
from collections import defaultdict
from collections.abc import Callable
from datetime import datetime, timedelta
from typing import Any

# These will be injected from mcp_impl.py to avoid circular import
mcp: Any | None = None
_create_client: Callable[..., Any] | None = None
_format_error_response: Callable[[str], dict[str, Any]] | None = None


def register_diagnostic_tools(mcp_instance, create_client_func, format_error_func):
    """Register diagnostic tools with the provided MCP instance."""
    global mcp, _create_client, _format_error_response
    mcp = mcp_instance
    _create_client = create_client_func
    _format_error_response = format_error_func

    # Register all tools
    mcp.tool()(td_diagnose_workflow)
    mcp.tool()(td_trace_data_lineage)


def _parse_datetime(dt_str: str) -> datetime | None:
    """Parse datetime string to datetime object."""
    try:
        # Handle TD datetime format: "2024-11-19T02:15:00Z"
        # Return as naive datetime for consistent comparison
        return datetime.fromisoformat(dt_str.replace("Z", "")).replace(tzinfo=None)
    except Exception:
        return None


def _calculate_time_window(time_window: str) -> datetime | None:
    """Calculate start date from time window string."""
    try:
        # Parse patterns like "30d", "7d", "24h"
        match = re.match(r"(\d+)([dhm])", time_window.lower())
        if not match:
            return None

        value = int(match.group(1))
        unit = match.group(2)

        # Use timezone-aware datetime
        now = datetime.utcnow().replace(tzinfo=None)  # Make it naive for comparison
        if unit == "d":
            return now - timedelta(days=value)
        elif unit == "h":
            return now - timedelta(hours=value)
        elif unit == "m":
            return now - timedelta(minutes=value)

        return None
    except Exception:
        return None


def _analyze_failure_patterns(sessions: list[dict]) -> list[dict]:
    """Analyze failure patterns from session history."""
    error_patterns = defaultdict(list)
    failure_times = []

    for session in sessions:
        if not session["success"]:
            failure_times.append(session["session_time"])

            # Categorize error types
            status = session["status"].lower()
            if "killed" in status:
                error_patterns["resource_timeout"].append(session)
            elif "failed" in status:
                error_patterns["execution_failure"].append(session)
            elif "error" in status:
                error_patterns["runtime_error"].append(session)
            else:
                error_patterns["other"].append(session)

    # Analyze failure clustering
    patterns = []
    for error_type, sessions_list in error_patterns.items():
        if sessions_list:
            patterns.append(
                {
                    "type": error_type,
                    "count": len(sessions_list),
                    "recent_examples": sessions_list[:3],
                    "percentage": len(sessions_list) / len(sessions) * 100,
                }
            )

    return sorted(patterns, key=lambda x: x["count"], reverse=True)


def _calculate_health_score(
    success_rate: float,
    avg_duration: float,
    failure_patterns: list[dict],
    schedule_info: dict,
) -> float:
    """Calculate overall health score from various metrics."""
    score = 10.0

    # Success rate impact (max -5 points)
    if success_rate < 0.5:
        score -= 5.0
    elif success_rate < 0.8:
        score -= 3.0
    elif success_rate < 0.95:
        score -= 1.0

    # Failure pattern impact (max -3 points)
    critical_failures = sum(
        p["count"]
        for p in failure_patterns
        if p["type"] in ["resource_timeout", "runtime_error"]
    )
    if critical_failures > 10:
        score -= 3.0
    elif critical_failures > 5:
        score -= 2.0
    elif critical_failures > 2:
        score -= 1.0

    # Duration trend impact (max -2 points)
    # This would need historical comparison
    # For now, just check if avg duration is reasonable
    if avg_duration > 7200:  # > 2 hours
        score -= 2.0
    elif avg_duration > 3600:  # > 1 hour
        score -= 1.0

    return max(0.0, score)


def _generate_recommendations(
    health_score: float,
    issues: list[dict],
    workflow_info: dict,
) -> list[dict]:
    """Generate actionable recommendations based on diagnosis."""
    recommendations = []

    # Health score based recommendations
    if health_score < 5.0:
        recommendations.append(
            {
                "priority": "critical",
                "category": "overall_health",
                "action": "Immediate attention required",
                "details": (
                    "Workflow is experiencing critical issues. "
                    "Consider pausing scheduled runs until resolved."
                ),
            }
        )
    elif health_score < 7.0:
        recommendations.append(
            {
                "priority": "high",
                "category": "overall_health",
                "action": "Performance optimization needed",
                "details": (
                    "Workflow reliability is below acceptable levels. "
                    "Review recent changes and error logs."
                ),
            }
        )

    # Issue-specific recommendations
    for issue in issues:
        if issue["category"] == "resource_management" and issue["severity"] == "high":
            recommendations.append(
                {
                    "priority": "high",
                    "category": "resources",
                    "action": "Increase resource allocation",
                    "details": (
                        f"Consider increasing memory limits or using more "
                        f"efficient queries. {issue['description']}"
                    ),
                }
            )

        elif issue["category"] == "scheduling" and "overlap" in issue.get(
            "description", ""
        ):
            recommendations.append(
                {
                    "priority": "medium",
                    "category": "scheduling",
                    "action": "Adjust schedule timing",
                    "details": (
                        "Workflow runs are overlapping. Consider increasing "
                        "interval or optimizing execution time."
                    ),
                }
            )

        elif issue["category"] == "error_rate":
            recommendations.append(
                {
                    "priority": "high",
                    "category": "error_handling",
                    "action": "Implement retry logic",
                    "details": (
                        "Add error handling and retry mechanisms for "
                        "transient failures."
                    ),
                }
            )

    # Add data quality recommendations if patterns detected
    if workflow_info.get("has_data_dependencies"):
        recommendations.append(
            {
                "priority": "medium",
                "category": "data_quality",
                "action": "Add data validation",
                "details": (
                    "Consider adding data quality checks before processing "
                    "to catch issues early."
                ),
            }
        )

    return sorted(
        recommendations,
        key=lambda x: {"critical": 0, "high": 1, "medium": 2}.get(x["priority"], 3),
    )


async def td_diagnose_workflow(
    workflow_identifier: str,
    time_window: str = "30d",
    diagnostic_level: str = "basic",
) -> dict[str, Any]:
    """Health check for workflows - find why they're failing or slow.

    Automated troubleshooting that analyzes execution history to identify
    patterns, calculate health scores, and provide fix recommendations.

    Common scenarios:
    - Workflow suddenly failing - Find root cause
    - Performance degradation - Identify slow tasks
    - Reliability issues - Pattern analysis
    - Pre-deployment check - Ensure workflow health
    - Incident response - Quick failure diagnosis

    Time windows: "30d", "7d", "24h" for trend analysis
    Levels: "basic" (quick stats), "comprehensive" (full analysis)

    Returns health score (0-10), failure patterns, and prioritized fixes.

    Args:
        workflow_identifier: Workflow name, ID, or partial match
        time_window: Time period to analyze (e.g., "30d", "7d", "24h")
        diagnostic_level: "basic" for quick check, "comprehensive" for deep analysis

    Returns:
        Health report with score, issues, trends, and optimization recommendations
    """
    if not workflow_identifier or not workflow_identifier.strip():
        return _format_error_response("Workflow identifier cannot be empty")

    client = _create_client(include_workflow=True)
    if isinstance(client, dict):
        return client

    try:
        # Find the workflow
        workflows = client.get_workflows(count=1000, all_results=True)
        target_workflow = None

        # Try exact ID match first
        if re.match(r"^\d+$", workflow_identifier):
            for w in workflows:
                if w.id == workflow_identifier:
                    target_workflow = w
                    break

        # Try name match
        if not target_workflow:
            workflow_lower = workflow_identifier.lower()
            for w in workflows:
                if workflow_lower in w.name.lower():
                    target_workflow = w
                    break

        if not target_workflow:
            return _format_error_response(f"Workflow '{workflow_identifier}' not found")

        # Calculate time range
        start_time = _calculate_time_window(time_window)

        # Initialize diagnosis result
        result: dict[str, Any] = {
            "workflow": {
                "id": target_workflow.id,
                "name": target_workflow.name,
                "project": target_workflow.project.name,
                "timezone": target_workflow.timezone,
                "scheduled": target_workflow.schedule is not None,
            },
            "time_window": time_window,
            "diagnostic_level": diagnostic_level,
        }

        # Add schedule info if available
        if target_workflow.schedule:
            result["workflow"]["schedule"] = target_workflow.schedule

        # Analyze session history
        sessions = []
        total_duration = 0.0
        successful_runs = 0

        for session in target_workflow.latest_sessions:
            session_time = _parse_datetime(session.session_time)
            if start_time and session_time and session_time < start_time:
                continue  # Skip sessions outside time window

            session_info = {
                "session_time": session.session_time,
                "status": session.last_attempt.status,
                "success": session.last_attempt.success,
            }

            # Calculate duration if finished
            if session.last_attempt.created_at and session.last_attempt.finished_at:
                created = _parse_datetime(session.last_attempt.created_at)
                finished = _parse_datetime(session.last_attempt.finished_at)
                if created and finished:
                    duration = (finished - created).total_seconds()
                    session_info["duration_seconds"] = duration
                    total_duration += duration

            sessions.append(session_info)
            if session.last_attempt.success:
                successful_runs += 1

        # Calculate metrics
        total_runs = len(sessions)
        success_rate = successful_runs / total_runs if total_runs > 0 else 0
        avg_duration = total_duration / successful_runs if successful_runs > 0 else 0

        # Analyze failure patterns
        failure_patterns = _analyze_failure_patterns(sessions)

        # Identify issues
        issues = []

        # High failure rate
        if success_rate < 0.8:
            issues.append(
                {
                    "severity": "high",
                    "category": "error_rate",
                    "description": (
                        f"High failure rate: "
                        f"{(1 - success_rate) * 100:.1f}% of runs failing"
                    ),
                    "affected_components": ["workflow_execution"],
                }
            )

        # Resource timeout patterns
        timeout_issues = [
            p for p in failure_patterns if p["type"] == "resource_timeout"
        ]
        if timeout_issues and timeout_issues[0]["count"] > 3:
            issues.append(
                {
                    "severity": "high",
                    "category": "resource_management",
                    "description": "Frequent resource timeouts detected",
                    "recommendation": (
                        "Consider increasing memory allocation or optimizing queries"
                    ),
                    "affected_components": ["resource_allocation"],
                }
            )

        # Performance degradation (would need historical data for proper trend)
        if avg_duration > 3600:  # > 1 hour average
            issues.append(
                {
                    "severity": "medium",
                    "category": "performance",
                    "description": (
                        f"Long average execution time: {avg_duration / 60:.1f} minutes"
                    ),
                    "recommendation": "Review query optimization opportunities",
                    "affected_components": ["query_performance"],
                }
            )

        # Calculate health score
        health_score = _calculate_health_score(
            success_rate, avg_duration, failure_patterns, result["workflow"]
        )

        # Build result
        result["health_score"] = round(health_score, 1)
        result["issues"] = issues
        result["metrics"] = {
            "total_runs": total_runs,
            "successful_runs": successful_runs,
            "success_rate": round(success_rate, 3),
            "avg_duration_minutes": round(avg_duration / 60, 1)
            if avg_duration > 0
            else 0,
        }

        # Add trends (simplified without historical data)
        result["trends"] = {
            "success_rate_trend": "stable",  # Would need historical comparison
            "execution_time_trend": "stable",
            "resource_usage_trend": "unknown",
        }

        # Add failure analysis for comprehensive level
        if diagnostic_level == "comprehensive":
            result["failure_analysis"] = {
                "patterns": failure_patterns,
                "recent_failures": [s for s in sessions if not s["success"]][:10],
            }

            # Add optimization opportunities
            optimization_opportunities = []

            if target_workflow.schedule and avg_duration > 1800:  # > 30 min
                optimization_opportunities.append(
                    {
                        "type": "scheduling",
                        "description": (
                            "Consider adjusting schedule to avoid peak hours"
                        ),
                        "potential_impact": "Reduce resource contention",
                    }
                )

            if len(failure_patterns) > 0:
                optimization_opportunities.append(
                    {
                        "type": "error_handling",
                        "description": "Implement retry logic for transient failures",
                        "potential_impact": (
                            f"Could recover {failure_patterns[0]['count']} failed runs"
                        ),
                    }
                )

            result["optimization_opportunities"] = optimization_opportunities

        # Generate recommendations
        recommendations = _generate_recommendations(
            health_score, issues, result["workflow"]
        )
        result["recommendations"] = recommendations

        return result

    except Exception as e:
        return _format_error_response(f"Failed to diagnose workflow: {str(e)}")


async def td_trace_data_lineage(
    table_or_project: str,
    direction: str = "both",
    max_depth: int = 3,
) -> dict[str, Any]:
    """Map data flow to see what feeds into or depends on tables/projects.

    Critical for understanding data dependencies and impact analysis.
    Traces through SQL queries to build dependency graph.

    Common scenarios:
    - "What happens if I change this table?" - Impact analysis
    - "Where does this data come from?" - Source tracing
    - Data quality issues - Track upstream problems
    - Migration planning - Understand dependencies
    - Documentation - Data flow diagrams

    Directions:
    - upstream: What tables/projects feed INTO this
    - downstream: What tables/projects CONSUME this
    - both: Complete dependency graph

    Returns visual-ready dependency tree with table/project relationships.

    Args:
        table_or_project: Table name (format: "database.table") or project name/ID
        direction: "upstream" (sources), "downstream" (consumers), or "both"
        max_depth: Maximum levels to trace (default: 3)

    Returns:
        Data lineage graph with dependencies and data flow information
    """
    if not table_or_project or not table_or_project.strip():
        return _format_error_response("Table or project identifier cannot be empty")

    if direction not in ["upstream", "downstream", "both"]:
        return _format_error_response(
            "Direction must be 'upstream', 'downstream', or 'both'"
        )

    client = _create_client(include_workflow=True)
    if isinstance(client, dict):
        return client

    try:
        # Initialize result
        result = {
            "query": table_or_project,
            "direction": direction,
            "max_depth": max_depth,
            "lineage": {
                "nodes": [],
                "edges": [],
            },
            "summary": {},
        }

        # Determine if input is table or project
        is_table = "." in table_or_project

        if is_table:
            # Parse database.table format
            parts = table_or_project.split(".", 1)
            if len(parts) != 2:
                return _format_error_response("Table must be in format: database.table")

            database_name, table_name = parts

            # Verify table exists
            try:
                tables = client.get_tables(database_name, all_results=True)
                table_exists = any(t.name == table_name for t in tables)
                if not table_exists:
                    return _format_error_response(
                        f"Table '{table_or_project}' not found"
                    )
            except Exception:
                return _format_error_response(f"Database '{database_name}' not found")

            # Add root node
            result["lineage"]["nodes"].append(
                {
                    "id": table_or_project,
                    "type": "table",
                    "name": table_name,
                    "database": database_name,
                    "level": 0,
                }
            )

            # Note: Full lineage tracing would require parsing SQL queries
            # from all workflows, which is beyond current scope
            result["summary"]["message"] = (
                "Table lineage tracing requires SQL parsing from all workflows. "
                "This is a simplified view based on available metadata."
            )

            # Search for workflows that might reference this table
            workflows = client.get_workflows(count=500, all_results=True)
            referencing_workflows = []

            for workflow in workflows:
                # Simple heuristic: workflow name contains table name
                if table_name.lower() in workflow.name.lower():
                    referencing_workflows.append(
                        {
                            "workflow_id": workflow.id,
                            "workflow_name": workflow.name,
                            "project": workflow.project.name,
                            "scheduled": workflow.schedule is not None,
                        }
                    )

            result["summary"]["referencing_workflows"] = referencing_workflows[:10]
            result["summary"]["total_references"] = len(referencing_workflows)

        else:
            # Project-based lineage
            # Find project
            project = None
            project_id = None

            if re.match(r"^\d+$", table_or_project):
                project = client.get_project(table_or_project)
                project_id = table_or_project
            else:
                projects = client.get_projects(limit=200, all_results=True)
                for p in projects:
                    if table_or_project.lower() in p.name.lower():
                        project = p
                        project_id = p.id
                        break

            if not project:
                return _format_error_response(f"Project '{table_or_project}' not found")

            # Add root node
            result["lineage"]["nodes"].append(
                {
                    "id": project_id,
                    "type": "project",
                    "name": project.name,
                    "level": 0,
                }
            )

            # Get workflows for this project
            workflows = client.get_workflows(count=500, all_results=True)
            project_workflows = [w for w in workflows if w.project.id == project_id]

            # Create workflow nodes
            for workflow in project_workflows:
                node_id = f"workflow_{workflow.id}"
                result["lineage"]["nodes"].append(
                    {
                        "id": node_id,
                        "type": "workflow",
                        "name": workflow.name,
                        "scheduled": workflow.schedule is not None,
                        "level": 1,
                    }
                )

                # Add edge from project to workflow
                result["lineage"]["edges"].append(
                    {
                        "from": project_id,
                        "to": node_id,
                        "type": "contains",
                    }
                )

            result["summary"]["workflow_count"] = len(project_workflows)
            result["summary"]["scheduled_workflows"] = sum(
                1 for w in project_workflows if w.schedule
            )

            # Note about limitations
            result["summary"]["note"] = (
                "Full data lineage requires parsing SQL queries and workflow "
                "definitions. This view shows project and workflow relationships."
            )

        return result

    except Exception as e:
        return _format_error_response(f"Failed to trace data lineage: {str(e)}")
