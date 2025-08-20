"""
JSON declaration structure
"""

from __future__ import annotations
from typing import List, Optional
from pydantic import BaseModel, model_validator

import re

# Regexp to check names
alphanumRegexp = r'^[a-zA-Z0-9\ \-\_]+$'


class NmsCertificate(BaseModel, extra="forbid"):
    type: str
    name: str
    contents: Optional[ObjectFromSourceOfTruth] = {}

    @model_validator(mode='after')
    def check_type(self) -> 'NmsCertificate':
        _type = self.type

        valid = ['certificate', 'key']
        if _type not in valid:
            raise ValueError(f"Invalid certificate type [{_type}] must be one of {str(valid)}")

        return self


class NGINXPolicyVersion(BaseModel, extra="forbid"):
    tag: str = ""
    displayName: Optional[str] = ""
    description: Optional[str] = ""
    contents: Optional[ObjectFromSourceOfTruth] = {}


class NGINXPolicy(BaseModel, extra="forbid"):
    type: str = ""
    name: str = "" # Name must be identical to the policy name used in the App Protect policy JSON file
    active_tag: str = ""
    versions: Optional[List[NGINXPolicyVersion]] = []

    @model_validator(mode='after')
    def check_type(self) -> 'NGINXPolicy':
        _type = self.type

        valid = ['app_protect']
        if _type not in valid:
            raise ValueError(f"Invalid policy type [{_type}] must be one of {str(valid)}")

        return self


class AppProtectLogProfile(BaseModel, extra="forbid"):
    name: str
    format: Optional[str] = "default"
    format_string: Optional[str] = ""
    type: Optional[str] = "blocked"
    max_request_size: Optional[str] = "any"
    max_message_size: Optional[str] = "5k"

    @model_validator(mode='after')
    def check_type(self) -> 'AppProtectLogProfile':
        _type, _format, _format_string = self.type, self.format, self.format_string

        valid = ['all', 'illegal', 'blocked']
        if _type not in valid:
            raise ValueError(f"Invalid NGINX App Protect log type [{_type}] must be one of {str(valid)}")

        valid = ['default', 'grpc', 'arcsight', 'splunk', 'user-defined']
        if _format not in valid:
            raise ValueError(f"Invalid NGINX App Protect log format [{_format}] must be one of {str(valid)}")

        if _format == 'user-defined' and _format_string == "":
            raise ValueError(f"NGINX App Protect log format {_format} requires format_string")

        return self


class LogProfile(BaseModel, extra="forbid"):
    type: str
    app_protect: Optional[AppProtectLogProfile] = {}

    @model_validator(mode='after')
    def check_type(self) -> 'LogProfile':
        _type, app_protect = self.type, self.app_protect

        valid = ['app_protect']
        if _type not in valid:
            raise ValueError(f"Invalid log profile type [{_type}] must be one of {str(valid)}")

        isError = False
        if _type == 'app_protect':
            if app_protect is None:
                isError = True

        if isError:
            raise ValueError(f"Invalid log profile data for type [{_type}]")

        return self


class OutputNMS(BaseModel, extra="forbid"):
    url: str = ""
    username: str = ""
    password: str = ""
    instancegroup: str = ""
    synctime: Optional[int] = 0
    modules: Optional[List[str]] = []
    certificates: Optional[List[NmsCertificate]] = []
    policies: Optional[List[NGINXPolicy]] = []
    log_profiles: Optional[List[LogProfile]] = []


class OutputNGINXOne(BaseModel, extra="forbid"):
    url: str = ""
    namespace: str = ""
    token: str = ""
    configsyncgroup: str = ""
    synctime: Optional[int] = 0
    modules: Optional[List[str]] = []
    certificates: Optional[List[NmsCertificate]] = []
    policies: Optional[List[NGINXPolicy]] = []
    log_profiles: Optional[List[LogProfile]] = []


class License(BaseModel, extra="forbid"):
    endpoint: Optional[str] = "product.connect.nginx.com"
    token: Optional[str] = ""
    ssl_verify: bool = True
    grace_period: bool = False


