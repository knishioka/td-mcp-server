"""
Exploration and analysis tools for Treasure Data MCP Server.
Provides high-level project understanding and analysis capabilities.
"""

import hashlib
import re
import tarfile
import tempfile
from collections import defaultdict
from collections.abc import Callable
from pathlib import Path
from typing import Any

# These will be injected from mcp_impl.py to avoid circular import
mcp: Any | None = None
_create_client: Callable[..., Any] | None = None
_format_error_response: Callable[[str], dict[str, Any]] | None = None
_validate_project_id: Callable[[str], bool] | None = None
_safe_extract_member: Callable[..., bool] | None = None

MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB


def register_exploration_tools(
    mcp_instance,
    create_client_func,
    format_error_func,
    validate_project_func,
    safe_extract_func,
):
    """Register exploration tools with the provided MCP instance."""
    global \
        mcp, \
        _create_client, \
        _format_error_response, \
        _validate_project_id, \
        _safe_extract_member
    mcp = mcp_instance
    _create_client = create_client_func
    _format_error_response = format_error_func
    _validate_project_id = validate_project_func
    _safe_extract_member = safe_extract_func

    # Register all tools
    mcp.tool()(td_explore_project)


def _analyze_sql_file(content: str) -> dict[str, Any]:
    """Analyze SQL file content for patterns and issues."""
    analysis = {
        "type": "sql",
        "line_count": len(content.splitlines()),
        "patterns": {},
        "issues": [],
    }

    # Check for hardcoded values
    hardcoded_patterns = [
        (r"(cluster_num|cluster_count)\s*=\s*\d+", "hardcoded_cluster_count"),
        (r"(database|db)\s*=\s*['\"][^'\"]+['\"]", "hardcoded_database"),
        (r"limit\s+\d{4,}", "large_limit_value"),
    ]

    for pattern, issue_type in hardcoded_patterns:
        matches = re.findall(pattern, content, re.IGNORECASE)
        if matches:
            analysis["issues"].append(
                {"type": issue_type, "count": len(matches), "examples": matches[:3]}
            )

    # Analyze query patterns
    if "SELECT" in content.upper():
        analysis["patterns"]["has_select"] = True
        if "JOIN" in content.upper():
            analysis["patterns"]["has_joins"] = True
        if "GROUP BY" in content.upper():
            analysis["patterns"]["has_aggregation"] = True

    # Check for potential performance issues
    if re.search(r"SELECT\s+\*", content, re.IGNORECASE):
        analysis["issues"].append(
            {
                "type": "select_star",
                "severity": "medium",
                "message": "Consider selecting specific columns instead of *",
            }
        )

    return analysis


def _analyze_dig_file(content: str) -> dict[str, Any]:
    """Analyze Digdag workflow file for patterns and structure."""
    analysis = {
        "type": "digdag",
        "line_count": len(content.splitlines()),
        "tasks": [],
        "operators": defaultdict(int),
        "schedule": None,
        "dependencies": [],
    }

    # Extract schedule
    schedule_match = re.search(r"schedule:\s*(.+)", content)
    if schedule_match:
        analysis["schedule"] = schedule_match.group(1).strip()

    # Extract tasks and operators
    task_pattern = r"\+(.+):"
    operator_pattern = r"(td|py|sh|echo|call)>:"

    for line in content.splitlines():
        task_match = re.match(task_pattern, line)
        if task_match:
            task_name = task_match.group(1)
            analysis["tasks"].append(task_name)

        operator_match = re.search(operator_pattern, line)
        if operator_match:
            operator = operator_match.group(1)
            analysis["operators"][operator] += 1

    # Analyze workflow complexity
    analysis["complexity_score"] = (
        len(analysis["tasks"]) * 0.5 + sum(analysis["operators"].values()) * 0.3
    )

    return analysis


def _analyze_project_structure(files_info: list[dict]) -> dict[str, Any]:
    """Analyze overall project structure and patterns."""
    structure = {
        "total_files": len(files_info),
        "file_types": defaultdict(int),
        "directories": set(),
        "sql_files": [],
        "dig_files": [],
        "python_files": [],
        "total_size": 0,
    }

    for file_info in files_info:
        if file_info["type"] == "file":
            ext = file_info.get("extension", "")
            structure["file_types"][ext] += 1
            structure["total_size"] += file_info.get("size", 0)

            # Categorize files
            if ext == ".sql":
                structure["sql_files"].append(file_info["name"])
            elif ext == ".dig":
                structure["dig_files"].append(file_info["name"])
            elif ext == ".py":
                structure["python_files"].append(file_info["name"])

        # Track directories
        path_parts = Path(file_info["name"]).parts
        for i in range(1, len(path_parts)):
            structure["directories"].add("/".join(path_parts[:i]))

    structure["directories"] = list(structure["directories"])
    return structure


