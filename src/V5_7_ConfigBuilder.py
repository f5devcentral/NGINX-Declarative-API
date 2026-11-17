"""
Helper functions used to build the NGINX configuration files (and validate the
declaration) for a single createconfig() call.

This module provides small, single-purpose functions. All of them operate on a shared
ConfigBuildContext instance (`ctx`) that holds the mutable state that used to
be a pile of local variables (configFiles, auxFiles, all_resolver_profiles,
...).

Convention used throughout this module:
- Functions that can fail validation return either `None` (success) or an
  error dict shaped like the one the API expects: {"status_code": ..., "message": ...}.
  Callers must check this and propagate it immediately.
- Functions that cannot fail (pure rendering / collection) return None and
  mutate `ctx` in place.
"""

import base64
import ipaddress
import re
from urllib.parse import urlparse

import v5_7.APIGateway
import v5_7.DevPortal
import v5_7.GitOps
import v5_7.MiscUtils
import v5_7.NGINXOneOutput
import v5_7.NIMOutput
import v5_7.OpenAPIParser
from jinja2 import Environment, FileSystemLoader

from NcgConfig import NcgConfig


# ---------------------------------------------------------------------------
# Shared state
# ---------------------------------------------------------------------------

class ConfigBuildContext:
    """Holds the mutable state shared by the build helper functions for a
    single createconfig() invocation."""

    def __init__(self, d: dict, apiversion: str):
        self.d = d or {}
        self.apiversion = apiversion

        self.j2_env = _build_jinja_environment(apiversion)

        # NGINX configuration / auxiliary files staged for output
        self.configFiles = {'files': []}
        self.auxFiles = {'files': []}

        # Extra manifests (e.g. Backstage) to be returned to the caller
        self.extraOutputManifests = []

        # Cross-reference lists used to validate the declaration
        self.all_resolver_profiles = []
        self.all_http_upstreams = []
        self.all_apigw_upstreams = set()
        self.all_layer4_upstreams = []
        self.all_ratelimits = []
        self.all_cache_profiles = []
        self.all_auth_client_profiles = []
        self.all_auth_server_profiles = []
        self.all_authz_client_profiles = []
        self.all_njs_profiles = []
        self.all_acme_issuers = []


def _build_jinja_environment(apiversion: str) -> Environment:
    templates_dir = f"{NcgConfig.config['templates']['root_dir']}/{apiversion}"
    j2_env = Environment(loader=FileSystemLoader(templates_dir), trim_blocks=True,
                         extensions=["jinja2_base64_filters.Base64Filters"])
    j2_env.filters['regex_replace'] = v5_7.MiscUtils.regex_replace
    return j2_env


# ---------------------------------------------------------------------------
# Small generic helpers
# ---------------------------------------------------------------------------

def _b64(text: str) -> str:
    return base64.b64encode(bytes(text, 'utf-8')).decode('utf-8')


def _validation_error(message: str, status_code: int = 422) -> dict:
    """Builds the standard "invalid declaration" error payload."""
    return {"status_code": status_code,
            "message": {"status_code": status_code,
                        "message": {"code": status_code, "content": message}}}


def _gitops_error(status_code: int, message) -> dict:
    """Builds the error payload used when an external (GitOps) fetch fails."""
    return {"status_code": 422, "message": {"status_code": status_code, "message": message}}


# ---------------------------------------------------------------------------
# Top level entry point
# ---------------------------------------------------------------------------

def build_config_files(ctx: ConfigBuildContext):
    """Runs every validation/rendering step for the declaration held in ctx.

    Returns None on success, or an error dict to be returned to the caller.
    """
    _process_resolvers(ctx)

    error = _process_http(ctx)
    if error is not None:
        return error

    return _process_layer4(ctx)


def dispatch_output(ctx: ConfigBuildContext, decltype: str, declaration, apiversion: str,
                    runfromautosync: bool, configUid: str):
    """
    Renders the final http/stream configs and publishes them to the
    configured output (NGINX Instance Manager or NGINX One Console).
    """
    b64_http_conf, b64_stream_conf = _render_main_configs(ctx)

    decltype_lower = decltype.lower()
    if decltype_lower == 'nms':
        ctx.configFiles['rootDir'] = NcgConfig.config['nms']['config_dir']
        ctx.auxFiles['rootDir'] = NcgConfig.config['nms']['config_dir']
        final_reply = v5_7.NIMOutput.NIMOutput(
            d=ctx.d, declaration=declaration, apiversion=apiversion,
            b64HttpConf=b64_http_conf, b64StreamConf=b64_stream_conf,
            configFiles=ctx.configFiles, auxFiles=ctx.auxFiles,
            runfromautosync=runfromautosync, configUid=configUid)
    elif decltype_lower == 'nginxone':
        ctx.configFiles['name'] = NcgConfig.config['nms']['config_dir']
        ctx.auxFiles['name'] = NcgConfig.config['nms']['config_dir']
        final_reply = v5_7.NGINXOneOutput.NGINXOneOutput(
            d=ctx.d, declaration=declaration, apiversion=apiversion,
            b64HttpConf=b64_http_conf, b64StreamConf=b64_stream_conf,
            configFiles=ctx.configFiles, auxFiles=ctx.auxFiles,
            runfromautosync=runfromautosync, configUid=configUid)
    else:
        return {"status_code": 422,
                "message": {"status_code": 422, "message": f"output type {decltype} unknown"}}

    if final_reply['status_code'] == 200 and ctx.extraOutputManifests:
        final_reply['message']['message']['content']['manifests'] = ctx.extraOutputManifests

    return final_reply


def _render_main_configs(ctx: ConfigBuildContext):
    declaration = ctx.d.get('declaration') or {}

    http_conf = ''
    if declaration.get('http'):
        http_conf = ctx.j2_env.get_template(NcgConfig.config['templates']['httpconf']).render(
            declaration=declaration, ncgconfig=NcgConfig.config)

    stream_conf = ''
    if declaration.get('layer4'):
        stream_conf = ctx.j2_env.get_template(NcgConfig.config['templates']['streamconf']).render(
            declaration=declaration, ncgconfig=NcgConfig.config)

    return _b64(http_conf), _b64(stream_conf)


