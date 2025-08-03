# Treasure Data MCP Server

A Model Context Protocol (MCP) server that provides Treasure Data API integration for Claude Code and Claude Desktop.

> **DISCLAIMER**: This is a personal development project and is not affiliated with, endorsed by, or related to Treasure Data Inc. in any way. This software is provided "as is" without warranty of any kind, and should be used at your own risk. The author is not responsible for any consequences resulting from the use of this software.

## Reference Documentation

For comprehensive Treasure Data documentation and tools:

- **Official API Documentation**: https://api-docs.treasuredata.com/en/overview/gettingstarted/
- **CLI Tool (td command)**: https://github.com/treasure-data/td
- **Console Interface**: https://console.treasuredata.com/
- **Detailed API Guide**: [docs/treasure-data-api-guide.md](docs/treasure-data-api-guide.md)

## Available MCP Tools

This MCP server provides a comprehensive set of tools for interacting with Treasure Data, organized by functionality. Currently offering 23 tools across 6 categories:

### Database Management

1. **td_list_databases**
   ```python
   td_list_databases(verbose=False, limit=30, offset=0, all_results=False)
   ```
   - Get databases in your Treasure Data account with pagination support
   - **Parameters**:
     - `verbose`: If True, return full details; if False, return only names (default)
     - `limit`: Maximum number of databases to retrieve (defaults to 30)
     - `offset`: Index to start retrieving from (defaults to 0)
     - `all_results`: If True, retrieves all databases ignoring limit and offset
   - **Examples**:
     ```
     # Get only database names (default, first 30 databases)
     td_list_databases

     # Get full database details
     td_list_databases verbose=True

     # Pagination options
     td_list_databases limit=10 offset=20

     # Get all databases regardless of the number
     td_list_databases all_results=True
     ```

2. **td_get_database**
   ```python
   td_get_database(database_name)
   ```
   - Get detailed information about a specific database
   - **Parameters**:
     - `database_name`: The name of the database to retrieve information for
   - **Example**:
     ```
     # Get information about a specific database
     td_get_database database_name=my_database_name
     ```

3. **td_list_tables**
   ```python
   td_list_tables(database_name, verbose=False, limit=30, offset=0, all_results=False)
   ```
   - Get tables in a specific Treasure Data database with pagination support
   - **Parameters**:
     - `database_name`: The name of the database to retrieve tables from
     - `verbose`: If True, return full details; if False, return only names (default)
     - `limit`: Maximum number of tables to retrieve (defaults to 30)
     - `offset`: Index to start retrieving from (defaults to 0)
     - `all_results`: If True, retrieves all tables ignoring limit and offset
   - **Examples**:
     ```
     # Get only table names in a database (default, first 30 tables)
     td_list_tables database_name=my_database_name

     # Get detailed information about tables in a database
     td_list_tables database_name=my_database_name verbose=True

     # Pagination options
     td_list_tables database_name=my_database_name limit=10 offset=20

     # Get all tables in a database
     td_list_tables database_name=my_database_name all_results=True
     ```

### Workflow Project Management

4. **td_list_projects**
   ```python
   td_list_projects(verbose=False, limit=30, offset=0, all_results=False, include_system=False)
   ```
   - Get workflow projects in your Treasure Data account with pagination support
   - **Parameters**:
     - `verbose`: If True, return full details; if False, return only names and IDs (default)
     - `limit`: Maximum number of projects to retrieve (defaults to 30)
     - `offset`: Index to start retrieving from (defaults to 0)
     - `all_results`: If True, retrieves all projects ignoring limit and offset
     - `include_system`: If True, include system-generated projects (with "sys" metadata); defaults to False
   - **Examples**:
     ```
     # Get basic project info (default, first 30 projects)
     td_list_projects

     # Get detailed project information
     td_list_projects verbose=True

     # Pagination options
     td_list_projects limit=10 offset=20

     # Get all projects regardless of the number
     td_list_projects all_results=True

     # Include system-generated projects
     td_list_projects include_system=True
     ```

5. **td_get_project**
   ```python
   td_get_project(project_id)
   ```
   - Get detailed information about a specific workflow project
   - Note: This provides basic project metadata only. For detailed content and files, use td_download_project_archive followed by td_list_project_files and td_read_project_file
   - **Parameters**:
     - `project_id`: The ID of the workflow project to retrieve information for
   - **Example**:
     ```
     # Get information about a specific project
     td_get_project project_id=123456
     ```

