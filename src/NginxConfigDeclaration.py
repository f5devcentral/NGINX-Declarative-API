"""
JSON declaration format
"""

from __future__ import annotations
from typing import List, Optional
from pydantic import BaseModel


class OutputConfigMap(BaseModel):
    name: str
    filename: str


class Output(BaseModel):
    type: str
    configmap: Optional[OutputConfigMap]


class Tls(BaseModel):
    certificate: str
    key: str
    trusted_ca: Optional[str]
    ciphers: Optional[str]
    protocols: Optional[List[str]] = ["TLSv1.3"]


class Listen(BaseModel):
    address: Optional[str]
    http2: Optional[bool]
    tls: Optional[Tls]


class Log(BaseModel):
    access: Optional[str] = "/dev/null"
    error: Optional[str] = "/dev/null"


class RateLimit(BaseModel):
    profile: Optional[str] = ""
    httpcode: Optional[int] = 429
    burst: Optional[int] = 0
    delay: Optional[int] = 0


class Location(BaseModel):
    uri: str
    urimatch: Optional[str] = "prefix"
    upstream: Optional[str]
    caching: Optional[str]
    rate_limit: Optional[RateLimit]
    health_check: Optional[bool]
    snippet: Optional[str]


class Server(BaseModel):
    names: List[str]
    listen: Optional[Listen] = {}
    log: Optional[Log] = {}
    locations: Optional[List[Location]] = []
    snippet: Optional[str]


class Sticky(BaseModel):
    cookie: str
    expires: Optional[str]
    domain: Optional[str]
    path: Optional[str]


class Origin(BaseModel):
    server: str
    weight: Optional[int]
    max_fails: Optional[int]
    fail_timeout: Optional[str]
    max_conns: Optional[int]
    slow_start: Optional[str]
    backup: Optional[bool]


class Upstream(BaseModel):
    name: str
    origin: List[Origin]
    sticky: Optional[Sticky] = {}
    snippet: Optional[str] = ""


class ValidItem(BaseModel):
    codes: Optional[List[int]] = [200]
    ttl: Optional[str] = 60


class CachingItem(BaseModel):
    name: str
    key: str
    valid: Optional[List[ValidItem]] = []


class RateLimitItem(BaseModel):
    name: str
    key: str
    size: Optional[str] = "10m"
    rate: Optional[str] = "1r/s"


class NginxPlusApi(BaseModel):
    write: Optional[bool] = True
    listen: Optional[str] = "127.0.0.1:8080"
    allow_acl: Optional[str] = "127.0.0.1"


class Declaration(BaseModel):
    servers: Optional[List[Server]]
    upstreams: Optional[List[Upstream]]
    caching: Optional[List[CachingItem]]
    rate_limit: Optional[List[RateLimitItem]]
    nginx_plus_api: Optional[NginxPlusApi]


class ConfigDeclaration(BaseModel):
    output: Output
    declaration: Declaration
