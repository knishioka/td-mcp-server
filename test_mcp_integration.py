#!/usr/bin/env python
"""
MCP Integration Test for Treasure Data MCP Server

This script tests the MCP tools with real API calls but uses safe practices:
- No hardcoded production data (IDs, names)
- Limited output to avoid exposing sensitive information
- Uses generic search terms
- Requires TD_API_KEY environment variable

Usage:
    export TD_API_KEY="your-api-key"
    python test_mcp_integration.py
"""

import asyncio
import json
import os
import sys
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


# Safety check for API key
if "TD_API_KEY" not in os.environ:
    print("Error: TD_API_KEY environment variable is required")
    print("Usage: export TD_API_KEY='your-api-key'")
    sys.exit(1)


async def test_tool_safely(session: ClientSession, tool_name: str, arguments: dict = None):
    """Test a tool and return summary result only"""
    try:
        result = await session.call_tool(tool_name, arguments=arguments or {})
        
        if result.content and hasattr(result.content[0], 'text'):
            data = json.loads(result.content[0].text)
            
            # Return summary based on tool type
            if "error" in data:
                return f"❌ Error: {data['error']}"
            
            if tool_name == "td_list_databases":
                count = len(data.get("databases", []))
                return f"✅ Found {count} databases"
            
            elif tool_name == "td_list_projects":
                count = len(data.get("projects", []))
                return f"✅ Found {count} projects"
            
            elif tool_name == "td_smart_search":
                count = data.get("total_found", 0)
                return f"✅ Found {count} results"
            
            elif tool_name == "td_explore_project":
                name = data.get("project", {}).get("name", "unknown")
                return f"✅ Analyzed project (name hidden for privacy)"
            
            elif tool_name == "td_diagnose_workflow":
                score = data.get("health_score", "N/A")
                return f"✅ Health score: {score}"
            
            elif tool_name == "td_trace_data_lineage":
                nodes = len(data.get("lineage", {}).get("nodes", []))
                return f"✅ Found {nodes} nodes in lineage"
            
            else:
                return "✅ Success"
                
    except Exception as e:
        return f"❌ Exception: {str(e)}"


async def run_integration_tests():
    """Run integration tests for all MCP tools"""
    
    print("=" * 60)
    print("MCP Integration Test")
    print("=" * 60)
    print()
    
    # Start MCP server
    server_params = StdioServerParameters(
        command="python",
        args=["-m", "td_mcp_server.server"],
        env={**os.environ}
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # Get available tools
            tools_result = await session.list_tools()
            available_tools = [tool.name for tool in tools_result.tools]
            print(f"Available tools: {len(available_tools)}")
            print()
            
            # Test basic functionality
            print("Testing Core Tools:")
            print("-" * 40)
            
            # 1. Database operations
            result = await test_tool_safely(session, "td_list_databases", {"limit": 5})
            print(f"td_list_databases: {result}")
            
            # 2. Project operations
            result = await test_tool_safely(session, "td_list_projects", {"limit": 5})
            print(f"td_list_projects: {result}")
            
            # 3. Smart search with generic term
            result = await test_tool_safely(session, "td_smart_search", {
                "query": "data",  # Generic search term
                "search_scope": "projects",
                "min_relevance": 0.5
            })
            print(f"td_smart_search: {result}")
            
            print()
            print("Testing New Analysis Tools:")
            print("-" * 40)
            
            # Get first available project ID for testing (without exposing it)
            list_result = await session.call_tool("td_list_projects", arguments={"limit": 1})
            project_id = None
            if list_result.content and hasattr(list_result.content[0], 'text'):
                data = json.loads(list_result.content[0].text)
                if data.get("projects"):
                    project_id = data["projects"][0]["id"]
            
            if project_id:
                # 4. Project exploration
                result = await test_tool_safely(session, "td_explore_project", {
                    "identifier": project_id,
                    "analysis_depth": "overview"
                })
                print(f"td_explore_project: {result}")
                
                # 5. Data lineage
                result = await test_tool_safely(session, "td_trace_data_lineage", {
                    "table_or_project": project_id,
                    "direction": "both",
                    "max_depth": 2
                })
                print(f"td_trace_data_lineage: {result}")
            else:
                print("td_explore_project: ⚠️  No project available for testing")
                print("td_trace_data_lineage: ⚠️  No project available for testing")
            
            # Get first workflow for testing
            wf_result = await session.call_tool("td_list_workflows", arguments={"count": 1})
            workflow_id = None
            if wf_result.content and hasattr(wf_result.content[0], 'text'):
                data = json.loads(wf_result.content[0].text)
                if data.get("workflows"):
                    workflow_id = data["workflows"][0]["id"]
            
            if workflow_id:
                # 6. Workflow diagnosis
                result = await test_tool_safely(session, "td_diagnose_workflow", {
                    "workflow_identifier": workflow_id,
                    "time_window": "7d"
                })
                print(f"td_diagnose_workflow: {result}")
            else:
                print("td_diagnose_workflow: ⚠️  No workflow available for testing")
            
            print()
            print("Testing Error Handling:")
            print("-" * 40)
            
            # Test with invalid inputs
            result = await test_tool_safely(session, "td_smart_search", {"query": ""})
            print(f"Empty search: {result}")
            
            result = await test_tool_safely(session, "td_explore_project", {
                "identifier": "nonexistent_project_12345"
            })
            print(f"Invalid project: {result}")
            
            print()
            print("=" * 60)
            print("✅ Integration test completed")
            print("=" * 60)


if __name__ == "__main__":
    try:
        asyncio.run(run_integration_tests())
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"\nTest failed with error: {e}")
        sys.exit(1)