6. **td_download_project_archive**
   ```python
   td_download_project_archive(project_id)
   ```
   - Download a project's archive (tar.gz) and return information about the download
   - Recommended for examining detailed project contents including SQL queries and workflow definitions
   - **Parameters**:
     - `project_id`: The ID of the workflow project to download
   - **Example**:
     ```
     # Download a project's archive
     td_download_project_archive project_id=123456
     ```

7. **td_list_project_files**
   ```python
   td_list_project_files(archive_path)
   ```
   - List all files contained in a project archive
   - **Parameters**:
     - `archive_path`: The path to the downloaded project archive (.tar.gz file)
   - **Example**:
     ```
     # List files in a downloaded project archive
     td_list_project_files archive_path=/tmp/td_project_123/project_123456.tar.gz
     ```

8. **td_read_project_file**
   ```python
   td_read_project_file(archive_path, file_path)
   ```
   - Read the contents of a specific file from a project archive
   - **Parameters**:
     - `archive_path`: The path to the downloaded project archive (.tar.gz file)
     - `file_path`: The path of the file within the archive to read
   - **Example**:
     ```
     # Read a specific file from a project archive
     td_read_project_file archive_path=/tmp/td_project_123/project_123456.tar.gz file_path=workflow.dig
     ```

9. **td_list_workflows**
   ```python
   td_list_workflows(verbose=False, count=100, include_system=False, status_filter=None)
   ```
   - Get workflows across all projects in your Treasure Data account
   - **Parameters**:
     - `verbose`: If True, return full details including sessions; if False, return summary (default)
     - `count`: Maximum number of workflows to retrieve (defaults to 100, max 12000)
     - `include_system`: If True, include system-generated workflows (with "sys" metadata)
     - `status_filter`: Filter workflows by their last session status ('success', 'error', 'running', None for all)
   - **Examples**:
     ```
     # Get workflow summary (default)
     td_list_workflows

     # Get full workflow details with recent sessions
     td_list_workflows verbose=True

     # Get only failed workflows
     td_list_workflows status_filter=error

     # Get successful workflows including system workflows
     td_list_workflows status_filter=success include_system=True

     # Get more workflows (up to 12000)
     td_list_workflows count=500
     ```

### Search and Discovery Tools

10. **td_smart_search**
   ```python
   td_smart_search(query, search_scope="all", search_mode="fuzzy", active_only=True, min_relevance=0.7)
   ```
   - Intelligent search across all Treasure Data resources with fuzzy matching and relevance scoring
   - **Parameters**:
     - `query`: Search term or phrase
     - `search_scope`: Where to search - "projects", "workflows", "tables", "all" (default: "all")
     - `search_mode`: Search algorithm - "exact", "fuzzy", "semantic" (default: "fuzzy")
     - `active_only`: Filter to only active/non-deleted resources (default: True)
     - `min_relevance`: Minimum relevance score (0-1) for results (default: 0.7)
   - **Examples**:
     ```
     # Search everywhere with fuzzy matching
     td_smart_search query="customer clustering"

     # Exact search for projects only
     td_smart_search query="my_project" search_scope=projects search_mode=exact

     # Semantic search for workflows
     td_smart_search query="recommendation engine" search_scope=workflows search_mode=semantic

     # Lower relevance threshold for broader results
     td_smart_search query="sales" min_relevance=0.5
     ```

11. **td_find_project**
   ```python
   td_find_project(search_term, exact_match=False)
   ```
   - Find project by name or partial name match
   - **Parameters**:
     - `search_term`: Project name or partial name to search for
     - `exact_match`: If True, only return exact matches (default: False)
   - **Examples**:
     ```
     # Find projects containing "cluster"
     td_find_project search_term=cluster

     # Find exact project name
     td_find_project search_term="customer_analytics" exact_match=True
     ```

12. **td_find_workflow**
   ```python
   td_find_workflow(search_term, project_name=None, exact_match=False, status_filter=None)
   ```
   - Find workflows by name with optional filters
   - **Parameters**:
     - `search_term`: Workflow name or partial name to search for
     - `project_name`: Optional project name to filter by
     - `exact_match`: If True, only return exact matches (default: False)
     - `status_filter`: Filter by status ('success', 'error', 'running', None)
   - **Examples**:
     ```
     # Find workflows containing "scoring"
     td_find_workflow search_term=scoring

     # Find workflows in specific project
     td_find_workflow search_term=daily project_name=my_project

     # Find failed workflows with exact name
     td_find_workflow search_term="ore_heaven_scoring" exact_match=True status_filter=error
     ```

