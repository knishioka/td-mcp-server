# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## API Development Guidelines

### API Endpoint Testing

When working with APIs in this project:

1. **Use curl for API endpoint verification**
   - Always test API endpoints directly with curl first
   - Parse responses using jq for structured data extraction
   - Avoid creating unnecessary test scripts

   Example:
   ```bash
   # Test API endpoint
   curl -s -H "Authorization: TD1 $TD_API_KEY" "https://api.treasuredata.com/v3/database/list" | jq '.'

   # Extract specific fields
   curl -s -H "Authorization: TD1 $TD_API_KEY" "https://api.treasuredata.com/v3/database/list" | jq '.databases[].name'
   ```

2. **Minimal testing approach**
   - Use inline Python commands with `uv run python -c` for quick validation
   - Avoid creating separate test files unless absolutely necessary
   - Leverage existing test infrastructure rather than creating new test scripts

3. **API exploration workflow**
   - First: Test endpoint with curl and jq
   - Second: Implement based on actual API response
   - Third: Validate with minimal inline code

## Important Development Guidelines

### Code Quality Standards

This project uses pre-commit hooks to enforce several code quality standards:

#### Trailing Whitespace

- All trailing whitespace will be automatically removed during commits
- **CRITICAL FOR CLAUDE CODE**: Always run automated checks before committing to prevent pre-commit failures
- Claude Code may occasionally add trailing whitespace that will trigger pre-commit hook warnings
- **Automated Check Command**: `uv run pre-commit run trailing-whitespace --all-files && uv run ruff format td_mcp_server tests`
- **When to run**: After any file editing, before git commits
- **Quick fix command**: `uv run ruff format td_mcp_server tests` to auto-fix most formatting issues

#### Newline at End of File

- All files must end with a newline character
- The pre-commit hook 'end-of-file-fixer' enforces this requirement
- When creating or editing files with Claude Code, always ensure there is a newline at the end of the file
- This is a standard convention in Unix/Linux systems and helps prevent issues with certain tools

### Documentation Guidelines

#### MCP Tools Documentation

- When adding new MCP tools to the server, always update the README.md file with complete documentation
- Each tool should be documented with:
  - Function signature with parameters
  - Description of what the tool does
  - Parameter descriptions and default values
  - Usage examples without any command prefix (like `/mcp`)
- The README.md should focus primarily on the available MCP tools to make it easy for users to understand what functionality is available
- Organization by categories (e.g., Database Management, Workflow Project Management) improves readability

## Treasure Data MCP Server Overview

This repository contains a Model Context Protocol (MCP) server that provides Treasure Data API integration for Claude Code and Claude Desktop, allowing for database management and listing functionality.

## API Reference

For Treasure Data API specifications, endpoint details, example responses, and other API-related information, refer to these resources:

### Official Documentation
- **Official API Documentation**: https://api-docs.treasuredata.com/en/overview/gettingstarted/
- **CLI Tool (td command)**: https://github.com/treasure-data/td
- **Console Interface**: https://console.treasuredata.com/

### Project-Specific Documentation
**docs/treasure-data-api-guide.md** - Local API guide including:
- API endpoint URLs for different regions
- Authentication methods
- Example API requests and responses
- Available API operations (databases, tables, jobs, etc.)
- Response structures and field descriptions

## Automated Quality Checks for Claude Code

### Pre-Commit Automation

**ALWAYS run these commands after editing files and before committing:**

```bash
# Comprehensive pre-commit check (run this first)
uv run pre-commit run --all-files

# If pre-commit fails, fix issues with:
uv run ruff format td_mcp_server tests
uv run ruff check --fix td_mcp_server tests

# Verify fixes worked:
uv run pre-commit run --all-files
```

### Quick Check Commands

```bash
# Check only trailing whitespace
uv run pre-commit run trailing-whitespace --all-files

# Check and fix end-of-file issues
uv run pre-commit run end-of-file-fixer --all-files

# Run all formatting and linting
uv run ruff format td_mcp_server tests && uv run ruff check --fix td_mcp_server tests
```

### Commit Workflow for Claude Code

1. **Edit files** (using Claude Code tools)
2. **Run automated checks**: `uv run pre-commit run --all-files`
3. **Fix any issues**: `uv run ruff format td_mcp_server tests`
4. **Verify clean**: `uv run pre-commit run --all-files`
5. **Commit and push**: `git add . && git commit -m "message" && git push`
6. **🚨 CRITICAL: Check GitHub Actions**: Always verify CI/CD pipeline status after push

### GitHub Actions Monitoring

**MANDATORY after every push:**

```bash
# Check GitHub Actions status using gh CLI
gh run list --limit 5

# Watch the latest workflow run
gh run watch

# View logs if workflow fails
gh run view --log
```

