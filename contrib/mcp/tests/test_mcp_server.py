"""Lightweight smoke tests using httpx's MockTransport -- no live NDAPI
instance required. Run with: pytest contrib/mcp/tests
"""
import httpx
import pytest

from nginx_declarative_api_mcp.client import DeclarativeAPIClient, DeclarativeAPIError
from nginx_declarative_api_mcp.config import Settings
from nginx_declarative_api_mcp.schema_cache import SchemaCache
from nginx_declarative_api_mcp.tools import register

try:
    from mcp.server.mcpserver import MCPServer as ServerClass
except ImportError:  # mcp SDK 1.x
    from mcp.server.fastmcp import FastMCP as ServerClass


def _client_with_transport(transport: httpx.MockTransport) -> DeclarativeAPIClient:
    settings = Settings(ndapi_base_url="http://ndapi.test", ndapi_version="v5.7")
    client = DeclarativeAPIClient(settings)
    client._client = httpx.AsyncClient(
        base_url=settings.ndapi_base_url, transport=transport
    )
    return client


@pytest.mark.asyncio
async def test_create_declaration_success():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/v5.7/config"
        assert request.method == "POST"
        return httpx.Response(200, json={"configUid": "abc123"})

    client = _client_with_transport(httpx.MockTransport(handler))
    result = await client.create_declaration({"declaration": {}, "output": {}})
    assert result["configUid"] == "abc123"
    await client.aclose()


@pytest.mark.asyncio
async def test_get_declaration_error_raises():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={"detail": "not found"})

    client = _client_with_transport(httpx.MockTransport(handler))
    with pytest.raises(DeclarativeAPIError) as exc_info:
        await client.get_declaration("missing")
    assert exc_info.value.status_code == 404
    await client.aclose()


@pytest.mark.asyncio
async def test_call_rejects_foreign_host():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={})

    client = _client_with_transport(httpx.MockTransport(handler))
    with pytest.raises(ValueError):
        await client.call("GET", "https://evil.example.com/steal")
    await client.aclose()


# -- end-to-end tests through the real MCP tool-dispatch layer ---------------


def _build_mcp_server(handler):
    settings = Settings(ndapi_base_url="http://ndapi.test", ndapi_version="v5.7")
    client = DeclarativeAPIClient(settings)
    client._client = httpx.AsyncClient(
        base_url=settings.ndapi_base_url, transport=httpx.MockTransport(handler)
    )
    schema_cache = SchemaCache(client)
    mcp = ServerClass(name="nginx-declarative-api")
    register(mcp, client, schema_cache)
    return mcp, client


@pytest.mark.asyncio
async def test_tools_register_on_server():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={})

    mcp, client = _build_mcp_server(handler)
    tools = await mcp.list_tools()
    names = {t.name for t in tools}
    assert {
        "get_api_schema",
        "list_declarations",
        "get_declaration",
        "create_declaration",
        "update_declaration",
        "delete_declaration",
        "get_submission_status",
        "validate_declaration_locally",
        "call_declarative_api",
    } <= names

    prompts = await mcp.list_prompts()
    assert any(p.name == "declarative-api-primer" for p in prompts)
    await client.aclose()


@pytest.mark.asyncio
async def test_create_declaration_end_to_end_via_call_tool():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/v5.7/config" and request.method == "POST":
            return httpx.Response(200, json={"configUid": "petstore-001"})
        return httpx.Response(404, json={"detail": "not found"})

    mcp, client = _build_mcp_server(handler)
    result = await mcp.call_tool(
        "create_declaration",
        {"declaration_json": {"declaration": {}, "output": {"nginxone": {}}}},
    )
    assert result.is_error is False
    assert "petstore-001" in result.content[0].text
    await client.aclose()


@pytest.mark.asyncio
async def test_call_declarative_api_tool_blocks_foreign_host():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={})

    mcp, client = _build_mcp_server(handler)
    result = await mcp.call_tool(
        "call_declarative_api", {"method": "GET", "path": "https://evil.example.com/x"}
    )
    assert "evil.example.com" in result.content[0].text
    assert "only" in result.content[0].text
    await client.aclose()
