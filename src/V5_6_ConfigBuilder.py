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
from urllib.parse import urlparse

import v5_6.APIGateway
import v5_6.DevPortal
import v5_6.GitOps
import v5_6.MiscUtils
import v5_6.NGINXOneOutput
import v5_6.NIMOutput
from jinja2 import Environment, FileSystemLoader

from NcgConfig import NcgConfig


# ---------------------------------------------------------------------------
# Shared state
# ---------------------------------------------------------------------------

class ConfigBuildContext:
    """Holds the mutable state shared by the build helper functions for a
    single createconfig() invocation."""

    def __init__(self, d: dict, apiversion: str):
        self.d = d
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
    j2_env.filters['regex_replace'] = v5_6.MiscUtils.regex_replace
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
    """Renders the final http/stream configs and publishes them to the
    configured output (NGINX Instance Manager or NGINX One Console)."""
    b64_http_conf, b64_stream_conf = _render_main_configs(ctx)

    decltype_lower = decltype.lower()
    if decltype_lower == 'nms':
        ctx.configFiles['rootDir'] = NcgConfig.config['nms']['config_dir']
        ctx.auxFiles['rootDir'] = NcgConfig.config['nms']['config_dir']
        final_reply = v5_6.NIMOutput.NIMOutput(
            d=ctx.d, declaration=declaration, apiversion=apiversion,
            b64HttpConf=b64_http_conf, b64StreamConf=b64_stream_conf,
            configFiles=ctx.configFiles, auxFiles=ctx.auxFiles,
            runfromautosync=runfromautosync, configUid=configUid)
    elif decltype_lower == 'nginxone':
        ctx.configFiles['name'] = NcgConfig.config['nms']['config_dir']
        ctx.auxFiles['name'] = NcgConfig.config['nms']['config_dir']
        final_reply = v5_6.NGINXOneOutput.NGINXOneOutput(
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
    declaration = ctx.d['declaration']

    http_conf = ''
    if 'http' in declaration:
        http_conf = ctx.j2_env.get_template(NcgConfig.config['templates']['httpconf']).render(
            declaration=declaration['http'], ncgconfig=NcgConfig.config)

    stream_conf = ''
    if 'layer4' in declaration:
        stream_conf = ctx.j2_env.get_template(NcgConfig.config['templates']['streamconf']).render(
            declaration=declaration['layer4'], ncgconfig=NcgConfig.config)

    return _b64(http_conf), _b64(stream_conf)


# ---------------------------------------------------------------------------
# Resolver profiles
# ---------------------------------------------------------------------------

def _process_resolvers(ctx: ConfigBuildContext):
    if 'resolvers' not in ctx.d['declaration']:
        return

    d_resolver_profiles = v5_6.MiscUtils.getDictKey(ctx.d, 'declaration.resolvers')
    if d_resolver_profiles is None:
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
    if 'http' not in ctx.d['declaration']:
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
    http = ctx.d['declaration']['http']
    if 'snippet' not in http:
        return None

    status, snippet = v5_6.GitOps.getObjectFromRepo(object=http['snippet'], authProfiles=http['authentication'])
    if status != 200:
        return _gitops_error(status, snippet)
    http['snippet'] = snippet
    return None


def _process_http_upstreams(ctx: ConfigBuildContext):
    http = ctx.d['declaration']['http']
    upstreams = http.get('upstreams')
    if not upstreams:
        return None

    for i, upstream in enumerate(upstreams):
        if upstream['resolver'] and upstream['resolver'] not in ctx.all_resolver_profiles:
            return _validation_error(
                f"invalid resolver profile [{upstream['resolver']}] in HTTP upstream "
                f"[{upstream['name']}], must be one of {ctx.all_resolver_profiles}")

        if upstream['snippet']:
            status, snippet = v5_6.GitOps.getObjectFromRepo(
                object=upstream['snippet'], authProfiles=http['authentication'])
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
    d_rate_limit = v5_6.MiscUtils.getDictKey(ctx.d, 'declaration.http.rate_limit')
    if d_rate_limit is None:
        return
    ctx.all_ratelimits.extend(rl['name'] for rl in d_rate_limit)


def _collect_cache_profiles(ctx: ConfigBuildContext):
    d_cache_profiles = v5_6.MiscUtils.getDictKey(ctx.d, 'declaration.http.cache')
    if d_cache_profiles is None:
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
    d_auth_profiles = v5_6.MiscUtils.getDictKey(ctx.d, 'declaration.http.authentication')
    if d_auth_profiles is None or 'client' not in d_auth_profiles:
        return

    for auth_profile in d_auth_profiles['client']:
        match auth_profile['type']:
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
    d_auth_profiles = v5_6.MiscUtils.getDictKey(ctx.d, 'declaration.http.authentication')
    if d_auth_profiles is None or 'server' not in d_auth_profiles:
        return

    for auth_profile in d_auth_profiles['server']:
        match auth_profile['type']:
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
    d_authz_profiles = v5_6.MiscUtils.getDictKey(ctx.d, 'declaration.http.authorization')
    if d_authz_profiles is None:
        return

    for authz_profile in d_authz_profiles:
        match authz_profile['type']:
            case 'jwt':
                _render_jwt_client_authz(ctx, authz_profile)


# ---------------------------------------------------------------------------
# NGINX Javascript (njs) profiles + ACME issuers
# ---------------------------------------------------------------------------

def _process_njs_profiles(ctx: ConfigBuildContext):
    d_njs_files = v5_6.MiscUtils.getDictKey(ctx.d, 'declaration.http.njs_profiles')
    if d_njs_files is None:
        return None

    auth_profiles = ctx.d['declaration']['http']['authentication']
    for njs_file in d_njs_files:
        njs_filename = njs_file['name'].replace(' ', '_')
        status, content = v5_6.GitOps.getObjectFromRepo(object=njs_file['file'], authProfiles=auth_profiles)
        if status != 200:
            return _gitops_error(status, content)
        ctx.auxFiles['files'].append({
            'contents': content['content'],
            'name': f"{NcgConfig.config['nms']['njs_dir']}/{njs_filename}.js"})
        ctx.all_njs_profiles.append(njs_filename)

    return None


def _process_acme_issuers(ctx: ConfigBuildContext):
    d_acme_issuers = v5_6.MiscUtils.getDictKey(ctx.d, 'declaration.http.acme_issuers')
    if d_acme_issuers is None:
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
    d_http_njs_hooks = v5_6.MiscUtils.getDictKey(ctx.d, 'declaration.http.njs')
    if d_http_njs_hooks is None:
        return None

    for hook in d_http_njs_hooks:
        if hook['profile'] not in ctx.all_njs_profiles:
            return _validation_error(
                f"invalid njs profile [{hook['profile']}] in HTTP declaration, "
                f"must be one of {ctx.all_njs_profiles}")
    return None


def _validate_http_resolver(ctx: ConfigBuildContext):
    d_http_resolver = v5_6.MiscUtils.getDictKey(ctx.d, 'declaration.http.resolver')
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
    d_servers = v5_6.MiscUtils.getDictKey(ctx.d, 'declaration.http.servers')
    if d_servers is None:
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
    if server['snippet']:
        error, server_snippet = _fetch_server_snippet(ctx, server)
        if error is not None:
            return error

    _render_http_server_conf(ctx, server)

    for loc in server['locations']:
        error = _process_location(ctx, server, loc)
        if error is not None:
            return error

    # Preserves the original behaviour of re-encoding the server snippet
    # contents after every location has been processed.
    server['snippet']['content'] = _b64(server_snippet)

    return None


def _validate_server(ctx: ConfigBuildContext, server):
    if server['resolver'] and server['resolver'] not in ctx.all_resolver_profiles:
        return _validation_error(
            f"invalid resolver profile [{server['resolver']}] in HTTP server "
            f"[{server['name']}], must be one of {ctx.all_resolver_profiles}")

    if server['cache']:
        profile = server['cache']['profile']
        if profile not in ctx.all_cache_profiles and profile != "":
            return _validation_error(
                f"invalid cache profile [{profile}] in HTTP server "
                f"[{server['name']}], must be one of {ctx.all_cache_profiles}")

    if server['njs']:
        for hook in server['njs']:
            if hook['profile'] not in ctx.all_njs_profiles:
                return _validation_error(
                    f"invalid njs profile [{hook['profile']}] in server "
                    f"[{server['name']}], must be one of {ctx.all_njs_profiles}")

    if server.get('authentication'):
        for auth_profile in server['authentication']['client']:
            if auth_profile['profile'] not in ctx.all_auth_client_profiles:
                return _validation_error(
                    f"invalid client authentication profile [{auth_profile['profile']}] "
                    f"in server [{server['name']}] must be one of {ctx.all_auth_client_profiles}")

    if server.get('authorization'):
        profile = server['authorization']['profile']
        if profile and profile not in ctx.all_authz_client_profiles:
            return _validation_error(
                f"invalid client authorization profile [{profile}] in server "
                f"[{server['name']}] must be one of {ctx.all_authz_client_profiles}")

    tls = server['listen']['tls']
    if 'authentication' in tls and 'client' in tls['authentication']:
        for mtls_profile in tls['authentication']['client']:
            if mtls_profile['profile'] not in ctx.all_auth_client_profiles:
                return _validation_error(
                    f"invalid client authentication profile [{mtls_profile['profile']}] "
                    f"in server [{server['name']}] must be one of {ctx.all_auth_client_profiles}")

    if 'acme_issuer' in tls:
        acme_issuer = tls['acme_issuer']
        if acme_issuer and acme_issuer not in ctx.all_acme_issuers:
            return _validation_error(
                f"invalid ACME issuer [{acme_issuer}] in server "
                f"[{server['name']}] must be one of {ctx.all_acme_issuers}")

    return None


def _fetch_server_snippet(ctx: ConfigBuildContext, server):
    auth_profiles = ctx.d['declaration']['http']['authentication']
    status, server_snippet = v5_6.GitOps.getObjectFromRepo(
        object=server['snippet'], authProfiles=auth_profiles, base64Encode=False)
    if status != 200:
        return _gitops_error(status, server_snippet), ''
    return None, server_snippet['content']


def _render_http_server_conf(ctx: ConfigBuildContext, server):
    rendered = ctx.j2_env.get_template(NcgConfig.config['templates']['server_http']).render(
        declaration=ctx.d['declaration']['http'], s=server, ncgconfig=NcgConfig.config)
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
    if not loc['njs']:
        return None
    for hook in loc['njs']:
        if hook['profile'] not in ctx.all_njs_profiles:
            return _validation_error(
                f"invalid njs profile [{hook['profile']}] in location "
                f"[{loc['uri']}], must be one of {ctx.all_njs_profiles}")
    return None


def _process_location_snippet(ctx: ConfigBuildContext, loc):
    if not loc['snippet']:
        return None
    auth_profiles = ctx.d['declaration']['http']['authentication']
    status, snippet = v5_6.GitOps.getObjectFromRepo(object=loc['snippet'], authProfiles=auth_profiles)
    if status != 200:
        return _gitops_error(status, snippet)
    loc['snippet'] = snippet
    return None


def _validate_location_upstream(ctx: ConfigBuildContext, loc):
    if 'upstream' in loc and loc['upstream'] and urlparse(loc['upstream']).netloc not in ctx.all_http_upstreams:
        return _validation_error(f"invalid HTTP upstream [{loc['upstream']}]")
    return None


def _validate_location_auth_client(ctx: ConfigBuildContext, loc):
    if 'authentication' in loc and loc['authentication']:
        for auth_profile in loc['authentication']['client']:
            if auth_profile['profile'] not in ctx.all_auth_client_profiles:
                return _validation_error(
                    f"invalid client authentication profile [{auth_profile['profile']}] "
                    f"in location [{loc['uri']}] must be one of {ctx.all_auth_client_profiles}")
    return None


def _validate_location_authz(ctx: ConfigBuildContext, loc):
    if 'authorization' in loc and loc['authorization']:
        profile = loc['authorization']['profile']
        if profile and profile not in ctx.all_authz_client_profiles:
            return _validation_error(
                f"invalid client authorization profile [{profile}] in location "
                f"[{loc['uri']}] must be one of {ctx.all_authz_client_profiles}")
    return None


def _validate_location_auth_server(ctx: ConfigBuildContext, loc):
    if 'authentication' in loc and loc['authentication']:
        for auth_profile in loc['authentication']['server']:
            if auth_profile['profile'] not in ctx.all_auth_server_profiles:
                return _validation_error(
                    f"invalid server authentication profile [{auth_profile['profile']}] "
                    f"in location [{loc['uri']}]")
    return None


def _validate_location_rate_limit(ctx: ConfigBuildContext, loc):
    rate_limit = loc['rate_limit']
    if rate_limit and rate_limit.get('profile') and rate_limit['profile'] not in ctx.all_ratelimits:
        return _validation_error(f"invalid rate_limit profile [{rate_limit['profile']}]")
    return None


def _validate_location_cache(ctx: ConfigBuildContext, loc):
    cache = loc['cache']
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
    apigateway = loc['apigateway']
    if not (apigateway and apigateway['visibility']):
        return enabled_integrations

    for vis in apigateway['visibility']:
        if not vis['enabled']:
            continue
        enabled_integrations[vis['type']] = True
        if vis['type'].lower() == 'moesif':
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
    apigateway = loc['apigateway']
    schema_content = apigateway['openapi_schema']['content']

    if apigateway['authentication'] and apigateway['authentication']['client']:
        for profile in apigateway['authentication']['client']:
            if profile['profile'] not in ctx.all_auth_client_profiles:
                return _validation_error(
                    f"invalid API Gateway authentication profile [{profile['profile']}] "
                    f"for OpenAPI schema [{schema_content}] must be one of {ctx.all_auth_client_profiles}")

    if apigateway['authorization']:
        for profile in apigateway['authorization']:
            if profile['profile'] not in ctx.all_authz_client_profiles:
                return _validation_error(
                    f"invalid API Gateway authorization profile [{profile['profile']}] "
                    f"for OpenAPI schema [{schema_content}] must be one of {ctx.all_authz_client_profiles}")

    if apigateway['rate_limit']:
        for profile in apigateway['rate_limit']:
            if profile['profile'] not in ctx.all_ratelimits:
                return _validation_error(
                    f"invalid API Gateway rate limit profile [{profile['profile']}] "
                    f"for OpenAPI schema [{schema_content}] must be one of {ctx.all_ratelimits}")

    openapi_auth_profile = apigateway['openapi_schema']['authentication']
    if openapi_auth_profile and openapi_auth_profile[0]['profile'] not in ctx.all_auth_server_profiles:
        return _validation_error(
            f"invalid server authentication profile [{openapi_auth_profile[0]['profile']}] "
            f"for OpenAPI schema [{schema_content}]")

    return None


def _process_api_gateway_provisioning(ctx: ConfigBuildContext, server, loc, enabled_visibility):
    """Provisions the API Gateway configuration for a location, if enabled.

    Returns a (error, openAPISchemaJSON) tuple.
    """
    apigateway = loc['apigateway']
    api_gateway_settings = apigateway.get('api_gateway') if apigateway else None
    if not (api_gateway_settings and api_gateway_settings.get('enabled')):
        return None, None

    error = _validate_api_gateway_profiles(ctx, loc)
    if error is not None:
        return error, None

    schema_content = apigateway['openapi_schema']['content']
    status, api_gateway_declaration, openapi_schema_json = v5_6.APIGateway.createAPIGateway(
        locationDeclaration=loc, authProfiles=apigateway['openapi_schema']['authentication'])
    if status != 200:
        return ({"status_code": 412,
                "message": {"status_code": status,
                            "message": {"code": status,
                                       "content": f"OpenAPI schema fetch failed for {schema_content}"}}},
                None)

    if api_gateway_declaration:
        _render_api_gateway_files(ctx, server, loc, api_gateway_declaration, enabled_visibility)

    return None, openapi_schema_json


def _render_api_gateway_files(ctx: ConfigBuildContext, server, loc, api_gateway_declaration, enabled_visibility):
    server_name = server['names'][0]

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


# ---------------------------------------------------------------------------
# API Gateway: developer portal
# ---------------------------------------------------------------------------

def _process_developer_portal(ctx: ConfigBuildContext, loc, openapi_schema_json):
    apigateway = loc['apigateway']
    dev_portal = apigateway.get('developer_portal') if apigateway else None
    if not (dev_portal and dev_portal.get('enabled')):
        return None

    portal_type = dev_portal['type'].lower()
    if portal_type == 'redocly':
        return _process_redocly_developer_portal(ctx, loc)
    elif portal_type == 'backstage':
        _process_backstage_developer_portal(ctx, loc, openapi_schema_json)
    return None


def _process_redocly_developer_portal(ctx: ConfigBuildContext, loc):
    auth_profiles = ctx.d['declaration']['http']['authentication']
    status, dev_portal_html = v5_6.DevPortal.createDevPortal(locationDeclaration=loc, authProfiles=auth_profiles)
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
        openAPISchema=v5_6.MiscUtils.json_to_yaml(openapi_schema_json),
        ncgconfig=NcgConfig.config)
    ctx.extraOutputManifests.append(manifest)