class Output(BaseModel, extra="forbid"):
    type: str
    synchronous: bool = True
    license: Optional[License] = {}
    nms: Optional[OutputNMS] = {}
    nginxone: Optional[OutputNGINXOne] = {}

    @model_validator(mode='after')
    def check_type(self) -> 'Output':
        _type,nms, nginxone = self.type, self.nms, self.nginxone

        valid = ['nms', 'nginxone']
        if _type not in valid:
            raise ValueError(f"Invalid output type [{_type}] must be one of {str(valid)}")

        isError = False

        if _type == 'nms' and not nms:
            isError = True
        elif _type == 'nginxone' and not nginxone:
            isError = True

        if isError:
            raise ValueError(f"Invalid output data for type [{_type}]")

        return self


class OcspStapling(BaseModel, extra="forbid"):
    enabled: Optional[bool] = False
    verify: Optional[bool] = False
    responder: Optional[str] = ""


class Ocsp(BaseModel, extra="forbid"):
    enabled: Optional[str] = "off"
    responder: Optional[str] = ""

    @model_validator(mode='after')
    def check_type(self) -> 'Ocsp':
        _enabled = self.enabled

        valid = ['on', 'off', 'leaf']
        if _enabled not in valid:
            raise ValueError(f"Invalid OCSP validation type type [{_enabled}] must be one of {str(valid)}")

        return self


class AuthClientMtls(BaseModel, extra="forbid"):
    enabled: Optional[str] = "off"
    client_certificates: str = ""
    trusted_ca_certificates: Optional[str] = ""
    ocsp: Optional[Ocsp] = {}
    stapling: Optional[OcspStapling] = {}

    @model_validator(mode='after')
    def check_type(self) -> 'AuthClientMtls':
        _enabled = self.enabled

        valid = ['on', 'off', 'optional', 'optional_no_ca']
        if _enabled not in valid:
            raise ValueError(f"Invalid mTLS type [{_enabled}] must be one of {str(valid)}")

        return self


class Tls(BaseModel, extra="forbid"):
    certificate: str = ""
    key: str = ""
    ciphers: Optional[str] = ""
    protocols: Optional[List[str]] = []
    authentication: Optional[LocationAuth] = {}


class Listen(BaseModel, extra="forbid"):
    address: Optional[str] = ""
    http2: Optional[bool] = False
    tls: Optional[Tls] = {}


class ListenL4(BaseModel, extra="forbid"):
    address: Optional[str] = ""
    protocol: Optional[str] = "tcp"
    tls: Optional[Tls] = {}

    @model_validator(mode='after')
    def check_type(self) -> 'ListenL4':
        protocol, tls = self.protocol, self.tls

        valid = ['tcp', 'udp']
        if protocol not in valid:
            raise ValueError(f"Invalid protocol [{protocol}] must be one of {str(valid)}")

        if protocol != 'tcp' and tls and tls.certificate:
            raise ValueError("TLS termination over UDP is not supported")

        return self


class Log(BaseModel, extra="forbid"):
    access: Optional[LogAccess] = {}
    error: Optional[LogError] = {}


class LogAccess(BaseModel, extra="forbid"):
    destination: str
    format: Optional[str] = "combined"
    condition: Optional[str] = ""


class LogError(BaseModel, extra="forbid"):
    destination: str
    level: Optional[str] = "info"

    @model_validator(mode='after')
    def check_type(self) -> 'LogError':
        level = self.level

        valid = ['debug','info','notice','warn','error','crit','alert','emerg']
        if level not in valid:
            raise ValueError(f"Invalid error log level [{level}] must be one of {str(valid)}")

        return self

class RateLimit(BaseModel, extra="forbid"):
    profile: Optional[str] = ""
    httpcode: Optional[int] = 429
    burst: Optional[int] = 0
    delay: Optional[int] = 0


