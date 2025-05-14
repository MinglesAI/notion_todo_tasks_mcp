import pytest
import os
import asyncio
from unittest.mock import patch, AsyncMock, MagicMock
from mcp.server.fastmcp import FastMCP
from notion_mcp.server import (
    mcp,
    list_tasks,
    add_task,
    complete_task,
    uncomplete_task,
    set_task_time,
    query_database,
    create_page,
    update_page
)

@pytest.fixture
def mock_env_vars():
    """Mock environment variables needed for tests."""
    with patch.dict(os.environ, {
        "NOTION_API_KEY": "test_api_key",
        "NOTION_DATABASE_ID": "test_database_id"
    }):
        yield

@pytest.fixture
def mock_httpx_client():
    """Mock httpx AsyncClient for API calls."""
    with patch("httpx.AsyncClient") as mock_client:
        mock_instance = AsyncMock()
        mock_response = MagicMock()
        mock_response.raise_for_status = AsyncMock()
        mock_response.json = MagicMock(return_value={"results": []})
        mock_instance.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
        mock_instance.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
        mock_instance.__aenter__.return_value.patch = AsyncMock(return_value=mock_response)
        mock_client.return_value = mock_instance
        yield mock_client

@pytest.mark.asyncio
async def test_query_database(mock_env_vars, mock_httpx_client):
    """Test query_database function."""
    result = await query_database()
    assert result == []
    
    # Verify API call was made correctly
    mock_instance = mock_httpx_client.return_value.__aenter__.return_value
    mock_instance.post.assert_called_once()
    args, kwargs = mock_instance.post.call_args
    assert "databases/test_database_id/query" in args[0]
    assert kwargs["headers"]["Authorization"] == "Bearer test_api_key"

@pytest.mark.asyncio
async def test_create_page(mock_env_vars, mock_httpx_client):
    """Test create_page function."""
    mock_properties = {
        "Task": {"title": [{"text": {"content": "Test task"}}]},
        "When": {"select": {"name": "today"}},
        "Checkbox": {"checkbox": False}
    }
    
    # Configure mock response for create_page
    mock_response = MagicMock()
    mock_response.raise_for_status = AsyncMock()
    mock_response.json = MagicMock(return_value={"id": "test_page_id", "properties": mock_properties})
    mock_httpx_client.return_value.__aenter__.return_value.post.return_value = mock_response
    
    result = await create_page(mock_properties)
    
    assert result["id"] == "test_page_id"
    # Verify API call was made correctly
    mock_instance = mock_httpx_client.return_value.__aenter__.return_value
    mock_instance.post.assert_called_once()
    args, kwargs = mock_instance.post.call_args
    assert "pages" in args[0]
    assert kwargs["json"]["parent"]["database_id"] == "test_database_id"
    assert kwargs["json"]["properties"] == mock_properties

@pytest.mark.asyncio
async def test_update_page(mock_env_vars, mock_httpx_client):
    """Test update_page function."""
    mock_properties = {"Checkbox": {"checkbox": True}}
    page_id = "test_page_id"
    
    # Configure mock response for update_page
    mock_response = MagicMock()
    mock_response.raise_for_status = AsyncMock()
    mock_response.json = MagicMock(return_value={
        "id": page_id,
        "properties": {
            "Task": {"title": [{"text": {"content": "Test task"}}]},
            "When": {"select": {"name": "today"}},
            "Checkbox": {"checkbox": True}
        }
    })
    mock_httpx_client.return_value.__aenter__.return_value.patch.return_value = mock_response
    
    result = await update_page(page_id, mock_properties)
    
    assert result["id"] == page_id
    assert result["properties"]["Checkbox"]["checkbox"] is True
    # Verify API call was made correctly
    mock_instance = mock_httpx_client.return_value.__aenter__.return_value
    mock_instance.patch.assert_called_once()
    args, kwargs = mock_instance.patch.call_args
    assert f"pages/{page_id}" in args[0]
    assert kwargs["json"]["properties"] == mock_properties