13. **td_get_project_by_name**
   ```python
   td_get_project_by_name(project_name)
   ```
   - Get project details by exact name match (convenient alternative to finding ID first)
   - **Parameters**:
     - `project_name`: Exact project name
   - **Example**:
     ```
     # Get project details by name
     td_get_project_by_name project_name="customer_analytics"
     ```

### URL Analysis Tools

14. **td_analyze_url**
   ```python
   td_analyze_url(url)
   ```
   - Extract and retrieve information from a Treasure Data console URL
   - **Parameters**:
     - `url`: Console URL to analyze
   - **Supported URL formats**:
     - Workflow: `https://console.us01.treasuredata.com/app/workflows/12345678/info`
     - Project: `https://console.us01.treasuredata.com/app/projects/123456`
     - Job: `https://console.us01.treasuredata.com/app/jobs/123456`
   - **Example**:
     ```
     # Analyze a workflow URL
     td_analyze_url url="https://console.us01.treasuredata.com/app/workflows/12345678/info"
     ```

15. **td_get_workflow**
   ```python
   td_get_workflow(workflow_id)
   ```
   - Get workflow details by numeric ID (useful for console URLs)
   - **Parameters**:
     - `workflow_id`: Numeric workflow ID
   - **Example**:
     ```
     # Get workflow by ID
     td_get_workflow workflow_id=12345678
     ```

### Project Analysis and Diagnostics (New)

16. **td_explore_project**
   ```python
   td_explore_project(identifier, analysis_depth="detailed", focus_areas=None)
   ```
   - Analyze a TD project comprehensively for documentation or debugging
   - **Parameters**:
     - `identifier`: Project name, ID, or search term
     - `analysis_depth`: Level of analysis - "overview", "detailed", or "deep" (default: "detailed")
     - `focus_areas`: Specific aspects to analyze - ["code", "data_flow", "performance", "errors"] (default: ["code", "data_flow"])
   - **Examples**:
     ```
     # Get detailed project analysis
     td_explore_project identifier="my_project"

     # Deep analysis focusing on performance
     td_explore_project identifier="analytics_workflow" analysis_depth=deep focus_areas=["performance", "errors"]

     # Quick overview
     td_explore_project identifier=1664373 analysis_depth=overview
     ```

17. **td_diagnose_workflow**
   ```python
   td_diagnose_workflow(workflow_identifier, time_window="30d", diagnostic_level="basic")
   ```
   - Diagnose workflow health and identify issues
   - **Parameters**:
     - `workflow_identifier`: Workflow name, ID, or partial match
     - `time_window`: Time period to analyze (e.g., "30d", "7d", "24h") (default: "30d")
     - `diagnostic_level`: "basic" for quick check, "comprehensive" for deep analysis (default: "basic")
   - **Examples**:
     ```
     # Basic health check for last 30 days
     td_diagnose_workflow workflow_identifier="ore_heaven_scoring"

     # Comprehensive diagnosis for last week
     td_diagnose_workflow workflow_identifier=12345678 time_window=7d diagnostic_level=comprehensive

     # Quick check for recent issues
     td_diagnose_workflow workflow_identifier="daily_batch" time_window=24h
     ```

18. **td_trace_data_lineage**
   ```python
   td_trace_data_lineage(table_or_project, direction="both", max_depth=3)
   ```
   - Trace data dependencies and lineage for tables or projects
   - **Parameters**:
     - `table_or_project`: Table name (format: "database.table") or project name/ID
     - `direction`: "upstream" (sources), "downstream" (consumers), or "both" (default: "both")
     - `max_depth`: Maximum levels to trace (default: 3)
   - **Examples**:
     ```
     # Trace table dependencies
     td_trace_data_lineage table_or_project="production.customer_segments"

     # Find upstream sources only
     td_trace_data_lineage table_or_project="analytics.recommendations" direction=upstream

     # Trace project data flow
     td_trace_data_lineage table_or_project="my_project" max_depth=5
     ```

### Workflow Execution Management Tools

19. **td_get_session**
   ```python
   td_get_session(session_id)
   ```
   - Get detailed information about a workflow session
   - **Parameters**:
     - `session_id`: The ID of the session to retrieve
   - **Examples**:
     ```
     # Get session details
     td_get_session session_id=123456789
     ```

20. **td_list_sessions**
   ```python
   td_list_sessions(workflow_id=None, count=20)
   ```
   - List recent sessions for workflows
   - **Parameters**:
     - `workflow_id`: Optional workflow ID to filter sessions
     - `count`: Number of recent sessions to retrieve (default 20)
   - **Examples**:
     ```
     # List recent sessions across all workflows
     td_list_sessions

     # List sessions for a specific workflow
     td_list_sessions workflow_id=12345678 count=50
     ```