class LocationAuthClient(BaseModel, extra="forbid"):
    profile: Optional[str] = ""


class LocationAuthServer(BaseModel, extra="forbid"):
    profile: Optional[str] = ""


class LocationHeaderToClient(BaseModel, extra="forbid"):
    add: Optional[List[HTTPHeader]] = []
    delete: Optional[List[str]] = []
    replace: Optional[List[HTTPHeader]] = []


class LocationHeaderToServer(BaseModel, extra="forbid"):
    set: Optional[List[HTTPHeader]] = []
    delete: Optional[List[str]] = []


class HTTPHeader(BaseModel, extra="forbid"):
    name: str = ""
    value: str = ""


class LocationAuth(BaseModel, extra="forbid"):
    client: Optional[List[LocationAuthClient]] = []
    server: Optional[List[LocationAuthServer]] = []


class AuthorizationProfileReference(BaseModel, extra="forbid"):
    profile: Optional[str] = ""

class LocationHeaders(BaseModel, extra="forbid"):
    to_server: Optional[LocationHeaderToServer] = {}
    to_client: Optional[LocationHeaderToClient] = {}

class RateLimitApiGw(BaseModel, extra="forbid"):
    profile: Optional[str] = ""
    httpcode: Optional[int] = 429
    burst: Optional[int] = 0
    delay: Optional[int] = 0
    enforceOnPaths: Optional[bool] = True
    paths: Optional[List[str]] = []

class APIGatewayAuthentication(BaseModel, extra="forbid"):
    client: Optional[List[LocationAuthClient]] = []
    enforceOnPaths: Optional[bool] = True
    paths: Optional[List[str]] = []


class APIGatewayAuthorization(BaseModel, extra="forbid"):
    profile: str
    enforceOnPaths: Optional[bool] = True
    paths: Optional[List[str]] = []


class APIGatewayCache(BaseModel, extra="forbid"):
    profile: str
    key: Optional[str] = "$scheme$proxy_host$request_uri";
    validity: Optional[List[CacheObjectTTL]] = []
    enforceOnPaths: Optional[bool] = True
    paths: Optional[List[str]] = []

    @model_validator(mode='after')
    def check_type(self) -> 'APIGatewayCache':
        profile = self.profile

        if not re.search(alphanumRegexp,profile):
            raise ValueError(f"Invalid cache item [{profile}] should match regexp {alphanumRegexp}")

        return self


class AuthClientJWT(BaseModel, extra="forbid"):
    realm: str = "JWT Authentication"
    key: str = ""
    cachetime: Optional[int] = 0
    jwt_type: str = "signed"
    token_location: Optional[str] = ""

    @model_validator(mode='after')
    def check_type(self) -> 'AuthClientJWT':
        jwt_type, key = self.jwt_type, self.key

        #if not key.strip():
        #    raise ValueError(f"Invalid: JWT key must not be empty")

        valid = ['signed', 'encrypted', 'nested']
        if jwt_type not in valid:
            raise ValueError(f"Invalid JWT type [{jwt_type}] must be one of {str(valid)}")

        return self


class AcmeIssuers(BaseModel, extra="forbid"):
    uri: str = ""
    account_key: Optional[str] = ""
    contact: Optional[str] = ""
    ssl_trusted_certificate: Optional[ObjectFromSourceOfTruth] = {}
    ssl_verify: Optional[bool] = False
    state_path: Optional[str] = ""
    accept_terms_of_service: Optional[bool] = False
    acme_shared_zone: Optional[str] = ""


class AuthClientOIDC(BaseModel, extra="forbid"):
    issuer: str = ""
    client_id: str = ""
    client_secret: str = ""
    config_url: Optional[str] = ""
    cookie_name: Optional[str] = ""
    extra_auth_args: Optional[str] = ""
    redirect_uri: Optional[str] = "/oidc_callback"
    logout_uri: Optional[str] = ""
    post_logout_uri: Optional[str] = ""
    logout_token_hint: Optional[bool] = False
    scope: Optional[str] = "openid"
    session_store: Optional[str] = ""
    session_timeout: Optional[str] = "8h"
    ssl_crl: Optional[str] = ""
    ssl_trusted_certificate: Optional[str] = ""
    userinfo: Optional[bool] = False