# ---------------------------------------------------------------------------
# Resolver profiles
# ---------------------------------------------------------------------------

def _process_resolvers(ctx: ConfigBuildContext):
    declaration = ctx.d.get('declaration') or {}
    if 'resolvers' not in declaration:
        return

    d_resolver_profiles = v5_7.MiscUtils.getDictKey(ctx.d, 'declaration.resolvers')
    if not d_resolver_profiles:
        return

    for resolver_profile in d_resolver_profiles:
        template_name = NcgConfig.config['templates']['resolver']
        rendered = ctx.j2_env.get_template(template_name).render(
            resolverprofile=resolver_profile, ncgconfig=NcgConfig.config)
        config_file_name = (NcgConfig.config['nms']['resolver_dir'] + '/' +
                            resolver_profile['name'].replace(' ', '_') + ".conf")
        ctx.configFiles['files'].append({'contents': _b64(rendered), 'name': config_file_name})
        ctx.all_resolver_profiles.append(resolver_profile['name'])


# ---------------------------------------------------------------------------
# HTTP block orchestration
# ---------------------------------------------------------------------------

def _process_http(ctx: ConfigBuildContext):
    declaration = ctx.d.get('declaration') or {}
    if 'http' not in declaration or not declaration.get('http'):
        return None

    for step in (_process_http_snippet, _process_http_upstreams):
        error = step(ctx)
        if error is not None:
            return error

    _collect_rate_limit_profiles(ctx)
    _collect_cache_profiles(ctx)
    _process_auth_client_profiles(ctx)
    _process_auth_server_profiles(ctx)
    _process_authz_profiles(ctx)

    error = _process_njs_profiles(ctx)
    if error is not None:
        return error

    _process_acme_issuers(ctx)

    for step in (_validate_http_njs_hooks, _validate_http_resolver, _process_http_servers):
        error = step(ctx)
        if error is not None:
            return error

    return None


def _process_http_snippet(ctx: ConfigBuildContext):
    d = ctx.d.get('declaration') or {}
    http = d.get('http') or {}
    if not http.get('snippet'):
        return None

    status, snippet = v5_7.GitOps.getObjectFromRepo(object=http['snippet'], authProfiles=d.get('authentication'))
    if status != 200:
        return _gitops_error(status, snippet)
    http['snippet'] = snippet
    return None


def _process_http_upstreams(ctx: ConfigBuildContext):
    d = ctx.d.get('declaration') or {}
    http = d.get('http') or {}
    upstreams = http.get('upstreams')
    if not upstreams:
        return None

    for i, upstream in enumerate(upstreams):
        if upstream.get('resolver') and upstream['resolver'] not in ctx.all_resolver_profiles:
            return _validation_error(
                f"invalid resolver profile [{upstream['resolver']}] in HTTP upstream "
                f"[{upstream['name']}], must be one of {ctx.all_resolver_profiles}")

        if upstream.get('snippet'):
            status, snippet = v5_7.GitOps.getObjectFromRepo(
                object=upstream['snippet'], authProfiles=d.get('authentication'))
            if status != 200:
                return _gitops_error(status, snippet)
            upstreams[i]['snippet'] = snippet

        template_name = NcgConfig.config['templates']['upstream_http']
        rendered = ctx.j2_env.get_template(template_name).render(u=upstream, ncgconfig=NcgConfig.config)
        config_file_name = (NcgConfig.config['nms']['upstream_http_dir'] + '/' +
                            upstream['name'].replace(' ', '_') + ".conf")
        ctx.configFiles['files'].append({'contents': _b64(rendered), 'name': config_file_name})
        ctx.all_http_upstreams.append(upstream['name'])

    return None


def _collect_rate_limit_profiles(ctx: ConfigBuildContext):
    d_rate_limit = v5_7.MiscUtils.getDictKey(ctx.d, 'declaration.http.rate_limit')
    if not d_rate_limit:
        return
    ctx.all_ratelimits.extend(rl['name'] for rl in d_rate_limit)


def _collect_cache_profiles(ctx: ConfigBuildContext):
    d_cache_profiles = v5_7.MiscUtils.getDictKey(ctx.d, 'declaration.http.cache')
    if not d_cache_profiles:
        return
    ctx.all_cache_profiles.extend(cp['name'] for cp in d_cache_profiles)


# ---------------------------------------------------------------------------
# Authentication profiles (client + server)
# ---------------------------------------------------------------------------

def _render_jwt_client_auth(ctx: ConfigBuildContext, auth_profile):
    root = NcgConfig.config['templates']['auth_client_root']
    name = auth_profile['name'].replace(' ', '_')

    rendered_jwt = ctx.j2_env.get_template(f"{root}/jwt.tmpl").render(
        authprofile=auth_profile, ncgconfig=NcgConfig.config)
    ctx.configFiles['files'].append({
        'contents': _b64(rendered_jwt),
        'name': f"{NcgConfig.config['nms']['auth_client_dir']}/{name}.conf"})
    ctx.all_auth_client_profiles.append(auth_profile['name'])

    rendered_jwks = ctx.j2_env.get_template(f"{root}/jwks.tmpl").render(
        authprofile=auth_profile, ncgconfig=NcgConfig.config)
    ctx.configFiles['files'].append({
        'contents': _b64(rendered_jwks),
        'name': f"{NcgConfig.config['nms']['auth_client_dir']}/jwks_{name}.conf"})


def _render_mtls_client_auth(ctx: ConfigBuildContext, auth_profile):
    root = NcgConfig.config['templates']['auth_client_root']
    name = auth_profile['name'].replace(' ', '_')
    rendered = ctx.j2_env.get_template(f"{root}/mtls.tmpl").render(
        authprofile=auth_profile, ncgconfig=NcgConfig.config)
    ctx.configFiles['files'].append({
        'contents': _b64(rendered),
        'name': f"{NcgConfig.config['nms']['auth_client_dir']}/{name}.conf"})
    ctx.all_auth_client_profiles.append(auth_profile['name'])


