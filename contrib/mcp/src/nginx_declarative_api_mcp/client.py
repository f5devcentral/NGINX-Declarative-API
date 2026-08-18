"""Thin async HTTP client for the NGINX Declarative API REST surface.

This module never encodes business logic about *what* a declaration should
contain -- it only knows how to talk HTTP to the endpoints documented for the
NGINX Declarative API (create/update/get/delete a declaration, check async
submission status, and fetch the live OpenAPI schema). Everything about the
*shape* of a v5.7 declaration is left to the LLM, grounded via the
`get_api_schema` tool and the `declarative-api-primer` prompt.
"""
from __future__ import annotations

import json
from typing import Any, Optional
from urllib.parse import urljoin, urlparse

import httpx

from .config import Settings


class DeclarativeAPIError(RuntimeError):
    def __init__(self, status_code: int, url: str, body: Any):
        self.status_code = status_code
        self.url = url
        self.body = body
        super().__init__(f"NGINX Declarative API returned {status_code} for {url}: {body}")


class DeclarativeAPIClient:
    """Async client bound to a single NGINX Declarative API instance."""

    def __init__(self, settings: Settings):
        self._settings = settings
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        auth = None

        if settings.auth_mode == "basic":
            auth = (settings.username, settings.password)
        elif settings.auth_mode == "apikey" and settings.api_key:
            headers["Authorization"] = f"Bearer {settings.api_key}"

        self._client = httpx.AsyncClient(
            base_url=settings.ndapi_base_url,
            headers=headers,
            auth=auth,
            timeout=settings.timeout_seconds,
            verify=settings.verify_tls,
        )

    async def aclose(self) -> None:
        await self._client.aclose()

    # -- schema -----------------------------------------------------------

    async def get_openapi_schema(self) -> dict:
        resp = await self._client.get("/openapi.json")
        self._raise_for_status(resp)
        return resp.json()

    # -- declaration lifecycle --------------------------------------------

    async def list_declarations(self) -> Any:
        resp = await self._client.get(f"/{self._settings.ndapi_version}/config")
        self._raise_for_status(resp)
        return self._body(resp)

    async def get_declaration(self, config_uid: str) -> Any:
        resp = await self._client.get(f"/{self._settings.ndapi_version}/config/{config_uid}")
        self._raise_for_status(resp)
        return self._body(resp)

    async def create_declaration(self, declaration: dict) -> Any:
        resp = await self._client.post(f"/{self._settings.ndapi_version}/config", json=declaration)
        self._raise_for_status(resp)
        return self._body(resp)

    async def update_declaration(self, config_uid: str, declaration: dict) -> Any:
        resp = await self._client.patch(
            f"/{self._settings.ndapi_version}/config/{config_uid}", json=declaration
        )
        self._raise_for_status(resp)
        return self._body(resp)

    async def delete_declaration(self, config_uid: str) -> Any:
        resp = await self._client.delete(f"/{self._settings.ndapi_version}/config/{config_uid}")
        self._raise_for_status(resp)
        return self._body(resp)

    async def get_submission_status(self, config_uid: str, submission_uid: str) -> Any:
        resp = await self._client.get(
            f"/{self._settings.ndapi_version}/config/{config_uid}/submission/{submission_uid}"
        )
        self._raise_for_status(resp)
        return self._body(resp)

    # -- generic escape hatch ----------------------------------------------

    async def call(
        self,
        method: str,
        path: str,
        body: Optional[dict] = None,
        query: Optional[dict] = None,
    ) -> Any:
        """Issue an arbitrary call against this instance only.

        `path` must be relative (e.g. "/v5.7/config/foo/publish") or an
        absolute URL whose origin matches NDAPI_BASE_URL -- anything else is
        rejected so the LLM cannot be tricked into calling other hosts.
        """
        if path.startswith("http://") or path.startswith("https://"):
            target_origin = f"{urlparse(path).scheme}://{urlparse(path).netloc}"
            allowed_origin = urlparse(self._settings.ndapi_base_url).scheme + "://" + urlparse(
                self._settings.ndapi_base_url
            ).netloc
            if target_origin != allowed_origin:
                raise ValueError(
                    f"Refusing to call host '{target_origin}': only "
                    f"'{allowed_origin}' (NDAPI_BASE_URL) is permitted."
                )
            url = path
        else:
            if not path.startswith("/"):
                path = "/" + path
            url = urljoin(self._settings.ndapi_base_url + "/", path.lstrip("/"))

        method = method.upper()
        if method not in ("GET", "POST", "PUT", "PATCH", "DELETE"):
            raise ValueError(f"Unsupported HTTP method: {method}")

        resp = await self._client.request(method, url, json=body, params=query)
        self._raise_for_status(resp)
        return self._body(resp)

    # -- helpers -------------------------------------------------------------

    @staticmethod
    def _body(resp: httpx.Response) -> Any:
        if not resp.content:
            return {"status_code": resp.status_code}
        try:
            return resp.json()
        except json.JSONDecodeError:
            return {"status_code": resp.status_code, "text": resp.text}

    @staticmethod
    def _raise_for_status(resp: httpx.Response) -> None:
        if resp.status_code >= 400:
            try:
                body = resp.json()
            except json.JSONDecodeError:
                body = resp.text
            raise DeclarativeAPIError(resp.status_code, str(resp.url), body)
