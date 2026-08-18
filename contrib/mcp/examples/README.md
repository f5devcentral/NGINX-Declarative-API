# Example MCP client configurations

Four ready-to-edit config snippets, one per (client × transport) combination.
Copy the relevant `mcpServers` entry into your client's config file — don't
just drop these files in as-is, since each client's config also holds your
other MCP servers.

| File | Client | Transport | Server process |
|---|---|---|---|
| `claude_desktop_config.stdio.json` | Claude Desktop | stdio | Launched locally by Claude Desktop |
| `claude_desktop_config.http.json` | Claude Desktop | Streamable HTTP | Already running (container/remote host) |
| `antigravity_mcp_config.stdio.json` | Google Antigravity / Gemini CLI | stdio | Launched locally by Antigravity |
| `antigravity_mcp_config.http.json` | Google Antigravity / Gemini CLI | Streamable HTTP | Already running (container/remote host) |

## Claude Desktop — stdio

Use when you want Claude Desktop itself to start and stop the MCP server
process. Requires the module installed into a local venv first:

```bash
cd contrib/mcp
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt && pip install -e .
```

Edit `claude_desktop_config.stdio.json`'s `command` to the absolute path of
that venv's `python` (or `python.exe` on Windows), and set `NDAPI_API_KEY` (or
switch `NDAPI_AUTH_MODE` to `basic`/`none` to match your instance).

Config file location:
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`

## Claude Desktop — Streamable HTTP

Claude Desktop's config schema currently only accepts **stdio** server
entries — a bare `url`/`type: "http"` entry is not supported, and on some
Desktop versions is silently dropped (or corrupts the `mcpServers` block) on
the next save. There are two supported ways to reach a remote/HTTP instance
of this MCP server from Claude Desktop instead:

1. **Custom Connector (recommended, no file editing)** — in the app, go to
   **Settings → Connectors → Add custom connector** and enter
   `http://<host>:8800/mcp`.
2. **`mcp-remote` bridge (file-based, shown in `claude_desktop_config.http.json`)**
   — a small stdio↔HTTP adapter process. Requires Node.js/npm. First start the
   server itself as a remote/container process (see the root
   `contrib/mcp/README.md`, "Option B — container"), then point `mcp-remote`
   at its `/mcp` endpoint as shown in the file.

## Google Antigravity / Gemini CLI — stdio

Same idea as the Claude Desktop stdio case: Antigravity launches the process
locally. Edit `command` to your venv's `python`, and either fill in
`NDAPI_API_KEY` directly or, since Antigravity supports `${VAR}` substitution
in `env` blocks, export `NDAPI_API_KEY` in your shell and leave the
`${NDAPI_API_KEY}` reference as-is.

Config file location:
- Antigravity 2.x (shared IDE/CLI/SDK): `~/.gemini/config/mcp_config.json`
- Older Antigravity IDE: `~/.gemini/antigravity/mcp_config.json` (macOS/Linux)
  or `C:\Users\<you>\.gemini\antigravity\mcp_config.json` (Windows)
- Workspace-only: `.agents/mcp_config.json`

Edit via the app: `...` menu (Agent panel) → **MCP Servers** → **Manage MCP
Servers** → **View raw config**.

## Google Antigravity / Gemini CLI — Streamable HTTP

Unlike Claude Desktop, Antigravity natively supports remote servers via a
`serverUrl` field (note: `serverUrl`, not `url`) — no bridge process needed.
Start the server as a remote/container process (see the root
`contrib/mcp/README.md`, "Option B — container"), then point `serverUrl` at
its `/mcp` endpoint as shown in the file. If you put the server behind a
reverse proxy that itself requires auth, add a `headers` object alongside
`serverUrl` (see Antigravity's MCP docs for the exact field name in your
version).

## Verifying any of the four

After editing and restarting/reloading the client, ask its agent: *"List the
nginx-declarative-api MCP tools."* You should see `get_api_schema`,
`create_declaration`, `update_declaration`, `get_declaration`,
`delete_declaration`, `list_declarations`, `get_submission_status`,
`validate_declaration_locally`, and `call_declarative_api`.