def _render_oidc_client_auth(ctx: ConfigBuildContext, auth_profile):
    root = NcgConfig.config['templates']['auth_client_root']
    name = auth_profile['name'].replace(' ', '_')
    rendered = ctx.j2_env.get_template(f"{root}/oidc.tmpl").render(
        authprofile=auth_profile, ncgconfig=NcgConfig.config)
    ctx.configFiles['files'].append({
        'contents': _b64(rendered),
        'name': f"{NcgConfig.config['nms']['auth_client_dir']}/oidc/{name}.conf"})
    ctx.all_auth_client_profiles.append(auth_profile['name'])


def _process_auth_client_profiles(ctx: ConfigBuildContext):
    d_auth_profiles = v5_7.MiscUtils.getDictKey(ctx.d, 'declaration.authentication')
    if not d_auth_profiles or not d_auth_profiles.get('client'):
        return

    for auth_profile in d_auth_profiles['client']:
        match auth_profile.get('type'):
            case 'jwt':
                _render_jwt_client_auth(ctx, auth_profile)
            case 'mtls':
                _render_mtls_client_auth(ctx, auth_profile)
            case 'oidc':
                _render_oidc_client_auth(ctx, auth_profile)


def _render_token_server_auth(ctx: ConfigBuildContext, auth_profile):
    root = NcgConfig.config['templates']['auth_server_root']
    name = auth_profile['name'].replace(' ', '_')
    rendered = ctx.j2_env.get_template(f"{root}/token.tmpl").render(
        authprofile=auth_profile, ncgconfig=NcgConfig.config)
    ctx.configFiles['files'].append({
        'contents': _b64(rendered),
        'name': f"{NcgConfig.config['nms']['auth_server_dir']}/{name}.conf"})
    ctx.all_auth_server_profiles.append(auth_profile['name'])


def _render_mtls_server_auth(ctx: ConfigBuildContext, auth_profile):
    root = NcgConfig.config['templates']['auth_server_root']
    name = auth_profile['name'].replace(' ', '_')
    rendered = ctx.j2_env.get_template(f"{root}/mtls.tmpl").render(
        authprofile=auth_profile, ncgconfig=NcgConfig.config)
    ctx.configFiles['files'].append({
        'contents': _b64(rendered),
        'name': f"{NcgConfig.config['nms']['auth_server_dir']}/{name}.conf"})
    ctx.all_auth_server_profiles.append(auth_profile['name'])


def _process_auth_server_profiles(ctx: ConfigBuildContext):
    d_auth_profiles = v5_7.MiscUtils.getDictKey(ctx.d, 'declaration.authentication')
    if not d_auth_profiles or not d_auth_profiles.get('server'):
        return

    for auth_profile in d_auth_profiles['server']:
        match auth_profile.get('type'):
            case 'token':
                _render_token_server_auth(ctx, auth_profile)
            case 'mtls':
                _render_mtls_server_auth(ctx, auth_profile)


# ---------------------------------------------------------------------------
# Authorization (authz) profiles
# ---------------------------------------------------------------------------

def _render_jwt_client_authz(ctx: ConfigBuildContext, authz_profile):
    root = NcgConfig.config['templates']['authz_client_root']
    name = authz_profile['name'].replace(' ', '_')

    rendered_maps = ctx.j2_env.get_template(f"{root}/jwt-authz-map.tmpl").render(
        authprofile=authz_profile, ncgconfig=NcgConfig.config)
    ctx.configFiles['files'].append({
        'contents': _b64(rendered_maps),
        'name': f"{NcgConfig.config['nms']['authz_client_dir']}/{name}.maps.conf"})
    ctx.all_authz_client_profiles.append(authz_profile['name'])

    rendered = ctx.j2_env.get_template(f"{root}/jwt.tmpl").render(
        authprofile=authz_profile, ncgconfig=NcgConfig.config)
    ctx.configFiles['files'].append({
        'contents': _b64(rendered),
        'name': f"{NcgConfig.config['nms']['authz_client_dir']}/{name}.conf"})


def _process_authz_profiles(ctx: ConfigBuildContext):
    d_authz_profiles = v5_7.MiscUtils.getDictKey(ctx.d, 'declaration.authorization')
    if not d_authz_profiles:
        return

    for authz_profile in d_authz_profiles:
        match authz_profile.get('type'):
            case 'jwt':
                _render_jwt_client_authz(ctx, authz_profile)


# ---------------------------------------------------------------------------
# NGINX Javascript (njs) profiles + ACME issuers
# ---------------------------------------------------------------------------

def _process_njs_profiles(ctx: ConfigBuildContext):
    d_njs_files = v5_7.MiscUtils.getDictKey(ctx.d, 'declaration.http.njs_profiles')
    if not d_njs_files:
        return None

    auth_profiles = (ctx.d.get('declaration') or {}).get('authentication')
    for njs_file in d_njs_files:
        njs_filename = njs_file['name'].replace(' ', '_')
        status, content = v5_7.GitOps.getObjectFromRepo(object=njs_file['file'], authProfiles=auth_profiles)
        if status != 200:
            return _gitops_error(status, content)
        ctx.auxFiles['files'].append({
            'contents': content['content'],
            'name': f"{NcgConfig.config['nms']['njs_dir']}/{njs_filename}.js"})
        ctx.all_njs_profiles.append(njs_filename)

    return None


def _process_acme_issuers(ctx: ConfigBuildContext):
    d_acme_issuers = v5_7.MiscUtils.getDictKey(ctx.d, 'declaration.http.acme_issuers')
    if not d_acme_issuers:
        return

    for acme_issuer in d_acme_issuers:
        template_name = NcgConfig.config['templates']['acme_issuer']
        rendered = ctx.j2_env.get_template(template_name).render(
            acmeprofile=acme_issuer, ncgconfig=NcgConfig.config)
        config_file_name = (NcgConfig.config['nms']['acme_dir'] + '/' +
                            acme_issuer['name'].replace(' ', '_') + ".conf")
        ctx.configFiles['files'].append({'contents': _b64(rendered), 'name': config_file_name})
        ctx.all_acme_issuers.append(acme_issuer['name'])


# ---------------------------------------------------------------------------
# HTTP context level validation
# ---------------------------------------------------------------------------