def _detect_duplication(files_content: dict[str, str]) -> dict[str, Any]:
    """Detect code duplication across files."""
    duplication_info = {
        "similar_files": [],
        "duplicated_patterns": [],
        "duplication_ratio": 0.0,
    }

    # Simple hash-based similarity detection
    file_hashes = {}
    for filepath, content in files_content.items():
        # Normalize content for comparison (remove whitespace variations)
        normalized = re.sub(r"\s+", " ", content.strip())
        content_hash = hashlib.md5(normalized.encode()).hexdigest()

        if content_hash in file_hashes:
            duplication_info["similar_files"].append(
                {
                    "file1": file_hashes[content_hash],
                    "file2": filepath,
                    "similarity": "exact_match",
                }
            )
        else:
            file_hashes[content_hash] = filepath

    # Calculate duplication ratio
    if len(files_content) > 0:
        duplicate_count = len(duplication_info["similar_files"])
        duplication_info["duplication_ratio"] = duplicate_count / len(files_content)

    return duplication_info


async def td_explore_project(
    identifier: str,
    analysis_depth: str = "detailed",
    focus_areas: list[str] | None = None,
) -> dict[str, Any]:
    """Deep-dive into project to understand workflows, SQL, and architecture.

    Comprehensive project analyzer that downloads and examines all files.
    Essential for understanding unfamiliar projects or debugging complex issues.

    Common scenarios:
    - "What does this project do?" - Full project understanding
    - Onboarding to new codebase - Architecture overview
    - Debugging workflow failures - Code quality analysis
    - Documentation generation - Structure and dependencies
    - Performance optimization - Finding bottlenecks

    Analysis levels:
    - overview: Quick project summary and structure
    - detailed: Code patterns and common issues (default)
    - deep: Full analysis including all SQL/Python code

    Focus areas: ["code", "data_flow", "performance", "errors"]
    Returns file structure, code patterns, issues, and recommendations.
    """
    if not identifier or not identifier.strip():
        return _format_error_response("Project identifier cannot be empty")

    # Default focus areas if not specified
    if focus_areas is None:
        focus_areas = ["code", "data_flow"]

    client = _create_client(include_workflow=True)
    if isinstance(client, dict):
        return client

    try:
        # First, try to find the project
        project = None
        project_id = None

        # Check if identifier is a numeric ID
        if re.match(r"^\d+$", identifier):
            project = client.get_project(identifier)
            project_id = identifier
        else:
            # Search for project by name
            projects = client.get_projects(limit=200, all_results=True)
            for p in projects:
                if identifier.lower() in p.name.lower():
                    project = p
                    project_id = p.id
                    break

        if not project:
            return _format_error_response(f"Project '{identifier}' not found")

        # Initialize analysis result
        result = {
            "project": {
                "id": project.id,
                "name": project.name,
                "created_at": project.created_at,
                "updated_at": project.updated_at,
                "status": "active",
            },
            "analysis_depth": analysis_depth,
            "focus_areas": focus_areas,
        }

        # For overview, just return basic info
        if analysis_depth == "overview":
            # Get workflows for this project
            workflows = client.get_workflows(count=100, all_results=True)
            project_workflows = [w for w in workflows if w.project.id == project_id]

            result["summary"] = {
                "workflow_count": len(project_workflows),
                "scheduled_workflows": sum(1 for w in project_workflows if w.schedule),
                "active_workflows": len(project_workflows),
            }
            return result

        # For detailed/deep analysis, download and analyze the project
        with tempfile.TemporaryDirectory(prefix="td_explore_") as temp_dir:
            archive_path = Path(temp_dir) / f"project_{project_id}.tar.gz"

            # Download project archive
            success = client.download_project_archive(project_id, str(archive_path))
            if not success:
                return _format_error_response("Failed to download project archive")

            # Extract and analyze files
            files_info = []
            files_content = {}
            sql_analyses = []
            dig_analyses = []

            with tarfile.open(archive_path, "r:gz") as tar:
                for member in tar.getmembers():
                    if not _safe_extract_member(member, temp_dir):
                        continue

                    file_info = {
                        "name": member.name,
                        "type": "directory" if member.isdir() else "file",
                        "size": member.size,
                    }

                    if not member.isdir():
                        ext = Path(member.name).suffix.lower()
                        file_info["extension"] = ext

                        # Extract and analyze content for specific file types
                        if "code" in focus_areas and ext in [".sql", ".dig", ".py"]:
                            try:
                                f = tar.extractfile(member)
                                if f and member.size < MAX_FILE_SIZE:
                                    content = f.read().decode("utf-8", errors="ignore")
                                    files_content[member.name] = content

                                    if ext == ".sql":
                                        sql_analyses.append(
                                            {
                                                "file": member.name,
                                                "analysis": _analyze_sql_file(content),
                                            }
                                        )
                                    elif ext == ".dig":
                                        dig_analyses.append(
                                            {
                                                "file": member.name,
                                                "analysis": _analyze_dig_file(content),
                                            }
                                        )
                            except Exception:
                                pass  # Skip files that can't be read

                    files_info.append(file_info)

            # Analyze project structure
            result["architecture"] = _analyze_project_structure(files_info)

            # Code analysis
            if "code" in focus_areas:
                code_analysis = {
                    "file_count": len(files_info),
                    "sql_files_analyzed": len(sql_analyses),
                    "workflow_files_analyzed": len(dig_analyses),
                    "issues": [],
                    "patterns": {},
                }

                # Aggregate SQL issues
                hardcoded_count = 0
                for sql_analysis in sql_analyses:
                    for issue in sql_analysis["analysis"]["issues"]:
                        if "hardcoded" in issue.get("type", ""):
                            hardcoded_count += issue.get("count", 0)

                if hardcoded_count > 0:
                    code_analysis["issues"].append(
                        {
                            "type": "hardcoded_values",
                            "count": hardcoded_count,
                            "severity": "medium",
                            "recommendation": (
                                "Consider using parameters or configuration files"
                            ),
                        }
                    )

                # Detect code duplication
                if analysis_depth == "deep":
                    duplication = _detect_duplication(files_content)
                    code_analysis["duplication"] = duplication
                    if duplication["duplication_ratio"] > 0.3:
                        code_analysis["issues"].append(
                            {
                                "type": "high_duplication",
                                "severity": "high",
                                "ratio": duplication["duplication_ratio"],
                                "recommendation": (
                                    "Consider refactoring duplicated code into "
                                    "functions"
                                ),
                            }
                        )

                result["code_analysis"] = code_analysis

            # Calculate complexity score
            total_files = len(files_info)
            sql_count = len(result["architecture"]["sql_files"])
            dig_count = len(result["architecture"]["dig_files"])

            complexity_score = (
                (total_files * 0.1) + (sql_count * 0.3) + (dig_count * 0.5)
            )
            result["project"]["complexity_score"] = min(10, complexity_score)

            # Performance analysis (if requested)
            if "performance" in focus_areas:
                # Get workflow execution data
                workflows = client.get_workflows(count=100, all_results=True)
                project_workflows = [w for w in workflows if w.project.id == project_id]

                performance_data = {
                    "workflow_count": len(project_workflows),
                    "success_rate": 0.0,
                    "recent_failures": [],
                }

                # Calculate success rate from recent sessions
                total_sessions = 0
                successful_sessions = 0

                for workflow in project_workflows:
                    for session in workflow.latest_sessions[:5]:  # Last 5 sessions
                        total_sessions += 1
                        if session.last_attempt.success:
                            successful_sessions += 1
                        elif not session.last_attempt.success:
                            performance_data["recent_failures"].append(
                                {
                                    "workflow": workflow.name,
                                    "session_time": session.session_time,
                                    "status": session.last_attempt.status,
                                }
                            )

                if total_sessions > 0:
                    performance_data["success_rate"] = (
                        successful_sessions / total_sessions
                    )

                result["performance"] = performance_data

            # Add recommendations based on analysis
            recommendations = []

            if result["project"]["complexity_score"] > 8:
                recommendations.append(
                    {
                        "priority": "high",
                        "category": "complexity",
                        "message": (
                            "Project has high complexity. Consider breaking down into "
                            "smaller modules."
                        ),
                    }
                )

            if "code_analysis" in result and len(result["code_analysis"]["issues"]) > 5:
                recommendations.append(
                    {
                        "priority": "medium",
                        "category": "code_quality",
                        "message": (
                            "Multiple code quality issues detected. Run code review "
                            "and refactoring."
                        ),
                    }
                )

            if "performance" in result and result["performance"]["success_rate"] < 0.8:
                recommendations.append(
                    {
                        "priority": "high",
                        "category": "reliability",
                        "message": (
                            "Low success rate detected. Investigate recent failures "
                            "and add error handling."
                        ),
                    }
                )

            result["recommendations"] = recommendations

        return result

    except Exception as e:
        return _format_error_response(f"Failed to explore project: {str(e)}")
