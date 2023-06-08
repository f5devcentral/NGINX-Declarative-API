"""
JSON declaration format
"""

from __future__ import annotations
from typing import List, Optional
from pydantic import BaseModel, Extra, validator, root_validator


class OutputConfigMap(BaseModel, extra=Extra.forbid):
    name: str = ""
    namespace: Optional[str] = ""
    filename: str = ""


class OutputHttp(BaseModel, extra=Extra.forbid):
    url: str = ""


class NmsCertificate(BaseModel, extra=Extra.forbid):
    type: str
    name: str
    contents: str

    @root_validator()
    def check_type(cls, values):
        _type = values.get('type')

        valid = ['certificate', 'key']
        if _type not in valid:
            raise ValueError("Invalid certificate type '" + _type + "' must be one of " + str(valid))

        return values


class NmsPolicyVersion(BaseModel, extra=Extra.forbid):
    tag: str = ""
    displayName: Optional[str] = ""
    description: Optional[str] = ""
    contents: str = ""


class NmsPolicy(BaseModel, extra=Extra.forbid):
    type: str = ""
    name: str = ""
    active_tag: str = ""
    versions: Optional[List[NmsPolicyVersion]] = []

    @root_validator()
    def check_type(cls, values):
        _type = values.get('type')

        valid = ['app_protect']
        if _type not in valid:
            raise ValueError("Invalid policy type '" + _type + "' must be one of " + str(valid))

        return values


class AppProtectLogProfile(BaseModel, extra=Extra.forbid):
    name: str
    format: Optional[str] = "default"
    format_string: Optional[str] = ""
    type: Optional[str]= "blocked"
    max_request_size: Optional[str] = "any"
    max_message_size: Optional[str] = "5k"

    @root_validator()
    def check_type(cls, values):
        _type = values.get('type')
        _format = values.get('format')
        _format_string = values.get('format_string')

        valid = ['all', 'illegal', 'blocked']
        if _type not in valid:
            raise ValueError("Invalid NGINX App Protect log type '" + _type + "' must be one of " + str(valid))

        valid = ['default', 'grpc', 'arcsight', 'splunk', 'user-defined']
        if _format not in valid:
            raise ValueError("Invalid NGINX App Protect log format '" + _format + "' must be one of " + str(valid))

        if _format == 'user-defined' and _format_string == "":
            raise ValueError(f"NGINX App Protect log format {_format} requires format_string")

        return values


class LogProfile(BaseModel, extra=Extra.forbid):
    type: str
    app_protect: Optional[AppProtectLogProfile] = []

    @root_validator()
    def check_type(cls, values):
        _type, app_protect = values.get('type'), values.get('app_protect')

        valid = ['app_protect']
        if _type not in valid:
            raise ValueError("Invalid log profile type '" + _type + "' must be one of " + str(valid))

        isError = False
        if _type == 'app_protect':
            if app_protect is None:
                isError = True

        if isError:
            raise ValueError("Invalid log profile data for type '" + _type + "'")

        return values


class OutputNMS(BaseModel, extra=Extra.forbid):
    url: str = ""
    username: str = ""
    password: str = ""
    instancegroup: str = ""
    synctime: Optional[int] = 0
    modules: Optional[List[str]] = []
    certificates: Optional[List[NmsCertificate]] = []
    policies: Optional[List[NmsPolicy]] = []
    log_profiles: Optional[List[LogProfile]] = []


class Output(BaseModel, extra=Extra.forbid):
    type: str
    configmap: Optional[OutputConfigMap] = []
    http: Optional[OutputHttp] = []
    nms: Optional[OutputNMS] = []

    @root_validator()
    def check_type(cls, values):
        _type, configmap, http, nms = values.get('type'), values.get('configmap'), values.get(
            'http'), values.get('nms')

        valid = ['plaintext', 'json', 'configmap', 'http', 'nms']
        if _type not in valid:
            raise ValueError("Invalid output type '" + _type + "' must be one of " + str(valid))

        isError = False

        if _type == 'configmap' and not configmap:
            isError = True
        elif _type == 'http' and not http:
            isError = True
        elif _type == 'nms' and not nms:
            isError = True

        if isError:
            raise ValueError("Invalid output data for type '" + _type + "'")

        return values


class OcspStapling(BaseModel, extra=Extra.forbid):
    enabled: Optional[bool] = False
    verify: Optional[bool] = False
    responder: Optional[str] = ""


class Ocsp(BaseModel, extra=Extra.forbid):
    enabled: Optional[str] = "off"
    responder: Optional[str] = ""


class Mtls(BaseModel, extra=Extra.forbid):
    enabled: Optional[str] = "off"
    trusted_ca_certificates: str = ""

    @root_validator()
    def check_type(cls, values):
        _enabled = values.get('enabled')

        valid = ['on', 'off', 'optional', 'optional_no_ca']
        if _enabled not in valid:
            raise ValueError("Invalid mTLS type '" + _enabled + "' must be one of " + str(valid))

        return values


class Tls(BaseModel, extra=Extra.forbid):
    certificate: str = ""
    key: str = ""
    ciphers: Optional[str] = ""
    protocols: Optional[List[str]] = []
    mtls: Optional[Mtls] = []
    ocsp: Optional[Ocsp] = []
    stapling: Optional[OcspStapling] = []


class Listen(BaseModel, extra=Extra.forbid):
    address: Optional[str] = ""
    http2: Optional[bool] = False
    tls: Optional[Tls] = []