def _validate_http_njs_hooks(ctx: ConfigBuildContext):
    d_http_njs_hooks = v5_7.MiscUtils.getDictKey(ctx.d, 'declaration.http.njs')
    if not d_http_njs_hooks:
        return None

    for hook in d_http_njs_hooks:
        if hook.get('profile') and hook['profile'] not in ctx.all_njs_profiles:
            return _validation_error(
                f"invalid njs profile [{hook['profile']}] in HTTP declaration, "
                f"must be one of {ctx.all_njs_profiles}")
    return None


def _validate_http_resolver(ctx: ConfigBuildContext):
    d_http_resolver = v5_7.MiscUtils.getDictKey(ctx.d, 'declaration.http.resolver')
    if not d_http_resolver:
        return None

    if d_http_resolver not in ctx.all_resolver_profiles:
        return _validation_error(
            f"invalid resolver profile [{d_http_resolver}] in HTTP context, "
            f"must be one of {ctx.all_resolver_profiles}")
    return None


# ---------------------------------------------------------------------------
# HTTP servers
# ---------------------------------------------------------------------------

def _process_http_servers(ctx: ConfigBuildContext):
    d_servers = v5_7.MiscUtils.getDictKey(ctx.d, 'declaration.http.servers')
    if not d_servers:
        return None

    for server in d_servers:
        error = _process_http_server(ctx, server)
        if error is not None:
            return error
    return None


def _process_http_server(ctx: ConfigBuildContext, server):
    error = _validate_server(ctx, server)
    if error is not None:
        return error

    server_snippet = ''
    if server.get('snippet'):
        error, server_snippet = _fetch_server_snippet(ctx, server)
        if error is not None:
            return error

    _render_http_server_conf(ctx, server)

    for loc in (server.get('locations') or []):
        error = _process_location(ctx, server, loc)
        if error is not None:
            return error

    if server.get('snippet'):
        server['snippet']['content'] = _b64(server_snippet)

    return None


def _validate_server(ctx: ConfigBuildContext, server):
    if server.get('resolver') and server['resolver'] not in ctx.all_resolver_profiles:
        return _validation_error(
            f"invalid resolver profile [{server['resolver']}] in HTTP server "
            f"[{server['name']}], must be one of {ctx.all_resolver_profiles}")

    if server.get('cache'):
        profile = server['cache'].get('profile')
        if profile and profile not in ctx.all_cache_profiles:
            return _validation_error(
                f"invalid cache profile [{profile}] in HTTP server "
                f"[{server['name']}], must be one of {ctx.all_cache_profiles}")

    if server.get('njs'):
        for hook in server['njs']:
            if hook.get('profile') and hook['profile'] not in ctx.all_njs_profiles:
                return _validation_error(
                    f"invalid njs profile [{hook['profile']}] in server "
                    f"[{server['name']}], must be one of {ctx.all_njs_profiles}")

    if server.get('authentication') and server['authentication'].get('client'):
        for auth_profile in server['authentication']['client']:
            if auth_profile.get('profile') and auth_profile['profile'] not in ctx.all_auth_client_profiles:
                return _validation_error(
                    f"invalid client authentication profile [{auth_profile['profile']}] "
                    f"in server [{server['name']}] must be one of {ctx.all_auth_client_profiles}")

    if server.get('authorization'):
        profile = server['authorization'].get('profile')
        if profile and profile not in ctx.all_authz_client_profiles:
            return _validation_error(
                f"invalid client authorization profile [{profile}] in server "
                f"[{server['name']}] must be one of {ctx.all_authz_client_profiles}")

    listen = server.get('listen') or {}
    tls = listen.get('tls')
    if tls:
        if tls.get('authentication') and tls['authentication'].get('client'):
            for mtls_profile in tls['authentication']['client']:
                if mtls_profile.get('profile') and mtls_profile['profile'] not in ctx.all_auth_client_profiles:
                    return _validation_error(
                        f"invalid client authentication profile [{mtls_profile['profile']}] "
                        f"in server [{server['name']}] must be one of {ctx.all_auth_client_profiles}")

        if tls.get('acme_issuer'):
            acme_issuer = tls['acme_issuer']
            if acme_issuer and acme_issuer not in ctx.all_acme_issuers:
                return _validation_error(
                    f"invalid ACME issuer [{acme_issuer}] in server "
                    f"[{server['name']}] must be one of {ctx.all_acme_issuers}")

    return None


def _fetch_server_snippet(ctx: ConfigBuildContext, server):
    auth_profiles = (ctx.d.get('declaration') or {}).get('authentication')
    status, server_snippet = v5_7.GitOps.getObjectFromRepo(
        object=server['snippet'], authProfiles=auth_profiles, base64Encode=False)
    if status != 200:
        return _gitops_error(status, server_snippet), ''
    return None, server_snippet['content']


def _render_http_server_conf(ctx: ConfigBuildContext, server):
    declaration = ctx.d.get('declaration') or {}
    rendered = ctx.j2_env.get_template(NcgConfig.config['templates']['server_http']).render(
        declaration=declaration, s=server, ncgconfig=NcgConfig.config)
    config_file_name = (NcgConfig.config['nms']['server_http_dir'] + '/' +
                        server['name'].replace(' ', '_') + ".conf")
    ctx.configFiles['files'].append({'contents': _b64(rendered), 'name': config_file_name})


# ---------------------------------------------------------------------------
# HTTP locations
# ---------------------------------------------------------------------------

def _process_location(ctx: ConfigBuildContext, server, loc):
    error = _validate_location_njs(ctx, loc)
    if error is not None:
        return error

    error = _process_location_snippet(ctx, loc)
    if error is not None:
        return error

    error = _validate_location_upstream(ctx, loc)
    if error is not None:
        return error

    error = _validate_location_auth_client(ctx, loc)
    if error is not None:
        return error

    error = _validate_location_authz(ctx, loc)
    if error is not None:
        return error

    error = _validate_location_auth_server(ctx, loc)
    if error is not None:
        return error

    enabled_visibility = _process_api_gateway_visibility(ctx, loc)

    error, openapi_schema_json = _process_api_gateway_provisioning(ctx, server, loc, enabled_visibility)
    if error is not None:
        return error

    error = _process_developer_portal(ctx, loc, openapi_schema_json)
    if error is not None:
        return error

    error = _validate_location_rate_limit(ctx, loc)
    if error is not None:
        return error

    error = _validate_location_cache(ctx, loc)
    if error is not None:
        return error

    return None


