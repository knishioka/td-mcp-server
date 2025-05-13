# Treasure Data MCP Server

A Machine Control Protocol (MCP) server for Treasure Data integration with Claude.

## Installation

```bash
# Install the package
pip install td-mcp-server
```

## Claude Code Configuration

```bash
# Add to Claude Code (replace with your API key)
claude mcp add td -e TD_API_KEY=your_api_key_here

# For Japan region
claude mcp add td -e TD_API_KEY=your_api_key_here -e TD_ENDPOINT=api.treasuredata.co.jp
```

## Claude Desktop Configuration

Create the following configuration file in `~/.mcp/servers/td.json`:

```json
{
  "name": "td",
  "command": ["python", "-m", "td_mcp_server.mcp"],
  "environment": {
    "TD_API_KEY": "your_api_key_here",
    "TD_ENDPOINT": "api.treasuredata.co.jp"
  }
}
```

## Features

- Database management
- Table management
- Query execution
- Job management

## Requirements

- Python 3.8+
- Treasure Data API key