# ---------------------------------------------------------------------------
# Layer4 / stream
# ---------------------------------------------------------------------------

def _process_layer4(ctx: ConfigBuildContext):
    if 'layer4' not in ctx.d['declaration']:
        return None

    error = _process_layer4_upstreams(ctx)
    if error is not None:
        return error

    return _process_layer4_servers(ctx)


def _process_layer4_upstreams(ctx: ConfigBuildContext):
    d_upstreams = v5_6.MiscUtils.getDictKey(ctx.d, 'declaration.layer4.upstreams')
    if d_upstreams is None:
        return None

    auth_profiles = ctx.d['declaration']['http']['authentication']
    for i, upstream in enumerate(d_upstreams):
        if upstream['resolver'] and upstream['resolver'] not in ctx.all_resolver_profiles:
            return _validation_error(
                f"invalid resolver profile [{upstream['resolver']}] in stream upstream "
                f"[{upstream['name']}], must be one of {ctx.all_resolver_profiles}")

        if upstream['snippet']:
            status, snippet = v5_6.GitOps.getObjectFromRepo(object=upstream['snippet'], authProfiles=auth_profiles)
            if status != 200:
                return _gitops_error(status, snippet)
            ctx.d['declaration']['layer4']['upstreams'][i]['snippet'] = snippet

        template_name = NcgConfig.config['templates']['upstream_stream']
        rendered = ctx.j2_env.get_template(template_name).render(u=upstream, ncgconfig=NcgConfig.config)
        config_file_name = (NcgConfig.config['nms']['upstream_stream_dir'] + '/' +
                            upstream['name'].replace(' ', '_') + ".conf")
        ctx.configFiles['files'].append({'contents': _b64(rendered), 'name': config_file_name})
        ctx.all_layer4_upstreams.append(d_upstreams[i]['name'])

    return None