21. **td_get_attempt**
   ```python
   td_get_attempt(attempt_id)
   ```
   - Get detailed information about a workflow attempt
   - **Parameters**:
     - `attempt_id`: The ID of the attempt to retrieve
   - **Examples**:
     ```
     # Get attempt details
     td_get_attempt attempt_id=987654321
     ```

22. **td_get_attempt_tasks**
   ```python
   td_get_attempt_tasks(attempt_id)
   ```
   - Get all tasks for a workflow attempt
   - **Parameters**:
     - `attempt_id`: The ID of the attempt
   - **Examples**:
     ```
     # Get task breakdown for an attempt
     td_get_attempt_tasks attempt_id=987654321
     ```

23. **td_analyze_execution**
   ```python
   td_analyze_execution(url_or_id)
   ```
   - Analyze workflow execution from URL or ID
   - **Parameters**:
     - `url_or_id`: Console URL, session ID, or attempt ID
   - **Examples**:
     ```
     # Analyze from console URL
     td_analyze_execution url_or_id="https://console.us01.treasuredata.com/app/sessions/123456"

     # Analyze from session ID
     td_analyze_execution url_or_id=123456789

     # Analyze from attempt ID
     td_analyze_execution url_or_id=987654321
     ```

## Testing

### Integration Testing

To test the MCP tools with real API calls:

```bash
# Set your API key (required)
export TD_API_KEY="your-api-key"

# Run integration tests
python test_mcp_integration.py
```

The integration test script (`test_mcp_integration.py`) safely tests all tools by:
- Using generic search terms (no production data hardcoded)
- Showing only summary results (no sensitive data exposed)
- Testing error handling with invalid inputs
- Requiring explicit API key configuration

**Important**: Never commit files containing:
- API keys or credentials
- Specific project IDs or names from production
- Detailed query results or data dumps
- Customer or business-sensitive information

## Setup Instructions

### Authentication

This MCP server requires a Treasure Data API key for authentication, which should be provided via the `TD_API_KEY` environment variable. You can also specify the Treasure Data endpoint using the `TD_ENDPOINT` environment variable (defaults to `api.treasuredata.com`).

### Setting up with Claude Code

1. Clone the repository
   ```bash
   git clone https://github.com/knishioka/td-mcp-server.git
   cd td-mcp-server
   ```

2. Install dependencies
   ```bash
   # Using pip
   pip install -r requirements.txt

   # Or using uv (recommended)
   uv pip install -e .
   ```

3. Set up environment variables and run
   ```bash
   # Set your API key
   export TD_API_KEY="your-api-key"
   export TD_ENDPOINT="api.treasuredata.com"  # Optional, defaults to US region

   # Run the MCP server
   mcp run td_mcp_server/server.py
   ```

### Setting up with Claude Desktop

Configure this MCP server for use with Claude Desktop by editing your configuration file (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "td": {
      "command": "uv",
      "args": [
        "--directory",
        "/absolute/path/to/td-mcp-server",
        "run",
        "td_mcp_server/server.py"
      ],
      "env": {
        "TD_API_KEY": "YOUR_API_KEY",
        "TD_ENDPOINT": "api.treasuredata.com"
      }
    }
  }
}
```

## Installation and Requirements

This project requires Python 3.11+ and the following dependencies:
- `requests>=2.28.0` - HTTP client for API requests
- `pydantic>=2.0.0` - Data validation and serialization
- `mcp[cli]>=1.8.1` - Model Context Protocol framework

Install the dependencies:

```bash
# Using pip
pip install -r requirements.txt

# Using uv (recommended for development)
uv pip install -e .
```

## Running the Server Directly

You can run the MCP server directly:

```bash
# Set your API key
export TD_API_KEY="your-api-key"

# For US region (default)
export TD_ENDPOINT="api.treasuredata.com"

# For Japan region
# export TD_ENDPOINT="api.treasuredata.co.jp"

# Run with MCP CLI
mcp run td_mcp_server/server.py
```

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run tests with coverage report
pytest --cov=td_mcp_server

# Run tests for a specific module
pytest tests/unit/test_api.py
```

### Code Formatting and Linting

```bash
# Run linting with Ruff
uv run ruff check td_mcp_server tests

# Format code with Ruff
uv run ruff format td_mcp_server tests

# Run pre-commit hooks on all files
uv run pre-commit run --all-files
```
# GitHub Actions formatting fix
