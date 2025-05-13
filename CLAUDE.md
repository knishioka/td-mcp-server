# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Treasure Data MCP Server Overview

This repository contains a Model Context Protocol (MCP) server that provides Treasure Data API integration for Claude Code and Claude Desktop, allowing for database management and listing functionality.

## API Reference

For Treasure Data API specifications, endpoint details, example responses, and other API-related information, refer to the detailed documentation in:

**docs/treasure-data-api-guide.md**

This guide includes:
- API endpoint URLs for different regions
- Authentication methods
- Example API requests and responses
- Available API operations (databases, tables, jobs, etc.)
- Response structures and field descriptions

## Key Commands

### Installation

```bash
# Install from source in development mode
pip install -e .

# Install with development dependencies
pip install -e ".[dev]"
```

### Running the MCP Server

```bash
# Run using uv (recommended)
uv run td-mcp

# Run directly after installation
td-mcp

# Run with API key specified
TD_API_KEY="your-api-key" td-mcp

# Run with different endpoint for Japan region
TD_API_KEY="your-api-key" TD_ENDPOINT="api.treasuredata.co.jp" td-mcp
```

### CLI Commands

```bash
# List databases (first 30 by default)
td-list-databases

# List databases with verbose output
td-list-databases --verbose

# List databases with pagination
td-list-databases --limit 10 --offset 20

# List all databases
td-list-databases --all

# Get database information
td-get-database my_database_name

# List tables in a database (first 30 by default)
td-list-tables my_database_name

# List tables with verbose output
td-list-tables my_database_name --verbose

# List tables with pagination
td-list-tables my_database_name --limit 10 --offset 20

# List all tables in a database
td-list-tables my_database_name --all
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

### Code Formatting and Type Checking

```bash
# Format code with Black
black td_mcp_server tests

# Sort imports with isort
isort td_mcp_server tests

# Run type checking
mypy td_mcp_server
```

## Architecture

The codebase is structured around the following key components:

### 1. API Client (`td_mcp_server/api.py`)

- `TreasureDataClient` class: Main client interface for Treasure Data API
- `Database` and `Table` models: Pydantic models for API responses
- Core API methods: `get_databases`, `get_database`, `get_tables`
- All methods support pagination with `limit`, `offset`, and `all_results` parameters

### 2. CLI Interface (`td_mcp_server/cli_api.py`)

- Command-line functions: `list_databases`, `get_database`, `list_tables`
- Entry points: `main_list_databases`, `main_get_database`, `main_list_tables`
- Supports various output formats (table, JSON) and verbosity levels

### 3. MCP Implementation (`td_mcp_server/mcp_impl.py`)

- Implements the FastMCP server: `mcp = FastMCP("treasure-data")`
- MCP tools: `td_list_databases`, `td_get_database`, `td_list_tables` 
- All tools are async functions with proper type annotations
- Tools read API credentials from environment variables: `TD_API_KEY`, `TD_ENDPOINT`

### 4. MCP Server Entry Point (`td_mcp_server/mcp.py`)

- Main entry point for the MCP server using stdio transport
- Called by CLI commands defined in pyproject.toml

### 5. Tests

- Unit tests for API client: `tests/unit/test_api.py`
- Unit tests for CLI commands: `tests/unit/test_cli_api.py` 
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