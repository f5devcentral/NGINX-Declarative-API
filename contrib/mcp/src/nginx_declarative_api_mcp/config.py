"""Environment-driven configuration for the NGINX Declarative API MCP server."""
from __future__ import annotations

import os
from dataclasses import dataclass, field

from dotenv import load_dotenv

load_dotenv()


def _bool_env(name: str, default: bool) -> bool:
    val = os.getenv(name)
    if val is None:
        return default
    return val.strip().lower() in ("1", "true", "yes", "on")


@dataclass(frozen=True)
class Settings:
    ndapi_base_url: str = field(
        default_factory=lambda: os.getenv("NDAPI_BASE_URL", "http://localhost:5000").rstrip("/")
    )
    ndapi_version: str = field(default_factory=lambda: os.getenv("NDAPI_VERSION", "v5.7"))
    auth_mode: str = field(default_factory=lambda: os.getenv("NDAPI_AUTH_MODE", "none").lower())
    username: str = field(default_factory=lambda: os.getenv("NDAPI_USERNAME", ""))
    password: str = field(default_factory=lambda: os.getenv("NDAPI_PASSWORD", ""))
    api_key: str = field(default_factory=lambda: os.getenv("NDAPI_API_KEY", ""))
    timeout_seconds: float = field(
        default_factory=lambda: float(os.getenv("NDAPI_TIMEOUT_SECONDS", "30"))
    )
    verify_tls: bool = field(default_factory=lambda: _bool_env("NDAPI_VERIFY_TLS", True))

    mcp_transport: str = field(default_factory=lambda: os.getenv("MCP_TRANSPORT", "stdio"))
    mcp_http_host: str = field(default_factory=lambda: os.getenv("MCP_HTTP_HOST", "0.0.0.0"))
    mcp_http_port: int = field(default_factory=lambda: int(os.getenv("MCP_HTTP_PORT", "8800")))

    @property
    def api_root(self) -> str:
        """Base URL including the version segment, e.g. http://host:5000/v5.7"""
        return f"{self.ndapi_base_url}/{self.ndapi_version}"


def get_settings() -> Settings:
    return Settings()