class AuthServerToken(BaseModel, extra="forbid"):
    token: str = ""
    type: Optional[str] = ""
    location: Optional[str] = ""
    username: Optional[str] = ""
    password: Optional[str] = ""

    @model_validator(mode='after')
    def check_type(self) -> 'AuthServerToken':
        tokentype, location, username, password = self.type.lower(), self.location, self.username, self.password

        valid = ['bearer', 'header', 'basic', '']
        if tokentype not in valid:
            raise ValueError(f"Invalid token type [{tokentype}] must be one of {str(valid)}")

        if tokentype in ['header'] and location == "":
            raise ValueError(f"Empty location for [{tokentype}] token")

        if tokentype in ['basic'] and (username == "" or password == ""):
            raise ValueError(f"Missing username/password for [{tokentype}] token")

        return self


class AuthServerMtls(BaseModel, extra="forbid"):
    certificate: str = ""
    key: str = ""


class JwtAuthZNameValue(BaseModel, extra="forbid"):
    name: str
    value: List[str]
    errorcode: Optional[int] = 401

    @model_validator(mode='after')
    def check_type(self) -> 'JwtAuthZNameValue':
        errorcode = self.errorcode

        valid = [401, 403]
        if errorcode not in valid:
            raise ValueError(f"Invalid errorcode [{errorcode}] must be one of {str(valid)}")

        return self


class AuthorizationJWT(BaseModel, extra="forbid"):
    claims: List[JwtAuthZNameValue]


class HealthCheck(BaseModel, extra="forbid"):
    enabled: Optional[bool] = False
    uri: Optional[str] = "/"
    interval: Optional[int] = 5
    fails: Optional[int] = 1
    passes: Optional[int] = 1


class AppProtectLog(BaseModel, extra="forbid"):
    enabled: Optional[bool] = False
    profile_name: Optional[str] = ""
    destination: Optional[str] = ""


class AppProtect(BaseModel, extra="forbid"):
    enabled: Optional[bool] = False
    policy: str = ""
    log: AppProtectLog = {}


class Location(BaseModel, extra="forbid"):
    uri: str
    urimatch: Optional[str] = "prefix"
    upstream: Optional[str] = ""
    log: Optional[Log] = {}
    apigateway: Optional[APIGateway] = {}
    caching: Optional[str] = ""
    rate_limit: Optional[RateLimit] = {}
    health_check: Optional[HealthCheck] = {}
    app_protect: Optional[AppProtect] = {}
    snippet: Optional[ObjectFromSourceOfTruth] = {}
    authentication: Optional[LocationAuth] = {}
    authorization: Optional[AuthorizationProfileReference] = {}
    headers: Optional[LocationHeaders] = {}
    njs: Optional[List[NjsHookLocation]] = []
    cache: Optional[CacheItem] = {}

    @model_validator(mode='after')
    def check_type(self) -> 'Location':
        urimatch = self.urimatch
        upstream = self.upstream

        valid = ['prefix', 'exact', 'regex', 'iregex', 'best']
        if urimatch not in valid:
            raise ValueError(f"Invalid URI match type [{urimatch}] must be one of {str(valid)}")

        prefixes = ["http://", "https://"]
        if upstream != "" and not upstream.lower().startswith(tuple(prefixes)):
            raise ValueError(f"Upstream must start with one of {str(prefixes)}")

        return self


class ObjectFromSourceOfTruth(BaseModel, extra="forbid"):
    content: str = ""
    authentication: Optional[List[LocationAuthServer]] = []


class NjsHook_js_body_filter(BaseModel, extra="forbid"):
    buffer_type: Optional[str] = ""


class NjsHook_js_periodic(BaseModel, extra="forbid"):
    interval: Optional[str] = ""
    jitter: Optional[int] = 0
    worker_affinity: Optional[str] = ""


