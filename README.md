# Treasure Data MCP Server

A Model Context Protocol (MCP) server that provides Treasure Data API integration for Claude Code and Claude Desktop, allowing for database management and listing functionality.

## Getting Started

```bash
# Clone the repository
git clone https://github.com/yourusername/td-mcp-server.git
cd td-mcp-server
```

## Authentication

The client requires a Treasure Data API key for authentication. You can provide this in two ways:

1. Set the `TD_API_KEY` environment variable:
   ```bash
   export TD_API_KEY="your-api-key"
   ```

2. Pass it directly to the command:
   ```bash
   python -m td_mcp_server --api-key="your-api-key" list-databases
   ```

## Usage

### Command Line Interface

The package provides a simple command-line interface for common operations that can be used without installation:

#### List databases

```bash
# Show only database names (default, first 30 databases)
python -m td_mcp_server.cli_api list

# Show detailed database information
python -m td_mcp_server.cli_api list --verbose

# Get only database names in JSON format
python -m td_mcp_server.cli_api list --format json

# Get detailed database information in JSON format
python -m td_mcp_server.cli_api list --format json --verbose

# Specify a different region endpoint
python -m td_mcp_server.cli_api list --endpoint api.treasuredata.co.jp

# Pagination options (default: limit=30, offset=0)
python -m td_mcp_server.cli_api list --limit 10 --offset 20

# Get all databases regardless of the number
python -m td_mcp_server.cli_api list --all
```

#### Get information about a specific database

```bash
# Get JSON output (default)
python -m td_mcp_server.cli_api get my_database_name

# Get table output
python -m td_mcp_server.cli_api get my_database_name --format table
```

#### List tables in a database

```bash
# Show only table names (default, first 30 tables)
python -m td_mcp_server.cli_api tables my_database_name

# Show detailed table information
python -m td_mcp_server.cli_api tables my_database_name --verbose

# Get only table names in JSON format
python -m td_mcp_server.cli_api tables my_database_name --format json

# Get detailed table information in JSON format
python -m td_mcp_server.cli_api tables my_database_name --format json --verbose

# Pagination options (default: limit=30, offset=0)
python -m td_mcp_server.cli_api tables my_database_name --limit 10 --offset 20

# Get all tables regardless of the number
python -m td_mcp_server.cli_api tables my_database_name --all
```

### Python API

You can also use the client directly in your Python code:

```python
from td_mcp_server.api import TreasureDataClient

# Initialize client with API key from environment variable
client = TreasureDataClient()

# Or provide API key directly
client = TreasureDataClient(api_key="your-api-key")

# Get databases with pagination (default: first 30 databases)
databases = client.get_databases(limit=30, offset=0)
for db in databases:
    print(f"Database: {db.name}, Tables: {db.count}")

# Get all databases regardless of the number
all_databases = client.get_databases(all_results=True)
for db in all_databases:
    print(f"Database: {db.name}, Tables: {db.count}")

# Get information about a specific database
db = client.get_database("my_database_name")
if db:
    print(f"Found database: {db.name}")
else:
    print("Database not found")

# Get tables in a database with pagination (default: first 30 tables)
tables = client.get_tables("my_database_name", limit=30, offset=0)
for table in tables:
    print(f"Table: {table.name}, Type: {table.type}, Count: {table.count}")

# Get all tables regardless of the number
all_tables = client.get_tables("my_database_name", all_results=True)
for table in all_tables:
    print(f"Table: {table.name}, Type: {table.type}, Count: {table.count}")
```

## API Endpoints

By default, the client uses the US region endpoint (`api.treasuredata.com`). If you need to use the Japan region, specify the endpoint:

```python
client = TreasureDataClient(endpoint="api.treasuredata.co.jp")
```

```bash
python -m td_mcp_server --endpoint=api.treasuredata.co.jp list-databases
```

## MCP Server Configuration

This server implements the Model Context Protocol (MCP) to provide Claude with access to Treasure Data API functionality. It uses the FastMCP library with `mcp.run(transport='stdio')` approach for standard MCP communication.

### Running the MCP Server

You can run the MCP server using the standard MCP CLI:

```bash
# Using MCP CLI
mcp run td_mcp_server/server.py
```

The server requires a Treasure Data API key, which should be provided via the `TD_API_KEY` environment variable:

```bash
# Using environment variable
export TD_API_KEY="your-api-key"
mcp run td_mcp_server/server.py

# For Claude Desktop integration, you can include the API key during installation
mcp install td_mcp_server/server.py -v TD_API_KEY="your-api-key" -v TD_ENDPOINT="api.treasuredata.com"
```

### FastMCP Implementation