def _validate_location_njs(ctx: ConfigBuildContext, loc):
    if not loc.get('njs'):
        return None
    for hook in loc['njs']:
        if hook.get('profile') and hook['profile'] not in ctx.all_njs_profiles:
            return _validation_error(
                f"invalid njs profile [{hook['profile']}] in location "
                f"[{loc['uri']}], must be one of {ctx.all_njs_profiles}")
    return None


def _process_location_snippet(ctx: ConfigBuildContext, loc):
    if not loc.get('snippet'):
        return None
    auth_profiles = (ctx.d.get('declaration') or {}).get('authentication')
    status, snippet = v5_7.GitOps.getObjectFromRepo(object=loc['snippet'], authProfiles=auth_profiles)
    if status != 200:
        return _gitops_error(status, snippet)
    loc['snippet'] = snippet
    return None


def _validate_location_upstream(ctx: ConfigBuildContext, loc):
    if loc.get('upstream') and urlparse(loc['upstream']).netloc not in ctx.all_http_upstreams:
        return _validation_error(f"invalid HTTP upstream [{loc['upstream']}]")
    return None


def _validate_location_auth_client(ctx: ConfigBuildContext, loc):
    auth = loc.get('authentication')
    if auth and auth.get('client'):
        for auth_profile in auth['client']:
            if auth_profile.get('profile') and auth_profile['profile'] not in ctx.all_auth_client_profiles:
                return _validation_error(
                    f"invalid client authentication profile [{auth_profile['profile']}] "
                    f"in location [{loc['uri']}] must be one of {ctx.all_auth_client_profiles}")
    return None


def _validate_location_authz(ctx: ConfigBuildContext, loc):
    authz = loc.get('authorization')
    if authz:
        profile = authz.get('profile')
        if profile and profile not in ctx.all_authz_client_profiles:
            return _validation_error(
                f"invalid client authorization profile [{profile}] in location "
                f"[{loc['uri']}] must be one of {ctx.all_authz_client_profiles}")
    return None


def _validate_location_auth_server(ctx: ConfigBuildContext, loc):
    auth = loc.get('authentication')
    if auth and auth.get('server'):
        for auth_profile in auth['server']:
            if auth_profile.get('profile') and auth_profile['profile'] not in ctx.all_auth_server_profiles:
                return _validation_error(
                    f"invalid server authentication profile [{auth_profile['profile']}] "
                    f"in location [{loc['uri']}]")
    return None


def _validate_location_rate_limit(ctx: ConfigBuildContext, loc):
    rate_limit = loc.get('rate_limit')
    if rate_limit and rate_limit.get('profile') and rate_limit['profile'] not in ctx.all_ratelimits:
        return _validation_error(f"invalid rate_limit profile [{rate_limit['profile']}]")
    return None


def _validate_location_cache(ctx: ConfigBuildContext, loc):
    cache = loc.get('cache')
    if cache and cache.get('profile') and cache['profile'] not in ctx.all_cache_profiles and cache['profile'] != "":
        return _validation_error(f"invalid cache profile [{cache['profile']}]")
    return None


# ---------------------------------------------------------------------------
# API Gateway: visibility integrations (e.g. Moesif)
# ---------------------------------------------------------------------------

def _process_api_gateway_visibility(ctx: ConfigBuildContext, loc):
    """Renders enabled API Gateway visibility integrations for a location.

    Returns a dict of enabled integration types, e.g. {'moesif': True}.
    """
    enabled_integrations = {}
    apigateway = loc.get('apigateway')
    if not (apigateway and apigateway.get('visibility')):
        return enabled_integrations

    for vis in apigateway['visibility']:
        if not vis.get('enabled'):
            continue
        enabled_integrations[vis['type']] = True
        if vis.get('type', '').lower() == 'moesif':
            _render_moesif_visibility(ctx, loc, vis)

    return enabled_integrations


def _render_moesif_visibility(ctx: ConfigBuildContext, loc, vis):
    root = NcgConfig.config['templates']['visibility_root']

    rendered_http = ctx.j2_env.get_template(f"{root}/moesif/http.tmpl").render(
        vis=vis, loc=loc, ncgconfig=NcgConfig.config)
    ctx.configFiles['files'].append({
        'contents': _b64(rendered_http),
        'name': f"{NcgConfig.config['nms']['visibility_dir']}{loc['uri']}-moesif-http.conf"})

    rendered_server = ctx.j2_env.get_template(f"{root}/moesif/server.tmpl").render(
        vis=vis, loc=loc, ncgconfig=NcgConfig.config)
    ctx.configFiles['files'].append({
        'contents': _b64(rendered_server),
        'name': f"{NcgConfig.config['nms']['visibility_dir']}{loc['uri']}-moesif-server.conf"})


# ---------------------------------------------------------------------------
# API Gateway: provisioning
# ---------------------------------------------------------------------------

def _validate_api_gateway_profiles(ctx: ConfigBuildContext, loc):
    apigateway = loc.get('apigateway')
    if not apigateway:
        return None

    openapi_schema = apigateway.get('openapi_schema') or {}
    schema_content = openapi_schema.get('content')

    if apigateway.get('authentication') and apigateway['authentication'].get('client'):
        for profile in apigateway['authentication']['client']:
            if profile.get('profile') and profile['profile'] not in ctx.all_auth_client_profiles:
                return _validation_error(
                    f"invalid API Gateway authentication profile [{profile['profile']}] "
                    f"for OpenAPI schema [{schema_content}] must be one of {ctx.all_auth_client_profiles}")

    if apigateway.get('authorization'):
        for profile in apigateway['authorization']:
            if profile.get('profile') and profile['profile'] not in ctx.all_authz_client_profiles:
                return _validation_error(
                    f"invalid API Gateway authorization profile [{profile['profile']}] "
                    f"for OpenAPI schema [{schema_content}] must be one of {ctx.all_authz_client_profiles}")

    if apigateway.get('rate_limit'):
        for profile in apigateway['rate_limit']:
            if profile.get('profile') and profile['profile'] not in ctx.all_ratelimits:
                return _validation_error(
                    f"invalid API Gateway rate limit profile [{profile['profile']}] "
                    f"for OpenAPI schema [{schema_content}] must be one of {ctx.all_ratelimits}")

    openapi_auth_profile = openapi_schema.get('authentication')
    if openapi_auth_profile and openapi_auth_profile[0].get('profile') not in ctx.all_auth_server_profiles:
        return _validation_error(
            f"invalid server authentication profile [{openapi_auth_profile[0]['profile']}] "
            f"for OpenAPI schema [{schema_content}]")

    return None


