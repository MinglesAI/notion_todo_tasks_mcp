# Notion MCP Integration

A simple Model Context Protocol (MCP) server that integrates with Notion's API to manage my personal todo list through Claude. This is a basic implementation tailored specifically for my minimalist todo list setup in Notion.

<p align="center">
  <img src="assets/demo.gif" width="600"/>
</p>

## Important Note

This is a personal project designed for a very specific use case: my simple Notion todo list that has just three properties:
- Task (title)
- When (select with only two options: "today" or "later")
- Checkbox (marks if completed)

[Example Notion Database](https://danhilse.notion.site/14e5549555a08078afb5ed5d374bb656?v=14e5549555a081f9b5a4000cdf952cb9&pvs=4)

While you can use this as a starting point for your own Notion integration, you'll likely need to modify the code to match your specific database structure.

## Features

- Add new todo items
- View all todos
- View today's tasks
- Check off a task as complete
- Multiple transport options: stdio, SSE, and Streamable HTTP

## Prerequisites

- Python 3.10 or higher
- A Notion account
- A Notion integration (API key)
- A Notion database that matches the exact structure described above (or willingness to modify the code for your structure)

## Setup

1. Clone this repository
2. Create a `.env` file in the root directory with the following variables:
   ```
   NOTION_API_KEY=your_notion_api_key_here
   NOTION_DATABASE_ID=your_database_id_here
   ```
3. Install dependencies:
   ```
   pip install -e .
   ```

## Running the Server

The server now uses the Streamable HTTP transport by default:

```bash
python -m notion_mcp
```

You can specify host and port:

```bash
python -m notion_mcp --host 127.0.0.1 --port 8000
```

### Running with Docker

You can also run the server using Docker:

1. Build and start the container:

```bash
docker build -t notion-mcp .
docker run -p 8000:8000 -e NOTION_API_KEY=your_key -e NOTION_DATABASE_ID=your_db_id notion-mcp
```

2. Or using Docker Compose:

```bash
# Create a .env file with your NOTION_API_KEY and NOTION_DATABASE_ID
docker-compose up -d
```

## Available Tools

The MCP server provides the following tools:

- `list_tasks`: List all tasks in the Notion database
- `add_task`: Add a new task to the database
- `complete_task`: Mark a task as completed
- `uncomplete_task`: Mark a task as not completed
- `set_task_time`: Set when a task should be done (today or later)

## Using with Claude

To use this MCP server with Claude, you'll need to configure a client that can connect to the Streamable HTTP transport. For example, you can use the MCP Python SDK to create a client:

```python
from mcp.client import Client
from mcp.client.transport import StreamableHttpTransport

# Create a client with the Streamable HTTP transport
transport = StreamableHttpTransport(url="http://127.0.0.1:8000")
client = Client(transport=transport)

# Connect to the server
await client.connect()

# List the available tools
tools = await client.list_tools()
print(tools)

# Call a tool
result = await client.call_tool("list_tasks")
print(result)
```

## Usage

Basic commands through Claude:
- "Show all my todos"
- "What's on my list for today?"
- "Add a todo for today: check emails"
- "Add a task for later: review project"

## Limitations

- Only works with a specific Notion database structure
- No support for complex database schemas
- Limited to "today" or "later" task scheduling
- No support for additional properties or custom fields
- Basic error handling
- No advanced features like recurring tasks, priorities, or tags

## Customization

If you want to use this with a different database structure, you'll need to modify the `server.py` file, particularly:
- The `create_todo()` function to match your database properties
- The todo formatting in `call_tool()` to handle your data structure
- The input schema in `list_tools()` if you want different options

## Project Structure
```
notion_mcp/
├── pyproject.toml
├── README.md
├── .env                   # Not included in repo
└── src/
    └── notion_mcp/
        ├── __init__.py
        ├── __main__.py
        └── server.py      # Main implementation
```

## License

MIT License - Use at your own risk

## Acknowledgments

- Built to work with Claude Desktop
- Uses Notion's API
