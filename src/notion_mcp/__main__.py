#!/usr/bin/env python3
from .server import mcp

# Точка входа для запуска через python -m notion_mcp
if __name__ == "__main__":
    import argparse
    import logging
    
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Run the Notion MCP server')
    parser.add_argument('--host', type=str, default='127.0.0.1', help='Host to bind the server to')
    parser.add_argument('--port', type=int, default=8000, help='Port to bind the server to')
    parser.add_argument('--transport', type=str, default='streamable-http', help='Transport to use (streamable-http or sse)')
    args = parser.parse_args()
    
    logger = logging.getLogger('notion_mcp')
    logger.info(f"Starting Notion MCP server on {args.host}:{args.port} with {args.transport} transport")
    
    # Запускаем синхронно, как в базовом примере
    if args.transport == 'streamable-http':
        logger.info(f"MCP API will be available at http://{args.host}:{args.port}/")
        mcp.run(transport=args.transport)
    else:
        mcp.run(transport="stdio")