class NjsHook_js_preload_object(BaseModel, extra="forbid"):
    file: str


class NjsHook_js_set(BaseModel, extra="forbid"):
    variable: str


class NjsHookHttpServerDetails(BaseModel, extra="forbid"):
    type: str
    js_preload_object: Optional[NjsHook_js_preload_object] = {}
    js_set: Optional[NjsHook_js_set] = {}

    @model_validator(mode='after')
    def check_type(self) -> 'NjsHookHttpServerDetails':
        _type = self.type

        valid = ['js_preload_object', 'js_set']
        if _type not in valid:
            raise ValueError(f"Invalid hook [{_type}] must be one of {str(valid)}")

        return self


class NjsHookLocationDetails(BaseModel, extra="forbid"):
    type: str
    js_preload_object: Optional[NjsHook_js_preload_object] = {}
    js_set: Optional[NjsHook_js_set] = {}
    js_body_filter: Optional[NjsHook_js_body_filter] = {}
    js_periodic: Optional[NjsHook_js_periodic] = {}

    @model_validator(mode='after')
    def check_type(self) -> 'NjsHookLocationDetails':
        _type = self.type

        valid = ['js_body_filter', 'js_content', 'js_header_filter', 'js_periodic', 'js_preload_object', 'js_set']
        if _type not in valid:
            raise ValueError(f"Invalid hook [{_type}] must be one of {str(valid)}")

        return self


class NjsHookHttpServer(BaseModel, extra="forbid"):
    hook: NjsHookHttpServerDetails
    profile: str
    function: str


class NjsHookLocation(BaseModel, extra="forbid"):
    hook: NjsHookLocationDetails
    profile: str
    function: str


class Server(BaseModel, extra="forbid"):
    name: str
    names: Optional[List[str]] = []
    resolver: Optional[str] = ""
    listen: Optional[Listen] = {}
    log: Optional[Log] = {}
    locations: Optional[List[Location]] = []
    app_protect: Optional[AppProtect] = {}
    snippet: Optional[ObjectFromSourceOfTruth] = {}
    headers: Optional[LocationHeaders] = {}
    njs: Optional[List[NjsHookHttpServer]] = []
    authentication: Optional[LocationAuth] = {}
    authorization: Optional[AuthorizationProfileReference] = {}
    cache: Optional[CacheItem] = {}

    @model_validator(mode='after')
    def check_type(self) -> 'Server':
        name = self.name

        if not re.search(alphanumRegexp,name):
            raise ValueError(f"Invalid name [{name}] should match regexp {alphanumRegexp}")

        return self


class L4Server(BaseModel, extra="forbid"):
    name: str
    resolver: Optional[str] = ""
    listen: Optional[ListenL4] = {}
    upstream: Optional[str] = ""
    snippet: Optional[ObjectFromSourceOfTruth] = {}

    @model_validator(mode='after')
    def check_type(self) -> 'L4Server':
        name = self.name

        if not re.search(alphanumRegexp,name):
            raise ValueError(f"Invalid name [{name}] should match regexp {alphanumRegexp}")

        return self


class Sticky(BaseModel, extra="forbid"):
    cookie: str = ""
    expires: Optional[str] = ""
    domain: Optional[str] = ""
    path: Optional[str] = ""


class Origin(BaseModel, extra="forbid"):
    server: str
    weight: Optional[int] = 1
    max_fails: Optional[int] = 1
    fail_timeout: Optional[str] = "10s"
    max_conns: Optional[int] = 0
    slow_start: Optional[str] = "0"
    backup: Optional[bool] = False


class L4Origin(BaseModel, extra="forbid"):
    server: str
    weight: Optional[int] = 1
    max_fails: Optional[int] = 1
    fail_timeout: Optional[str] = "10s"
    max_conns: Optional[int] = 0
    slow_start: Optional[str] = "0"
    backup: Optional[bool] = False