def _process_layer4_servers(ctx: ConfigBuildContext):
    d_servers = v5_6.MiscUtils.getDictKey(ctx.d, 'declaration.layer4.servers')
    if d_servers is None:
        return None

    for server in d_servers:
        error = _process_layer4_server(ctx, server)
        if error is not None:
            return error
    return None


def _process_layer4_server(ctx: ConfigBuildContext, server):
    if server['resolver'] and server['resolver'] not in ctx.all_resolver_profiles:
        return _validation_error(
            f"invalid resolver profile [{server['resolver']}] in stream server "
            f"[{server['name']}], must be one of {ctx.all_resolver_profiles}")

    if server['snippet']:
        auth_profiles = ctx.d['declaration']['http']['authentication']
        status, snippet = v5_6.GitOps.getObjectFromRepo(object=server['snippet'], authProfiles=auth_profiles)
        if status != 200:
            return _gitops_error(status, snippet)
        server['snippet'] = snippet

    if 'upstream' in server and server['upstream'] and server['upstream'] not in ctx.all_layer4_upstreams:
        return _validation_error(f"invalid Layer4 upstream {server['upstream']}")

    rendered = ctx.j2_env.get_template(NcgConfig.config['templates']['server_stream']).render(
        s=server, ncgconfig=NcgConfig.config)
    config_file_name = (NcgConfig.config['nms']['server_stream_dir'] + '/' +
                        server['name'].replace(' ', '_') + ".conf")
    ctx.configFiles['files'].append({'contents': _b64(rendered), 'name': config_file_name})

    return None
