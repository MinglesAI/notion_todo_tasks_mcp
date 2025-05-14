from mcp.server.fastmcp import FastMCP, Context
from mcp.types import (
    Resource, 
    Tool,
    TextContent,
    EmbeddedResource
)
from pydantic import AnyUrl
import os
import json
from datetime import datetime
import httpx
from typing import Any, Sequence
from dotenv import load_dotenv
from pathlib import Path
import logging
import uvicorn
import argparse
import asyncio
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from dataclasses import dataclass

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('notion_mcp')

# Find and load .env file from project root
project_root = Path(__file__).parent.parent.parent
env_path = project_root / '.env'
if not env_path.exists():
    raise FileNotFoundError(f"No .env file found at {env_path}")
load_dotenv(env_path)

# Configuration with validation
NOTION_API_KEY = os.getenv("NOTION_API_KEY")
if not NOTION_API_KEY:
    raise ValueError("NOTION_API_KEY environment variable is required")

NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")
if not NOTION_DATABASE_ID:
    raise ValueError("NOTION_DATABASE_ID environment variable is required")

NOTION_API_URL = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"

# Headers for Notion API requests
HEADERS = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Content-Type": "application/json",
    "Notion-Version": NOTION_VERSION,
}

# Определение класса для контекста приложения
@dataclass
class NotionContext:
    client: httpx.AsyncClient

# Определение функции жизненного цикла
@asynccontextmanager
async def notion_lifespan(server: FastMCP) -> AsyncIterator[NotionContext]:
    """Управление жизненным циклом подключения к Notion API"""
    # Инициализация клиента при запуске
    client = httpx.AsyncClient(headers=HEADERS)
    logger.info("Initialized Notion API client")
    try:
        yield NotionContext(client=client)
    finally:
        # Закрытие клиента при завершении
        await client.aclose()
        logger.info("Closed Notion API client")

# Initialize server with FastMCP and lifespan
mcp = FastMCP("notion-todo", stateless_http=True, lifespan=notion_lifespan)

async def get_database_schema(ctx: Context) -> dict:
    """Get the schema of the Notion database."""
    client = ctx.request_context.lifespan_context.client
    response = await client.get(f"{NOTION_API_URL}/databases/{NOTION_DATABASE_ID}")
    response.raise_for_status()
    return response.json()

async def query_database(filter_params: dict = None, ctx: Context = None) -> list:
    """Query the Notion database with optional filters."""
    url = f"{NOTION_API_URL}/databases/{NOTION_DATABASE_ID}/query"
    
    # Default payload with no filters
    payload = {}
    
    # Add filters if provided
    if filter_params:
        payload = filter_params
    
    # Используем клиент из контекста, если он доступен
    if ctx and ctx.request_context.lifespan_context:
        client = ctx.request_context.lifespan_context.client
        response = await client.post(url, json=payload)
    else:
        # Для обратной совместимости
        async with httpx.AsyncClient(headers=HEADERS) as client:
            response = await client.post(url, json=payload)
    
    response.raise_for_status()
    return response.json().get("results", [])

async def create_page(properties: dict, ctx: Context = None) -> dict:
    """Create a new page (task) in the Notion database."""
    url = f"{NOTION_API_URL}/pages"
    
    payload = {
        "parent": {"database_id": NOTION_DATABASE_ID},
        "properties": properties,
    }
    
    # Используем клиент из контекста, если он доступен
    if ctx and ctx.request_context.lifespan_context:
        client = ctx.request_context.lifespan_context.client
        response = await client.post(url, json=payload)
    else:
        # Для обратной совместимости
        async with httpx.AsyncClient(headers=HEADERS) as client:
            response = await client.post(url, json=payload)
    
    response.raise_for_status()
    return response.json()

async def update_page(page_id: str, properties: dict, ctx: Context = None) -> dict:
    """Update a page (task) in the Notion database."""
    url = f"{NOTION_API_URL}/pages/{page_id}"
    
    payload = {
        "properties": properties,
    }
    
    # Используем клиент из контекста, если он доступен
    if ctx and ctx.request_context.lifespan_context:
        client = ctx.request_context.lifespan_context.client
        response = await client.patch(url, json=payload)
    else:
        # Для обратной совместимости
        async with httpx.AsyncClient(headers=HEADERS) as client:
            response = await client.patch(url, json=payload)
    
    response.raise_for_status()
    return response.json()

# Define available tools using FastMCP decorators
@mcp.tool()
async def list_tasks(ctx: Context) -> list[Resource]:
    """List all tasks in the Notion database."""
    try:
        tasks = await query_database(ctx=ctx)
        
        resources = []
        for task in tasks:
            task_name = task["properties"]["Task"]["title"][0]["text"]["content"] if task["properties"]["Task"]["title"] else "Untitled"
            when = task["properties"]["When"]["select"]["name"] if task["properties"]["When"]["select"] else "later"
            completed = task["properties"]["Checkbox"]["checkbox"]
            
            status = "✅ " if completed else "⬜ "
            when_emoji = "🔴 " if when.lower() == "today" else "⚪ "
            
            resources.append(
                Resource(
                    id=task["id"],
                    uri=f"notion://task/{task['id']}",
                    name=f"{status}{when_emoji}{task_name}",
                    description=f"When: {when}, Completed: {completed}",
                )
            )
        
        return resources
    except Exception as e:
        logger.error(f"Error listing tasks: {e}")
        return [TextContent(type="text", text=f"Error listing tasks: {str(e)}")]

