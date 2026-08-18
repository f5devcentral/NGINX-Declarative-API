# NGINX Declarative API — MCP Server (contrib)

This contrib module implements a **Model Context Protocol (MCP) server** that lets
an LLM (Claude, or any other MCP-compatible client) drive the
[NGINX Declarative API](https://github.com/f5devcentral/NGINX-Declarative-API)
(branch `v5.7`) using natural language, instead of hand-writing JSON declarations
and calling the REST endpoints directly.

It does **not** reimplement the Declarative API. It is a thin, stateless MCP
process that sits in front of an already-running NGINX Declarative API instance and talks to it over HTTP.

```
LLM / MCP Client (Claude Desktop, Claude Code, claude.ai connector, etc.)
        │  MCP (stdio or streamable-HTTP)
        ▼
contrib/mcp  (this module)
        │  REST (HTTP/JSON, api-key or basic auth)
        ▼
NGINX Declarative API  (v5.7)  ── publishes to ──▶  NGINX Instance Manager / NGINX One
```

## Why this design

Rather than hard-coding the full v5.7 declaration JSON schema into the server
(which would drift every time the Declarative API adds a feature), this module:

1. Fetches the **live OpenAPI schema** from the running instance
   (`GET /openapi.json`) and exposes it to the LLM as an MCP resource/tool, so
   the model always grounds itself against the actual deployed version rather
   than a stale copy.
2. Exposes a small set of **curated, high-level tools** for the common
   declarative-config lifecycle (create, update, retrieve, delete, check async
   submission status, list), which map to the documented `v5.7` REST surface:
   - `POST   /v5.7/config`
   - `PATCH  /v5.7/config/{configUid}`
   - `GET    /v5.7/config/{configUid}`
   - `GET    /v5.7/config`
   - `DELETE /v5.7/config/{configUid}`
   - `GET    /v5.7/config/{configUid}/submission/{submissionUid}`
3. Exposes one **generic escape-hatch tool** (`call_declarative_api`) that lets
   the LLM issue an arbitrary method/path/body call for anything not covered by
   the curated tools (new v5.7 features, NGINX App Protect policy endpoints,
   certificate endpoints, developer portal endpoints, etc.), always validated
   against the live schema first.

This means the module keeps working even as the Declarative API evolves across
`v5.x` releases — only `NDAPI_VERSION` needs to change.

## Installation

### Option A — local (stdio transport, for Claude Desktop / Claude Code)

```bash
cd contrib/mcp
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # edit with your NDAPI endpoint + credentials
python -m nginx_declarative_api_mcp.server
```

Register it with Claude Desktop by adding the `mcpServers` entry from
[`examples/claude_desktop_config.stdio.json`](examples/claude_desktop_config.stdio.json)
to your `claude_desktop_config.json`.

### Option B — container (streamable-HTTP transport, shareable over the network)

Use [docker compose](/contrib/docker-compose)

The server then listens on `http://<host>:8800/mcp` and can be added as a remote MCP connector — see

* [`examples/claude_desktop_config.http.json`](examples/claude_desktop_config.http.json)
* [`examples/claude_desktop_config.stdio.json`](examples/claude_desktop_config.stdio.json)

and

* [`examples/antigravity_mcp_config.http.json`](examples/antigravity_mcp_config.http.json)
* [`examples/antigravity_mcp_config.stdio.json`](examples/antigravity_mcp_config.stdio.json)

## Using it from other MCP clients

See [`examples/README.md`](examples/README.md) for ready-to-edit config
snippets and setup notes for both Claude Desktop and Google Antigravity /
Gemini CLI, covering both stdio and Streamable HTTP transports:

| | stdio | Streamable HTTP |
|---|---|---|
| **Claude Desktop** | `examples/claude_desktop_config.stdio.json` | `examples/claude_desktop_config.http.json` (via `mcp-remote` bridge, or use Settings → Connectors) |
| **Antigravity / Gemini CLI** | `examples/antigravity_mcp_config.stdio.json` | `examples/antigravity_mcp_config.http.json` (native `serverUrl`) |


## MCP SDK compatibility

The `mcp` Python SDK released a breaking `2.0.0` on 2026-07-28: `FastMCP` was
renamed to `MCPServer` and moved from `mcp.server.fastmcp` to
`mcp.server.mcpserver` (decorator API — `@mcp.tool()`, `@mcp.prompt()` —
is unchanged). `server.py` and `tools.py` in this module detect which one is
installed at import time and use the matching class, so `pip install -r
requirements.txt` works whether it resolves to the current `2.x` line or an
older pinned `1.x` environment. No action needed either way.

## Configuration

All configuration is via environment variables (see `.env.example`):

| Variable                  | Default                 | Description                                                            |
|----------------------------|--------------------------|--------------------------------------------------------------------------|
| `NDAPI_BASE_URL`           | `http://localhost:5000` | Base URL of the running NGINX Declarative API instance                  |
| `NDAPI_VERSION`             | `v5.7`                   | API version path segment (`/v5.7/...`)                                  |
| `NDAPI_AUTH_MODE`           | `none`                   | `none`, `basic`, or `apikey`                                            |
| `NDAPI_USERNAME` / `NDAPI_PASSWORD` | —              | Used when `NDAPI_AUTH_MODE=basic`                                       |
| `NDAPI_API_KEY`             | —                        | Used when `NDAPI_AUTH_MODE=apikey` (sent as `Authorization: Bearer ...`) |
| `NDAPI_TIMEOUT_SECONDS`     | `30`                     | HTTP client timeout                                                     |
| `NDAPI_VERIFY_TLS`          | `true`                   | Set to `false` for self-signed lab certs                                |
| `MCP_TRANSPORT`             | `stdio`                  | `stdio` or `streamable-http`                                            |
| `MCP_HTTP_HOST`             | `0.0.0.0`                | Used when `MCP_TRANSPORT=streamable-http`                               |
| `MCP_HTTP_PORT`             | `8800`                   | Used when `MCP_TRANSPORT=streamable-http`                               |

## Tools exposed to the LLM

| Tool                          | Purpose                                                                             |
|--------------------------------|---------------------------------------------------------------------------------------|
| `get_api_schema`               | Fetch/refresh the live OpenAPI schema of the connected v5.7 instance                 |
| `list_declarations`            | List existing declaration UIDs known to the instance                                 |
| `get_declaration`               | Retrieve an existing declaration by `configUid`                                      |
| `create_declaration`            | Submit a brand-new JSON declaration (`POST /v5.7/config`)                            |
| `update_declaration`            | Patch/replace an existing declaration (`PATCH /v5.7/config/{configUid}`)             |
| `delete_declaration`            | Remove a declaration                                                                  |
| `get_submission_status`         | Poll the status of an asynchronous PATCH submission                                  |
| `validate_declaration_locally`  | JSON-syntax + required-field sanity check before submitting (fast fail)              |
| `call_declarative_api`          | Generic escape hatch: arbitrary method/path/body call against the v5.7 REST surface  |

A `system prompt` primer describing how declarations are structured
(`.declaration`, `.output.nms` / `.output.nginxone`, source-of-truth
references, synctime, etc.) is exposed as an MCP prompt (`declarative-api-primer`)
so the LLM can compose valid declarations from natural language without the
user having to paste the schema themselves.

## Example natural-language usage

> "Create an NGINX One config called `petstore` that reverse-proxies to
> `https://api.petstore.internal:8443`, rate-limits clients to 10 req/s, and
> publish it synchronously."

> "What's the status of submission `3f9a...` for config `petstore`?"

> "Update `petstore` to add a WAF policy fetched from
> `https://git.example.com/policies/petstore-waf.json` and re-check it every
> 300 seconds."

See [`examples/example_prompts.md`](examples/example_prompts.md) for more.

## Security notes

- This module only ever talks to the Declarative API endpoint you configure —
  it has no other network access.
- Credentials (`NDAPI_API_KEY` / `NDAPI_USERNAME` / `NDAPI_PASSWORD`) are read
  from the environment only; they are never logged or echoed back to the LLM.
- `call_declarative_api` is restricted to the configured `NDAPI_BASE_URL` and
  will refuse absolute URLs pointing elsewhere.