def _process_api_gateway_provisioning(ctx: ConfigBuildContext, server, loc, enabled_visibility):
    """Provisions the API Gateway configuration for a location, if enabled.

    Returns a (error, openAPISchemaJSON) tuple.
    """
    apigateway = loc.get('apigateway')
    api_gateway_settings = apigateway.get('api_gateway') if apigateway else None
    if not (api_gateway_settings and api_gateway_settings.get('enabled')):
        return None, None

    error = _validate_api_gateway_profiles(ctx, loc)
    if error is not None:
        return error, None

    schema_content = apigateway.get('openapi_schema', {}).get('content')
    status, api_gateway_declaration, openapi_schema_json = v5_7.APIGateway.createAPIGateway(
        locationDeclaration=loc, authProfiles=apigateway.get('openapi_schema', {}).get('authentication'))
    if status != 200:
        return ({"status_code": 412,
                "message": {"status_code": status,
                            "message": {"code": status,
                                       "content": f"OpenAPI schema fetch failed for {schema_content}"}}},
                None)

    if api_gateway_declaration:
        error, upstream_info = _resolve_api_gateway_upstream(ctx, server, loc, api_gateway_declaration)
        if error is not None:
            return error, None
        api_gateway_declaration['upstream'] = upstream_info['primary']
        api_gateway_declaration['upstreams'] = upstream_info['upstreams']
        _render_api_gateway_files(ctx, server, loc, api_gateway_declaration, enabled_visibility)

    return None, openapi_schema_json


def _normalize_gateway_url(url: str, server_url: str) -> str:
    cleaned = (url or '').strip()
    if not cleaned:
        return server_url
    if cleaned.lower().startswith(('http://', 'https://')):
        return cleaned
    if cleaned.startswith('//') and server_url:
        parsed_base = urlparse(server_url)
        if parsed_base.scheme:
            return f"{parsed_base.scheme}:{cleaned}"
    if cleaned in ('/', '.'):
        return server_url.rstrip('/')
    if server_url:
        return f"{server_url.rstrip('/')}/{cleaned.lstrip('/')}"
    return cleaned


def _parse_upstream_server(ctx: ConfigBuildContext, server: dict, loc: dict, dest_url: str):
    if not dest_url:
        return _validation_error(
            f"missing API Gateway destination server URL in location [{loc.get('uri', '')}]"), None

    if '{' in dest_url or '}' in dest_url:
        return _validation_error(
            f"unresolved server variable in API Gateway destination server URL [{dest_url}] in location [{loc.get('uri', '')}]"), None

    parsed = urlparse(dest_url)
    scheme = parsed.scheme.lower()
    if scheme not in ('http', 'https') or not parsed.hostname:
        return _validation_error(
            f"invalid API Gateway destination server URL [{dest_url}] in location [{loc.get('uri', '')}]"), None

    try:
        explicit_port = parsed.port
    except ValueError:
        return _validation_error(
            f"invalid port in API Gateway destination server URL [{dest_url}] in location [{loc.get('uri', '')}]"), None

    hostname = parsed.hostname
    try:
        ip_obj = ipaddress.ip_address(hostname)
        is_ip = True
        is_ipv6 = isinstance(ip_obj, ipaddress.IPv6Address)
    except ValueError:
        is_ip = False
        is_ipv6 = False

    host_for_nginx = f"[{hostname}]" if is_ipv6 else hostname
    port = explicit_port if explicit_port is not None else (443 if scheme == 'https' else 80)
    origin = f"{host_for_nginx}:{port}"

    base_path = parsed.path.rstrip('/')
    host_header = parsed.netloc
    ssl_name = hostname if (scheme == 'https' and not is_ip) else ''

    server_resolver = server.get('resolver') or ''
    http_resolver = ((ctx.d.get('declaration') or {}).get('http') or {}).get('resolver') or ''
    resolve = (not is_ip) and bool(server_resolver or http_resolver)

    return None, {
        'destination_server': dest_url,
        'scheme': scheme,
        'hostname': hostname,
        'port': port,
        'origin': origin,
        'base_path': base_path,
        'host_header': host_header,
        'ssl_name': ssl_name,
        'resolve': resolve,
        'is_ip': is_ip,
    }


def _build_upstream_info(ctx: ConfigBuildContext, server: dict, loc: dict, base_name: str, dest_urls: list):
    parsed_servers = []
    for d_url in dest_urls:
        err, s_info = _parse_upstream_server(ctx, server, loc, d_url)
        if err is not None:
            return err, None
        parsed_servers.append(s_info)

    if not parsed_servers:
        return _validation_error(
            f"missing API Gateway destination server URL in location [{loc.get('uri', '')}]"), None

    sanitized_base_name = re.sub(r'[^a-zA-Z0-9_-]', '_', base_name)
    used_names = set(ctx.all_http_upstreams) | ctx.all_apigw_upstreams
    upstream_name = sanitized_base_name
    suffix = 2
    while upstream_name in used_names:
        upstream_name = f"{sanitized_base_name}_{suffix}"
        suffix += 1
    ctx.all_apigw_upstreams.add(upstream_name)

    primary = parsed_servers[0]
    server_resolver = server.get('resolver') or ''
    any_needs_resolve = any(s['resolve'] for s in parsed_servers)
    resolver = server_resolver if (server_resolver and any_needs_resolve) else ''

    return None, {
        'name': upstream_name,
        'destination_server': ', '.join(dest_urls),
        'scheme': primary['scheme'],
        'origin': primary['origin'],
        'base_path': primary['base_path'],
        'host_header': primary['host_header'],
        'ssl_name': primary['ssl_name'],
        'resolver': resolver,
        'resolve': primary['resolve'],
        'servers': parsed_servers,
    }