@mcp.tool()
async def add_task(task_name: str, when: str = "later", ctx: Context = None) -> list[Resource]:
    """Add a new task to the Notion database."""
    try:
        # Validate 'when' parameter
        if when.lower() not in ["today", "later"]:
            when = "later"
        
        # Create properties for the new task
        properties = {
            "Task": {
                "title": [
                    {
                        "text": {
                            "content": task_name
                        }
                    }
                ]
            },
            "When": {
                "select": {
                    "name": when.lower()
                }
            },
            "Checkbox": {
                "checkbox": False
            }
        }
        
        # Create the task in Notion
        new_task = await create_page(properties, ctx=ctx)
        
        # Return the created task as a resource
        return [Resource(
            id=new_task["id"],
            uri=f"notion://task/{new_task['id']}",
            name=f"⬜ {'🔴 ' if when.lower() == 'today' else '⚪ '}{task_name}",
            description=f"When: {when}, Completed: False",
        )]
    except Exception as e:
        logger.error(f"Error adding task: {e}")
        return [TextContent(type="text", text=f"Error adding task: {str(e)}")]

@mcp.tool()
async def complete_task(task_id: str, ctx: Context = None) -> list[Resource]:
    """Mark a task as completed."""
    try:
        # Create properties to update
        properties = {
            "Checkbox": {
                "checkbox": True
            }
        }
        
        # Update the task in Notion
        updated_task = await update_page(task_id, properties, ctx=ctx)
        
        # Get the task name and when value
        task_name = updated_task["properties"]["Task"]["title"][0]["text"]["content"] if updated_task["properties"]["Task"]["title"] else "Untitled"
        when = updated_task["properties"]["When"]["select"]["name"] if updated_task["properties"]["When"]["select"] else "later"
        
        # Return the updated task as a resource
        return [Resource(
            id=updated_task["id"],
            uri=f"notion://task/{updated_task['id']}",
            name=f"✅ {'🔴 ' if when.lower() == 'today' else '⚪ '}{task_name}",
            description=f"When: {when}, Completed: True",
        )]
    except Exception as e:
        logger.error(f"Error completing task: {e}")
        return [TextContent(type="text", text=f"Error completing task: {str(e)}")]

@mcp.tool()
async def uncomplete_task(task_id: str, ctx: Context = None) -> list[Resource]:
    """Mark a task as not completed."""
    try:
        # Create properties to update
        properties = {
            "Checkbox": {
                "checkbox": False
            }
        }
        
        # Update the task in Notion
        updated_task = await update_page(task_id, properties, ctx=ctx)
        
        # Get the task name and when value
        task_name = updated_task["properties"]["Task"]["title"][0]["text"]["content"] if updated_task["properties"]["Task"]["title"] else "Untitled"
        when = updated_task["properties"]["When"]["select"]["name"] if updated_task["properties"]["When"]["select"] else "later"
        
        # Return the updated task as a resource
        return [Resource(
            id=updated_task["id"],
            uri=f"notion://task/{updated_task['id']}",
            name=f"⬜ {'🔴 ' if when.lower() == 'today' else '⚪ '}{task_name}",
            description=f"When: {when}, Completed: False",
        )]
    except Exception as e:
        logger.error(f"Error uncompleting task: {e}")
        return [TextContent(type="text", text=f"Error uncompleting task: {str(e)}")]

@mcp.tool()
async def set_task_time(task_id: str, when: str, ctx: Context = None) -> list[Resource]:
    """Set when a task should be done."""
    try:
        # Validate 'when' parameter
        if when.lower() not in ["today", "later"]:
            when = "later"
        
        # Create properties to update
        properties = {
            "When": {
                "select": {
                    "name": when.lower()
                }
            }
        }
        
        # Update the task in Notion
        updated_task = await update_page(task_id, properties, ctx=ctx)
        
        # Get the task name and completed value
        task_name = updated_task["properties"]["Task"]["title"][0]["text"]["content"] if updated_task["properties"]["Task"]["title"] else "Untitled"
        completed = updated_task["properties"]["Checkbox"]["checkbox"]
        
        # Return the updated task as a resource
        return [Resource(
            id=updated_task["id"],
            uri=f"notion://task/{updated_task['id']}",
            name=f"{'✅ ' if completed else '⬜ '}{'🔴 ' if when.lower() == 'today' else '⚪ '}{task_name}",
            description=f"When: {when}, Completed: {completed}",
        )]
    except Exception as e:
        logger.error(f"Error setting task time: {e}")
        return [TextContent(type="text", text=f"Error setting task time: {str(e)}")]

async def main():
    """Run the MCP server with Streamable HTTP transport."""
    parser = argparse.ArgumentParser(description='Run the Notion MCP server')
    parser.add_argument('--host', type=str, default='127.0.0.1', help='Host to bind the server to')
    parser.add_argument('--port', type=int, default=8000, help='Port to bind the server to')
    parser.add_argument('--transport', type=str, default='streamable-http', help='Transport to use (streamable-http or sse)')
    args = parser.parse_args()
    
    # Start the server with the specified transport
    logger.info(f"Starting Notion MCP server on {args.host}:{args.port} with {args.transport} transport")
    
    # Используем асинхронные методы напрямую
    if args.transport == 'streamable-http':
        logger.info(f"MCP API will be available at http://{args.host}:{args.port}/")
        await mcp.run_streamable_http_async()
    else:
        # Для других транспортов используем соответствующие методы
        await mcp.run_stdio_async()

# Для обратной совместимости, если файл запускается напрямую
if __name__ == "__main__":
    import asyncio
    asyncio.run(main())