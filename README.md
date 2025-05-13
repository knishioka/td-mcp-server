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

#### List all databases

```bash
# Show databases in table format (default)
python -m td_mcp_server list-databases

# Get JSON output
python -m td_mcp_server list-databases --format=json

# Specify a different region endpoint
python -m td_mcp_server --endpoint=api.treasuredata.co.jp list-databases
```

#### Get information about a specific database

```bash
# Get JSON output (default)
python -m td_mcp_server get-database my_database_name

# Get table output
python -m td_mcp_server get-database my_database_name --format=table
```

### Python API

You can also use the client directly in your Python code:

```python
from td_mcp_server.api import TreasureDataClient

# Initialize client with API key from environment variable
client = TreasureDataClient()

# Or provide API key directly
client = TreasureDataClient(api_key="your-api-key")

# Get all databases
databases = client.get_databases()
for db in databases:
    print(f"Database: {db.name}, Tables: {db.count}")

# Get information about a specific database
db = client.get_database("my_database_name")
if db:
    print(f"Found database: {db.name}")
else:
    print("Database not found")
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

This server implements the Model Context Protocol (MCP) to provide Claude with access to Treasure Data API functionality.

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

3. Create a `.claude/plugins.json` file in your project directory with the following content:
   ```json
   {
     "plugins": [
       {
         "name": "td-mcp",
         "description": "Treasure Data API plugin for database management",
         "command": {
           "args": ["python", "-m", "td_mcp_server", "--mcp-server"],
           "env": {
             "TD_API_KEY": "${TD_API_KEY}"
           }
         }
       }
     ]
   }
   ```

4. When using Claude Code in a project with this configuration, you'll have access to the following MCP tools:
   - `mcp__td_list_databases`: List all databases in your Treasure Data account
   - `mcp__td_get_database`: Get information about a specific database

### Setting up with Claude Desktop

To configure this MCP server for use with Claude Desktop:

1. Install the server as described above

2. In Claude Desktop, create a new MCP tool configuration:
   - Go to Settings > MCP Tools > Add New Tool
   - Name: Treasure Data API
   - Command: `python -m td_mcp_server --mcp-server`
   - Environment variables: Add your `TD_API_KEY` 

3. Save the configuration and restart Claude Desktop

4. You can now use the Treasure Data API tools in your Claude Desktop conversations

### Using MCP Tools in Claude

Once configured, you can use commands like:

```
/mcp td_list_databases
```

or

```
/mcp td_get_database my_database_name
```

## Development

To set up the development environment:

```bash
# Clone the repository
git clone https://github.com/yourusername/td-mcp-server.git
cd td-mcp-server

# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest
```