def _resolve_server_urls_list(servers: list, fallback_url: str) -> list:
    urls = []
    for s in servers or []:
        raw_u = v5_7.OpenAPIParser.OpenAPIParser._resolve_server_url(
            s.get('url') or '', s.get('variables')
        ).strip()
        if raw_u:
            urls.append(_normalize_gateway_url(raw_u, fallback_url))
    return urls


def _resolve_api_gateway_upstream(ctx: ConfigBuildContext, server: dict, loc: dict, api_gateway_declaration: dict):
    """Derives the NGINX HTTP upstream metadata for an API Gateway, supporting root,
    per-path, and per-operation servers with server variables and statistics collection.

    Returns an (error, upstream_info_dict) tuple.
    """
    srv_name = server.get('name') or (server['names'][0] if server.get('names') else 'server')
    server_header_name = server['names'][0] if server.get('names') else srv_name
    uri_slug = loc.get('uri', '').strip('/') or 'root'
    server_url = ((loc.get('apigateway') or {}).get('api_gateway') or {}).get('server_url') or ''
    server_url = server_url.strip()

    top_servers = api_gateway_declaration.get('servers') or []
    default_dest_urls = _resolve_server_urls_list(top_servers, server_url)
    if not default_dest_urls and server_url:
        default_dest_urls.append(server_url)

    path_fallback_server_url = server_url
    if not path_fallback_server_url and default_dest_urls:
        parsed_def = urlparse(default_dest_urls[0])
        if parsed_def.scheme and parsed_def.netloc:
            path_fallback_server_url = f"{parsed_def.scheme}://{parsed_def.netloc}"

    def _has_server_urls(servers_list):
        return any((s.get('url') or '').strip() for s in (servers_list or []))

    paths = api_gateway_declaration.get('paths') or []
    any_path_uses_default = (not paths) or any(
        (not _has_server_urls(p.get('servers'))) and (
            not p.get('methods') or any(not _has_server_urls(m.get('servers')) for m in p.get('methods'))
        )
        for p in paths
    )

    default_upstream = None
    if default_dest_urls and (any_path_uses_default or bool(top_servers)):
        default_base_name = f"apigw_{srv_name}_{uri_slug}"
        err, default_upstream = _build_upstream_info(ctx, server, loc, default_base_name, default_dest_urls)
        if err is not None:
            return err, None
    elif any_path_uses_default:
        return _validation_error(
            f"missing API Gateway destination server URL in location [{loc.get('uri', '')}]"), None

    extra_upstreams = []
    for p in paths:
        methods = p.get('methods') or []
        raw_path_slug = re.sub(r'[^a-zA-Z0-9_-]', '_', p.get('path', '').strip('/'))
        path_slug = re.sub(r'_+', '_', raw_path_slug).strip('_') or 'root'

        path_dest_urls = _resolve_server_urls_list(p.get('servers') or [], path_fallback_server_url)
        any_method_uses_path = (not methods) or any(not _has_server_urls(m.get('servers')) for m in methods)

        p_upstream = None
        if path_dest_urls and any_method_uses_path:
            path_base_name = f"apigw_{srv_name}_{uri_slug}_{path_slug}"
            err, p_upstream = _build_upstream_info(ctx, server, loc, path_base_name, path_dest_urls)
            if err is not None:
                return err, None
            extra_upstreams.append(p_upstream)

        op_fallback_url = path_fallback_server_url
        if not op_fallback_url and path_dest_urls:
            parsed_path_def = urlparse(path_dest_urls[0])
            if parsed_path_def.scheme and parsed_path_def.netloc:
                op_fallback_url = f"{parsed_path_def.scheme}://{parsed_path_def.netloc}"

        method_upstreams = []
        for m in methods:
            m_dest_urls = _resolve_server_urls_list(m.get('servers') or [], op_fallback_url)
            if m_dest_urls:
                m_name = m.get('method', '').lower()
                m_base_name = f"apigw_{srv_name}_{uri_slug}_{path_slug}_{m_name}"
                err, m_upstream = _build_upstream_info(ctx, server, loc, m_base_name, m_dest_urls)
                if err is not None:
                    return err, None
                m['upstream'] = m_upstream
                method_upstreams.append(m_upstream)
                extra_upstreams.append(m_upstream)
            else:
                m['upstream'] = None

        base_path_upstream = p_upstream if p_upstream is not None else default_upstream
        if method_upstreams and len(method_upstreams) == len(methods) and len(methods) == 1:
            p['upstream'] = method_upstreams[0]
            p['use_method_upstreams'] = False
        elif method_upstreams:
            for m in methods:
                m['effective_upstream'] = m['upstream'] if m['upstream'] is not None else base_path_upstream
            p['upstream'] = base_path_upstream if base_path_upstream is not None else method_upstreams[0]
            p['use_method_upstreams'] = True
            p['any_ssl_name'] = any(
                bool((m['effective_upstream'] or {}).get('ssl_name')) for m in methods
            ) or bool((p['upstream'] or {}).get('ssl_name'))
            p['var_suffix'] = re.sub(
                r'[^a-zA-Z0-9_]', '_',
                f"{server_header_name}{loc.get('uri', '')}{p.get('path', '')}"
            )
        else:
            p['upstream'] = base_path_upstream
            p['use_method_upstreams'] = False

    upstreams_to_render = []
    if default_upstream is not None:
        upstreams_to_render.append(default_upstream)
    upstreams_to_render.extend(extra_upstreams)

    primary_upstream = upstreams_to_render[0] if upstreams_to_render else default_upstream

    return None, {
        'primary': primary_upstream,
        'upstreams': upstreams_to_render,
    }


