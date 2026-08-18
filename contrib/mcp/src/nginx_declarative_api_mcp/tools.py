"""Tool + prompt registration for the NGINX Declarative API MCP server.

Each tool is a thin wrapper around DeclarativeAPIClient. Tools return plain
JSON-serializable Python objects; the MCP layer takes care of formatting them
back to the LLM as tool results.
"""
from __future__ import annotations

from typing import Any, Optional

try:
    # mcp SDK >= 2.0.0
    from mcp.server.mcpserver import MCPServer as _ServerType
except ImportError:  # pragma: no cover - fallback for mcp SDK 1.x installs
    from mcp.server.fastmcp import FastMCP as _ServerType

from .client import DeclarativeAPIClient, DeclarativeAPIError
from .schema_cache import SchemaCache

REQUIRED_TOP_LEVEL_KEYS = ("declaration",)


def _error_payload(exc: DeclarativeAPIError) -> dict:
    return {
        "error": True,
        "status_code": exc.status_code,
        "url": exc.url,
        "detail": exc.body,
    }


def register(mcp: "_ServerType", client: DeclarativeAPIClient, schema_cache: SchemaCache) -> None:

    # -- schema introspection -------------------------------------------------

    @mcp.tool()
    async def get_api_schema(force_refresh: bool = False) -> dict:
        """Fetch the live OpenAPI schema of the connected NGINX Declarative API
        instance. Always call this before composing a declaration you are not
        already certain about, since the exact fields supported (upstreams,
        TLS, WAF, rate limiting, header manipulation, etc.) depend on the
        specific v5.7 build/patch level of the running instance.

        Args:
            force_refresh: bypass the local cache and re-fetch from the instance.
        """
        return await schema_cache.get(force_refresh=force_refresh)

    # -- declaration lifecycle -------------------------------------------------

    @mcp.tool()
    async def list_declarations() -> Any:
        """List declaration configs known to the connected NGINX Declarative
        API instance (their configUid and, where available, summary info)."""
        try:
            return await client.list_declarations()
        except DeclarativeAPIError as exc:
            return _error_payload(exc)

    @mcp.tool()
    async def get_declaration(config_uid: str) -> Any:
        """Retrieve the full JSON declaration currently stored for a given
        configUid.

        Args:
            config_uid: the declaration's unique identifier.
        """
        try:
            return await client.get_declaration(config_uid)
        except DeclarativeAPIError as exc:
            return _error_payload(exc)

    @mcp.tool()
    async def validate_declaration_locally(declaration_json: dict) -> dict:
        """Perform a fast, local sanity check of a declaration object before
        submitting it to the NGINX Declarative API. This does NOT replace
        server-side validation, but catches obvious mistakes (missing
        `.declaration`, missing `.output`, wrong types) before spending a
        network round trip.

        Args:
            declaration_json: the full declaration object you intend to submit,
                e.g. {"declaration": {...}, "output": {"nginxone": {...}}}.
        """
        problems: list[str] = []

        if not isinstance(declaration_json, dict):
            return {"valid": False, "problems": ["Top-level declaration must be a JSON object."]}

        for key in REQUIRED_TOP_LEVEL_KEYS:
            if key not in declaration_json:
                problems.append(f"Missing required top-level key: '{key}'")

        if "output" in declaration_json:
            output = declaration_json["output"]
            if not isinstance(output, dict) or not (
                "nms" in output or "nginxone" in output
            ):
                problems.append(
                    "'.output' should contain an 'nms' and/or 'nginxone' object "
                    "describing where to publish the configuration."
                )
        else:
            problems.append(
                "No '.output' block present -- the declaration will be validated "
                "but not published anywhere. Add '.output.nms' or "
                "'.output.nginxone' if publishing is intended."
            )

        return {"valid": len(problems) == 0, "problems": problems}

    @mcp.tool()
    async def create_declaration(declaration_json: dict) -> Any:
        """Submit a brand-new declaration to the NGINX Declarative API
        (POST /{version}/config). Returns the assigned configUid and, if
        '.output' was set, the publish result.

        Prefer calling `validate_declaration_locally` and, if unsure about the
        schema, `get_api_schema` first.

        Args:
            declaration_json: the full declaration object, e.g.
                {"declaration": {...}, "output": {"nginxone": {...}}}.
        """
        try:
            return await client.create_declaration(declaration_json)
        except DeclarativeAPIError as exc:
            return _error_payload(exc)

    @mcp.tool()
    async def update_declaration(config_uid: str, declaration_json: dict) -> Any:
        """Update an existing declaration (PATCH /{version}/config/{configUid}).
        Depending on '.output.*.synchronous', this may return immediately with
        a submissionUid to poll via `get_submission_status`, or block until the
        publish completes.

        Args:
            config_uid: the declaration's unique identifier.
            declaration_json: the full replacement declaration object.
        """
        try:
            return await client.update_declaration(config_uid, declaration_json)
        except DeclarativeAPIError as exc:
            return _error_payload(exc)

    @mcp.tool()
    async def delete_declaration(config_uid: str) -> Any:
        """Delete a declaration by configUid.

        Args:
            config_uid: the declaration's unique identifier.
        """
        try:
            return await client.delete_declaration(config_uid)
        except DeclarativeAPIError as exc:
            return _error_payload(exc)

    @mcp.tool()
    async def get_submission_status(config_uid: str, submission_uid: str) -> Any:
        """Check the status of an asynchronous PATCH submission
        (GET /{version}/config/{configUid}/submission/{submissionUid}). Use
        this after `update_declaration` returns a submissionUid because
        '.output.*.synchronous' was set to false.

        Args:
            config_uid: the declaration's unique identifier.
            submission_uid: the submission identifier returned by update_declaration.
        """
        try:
            return await client.get_submission_status(config_uid, submission_uid)
        except DeclarativeAPIError as exc:
            return _error_payload(exc)

    # -- generic escape hatch ---------------------------------------------------

    @mcp.tool()
    async def call_declarative_api(
        method: str,
        path: str,
        body: Optional[dict] = None,
        query: Optional[dict] = None,
    ) -> Any:
        """Generic escape hatch for any NGINX Declarative API v5.7 endpoint not
        covered by the dedicated tools above (e.g. developer portal endpoints,
        certificate management, App Protect policy endpoints). Always check
        `get_api_schema` first to confirm the path, method, and expected body
        actually exist on this instance. Only the configured NDAPI instance can
        be reached -- calls to any other host are rejected.

        Args:
            method: one of GET, POST, PUT, PATCH, DELETE.
            path: request path, e.g. "/v5.7/config/petstore/publish" (relative
                to NDAPI_BASE_URL) or a full URL previously returned by this API.
            body: optional JSON request body.
            query: optional query-string parameters.
        """
        try:
            return await client.call(method=method, path=path, body=body, query=query)
        except DeclarativeAPIError as exc:
            return _error_payload(exc)
        except ValueError as exc:
            return {"error": True, "detail": str(exc)}

    # -- prompt: grounding primer for composing declarations ---------------------

    @mcp.prompt(name="declarative-api-primer")
    def declarative_api_primer() -> str:
        """Primer explaining how NGINX Declarative API JSON declarations are
        structured, to help the LLM compose valid ones from natural language."""
        return (
            "You are composing JSON declarations for the NGINX Declarative API "
            "(v5.7). A declaration is a single JSON object with two top-level "
            "sections:\n\n"
            "- `.declaration`: describes the desired NGINX configuration -- "
            "upstreams, HTTP servers/locations, TCP/UDP streams, TLS "
            "certificates/keys (which may be inlined base64 or fetched from an "
            "HTTP(S) source of truth), rate limiting, header manipulation "
            "(`headers.to_server` / `headers.to_client`), client "
            "authentication, upstream authentication, and NGINX App Protect "
            "WAF policies.\n"
            "- `.output`: describes where and how to publish the resulting "
            "configuration -- `.output.nms` for NGINX Instance Manager and/or "
            "`.output.nginxone` for NGINX One Console. Each supports "
            "`synchronous` (block until publish completes vs. return a "
            "submissionUid to poll), `synctime` (seconds between re-checks of "
            "HTTP(S)-referenced sources of truth for GitOps auto-sync), "
            "`modules` (NGINX modules required, e.g. `ngx_http_app_protect_module`, "
            "`ngx_http_js_module`), and `certificates` (name/type/contents "
            "triples for TLS material to publish alongside the config).\n\n"
            "Before writing a declaration from scratch:\n"
            "1. Call `get_api_schema` to confirm the exact fields this "
            "instance supports (features vary slightly by v5.x patch level).\n"
            "2. Ask the user for anything required but unspecified (target "
            "backend addresses, hostnames, desired rate limits, whether to "
            "publish to NIM or NGINX One, synchronous vs asynchronous publish).\n"
            "3. Call `validate_declaration_locally` before `create_declaration` "
            "or `update_declaration`.\n"
            "4. If `.output.*.synchronous` is false, use "
            "`get_submission_status` to report back the eventual publish result."
        )
