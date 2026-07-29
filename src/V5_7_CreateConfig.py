import json
import pickle

from fastapi.responses import JSONResponse
from pydantic import ValidationError
from requests.packages.urllib3.exceptions import InsecureRequestWarning
import requests

import v5_7.DeclarationPatcher
import v5_7.MiscUtils

from NcgRedis import NcgRedis

# pydantic models
from V5_7_NginxConfigDeclaration import *

from V5_7_ConfigBuilder import ConfigBuildContext, build_config_files, dispatch_output

# Tolerates self-signed TLS certificates
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


def configautosync(configUid):
    print("Autosyncing configuid [" + configUid + "]")

    declaration = ''
    decl_from_redis = NcgRedis.redis.get(f'ncg.declaration.{configUid}')
    if decl_from_redis is not None:
        declaration = pickle.loads(decl_from_redis)

    apiversion = NcgRedis.redis.get(f'ncg.apiversion.{configUid}').decode()
    createconfig(declaration=declaration, apiversion=apiversion, runfromautosync=True, configUid=configUid)


# Create the given declarative configuration
# Return a JSON string:
# { "status_code": nnn, "headers": {}, "message": {} }
def createconfig(declaration: ConfigDeclaration, apiversion: str, runfromautosync: bool = False, configUid: str = ""):
    try:
        # Pydantic JSON validation
        ConfigDeclaration(**declaration.model_dump())
    except ValidationError as e:
        print(f"Invalid declaration {e}")

    d = declaration.model_dump()
    decltype = d['output']['type']

    ctx = ConfigBuildContext(d=d, apiversion=apiversion)

    error = build_config_files(ctx)
    if error is not None:
        return error

    return dispatch_output(ctx=ctx, decltype=decltype, declaration=declaration, apiversion=apiversion,
                           runfromautosync=runfromautosync, configUid=configUid)


# ---------------------------------------------------------------------------
# Section Patch Handlers
# ---------------------------------------------------------------------------

def _apply_nap_policy_patches(declaration_to_patch, current_declaration):
    # F5 WAF for NGINX policy updates
    policies = v5_7.MiscUtils.getDictKey(declaration_to_patch, 'declaration.http.policies')
    if policies is None:
        return current_declaration
    for policy in policies:
        current_declaration = v5_7.DeclarationPatcher.patchNAPPolicies(
            sourceDeclaration=current_declaration, patchedNAPPolicies=policy)
    return current_declaration


def _apply_certificate_patches(declaration_to_patch, current_declaration):
    # Patch .declaration.certificates
    certificates = v5_7.MiscUtils.getDictKey(declaration_to_patch, 'declaration.certificates')
    if not certificates or not isinstance(certificates, list):
        return current_declaration

    for cert in certificates:
        current_declaration = v5_7.DeclarationPatcher.patchCertificates(
            sourceDeclaration=current_declaration, patchedCertificates=cert
        )
    return current_declaration


def _apply_resolvers_patches(declaration_to_patch, current_declaration):
    # Patch .declaration.resolvers
    resolvers = v5_7.MiscUtils.getDictKey(declaration_to_patch, 'declaration.resolvers')
    if not resolvers or not isinstance(resolvers, list):
        return current_declaration

    for resolver in resolvers:
        current_declaration = v5_7.DeclarationPatcher._patch_section_item(
            current_declaration, ['declaration', 'resolvers'], resolver
        )
    return current_declaration


def _apply_authentication_patches(declaration_to_patch, current_declaration):
    # Patch .declaration.authentication (client and server)
    auth = v5_7.MiscUtils.getDictKey(declaration_to_patch, 'declaration.authentication')
    if not auth or not isinstance(auth, dict):
        return current_declaration

    for auth_type in ['client', 'server']:
        items = auth.get(auth_type)
        if items and isinstance(items, list):
            for item in items:
                current_declaration = v5_7.DeclarationPatcher._patch_section_item(
                    current_declaration, ['declaration', 'authentication', auth_type], item
                )
    return current_declaration


def _apply_authorization_patches(declaration_to_patch, current_declaration):
    # Patch .declaration.authorization
    authz = v5_7.MiscUtils.getDictKey(declaration_to_patch, 'declaration.authorization')
    if not authz or not isinstance(authz, list):
        return current_declaration

    for item in authz:
        current_declaration = v5_7.DeclarationPatcher._patch_section_item(
            current_declaration, ['declaration', 'authorization'], item
        )
    return current_declaration