def _render_api_gateway_files(ctx: ConfigBuildContext, server, loc, api_gateway_declaration, enabled_visibility):
    server_name = server['names'][0] if server.get('names') else server['name']

    snippet = ctx.j2_env.get_template(NcgConfig.config['templates']['apigwconf']).render(
        declaration=api_gateway_declaration, server=server_name,
        enabledVisibility=enabled_visibility, ncgconfig=NcgConfig.config)
    ctx.configFiles['files'].append({
        'contents': _b64(snippet),
        'name': f"{NcgConfig.config['nms']['apigw_dir']}/{server_name}{loc['uri']}.conf"})

    maps_snippet = ctx.j2_env.get_template(NcgConfig.config['templates']['apigwmapsconf']).render(
        declaration=api_gateway_declaration, server=server_name, ncgconfig=NcgConfig.config)
    uri_for_filename = loc['uri'].replace('/', '_')
    ctx.configFiles['files'].append({
        'contents': _b64(maps_snippet),
        'name': f"{NcgConfig.config['nms']['apigw_maps_dir']}/{server_name}{uri_for_filename}.conf"})

    upstreams_snippet = ctx.j2_env.get_template(NcgConfig.config['templates']['apigwupstreamsconf']).render(
        declaration=api_gateway_declaration, server=server_name, ncgconfig=NcgConfig.config)
    ctx.configFiles['files'].append({
        'contents': _b64(upstreams_snippet),
        'name': f"{NcgConfig.config['nms']['apigw_upstreams_dir']}/{api_gateway_declaration['upstream']['name']}.conf"})


# ---------------------------------------------------------------------------
# API Gateway: developer portal
# ---------------------------------------------------------------------------

def _process_developer_portal(ctx: ConfigBuildContext, loc, openapi_schema_json):
    apigateway = loc.get('apigateway')
    dev_portal = apigateway.get('developer_portal') if apigateway else None
    if not (dev_portal and dev_portal.get('enabled')):
        return None

    portal_type = dev_portal.get('type', '').lower()
    if portal_type == 'redocly':
        return _process_redocly_developer_portal(ctx, loc)
    elif portal_type == 'backstage':
        _process_backstage_developer_portal(ctx, loc, openapi_schema_json)
    return None


def _process_redocly_developer_portal(ctx: ConfigBuildContext, loc):
    auth_profiles = (ctx.d.get('declaration') or {}).get('authentication')
    status, dev_portal_html = v5_7.DevPortal.createDevPortal(locationDeclaration=loc, authProfiles=auth_profiles)
    if status != 200:
        return {"status_code": 412,
                "message": {"status_code": status,
                            "message": {"code": status,
                                       "content": f"Developer Portal creation failed for {loc['uri']}"}}}

    ctx.auxFiles['files'].append({
        'contents': dev_portal_html,
        'name': NcgConfig.config['nms']['devportal_dir'] + loc['apigateway']['developer_portal']['redocly']['uri']})
    return None


def _process_backstage_developer_portal(ctx: ConfigBuildContext, loc, openapi_schema_json):
    template_name = f"{NcgConfig.config['templates']['devportal_root']}/backstage.tmpl"
    manifest = ctx.j2_env.get_template(template_name).render(
        declaration=loc['apigateway']['developer_portal']['backstage'],
        openAPISchema=v5_7.MiscUtils.json_to_yaml(openapi_schema_json),
        ncgconfig=NcgConfig.config)
    ctx.extraOutputManifests.append(manifest)


# ---------------------------------------------------------------------------
# Layer4 / stream
# ---------------------------------------------------------------------------

def _process_layer4(ctx: ConfigBuildContext):
    declaration = ctx.d.get('declaration') or {}
    if 'layer4' not in declaration or not declaration.get('layer4'):
        return None

    error = _process_layer4_upstreams(ctx)
    if error is not None:
        return error

    return _process_layer4_servers(ctx)


def _process_layer4_upstreams(ctx: ConfigBuildContext):
    d_upstreams = v5_7.MiscUtils.getDictKey(ctx.d, 'declaration.layer4.upstreams')
    if not d_upstreams:
        return None

    layer4 = (ctx.d.get('declaration') or {}).get('layer4') or {}
    auth_profiles = layer4.get('authentication')
    for i, upstream in enumerate(d_upstreams):
        if upstream.get('resolver') and upstream['resolver'] not in ctx.all_resolver_profiles:
            return _validation_error(
                f"invalid resolver profile [{upstream['resolver']}] in stream upstream "
                f"[{upstream['name']}], must be one of {ctx.all_resolver_profiles}")

        if upstream.get('snippet'):
            status, snippet = v5_7.GitOps.getObjectFromRepo(object=upstream['snippet'], authProfiles=auth_profiles)
            if status != 200:
                return _gitops_error(status, snippet)
            d_upstreams[i]['snippet'] = snippet

        template_name = NcgConfig.config['templates']['upstream_stream']
        rendered = ctx.j2_env.get_template(template_name).render(u=upstream, ncgconfig=NcgConfig.config)
        config_file_name = (NcgConfig.config['nms']['upstream_stream_dir'] + '/' +
                            upstream['name'].replace(' ', '_') + ".conf")
        ctx.configFiles['files'].append({'contents': _b64(rendered), 'name': config_file_name})
        ctx.all_layer4_upstreams.append(d_upstreams[i]['name'])

    return None


def _process_layer4_servers(ctx: ConfigBuildContext):
    d_servers = v5_7.MiscUtils.getDictKey(ctx.d, 'declaration.layer4.servers')
    if not d_servers:
        return None

    for server in d_servers:
        error = _process_layer4_server(ctx, server)
        if error is not None:
            return error
    return None


def _process_layer4_server(ctx: ConfigBuildContext, server):
    if server.get('resolver') and server['resolver'] not in ctx.all_resolver_profiles:
        return _validation_error(
            f"invalid resolver profile [{server['resolver']}] in stream server "
            f"[{server['name']}], must be one of {ctx.all_resolver_profiles}")

    if server.get('snippet'):
        auth_profiles = (ctx.d.get('declaration') or {}).get('authentication')
        status, snippet = v5_7.GitOps.getObjectFromRepo(object=server['snippet'], authProfiles=auth_profiles)
        if status != 200:
            return _gitops_error(status, snippet)
        server['snippet'] = snippet

    if server.get('upstream') and server['upstream'] not in ctx.all_layer4_upstreams:
        return _validation_error(f"invalid Layer4 upstream [{server['upstream']}]")

    rendered = ctx.j2_env.get_template(NcgConfig.config['templates']['server_stream']).render(
        s=server, ncgconfig=NcgConfig.config)
    config_file_name = (NcgConfig.config['nms']['server_stream_dir'] + '/' +
                        server['name'].replace(' ', '_') + ".conf")
    ctx.configFiles['files'].append({'contents': _b64(rendered), 'name': config_file_name})

    return None
