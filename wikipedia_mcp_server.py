#!/usr/bin/env python3
"""
Wikipedia MCP Server
Provides Wikipedia search and article retrieval functionality via MCP protocol.
"""

import asyncio
import json
import sys
from typing import Any, Dict, List, Optional, Sequence

import wikipedia
from mcp.server.stdio import stdio_server
from mcp import types


# Define the Wikipedia tools
WIKIPEDIA_TOOLS = [
    types.Tool(
        name="wikipedia_search",
        description="Search Wikipedia articles by query",
        inputSchema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query for Wikipedia articles"
                },
                "results": {
                    "type": "integer",
                    "description": "Number of search results to return (default: 5)",
                    "default": 5
                }
            },
            "required": ["query"]
        }
    ),
    types.Tool(
        name="wikipedia_summary",
        description="Get summary of a Wikipedia article",
        inputSchema={
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Title of the Wikipedia article"
                },
                "sentences": {
                    "type": "integer",
                    "description": "Number of sentences in summary (default: 3)",
                    "default": 3
                }
            },
            "required": ["title"]
        }
    ),
    types.Tool(
        name="wikipedia_content",
        description="Get full content of a Wikipedia article",
        inputSchema={
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Title of the Wikipedia article"
                }
            },
            "required": ["title"]
        }
    ),
    types.Tool(
        name="wikipedia_page_info",
        description="Get detailed information about a Wikipedia page",
        inputSchema={
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Title of the Wikipedia article"
                }
            },
            "required": ["title"]
        }
    )
]


async def list_tools() -> List[types.Tool]:
    """List available Wikipedia tools."""
    return WIKIPEDIA_TOOLS


async def call_tool(name: str, arguments: Dict[str, Any]) -> Sequence[types.TextContent]:
    """Handle tool calls."""
    try:
        if name == "wikipedia_search":
            return await wikipedia_search(arguments)
        elif name == "wikipedia_summary":
            return await wikipedia_summary(arguments)
        elif name == "wikipedia_content":
            return await wikipedia_content(arguments)
        elif name == "wikipedia_page_info":
            return await wikipedia_page_info(arguments)
        else:
            return [types.TextContent(type="text", text=f"Unknown tool: {name}")]
    except Exception as e:
        return [types.TextContent(type="text", text=f"Error: {str(e)}")]


async def wikipedia_search(arguments: Dict[str, Any]) -> Sequence[types.TextContent]:
    """Search Wikipedia articles."""
    query = arguments.get("query", "")
    results_count = arguments.get("results", 5)
    
    try:
        search_results = wikipedia.search(query, results=results_count)
        
        if not search_results:
            return [types.TextContent(type="text", text=f"No results found for query: {query}")]
        
        result_text = f"Wikipedia search results for '{query}':\n\n"
        for i, title in enumerate(search_results, 1):
            result_text += f"{i}. {title}\n"
        
        return [types.TextContent(type="text", text=result_text)]
    except wikipedia.exceptions.DisambiguationError as e:
        suggestions = e.options[:5]
        result_text = f"Multiple articles found for '{query}'. Did you mean:\n\n"
        for i, suggestion in enumerate(suggestions, 1):
            result_text += f"{i}. {suggestion}\n"
        
        return [types.TextContent(type="text", text=result_text)]


async def wikipedia_summary(arguments: Dict[str, Any]) -> Sequence[types.TextContent]:
    """Get Wikipedia article summary."""
    title = arguments.get("title", "")
    sentences = arguments.get("sentences", 3)
    
    try:
        summary = wikipedia.summary(title, sentences=sentences)
        return [types.TextContent(type="text", text=f"Summary of '{title}':\n\n{summary}")]
    except wikipedia.exceptions.DisambiguationError as e:
        suggestions = e.options[:3]
        result_text = f"Multiple articles found for '{title}'. Did you mean:\n"
        for suggestion in suggestions:
            result_text += f"- {suggestion}\n"
        return [types.TextContent(type="text", text=result_text)]
    except wikipedia.exceptions.PageError:
        return [types.TextContent(type="text", text=f"No Wikipedia page found for '{title}'")]


async def wikipedia_content(arguments: Dict[str, Any]) -> Sequence[types.TextContent]:
    """Get full Wikipedia article content."""
    title = arguments.get("title", "")
    
    try:
        page = wikipedia.page(title)
        content = f"Title: {page.title}\n"
        content += f"URL: {page.url}\n\n"
        content += f"Content:\n{page.content}"
        
        return [types.TextContent(type="text", text=content)]
    except wikipedia.exceptions.DisambiguationError as e:
        suggestions = e.options[:3]
        result_text = f"Multiple articles found for '{title}'. Did you mean:\n"
        for suggestion in suggestions:
            result_text += f"- {suggestion}\n"
        return [types.TextContent(type="text", text=result_text)]
    except wikipedia.exceptions.PageError:
        return [types.TextContent(type="text", text=f"No Wikipedia page found for '{title}'")]


async def wikipedia_page_info(arguments: Dict[str, Any]) -> Sequence[types.TextContent]:
    """Get detailed Wikipedia page information."""
    title = arguments.get("title", "")
    
    try:
        page = wikipedia.page(title)
        
        info = f"Title: {page.title}\n"
        info += f"URL: {page.url}\n"
        info += f"Page ID: {page.pageid}\n"
        info += f"Categories: {', '.join(page.categories[:10])}\n"
        info += f"Links count: {len(page.links)}\n"
        info += f"References count: {len(page.references)}\n"
        
        if page.images:
            info += f"Images: {len(page.images)} found\n"
            info += f"First image: {page.images[0] if page.images else 'None'}\n"
        
        return [types.TextContent(type="text", text=info)]
    except wikipedia.exceptions.DisambiguationError as e:
        suggestions = e.options[:3]
        result_text = f"Multiple articles found for '{title}'. Did you mean:\n"
        for suggestion in suggestions:
            result_text += f"- {suggestion}\n"
        return [types.TextContent(type="text", text=result_text)]
    except wikipedia.exceptions.PageError:
        return [types.TextContent(type="text", text=f"No Wikipedia page found for '{title}'")]


async def main():
    """Main entry point."""
    from mcp.server.stdio import stdio_server
    
    async with stdio_server() as (read_stream, write_stream):
        from mcp.server import Server
        
        server = Server("wikipedia-mcp")
        
        @server.list_tools()
        async def handle_list_tools():
            return WIKIPEDIA_TOOLS
        
        @server.call_tool()
        async def handle_call_tool(name: str, arguments: Dict[str, Any]):
            return await call_tool(name, arguments)
        
        await server.run(
            read_stream,
            write_stream,
            types.InitializationOptions()
        )


if __name__ == "__main__":
    asyncio.run(main())