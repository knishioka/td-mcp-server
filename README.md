# Treasure Data MCP Server

A Model Context Protocol (MCP) server that provides Treasure Data API integration for Claude Code and Claude Desktop.

## Available MCP Tools

This MCP server provides the following tools for interacting with Treasure Data:

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
   td_list_projects(verbose=False, limit=30, offset=0, all_results=False)
   ```
   - Get workflow projects in your Treasure Data account with pagination support
   - **Parameters**:
     - `verbose`: If True, return full details; if False, return only names and IDs (default)
     - `limit`: Maximum number of projects to retrieve (defaults to 30)
     - `offset`: Index to start retrieving from (defaults to 0)
     - `all_results`: If True, retrieves all projects ignoring limit and offset
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
     ```

5. **td_get_project**
   ```python
   td_get_project(project_id)
   ```
   - Get detailed information about a specific workflow project
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

## Setup Instructions

### Authentication

This MCP server requires a Treasure Data API key for authentication, which should be provided via the `TD_API_KEY` environment variable. You can also specify the Treasure Data endpoint using the `TD_ENDPOINT` environment variable (defaults to `api.treasuredata.com`).

### Setting up with Claude Code

1. Clone the repository
   ```bash
   git clone https://github.com/knishioka/td-mcp-server.git
   ```

2. Add the MCP server using the Claude Code CLI
   ```bash
   # Navigate to your project directory
   cd your-project-directory

   # Add the MCP server (use absolute path to server.py)
   claude mcp add td -e TD_API_KEY=${TD_API_KEY} -e TD_ENDPOINT=api.treasuredata.com -- mcp run /absolute/path/to/td-mcp-server/td_mcp_server/server.py
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

This project requires Python 3.11+ and the following packages:
- requests
- pydantic
- mcp

Install the dependencies with pip:
```bash
pip install -r requirements.txt
```

Or with uv:
```bash
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
