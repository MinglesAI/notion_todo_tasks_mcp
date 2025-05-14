import pytest
import asyncio
from unittest.mock import patch, AsyncMock, MagicMock
from mcp.client import Client
from mcp.client.transport.streamable_http import StreamableHttpClient
from mcp.types import Resource

@pytest.fixture
def mock_transport():
    """Mock StreamableHttpClient."""
    mock = AsyncMock(spec=StreamableHttpClient)
    mock.connect = AsyncMock()
    mock.disconnect = AsyncMock()
    mock.send = AsyncMock()
    mock.receive = AsyncMock()
    return mock

@pytest.fixture
def client(mock_transport):
    """Create a client with mocked transport."""
    return Client(transport=mock_transport)

@pytest.mark.asyncio
async def test_client_connect(client, mock_transport):
    """Test client connect method."""
    await client.connect()
    mock_transport.connect.assert_called_once()

@pytest.mark.asyncio
async def test_client_disconnect(client, mock_transport):
    """Test client disconnect method."""
    await client.disconnect()
    mock_transport.disconnect.assert_called_once()

@pytest.mark.asyncio
async def test_list_tools(client, mock_transport):
    """Test listing tools from the server."""
    # Mock the receive method to return a list of tools
    mock_transport.receive.side_effect = [
        {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {
                "tools": [
                    {
                        "name": "list_tasks",
                        "description": "List all tasks in the Notion database."
                    },
                    {
                        "name": "add_task",
                        "description": "Add a new task to the Notion database."
                    }
                ]
            }
        }
    ]
    
    tools = await client.list_tools()
    
    assert len(tools) == 2
    assert tools[0]["name"] == "list_tasks"
    assert tools[1]["name"] == "add_task"
    
    # Verify the correct message was sent
    mock_transport.send.assert_called_once()
    sent_msg = mock_transport.send.call_args[0][0]
    assert sent_msg["method"] == "mcp.list_tools"
    assert sent_msg["id"] == 1

@pytest.mark.asyncio
async def test_call_tool(client, mock_transport):
    """Test calling a tool on the server."""
    # Mock tasks to be returned
    mock_tasks = [
        {
            "id": "task1",
            "name": "⬜ 🔴 Test task 1",
            "description": "When: today, Completed: False"
        },
        {
            "id": "task2",
            "name": "✅ ⚪ Test task 2",
            "description": "When: later, Completed: True"
        }
    ]
    
    # Mock the receive method to return tool results
    mock_transport.receive.side_effect = [
        {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {
                "resources": mock_tasks
            }
        }
    ]
    
    result = await client.call_tool("list_tasks")
    
    assert len(result["resources"]) == 2
    assert result["resources"][0]["id"] == "task1"
    assert result["resources"][1]["id"] == "task2"
    
    # Verify the correct message was sent
    mock_transport.send.assert_called_once()
    sent_msg = mock_transport.send.call_args[0][0]
    assert sent_msg["method"] == "mcp.call_tool"
    assert sent_msg["params"]["name"] == "list_tasks"
    assert sent_msg["id"] == 1

@pytest.mark.asyncio
async def test_call_tool_with_args(client, mock_transport):
    """Test calling a tool with arguments."""
    # Mock task to be returned
    mock_task = {
        "id": "new_task_id",
        "name": "⬜ 🔴 New task",
        "description": "When: today, Completed: False"
    }
    
    # Mock the receive method to return tool results
    mock_transport.receive.side_effect = [
        {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {
                "resources": [mock_task]
            }
        }
    ]
    
    result = await client.call_tool("add_task", {"task_name": "New task", "when": "today"})
    
    assert len(result["resources"]) == 1
    assert result["resources"][0]["id"] == "new_task_id"
    assert "New task" in result["resources"][0]["name"]
    
    # Verify the correct message was sent
    mock_transport.send.assert_called_once()
    sent_msg = mock_transport.send.call_args[0][0]
    assert sent_msg["method"] == "mcp.call_tool"
    assert sent_msg["params"]["name"] == "add_task"
    assert sent_msg["params"]["arguments"]["task_name"] == "New task"
    assert sent_msg["params"]["arguments"]["when"] == "today"
    assert sent_msg["id"] == 1

@pytest.mark.asyncio
async def test_streamable_http_client_integration():
    """Test creating a client with StreamableHttpClient."""
    # Mock the StreamableHttpClient class
    with patch("mcp.client.transport.streamable_http.StreamableHttpClient") as mock_client_class:
        # Create a mock instance
        mock_instance = AsyncMock()
        mock_client_class.return_value = mock_instance
        
        # Import the client module
        from mcp.client import Client
        
        # Create a client with the mocked transport
        client = Client("http://127.0.0.1:8000/mcp")
        
        # Verify that the client was created with the correct URL
        mock_client_class.assert_called_once()
        assert mock_client_class.call_args[0][0] == "http://127.0.0.1:8000/mcp" 