class Upstream(BaseModel, extra="forbid"):
    name: str
    resolver: Optional[str] = ""
    origin: Optional[List[Origin]] = []
    sticky: Optional[Sticky] = {}
    snippet: Optional[ObjectFromSourceOfTruth] = {}

    @model_validator(mode='after')
    def check_type(self) -> 'Upstream':
        name = self.name

        if not re.search(alphanumRegexp,name):
            raise ValueError(f"Invalid name [{name}] should match regexp {alphanumRegexp}")

        return self


class L4Upstream(BaseModel, extra="forbid"):
    name: str
    resolver: Optional[str] = ""
    origin: Optional[List[L4Origin]] = []
    snippet: Optional[ObjectFromSourceOfTruth] = {}

    @model_validator(mode='after')
    def check_type(self) -> 'L4Upstream':
        name = self.name

        if not re.search(alphanumRegexp,name):
            raise ValueError(f"Invalid name [{name}] should match regexp {alphanumRegexp}")

        return self


class ValidItem(BaseModel, extra="forbid"):
    codes: Optional[List[int]] = [200]
    ttl: Optional[str] = 60


class CachingItem(BaseModel, extra="forbid"):
    name: str
    key: str
    size: Optional[str] = "10m"
    valid: Optional[List[ValidItem]] = []

    @model_validator(mode='after')
    def check_type(self) -> 'CachingItem':
        name = self.name

        if not re.search(alphanumRegexp,name):
            raise ValueError(f"Invalid name [{name}] should match regexp {alphanumRegexp}")

        return self


class RateLimitItem(BaseModel, extra="forbid"):
    name: str
    key: str
    size: Optional[str] = ""
    rate: Optional[str] = ""

    @model_validator(mode='after')
    def check_type(self) -> 'RateLimitItem':
        name = self.name

        if not re.search(alphanumRegexp,name):
            raise ValueError(f"Invalid name [{name}] should match regexp {alphanumRegexp}")

        return self


class NginxPlusApi(BaseModel, extra="forbid"):
    write: Optional[bool] = False
    listen: Optional[str] = ""
    allow_acl: Optional[str] = ""


class MapEntry(BaseModel, extra="forbid"):
    key: str
    keymatch: str
    value: str

    @model_validator(mode='after')
    def check_type(self) -> 'MapEntry':
        keymatch = self.keymatch

        valid = ['exact', 'regex', 'iregex']
        if keymatch not in valid:
            raise ValueError(f"Invalid key match type [{keymatch}] must be one of {str(valid)}")

        return self


class Map(BaseModel, extra="forbid"):
    match: str
    variable: str
    entries: Optional[List[MapEntry]] = []


class Layer4(BaseModel, extra="forbid"):
    servers: Optional[List[L4Server]] = []
    upstreams: Optional[List[L4Upstream]] = []


class Resolver(BaseModel, extra="forbid"):
    name: str
    address: str
    valid: Optional[str] = ""
    ipv4: bool = True
    ipv6: bool = True
    timeout: str = "30s"

    @model_validator(mode='after')
    def check_type(self) -> 'Resolver':
        name = self.name

        if not re.search(alphanumRegexp,name):
            raise ValueError(f"Invalid resolver name [{name}] should match regexp {alphanumRegexp}")

        return self

class LogFormat(BaseModel, extra="forbid"):
    name: str
    escape: str = "default"
    format: str

    @model_validator(mode='after')
    def check_type(self) -> 'LogFormat':
        escape = self.escape

        valid = ['default', 'json', 'none']
        if escape not in valid:
            raise ValueError(f"Invalid escape mode [{escape}] must be one of {str(valid)}")

        return self


class CacheProfile(BaseModel, extra="forbid"):
    name: str
    basepath: Optional[str] = "/tmp"
    size: Optional[str] = "10m"
    ttl: Optional[str] = "10m"
    max_size: Optional[str] = ""
    min_free: Optional[str] = ""

    @model_validator(mode='after')
    def check_type(self) -> 'CacheProfile':
        name = self.name

        if not re.search(alphanumRegexp,name):
            raise ValueError(f"Invalid cache name [{name}] should match regexp {alphanumRegexp}")

        return self


