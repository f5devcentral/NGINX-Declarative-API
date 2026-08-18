"""Entry point for the NGINX Declarative API MCP server.

Run directly:
    python -m nginx_declarative_api_mcp.server

Or via the console script (after `pip install -e .`):
    nginx-declarative-api-mcp
"""
from __future__ import annotations

import asyncio
import logging
import sys

try:
    # mcp SDK >= 2.0.0 (released 2026-07-28): FastMCP was renamed to
    # MCPServer and moved to mcp.server.mcpserver. See:
    # https://py.sdk.modelcontextprotocol.io/whats-new/
    from mcp.server.mcpserver import MCPServer as _MCPServerClass

    _SDK_MAJOR = 2
except ImportError:  # pragma: no cover - fallback for mcp SDK 1.x installs
    from mcp.server.fastmcp import FastMCP as _MCPServerClass

    _SDK_MAJOR = 1

from .client import DeclarativeAPIClient
from .config import get_settings
from .schema_cache import SchemaCache
from .tools import register

logging.basicConfig(level=logging.INFO, stream=sys.stderr)
logger = logging.getLogger("nginx_declarative_api_mcp")


def build_server() -> "_MCPServerClass":
    settings = get_settings()
    logger.info(
        "Starting NGINX Declarative API MCP server (target=%s, version=%s, "
        "transport=%s, mcp-sdk-major=%s)",
        settings.ndapi_base_url,
        settings.ndapi_version,
        settings.mcp_transport,
        _SDK_MAJOR,
    )

    mcp = _MCPServerClass(
        name="nginx-declarative-api",
        instructions=(
            "Tools for managing NGINX configuration via the NGINX Declarative "
            "API (v5.7) using natural language. Use the 'declarative-api-primer' "
            "prompt and the 'get_api_schema' tool to ground yourself before "
            "composing or modifying declarations."
        ),
    )

    client = DeclarativeAPIClient(settings)
    schema_cache = SchemaCache(client)
    register(mcp, client, schema_cache)

    return mcp


def main() -> None:
    settings = get_settings()
    mcp = build_server()

    if settings.mcp_transport == "streamable-http":
        if _SDK_MAJOR >= 2:
            # mcp>=2.0.0: host/port are passed to run(), not mcp.settings
            mcp.run(
                transport="streamable-http",
                host=settings.mcp_http_host,
                port=settings.mcp_http_port,
            )
        else:  # mcp 1.x: host/port configured via mcp.settings
            mcp.settings.host = settings.mcp_http_host
            mcp.settings.port = settings.mcp_http_port
            mcp.run(transport="streamable-http")
    else:
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