**Alternative: Web Interface**
- Navigate to: https://github.com/knishioka/td-mcp-server/actions
- Verify latest workflow run status: ✅ Success / ❌ Failed
- If failed: Click on failed job → View logs → Fix issues

### CI/CD Failure Response Protocol

1. **Immediate Action**: Check GitHub Actions within 2-3 minutes of push
2. **If Failed**:
   - Download logs: `gh run view --log`
   - Fix issues locally
   - Re-run checks: `uv run pre-commit run --all-files`
   - Push fix: `git add . && git commit -m "Fix CI issues" && git push`
3. **Re-verify**: Check GitHub Actions again until ✅ Success


## Key Commands

### Dependencies

This project requires Python 3.11+ and the following packages:
- requests
- pydantic
- mcp

If you want to run tests, you'll also need:
- pytest
- pytest-mock
- pytest-cov
- responses
- mypy
- ruff
- pre-commit

### Running the MCP Server

```bash
# Run with MCP CLI (recommended for Claude Desktop integration)
mcp run td_mcp_server/server.py

# Install server for Claude Desktop
mcp install td_mcp_server/server.py -v TD_API_KEY="your-api-key" -v TD_ENDPOINT="api.treasuredata.com"

# Install server for Claude Desktop (Japan region)
mcp install td_mcp_server/server.py -v TD_API_KEY="your-api-key" -v TD_ENDPOINT="api.treasuredata.co.jp"
```


### Testing

```bash
# Run all tests
pytest

# Run tests with coverage report
pytest --cov=td_mcp_server

# Run tests for a specific module
pytest tests/unit/test_api.py

# Run a specific test
pytest tests/unit/test_api.py::TestTreasureDataClient::test_get_databases
```

### Code Formatting, Linting, and Type Checking

```bash
# Using pip

# Run linting with Ruff
ruff check td_mcp_server tests

# Run linting and auto-fix with Ruff
ruff check --fix td_mcp_server tests

# Format code with Ruff
ruff format td_mcp_server tests

# Run type checking
mypy td_mcp_server

# Initialize pre-commit (first time only)
pre-commit install

# Run pre-commit on all files
pre-commit run --all-files

# Using uv

# Install dependencies with uv
uv pip install -e ".[dev]"

# Run linting with Ruff
uv run ruff check td_mcp_server tests

# Run linting and auto-fix with Ruff
uv run ruff check --fix td_mcp_server tests

# Format code with Ruff
uv run ruff format td_mcp_server tests

# Run type checking
uv run mypy td_mcp_server

# Initialize pre-commit (first time only)
uv run pre-commit install

# Run pre-commit on all files
uv run pre-commit run --all-files
```

## Architecture

The codebase is structured around the following key components:

### 1. API Client (`td_mcp_server/api.py`)

- `TreasureDataClient` class: Main client interface for Treasure Data API
- `Database` and `Table` models: Pydantic models for API responses
- Core API methods: `get_databases`, `get_database`, `get_tables`
- All methods support pagination with `limit`, `offset`, and `all_results` parameters


### 2. MCP Implementation

#### Core MCP Tools (`td_mcp_server/mcp_impl.py`)
- Implements the FastMCP server: `mcp = FastMCP("treasure-data")`
- MCP tools:
  - Database Management: `td_list_databases`, `td_get_database`, `td_list_tables`
  - Workflow Project Management: `td_list_projects`, `td_get_project`, `td_download_project_archive`, `td_list_project_files`, `td_read_project_file`
- All tools are async functions with proper type annotations
- Tools read API credentials from environment variables: `TD_API_KEY`, `TD_ENDPOINT`
- When adding new tools, always update the README.md with complete documentation

#### Standalone Server (`td_mcp_server/server.py`)
- Standalone server script that can be run directly with `mcp run`
- Used for Claude Desktop integration with `mcp install`
- Provides all Treasure Data API functionality through the MCP protocol

### 3. Tests

- Unit tests for API client: `tests/unit/test_api.py`
- Unit tests for MCP tools: `tests/unit/test_mcp_impl.py`

## Data Flow

1. User invokes CLI command or MCP tool
2. Command/tool parses arguments and initializes TreasureDataClient
3. Client authenticates with Treasure Data API using API key
4. Client makes requests to appropriate API endpoints
5. Responses are parsed into Pydantic models
6. Results are formatted according to user preferences (table/JSON, verbose/simple)
7. Data is returned to the user through CLI output or MCP response

## Authentication

The Treasure Data API requires authentication via an API key provided in two ways:

1. Environment variable: `TD_API_KEY`
2. Command-line parameter: `--api-key`

Environment variables are always prioritized over command-line parameters.
