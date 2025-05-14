# server.py
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("StreamableServer", stateless_http=True)

@mcp.tool()
def reverse_text(text: str) -> str:
    """Переворачивает введённый текст"""
    return text[::-1]

@mcp.resource("time://now")
def get_current_time() -> str:
    """Возвращает текущее время"""
    from datetime import datetime
    return datetime.now().isoformat()

if __name__ == "__main__":
    mcp.run(transport="streamable-http")