def _apply_http_patches(declaration_to_patch, current_declaration):
    # Patch all profiles under .declaration.http
    http_patch = v5_7.MiscUtils.getDictKey(declaration_to_patch, 'declaration.http')
    if not http_patch or not isinstance(http_patch, dict):
        return current_declaration

    if 'declaration' not in current_declaration or not isinstance(current_declaration['declaration'], dict):
        current_declaration['declaration'] = {}
    if 'http' not in current_declaration['declaration'] or not isinstance(current_declaration['declaration']['http'], dict):
        current_declaration['declaration']['http'] = {}

    curr_http = current_declaration['declaration']['http']

    # 1. Named list profiles under .declaration.http
    named_list_fields = [
        'upstreams', 'servers', 'policies', 'caching', 'rate_limit',
        'njs_profiles', 'cache', 'logformats', 'acme_issuers', 'log_profiles'
    ]

    for field in named_list_fields:
        items = http_patch.get(field)
        if items and isinstance(items, list):
            for item in items:
                current_declaration = v5_7.DeclarationPatcher._patch_section_item(
                    current_declaration, ['declaration', 'http', field], item
                )

    # 2. Maps (keyed by variable or match if name is absent)
    maps = http_patch.get('maps')
    if maps and isinstance(maps, list):
        for m in maps:
            if 'name' not in m:
                m['name'] = m.get('variable') or m.get('match')
            current_declaration = v5_7.DeclarationPatcher._patch_section_item(
                current_declaration, ['declaration', 'http', 'maps'], m
            )

    # 3. Scalar and dictionary fields under .declaration.http
    for field in ['snippet', 'nginx_plus_api', 'resolver']:
        if field in http_patch and http_patch[field] is not None:
            curr_http[field] = http_patch[field]

    return current_declaration


def _apply_layer4_patches(declaration_to_patch, current_declaration):
    upstreams = v5_7.MiscUtils.getDictKey(declaration_to_patch, 'declaration.layer4.upstreams')
    if upstreams:
        for upstream in upstreams:
            current_declaration = v5_7.DeclarationPatcher.patchStreamUpstream(
                sourceDeclaration=current_declaration, patchedStreamUpstream=upstream)

    servers = v5_7.MiscUtils.getDictKey(declaration_to_patch, 'declaration.layer4.servers')
    if servers:
        for server in servers:
            current_declaration = v5_7.DeclarationPatcher.patchStreamServer(
                sourceDeclaration=current_declaration, patchedStreamServer=server)

    return current_declaration


# ---------------------------------------------------------------------------
# Declaration patching (PATCH /config/{configUid})
# ---------------------------------------------------------------------------

def patch_config(declaration: ConfigDeclaration, configUid: str, apiversion: str):
    if configUid not in NcgRedis.declarationsList:
        return JSONResponse(
            status_code=404,
            content={'code': 404, 'details': {'message': f'declaration {configUid} not found'}},
            headers={'Content-Type': 'application/json'}
        )

    declaration_to_patch = declaration.model_dump()
    _, current_declaration = get_declaration(configUid=configUid)

    # Snapshot current state to detect changes across all sections
    previous_declaration_json = json.dumps(current_declaration, sort_keys=True)

    # Apply patches across all supported sections
    current_declaration = _apply_nap_policy_patches(declaration_to_patch, current_declaration)
    current_declaration = _apply_certificate_patches(declaration_to_patch, current_declaration)
    current_declaration = _apply_resolvers_patches(declaration_to_patch, current_declaration)
    current_declaration = _apply_authentication_patches(declaration_to_patch, current_declaration)
    current_declaration = _apply_authorization_patches(declaration_to_patch, current_declaration)

    if 'declaration' in declaration_to_patch and declaration_to_patch['declaration']:
        current_declaration = _apply_http_patches(declaration_to_patch, current_declaration)
        current_declaration = _apply_layer4_patches(declaration_to_patch, current_declaration)

    # If the declaration changed anywhere, invalidate cached baseStagedConfig in Redis
    # to force NIMOutput/NGINXOneOutput to process and publish changes
    new_declaration_json = json.dumps(current_declaration, sort_keys=True)
    if previous_declaration_json != new_declaration_json:
        NcgRedis.redis.delete(f'ncg.basestagedconfig.{configUid}')

    # Apply the updated declaration
    config_declaration = ConfigDeclaration.model_validate_json(json.dumps(current_declaration))
    result = createconfig(declaration=config_declaration, apiversion=apiversion,
                          runfromautosync=True, configUid=configUid)

    message = result['message']
    if result['status_code'] != 200:
        current_declaration = {}

    response_content = {'code': result['status_code'], 'details': {'message': message},
                        'declaration': current_declaration, 'configUid': configUid}
    return JSONResponse(
        status_code=result['status_code'],
        content=response_content,
        headers={'Content-Type': 'application/json'}
    )


def get_declaration(configUid: str):
    cfg = NcgRedis.redis.get('ncg.declaration.' + configUid)
    if cfg is None:
        return 404, ""
    unpickled = pickle.loads(cfg)
    decl_dict = unpickled.model_dump() if hasattr(unpickled, 'model_dump') else unpickled.dict()
    return 200, decl_dict