Under the hood, this server uses the [FastMCP](https://modelcontextprotocol.io/quickstart/server) library, which provides an easy-to-use framework for building MCP servers. The implementation:

1. Creates a FastMCP server instance with the name "treasure-data"
2. Uses function decorators (`@mcp.tool()`) to register tools for database operations
3. The tools are implemented as async functions with proper type annotations
4. Uses `mcp.run(transport='stdio')` to start the server with standard I/O communication
5. Handles MCP requests and responses automatically through the FastMCP library

The implementation follows the standard pattern recommended in the Model Context Protocol documentation for Python servers, making it compatible with Claude Desktop and other MCP clients.

### Setting up with Claude Code

To configure this MCP server for use with Claude Code:

1. Clone the repository
   ```bash
   git clone https://github.com/yourusername/td-mcp-server.git
   ```

2. Set your Treasure Data API key as an environment variable
   ```bash
   export TD_API_KEY="your-api-key"
   ```

3. Add the MCP server using the Claude Code CLI
   ```bash
   # Navigate to your project directory
   cd your-project-directory

   # Add the MCP server (use absolute path to server.py)
   claude mcp add td -e TD_API_KEY=${TD_API_KEY} -e TD_ENDPOINT=api.treasuredata.com -- mcp run /absolute/path/to/td-mcp-server/td_mcp_server/server.py
   ```

   This will create or update the necessary configuration in your project's `.claude/plugins.json` file.

4. When using Claude Code in a project with this configuration, you'll have access to the following MCP tools:
   - `mcp__td_list_databases`: List databases in your Treasure Data account (only names by default, add `verbose=True` for full details, with pagination options `limit`, `offset`, and `all_results`)
   - `mcp__td_get_database`: Get information about a specific database
   - `mcp__td_list_tables`: List tables in a specific database (only names by default, add `verbose=True` for full details, with pagination options `limit`, `offset`, and `all_results`)

### Setting up with Claude Desktop

To configure this MCP server for use with Claude Desktop:

1. Clone the repository
   ```bash
   git clone https://github.com/yourusername/td-mcp-server.git
   ```

2. Method 1: Using the MCP CLI (Recommended)
   ```bash
   # Install the server with Claude Desktop using the MCP CLI
   mcp install /absolute/path/to/td-mcp-server/td_mcp_server/server.py -v TD_API_KEY="your-api-key" -v TD_ENDPOINT="api.treasuredata.com"

   # For Japan region
   mcp install /absolute/path/to/td-mcp-server/td_mcp_server/server.py -v TD_API_KEY="your-api-key" -v TD_ENDPOINT="api.treasuredata.co.jp"
   ```

3. Method 2: Using the Claude Desktop UI
   - Go to Settings > MCP Tools > Add New Tool
   - Name: Treasure Data API
   - Command: `mcp run /absolute/path/to/td-mcp-server/td_mcp_server/server.py`
   - Environment variables: Add your `TD_API_KEY` and optionally `TD_ENDPOINT`

4. You can now use the Treasure Data API tools in your Claude Desktop conversations

### Using MCP Tools in Claude

Once configured, you can use commands like:

```
# Get only database names (default, first 30 databases)
/mcp td_list_databases

# Get full database details
/mcp td_list_databases verbose=True

# Pagination options (default: limit=30, offset=0)
/mcp td_list_databases limit=10 offset=20

# Get all databases regardless of the number
/mcp td_list_databases all_results=True
```

```
# Get information about a specific database
/mcp td_get_database my_database_name
```

```
# Get only table names in a database (default, first 30 tables)
/mcp td_list_tables database_name=my_database_name

# Get detailed information about tables in a database
/mcp td_list_tables database_name=my_database_name verbose=True

# Pagination options (default: limit=30, offset=0)
/mcp td_list_tables database_name=my_database_name limit=10 offset=20

# Get all tables regardless of the number
/mcp td_list_tables database_name=my_database_name all_results=True
```

## Development

### Environment Requirements

This project requires Python 3.11+ and the following packages:
- requests >= 2.28.0
- pydantic >= 2.0.0
- mcp[cli] >= 1.8.1
- click >= 8.0.0, < 8.2.0
- typer >= 0.9.0

For development and testing:
- pytest >= 7.0.0
- pytest-mock >= 3.10.0
- pytest-cov >= 4.0.0
- responses >= 0.23.0
- black >= 23.0.0
- isort >= 5.12.0
- mypy >= 1.0.0
- ruff >= 0.0.270
- pre-commit >= 3.3.0

### Running Tests

This project uses pytest for unit testing. To run the tests:

```bash
# Create a virtual environment if you don't have one
python -m venv .venv

# Activate virtual environment
source .venv/bin/activate   # On Windows: .venv\Scripts\activate

# Install required dependencies
pip install pytest pytest-mock pytest-cov responses pytest-asyncio

# Run all tests
python -m pytest

# Run tests with coverage report
python -m pytest --cov=td_mcp_server

# Run tests for a specific module
python -m pytest tests/unit/test_api.py

# Run a specific test
python -m pytest tests/unit/test_api.py::TestTreasureDataClient::test_get_databases

# Run direct MCP integration tests
python -m pytest tests/integration/test_direct_mcp.py

### Test Structure

The tests are organized as follows:

- `tests/unit/test_api.py` - Tests for the Treasure Data API client
- `tests/unit/test_cli_api.py` - Tests for the CLI commands
- `tests/unit/test_mcp_impl.py` - Tests for the MCP tools implementation
- `tests/integration/test_direct_mcp.py` - Integration tests that directly call MCP functions in-process

### Code Formatting, Linting, and Pre-commit Hooks

The project uses Black, isort, and ruff for code formatting and linting, with pre-commit hooks to ensure code quality:

```bash
# Install development tools
pip install black isort ruff pre-commit

# Format code with Black
python -m black td_mcp_server tests

# Sort imports with isort
python -m isort td_mcp_server tests

# Run linting with Ruff
python -m ruff check td_mcp_server tests

# Run linting and auto-fix with Ruff
python -m ruff check --fix td_mcp_server tests

# Install pre-commit hooks (do this once)
pre-commit install

# Run all pre-commit hooks on all files
pre-commit run --all-files
```

The pre-commit hooks configuration is in `.pre-commit-config.yaml` and includes:
- Trailing whitespace removal
- End-of-file newline enforcement
- YAML file validation
- Ruff linting
- isort import sorting
- Black code formatting

### Type Checking

You can run static type checking with mypy:

```bash
# Install mypy
pip install mypy

# Run type checking
python -m mypy td_mcp_server
```
