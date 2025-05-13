# Treasure Data MCP Server

A Model Context Protocol (MCP) server that provides Treasure Data API integration for Claude Code and Claude Desktop, allowing for database management and listing functionality.

## Installation

```bash
# Install from source
git clone https://github.com/yourusername/td-mcp-server.git
cd td-mcp-server
pip install -e .
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

The package provides a simple command-line interface for common operations:

#### List databases

```bash
# Show only database names (default, first 30 databases)
uv run td-list-databases

# Show detailed database information
uv run td-list-databases --verbose

# Get only database names in JSON format
uv run td-list-databases --format json

# Get detailed database information in JSON format
uv run td-list-databases --format json --verbose

# Specify a different region endpoint
uv run td-list-databases --endpoint api.treasuredata.co.jp

# Pagination options (default: limit=30, offset=0)
uv run td-list-databases --limit 10 --offset 20

# Get all databases regardless of the number
uv run td-list-databases --all
```

#### Get information about a specific database

```bash
# Get JSON output (default)
uv run td-get-database my_database_name

# Get table output
uv run td-get-database my_database_name --format table
```

#### List tables in a database

```bash
# Show only table names (default, first 30 tables)
uv run td-list-tables my_database_name

# Show detailed table information
uv run td-list-tables my_database_name --verbose

# Get only table names in JSON format
uv run td-list-tables my_database_name --format json

# Get detailed table information in JSON format
uv run td-list-tables my_database_name --format json --verbose

# Pagination options (default: limit=30, offset=0)
uv run td-list-tables my_database_name --limit 10 --offset 20

# Get all tables regardless of the number
uv run td-list-tables my_database_name --all
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

You can run the MCP server in two ways:

```bash
# Using uv run (recommended)
uv run td-mcp

# Using the installed script (after pip install)
td-mcp
```

The server requires a Treasure Data API key, which should be provided via the `TD_API_KEY` environment variable or with the `--api-key` option:

```bash
# Using environment variable (recommended)
export TD_API_KEY="your-api-key"
uv run td-mcp

# Or providing the API key directly
uv run td-mcp --api-key="your-api-key"
```

For development or debugging, you can run the server with verbose logging:

```bash
# Enable verbose logging
uv run td-mcp --verbose
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

1. Install the server
   ```bash
   git clone https://github.com/yourusername/td-mcp-server.git
   cd td-mcp-server
   pip install -e .
   ```

2. Set your Treasure Data API key as an environment variable
   ```bash
   export TD_API_KEY="your-api-key"
   ```

3. Add the MCP server using the Claude Code CLI
   ```bash
   # Navigate to your project directory
   cd your-project-directory

   # Add the MCP server
   claude mcp add td -e TD_API_KEY=${TD_API_KEY} -e TD_ENDPOINT=api.treasuredata.com -- uv run td-mcp
   ```

   This will create or update the necessary configuration in your project's `.claude/plugins.json` file.

4. When using Claude Code in a project with this configuration, you'll have access to the following MCP tools:
   - `mcp__td_list_databases`: List databases in your Treasure Data account (only names by default, add `verbose=True` for full details, with pagination options `limit`, `offset`, and `all_results`)
   - `mcp__td_get_database`: Get information about a specific database
   - `mcp__td_list_tables`: List tables in a specific database (only names by default, add `verbose=True` for full details, with pagination options `limit`, `offset`, and `all_results`)

### Setting up with Claude Desktop

To configure this MCP server for use with Claude Desktop:

1. Install the server as described above

2. Method 1: Using the Claude Desktop UI
   - Go to Settings > MCP Tools > Add New Tool
   - Name: Treasure Data API
   - Command: `uv run td-mcp`
   - Environment variables: Add your `TD_API_KEY` 

3. Method 2: Using claude_desktop_config.json (recommended)
   - Create or update your claude_desktop_config.json file:
     - macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
     - Windows: `%APPDATA%\Claude\claude_desktop_config.json`
   - Add the following configuration:
     ```json
     {
       "mcpServers": {
         "treasure-data": {
           "command": "uv",
           "args": ["run", "td-mcp"],
           "env": {
             "TD_API_KEY": "your-api-key"
           }
         }
       }
     }
     ```
   - Replace `your-api-key` with your actual Treasure Data API key

4. Save the configuration and restart Claude Desktop

5. You can now use the Treasure Data API tools in your Claude Desktop conversations

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

### Setting Up the Development Environment

```bash
# Clone the repository
git clone https://github.com/yourusername/td-mcp-server.git
cd td-mcp-server

# Install dev dependencies
pip install -e ".[dev]"
```

### Running Tests

This project uses pytest for unit testing. To run the tests:

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

### Test Structure

The tests are organized as follows:

- `tests/unit/test_api.py` - Tests for the Treasure Data API client
- `tests/unit/test_cli_api.py` - Tests for the CLI commands
- `tests/unit/test_mcp_impl.py` - Tests for the MCP tools implementation

### Code Formatting

The project uses Black and isort for code formatting:

```bash
# Format code with Black
black td_mcp_server tests

# Sort imports with isort
isort td_mcp_server tests
```

### Type Checking

You can run static type checking with mypy:

```bash
mypy td_mcp_server
```