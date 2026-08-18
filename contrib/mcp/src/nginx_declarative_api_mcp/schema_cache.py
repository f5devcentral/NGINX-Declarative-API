"""In-memory cache for the OpenAPI schema of the connected NGINX Declarative
API instance, so we don't re-fetch it on every tool call but the LLM can force
a refresh (e.g. after the operator upgrades the instance)."""
from __future__ import annotations

import time
from typing import Optional

from .client import DeclarativeAPIClient

_DEFAULT_TTL_SECONDS = 300


class SchemaCache:
    def __init__(self, client: DeclarativeAPIClient, ttl_seconds: int = _DEFAULT_TTL_SECONDS):
        self._client = client
        self._ttl = ttl_seconds
        self._schema: Optional[dict] = None
        self._fetched_at: float = 0.0

    async def get(self, force_refresh: bool = False) -> dict:
        now = time.time()
        stale = (now - self._fetched_at) > self._ttl
        if force_refresh or self._schema is None or stale:
            self._schema = await self._client.get_openapi_schema()
            self._fetched_at = now
        return self._schema