class CacheObjectTTL(BaseModel, extra="forbid"):
    code: str = "any"
    ttl: str = "10m"

    @model_validator(mode='after')
    def check_type(self) -> 'CacheObjectTTL':
        code = self.code

        if (code.isdigit() and (int(code) < 100 or int(code) >= 600)) or (not code.isdigit() and code!="any"):
            raise ValueError(f"Invalid cache HTTP code [{code}] should be an integer between 100 and 599 or 'any'")

        return self


class CacheItem(BaseModel, extra="forbid"):
    profile: Optional[str] = ""
    key: Optional[str] = "$scheme$proxy_host$request_uri";
    validity: Optional[List[CacheObjectTTL]] = []

    @model_validator(mode='after')
    def check_type(self) -> 'CacheItem':
        profile = self.profile

        if not re.search(alphanumRegexp,profile) and profile != "":
            raise ValueError(f"Invalid cache item [{profile}] should match regexp {alphanumRegexp}")

        return self


class Authentication_Client(BaseModel, extra="forbid"):
    name: str
    type: str

    jwt: Optional[AuthClientJWT] = {}
    mtls: Optional[AuthClientMtls] = {}
    oidc: Optional[AuthClientOIDC] = {}

    @model_validator(mode='after')
    def check_type(self) -> 'Authentication_Client':
        _type, name = self.type, self.name

        valid = ['jwt', 'mtls', 'oidc']
        if _type not in valid:
            raise ValueError(f"Invalid client authentication type [{_type}] for profile [{name}] must be one of {str(valid)}")

        if not re.search(alphanumRegexp,name):
            raise ValueError(f"Invalid name [{name}] should match regexp {alphanumRegexp}")

        return self


class Authentication_Server(BaseModel, extra="forbid"):
    name: str
    type: str

    token: Optional[AuthServerToken] = {}
    mtls: Optional[AuthServerMtls] = {}

    @model_validator(mode='after')
    def check_type(self) -> 'Authentication_Server':
        _type, name = self.type, self.name

        valid = ['token', 'mtls']
        if _type not in valid:
            raise ValueError(f"Invalid server authentication type [{_type}] for profile [{name}] must be one of {str(valid)}")

        if not re.search(alphanumRegexp,name):
            raise ValueError(f"Invalid name [{name}] should match regexp {alphanumRegexp}")

        return self


class Authentication(BaseModel, extra="forbid"):
    client: Optional[List[Authentication_Client]] = []
    server: Optional[List[Authentication_Server]] = []


class Authorization(BaseModel, extra="forbid"):
    name: str
    type: str

    jwt: Optional[AuthorizationJWT] = {}

    @model_validator(mode='after')
    def check_type(self) -> 'Authorization':
        _type, name = self.type, self.name

        valid = ['jwt']
        if _type not in valid:
            raise ValueError(f"Invalid authorization type [{_type}] for profile [{name}] must be one of {str(valid)}")

        if not re.search(alphanumRegexp,name):
            raise ValueError(f"Invalid name [{name}] should match regexp {alphanumRegexp}")

        return self

class NjsFile(BaseModel, extra="forbid"):
    name: str
    file: ObjectFromSourceOfTruth

    @model_validator(mode='after')
    def check_type(self) -> 'NjsFile':
        name = self.name

        if not re.search(alphanumRegexp,name):
            raise ValueError(f"Invalid name [{name}] should match regexp {alphanumRegexp}")

        return self


