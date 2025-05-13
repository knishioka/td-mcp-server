#!/bin/bash

# Exit on error
set -e

# Style
BOLD='\033[1m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BOLD}${CYAN}=== Building and installing Treasure Data MCP Server ===${NC}"

# Install the package in dev mode
echo -e "${BOLD}${GREEN}Installing package...${NC}"
pip install -e .

# Check if TD_API_KEY is set
if [ -z "$TD_API_KEY" ]; then
  echo -e "${BOLD}${YELLOW}Warning: TD_API_KEY environment variable is not set.${NC}"
  echo -e "Setting a dummy key for testing. In production, use your real API key."
  export TD_API_KEY="dummy-key-for-testing"
fi

# Run the MCP server
echo -e "${BOLD}${GREEN}Starting MCP server...${NC}"
echo -e "Press Ctrl+C to stop the server"
echo

# Run with uv
uv run mcp