@pytest.mark.asyncio
async def test_list_tasks(mock_env_vars):
    """Test list_tasks function."""
    # Mock query_database to return sample tasks
    mock_tasks = [
        {
            "id": "task1",
            "properties": {
                "Task": {"title": [{"text": {"content": "Test task 1"}}]},
                "When": {"select": {"name": "today"}},
                "Checkbox": {"checkbox": False}
            }
        },
        {
            "id": "task2",
            "properties": {
                "Task": {"title": [{"text": {"content": "Test task 2"}}]},
                "When": {"select": {"name": "later"}},
                "Checkbox": {"checkbox": True}
            }
        }
    ]
    
    with patch("notion_mcp.server.query_database", return_value=mock_tasks):
        result = await list_tasks()
        
        assert len(result) == 2
        assert result[0].id == "task1"
        assert "Test task 1" in result[0].name
        assert "today" in result[0].description
        assert result[1].id == "task2"
        assert "Test task 2" in result[1].name
        assert "later" in result[1].description

@pytest.mark.asyncio
async def test_add_task(mock_env_vars):
    """Test add_task function."""
    # Mock create_page to return a sample task
    mock_task = {
        "id": "new_task_id",
        "properties": {
            "Task": {"title": [{"text": {"content": "New task"}}]},
            "When": {"select": {"name": "today"}},
            "Checkbox": {"checkbox": False}
        }
    }
    
    with patch("notion_mcp.server.create_page", return_value=mock_task):
        result = await add_task("New task", "today")
        
        assert len(result) == 1
        assert result[0].id == "new_task_id"
        assert "New task" in result[0].name
        assert "today" in result[0].description
        assert "False" in result[0].description

@pytest.mark.asyncio
async def test_complete_task(mock_env_vars):
    """Test complete_task function."""
    # Mock update_page to return an updated task
    mock_task = {
        "id": "task_id",
        "properties": {
            "Task": {"title": [{"text": {"content": "Test task"}}]},
            "When": {"select": {"name": "today"}},
            "Checkbox": {"checkbox": True}
        }
    }
    
    with patch("notion_mcp.server.update_page", return_value=mock_task):
        result = await complete_task("task_id")
        
        assert len(result) == 1
        assert result[0].id == "task_id"
        assert "Test task" in result[0].name
        assert "✅" in result[0].name
        assert "True" in result[0].description

@pytest.mark.asyncio
async def test_uncomplete_task(mock_env_vars):
    """Test uncomplete_task function."""
    # Mock update_page to return an updated task
    mock_task = {
        "id": "task_id",
        "properties": {
            "Task": {"title": [{"text": {"content": "Test task"}}]},
            "When": {"select": {"name": "today"}},
            "Checkbox": {"checkbox": False}
        }
    }
    
    with patch("notion_mcp.server.update_page", return_value=mock_task):
        result = await uncomplete_task("task_id")
        
        assert len(result) == 1
        assert result[0].id == "task_id"
        assert "Test task" in result[0].name
        assert "⬜" in result[0].name
        assert "False" in result[0].description

@pytest.mark.asyncio
async def test_set_task_time(mock_env_vars):
    """Test set_task_time function."""
    # Mock update_page to return an updated task
    mock_task = {
        "id": "task_id",
        "properties": {
            "Task": {"title": [{"text": {"content": "Test task"}}]},
            "When": {"select": {"name": "later"}},
            "Checkbox": {"checkbox": False}
        }
    }
    
    with patch("notion_mcp.server.update_page", return_value=mock_task):
        result = await set_task_time("task_id", "later")
        
        assert len(result) == 1
        assert result[0].id == "task_id"
        assert "Test task" in result[0].name
        assert "⚪" in result[0].name
        assert "later" in result[0].description

@pytest.mark.asyncio
async def test_streamable_http_server():
    """Test creating streamable_http_server."""
    # Mock the run_streamable_http_async method
    with patch.object(mcp, "run_streamable_http_async", AsyncMock()) as mock_run:
        from notion_mcp.server import main
        
        # Mock argparse to return specific arguments
        with patch("argparse.ArgumentParser.parse_args") as mock_args:
            mock_args.return_value.host = "127.0.0.1"
            mock_args.return_value.port = 8000
            mock_args.return_value.transport = "streamable_http"
            
            # Call the main function
            await main()
            
            # Verify that run_streamable_http_async was called with the correct arguments
            mock_run.assert_called_once_with(host="127.0.0.1", port=8000) 