class ListenL4(BaseModel, extra=Extra.forbid):
    address: Optional[str]
    protocol: Optional[str] = "tcp"
    tls: Optional[Tls] = []

    @root_validator()
    def check_type(cls, values):
        protocol = values.get('protocol')
        tls = values.get('tls')

        valid = ['tcp', 'udp']
        if protocol not in valid:
            raise ValueError("Invalid protocol '" + protocol + "'")

        if protocol != 'tcp' and tls and tls.certificate:
            raise ValueError("TLS termination over UDP is not supported")

        return values


class Log(BaseModel, extra=Extra.forbid):
    access: Optional[str] = ""
    error: Optional[str] = ""


class RateLimit(BaseModel, extra=Extra.forbid):
    profile: Optional[str] = ""
    httpcode: Optional[int] = 429
    burst: Optional[int] = 0
    delay: Optional[int] = 0


class HealthCheck(BaseModel, extra=Extra.forbid):
    enabled: Optional[bool] = False
    uri: Optional[str]
    interval: Optional[int]
    fails: Optional[int]
    passes: Optional[int]


class AppProtectLog(BaseModel, extra=Extra.forbid):
    enabled: Optional[bool] = False
    profile_name: Optional[str] = ""
    destination: Optional[str] = ""


class AppProtect(BaseModel, extra=Extra.forbid):
    enabled: Optional[bool] = False
    policy: str = ""
    log: AppProtectLog = ""


class Location(BaseModel, extra=Extra.forbid):
    uri: str
    urimatch: Optional[str] = "prefix"
    upstream: Optional[str] = ""
    caching: Optional[str] = ""
    rate_limit: Optional[RateLimit] = ""
    health_check: Optional[HealthCheck] = ""
    app_protect: Optional[AppProtect] = []
    snippet: Optional[str] = ""

    @root_validator()
    def check_type(cls, values):
        urimatch = values.get('urimatch')

        valid = ['prefix', 'exact', 'regex', 'iregex', 'best']
        if urimatch not in valid:
            raise ValueError("Invalid URI match type '" + urimatch + "' must be one of " + str(valid))

        return values


class Server(BaseModel, extra=Extra.forbid):
    name: str
    names: Optional[List[str]] = []
    resolver: Optional[str] = ""
    listen: Optional[Listen] = []
    log: Optional[Log] = []
    locations: Optional[List[Location]] = []
    app_protect: Optional[AppProtect] = []
    snippet: Optional[str] = ""


class L4Server(BaseModel, extra=Extra.forbid):
    name: str
    listen: Optional[ListenL4] = []
    upstream: Optional[str] = ""
    snippet: Optional[str] = ""


class Sticky(BaseModel, extra=Extra.forbid):
    cookie: str = ""
    expires: Optional[str] = ""
    domain: Optional[str] = ""
    path: Optional[str] = ""


class Origin(BaseModel, extra=Extra.forbid):
    server: str
    weight: Optional[int] = 1
    max_fails: Optional[int] = 1
    fail_timeout: Optional[str] = "10s"
    max_conns: Optional[int] = 0
    slow_start: Optional[str] = "0"
    backup: Optional[bool] = False


class L4Origin(BaseModel, extra=Extra.forbid):
    server: str
    weight: Optional[int] = 1
    max_fails: Optional[int] = 1
    fail_timeout: Optional[str] = ""
    max_conns: Optional[int] = 0
    slow_start: Optional[str] = ""
    backup: Optional[bool] = False


class Upstream(BaseModel, extra=Extra.forbid):
    name: str
    origin: Optional[List[Origin]] = []
    sticky: Optional[Sticky] = {}
    snippet: Optional[str] = ""


class L4Upstream(BaseModel, extra=Extra.forbid):
    name: str
    origin: Optional[List[L4Origin]] = []
    snippet: Optional[str] = ""


class ValidItem(BaseModel, extra=Extra.forbid):
    codes: Optional[List[int]] = [200]
    ttl: Optional[str] = 60


class CachingItem(BaseModel, extra=Extra.forbid):
    name: str
    key: str
    size: Optional[str] = "10m"
    valid: Optional[List[ValidItem]] = []


class RateLimitItem(BaseModel, extra=Extra.forbid):
    name: str
    key: str
    size: Optional[str] = ""
    rate: Optional[str] = ""


class NginxPlusApi(BaseModel, extra=Extra.forbid):
    write: Optional[bool] = False
    listen: Optional[str] = ""
    allow_acl: Optional[str] = ""


class MapEntry(BaseModel, extra=Extra.forbid):
    key: str
    keymatch: str
    value: str

    @root_validator()
    def check_type(cls, values):
        keymatch = values.get('keymatch')

        valid = ['exact', 'regex', 'iregex']
        if keymatch not in valid:
            raise ValueError("Invalid key match type '" + keymatch + "' must be one of " + str(valid))

        return values


class Map(BaseModel, extra=Extra.forbid):
    match: str
    variable: str
    entries: Optional[List[MapEntry]] = []


class Layer4(BaseModel, extra=Extra.forbid):
    servers: Optional[List[L4Server]] = []
    upstreams: Optional[List[L4Upstream]] = []


class Http(BaseModel, extra=Extra.forbid):
    servers: Optional[List[Server]] = []
    upstreams: Optional[List[Upstream]] = []
    caching: Optional[List[CachingItem]] = []
    rate_limit: Optional[List[RateLimitItem]] = []
    nginx_plus_api: Optional[NginxPlusApi] = []
    maps: Optional[List[Map]] = []
    snippet: Optional[str] = ""


class Declaration(BaseModel, extra=Extra.forbid):
    layer4: Optional[Layer4] = []
    http: Optional[Http] = []


class ConfigDeclaration(BaseModel, extra=Extra.forbid):
    output: Output
    declaration: Optional[Declaration]