class Http(BaseModel, extra="forbid"):
    servers: Optional[List[Server]] = []
    upstreams: Optional[List[Upstream]] = []
    caching: Optional[List[CachingItem]] = []
    rate_limit: Optional[List[RateLimitItem]] = []
    nginx_plus_api: Optional[NginxPlusApi] = {}
    maps: Optional[List[Map]] = []
    snippet: Optional[ObjectFromSourceOfTruth] = {}
    authentication: Optional[Authentication] = {}
    authorization: Optional[List[Authorization]] = []
    njs: Optional[List[NjsHookHttpServer]] = []
    njs_profiles: Optional[List[NjsFile]] = []
    cache: Optional[List[CacheProfile]] = []
    logformats: Optional[List[LogFormat]] = []
    resolver: Optional[str] = ""
    acme_issuers: Optional[List[AcmeIssuers]] = []


class Declaration(BaseModel, extra="forbid"):
    layer4: Optional[Layer4] = {}
    http: Optional[Http] = {}
    resolvers: Optional[List[Resolver]] = []


class API_Gateway(BaseModel, extra="forbid"):
    enabled: Optional[bool] = False
    strip_uri: Optional[bool] = False
    server_url: Optional[str] = ""


class DevPortal_Redocly(BaseModel, extra="forbid"):
    uri: Optional[str] = "/devportal.html"


class DevPortal_Backstage(BaseModel, extra="forbid"):
    name: str = ""
    lifecycle: Optional[str] = "production"
    owner: str = ""
    system: Optional[str] = ""

    @model_validator(mode='after')
    def check_type(self) -> 'DevPortal_Backstage':
        _lifecycle = self.lifecycle

        valid = ['experimental', 'production', 'deprecated']
        if _lifecycle not in valid:
            raise ValueError(f"Invalid developer portal type [{_lifecycle}] must be one of {str(valid)}")

        return self

      
class DeveloperPortal(BaseModel, extra="forbid"):
    enabled: Optional[bool] = False
    type: str = ""
    redocly: Optional[DevPortal_Redocly] = {}
    backstage: Optional[DevPortal_Backstage] = {}

    @model_validator(mode='after')
    def check_type(self) -> 'DeveloperPortal':
        _enabled, _type, _redocly, _backstage = self.enabled, self.type, self.redocly, self.backstage

        valid = ['redocly', 'backstage']

        if _enabled == True and _type not in valid:
            raise ValueError(f"Invalid developer portal type [{_type}] must be one of {str(valid)}")

        isError = False

        if _type == 'redocly' and not _redocly:
            isError = True

        if _type == 'backstage' and not _backstage:
            isError = True

        if isError:
            raise ValueError(f"Missing developer portal data for type [{_type}]")

        return self


class Visibility_Moesif(BaseModel, extra="forbid"):
    application_id: str = ""
    plugin_path: Optional[str] = "/usr/local/share/lua/5.1/resty/moesif"


class Visibility(BaseModel, extra="forbid"):
    enabled: Optional[bool] = False
    type: str = ""
    moesif: Optional[Visibility_Moesif] = {}

    @model_validator(mode='after')
    def check_type(self) -> 'Visibility':
        _enabled, _type, _moesif = self.enabled, self.type, self.moesif

        valid = ['moesif']

        if _enabled == True and _type not in valid:
            raise ValueError(f"Invalid visibility type [{_type}] must be one of {str(valid)}")

        isError = False

        if _type == 'moesif' and not _moesif:
            isError = True

        if isError:
            raise ValueError(f"Missing visibility data for type [{_type}]")

        return self

class APIGateway(BaseModel, extra="forbid"):
    openapi_schema: Optional[ObjectFromSourceOfTruth] = {}
    api_gateway: Optional[API_Gateway] =  {}
    developer_portal: Optional[DeveloperPortal] = {}
    visibility: Optional[List[Visibility]] = []
    rate_limit: Optional[List[RateLimitApiGw]] = []
    authentication: Optional[APIGatewayAuthentication] = {}
    authorization: Optional[List[APIGatewayAuthorization]] = []
    cache: Optional[List[APIGatewayCache]] = []
    log: Optional[Log] = {}


class ConfigDeclaration(BaseModel, extra="forbid"):
    output: Output
    declaration: Optional[Declaration] = {}
