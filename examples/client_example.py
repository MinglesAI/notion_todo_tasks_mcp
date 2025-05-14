#!/usr/bin/env python3
import asyncio
import json
from mcp.client import Client
from mcp.client.transport.streamable_http import StreamableHttpClient

async def main():
    """Example of using the MCP client with Streamable HTTP transport."""
    # Create a client with the Streamable HTTP transport
    client = Client("http://127.0.0.1:8000/mcp")
    
    try:
        # Connect to the server
        print("Connecting to MCP server...")
        await client.connect()
        print("Connected!")
        
        # List available tools
        print("\nListing available tools:")
        tools = await client.list_tools()
        for tool in tools:
            print(f"- {tool['name']}: {tool['description']}")
        
        # List all tasks
        print("\nListing all tasks:")
        result = await client.call_tool("list_tasks")
        if "resources" in result and result["resources"]:
            for task in result["resources"]:
                print(f"- {task['name']} ({task['id']})")
                print(f"  {task['description']}")
        else:
            print("No tasks found.")
        
        # Add a new task
        print("\nAdding a new task:")
        new_task_result = await client.call_tool(
            "add_task", 
            {"task_name": "Example task from client", "when": "today"}
        )
        if "resources" in new_task_result and new_task_result["resources"]:
            new_task = new_task_result["resources"][0]
            print(f"Added task: {new_task['name']} ({new_task['id']})")
            
            # Complete the task
            print("\nCompleting the task:")
            complete_result = await client.call_tool(
                "complete_task", 
                {"task_id": new_task["id"]}
            )
            if "resources" in complete_result and complete_result["resources"]:
                completed_task = complete_result["resources"][0]
                print(f"Task completed: {completed_task['name']}")
                
                # Uncomplete the task
                print("\nUncompleting the task:")
                uncomplete_result = await client.call_tool(
                    "uncomplete_task", 
                    {"task_id": new_task["id"]}
                )
                if "resources" in uncomplete_result and uncomplete_result["resources"]:
                    uncompleted_task = uncomplete_result["resources"][0]
                    print(f"Task uncompleted: {uncompleted_task['name']}")
                    
                    # Change task time
                    print("\nChanging task time:")
                    time_result = await client.call_tool(
                        "set_task_time", 
                        {"task_id": new_task["id"], "when": "later"}
                    )
                    if "resources" in time_result and time_result["resources"]:
                        updated_task = time_result["resources"][0]
                        print(f"Task time updated: {updated_task['name']}")
                    
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Disconnect from the server
        await client.disconnect()
        print("\nDisconnected from MCP server.")

if __name__ == "__main__":
    asyncio.run(main()) 