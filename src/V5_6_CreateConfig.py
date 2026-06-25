import json
import pickle

from fastapi.responses import JSONResponse
from pydantic import ValidationError
from requests.packages.urllib3.exceptions import InsecureRequestWarning
import requests

import v5_6.DeclarationPatcher
import v5_6.MiscUtils

from NcgRedis import NcgRedis

# pydantic models
from V5_6_NginxConfigDeclaration import *

from V5_6_ConfigBuilder import ConfigBuildContext, build_config_files, dispatch_output

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
# Declaration patching (PATCH /config/{configUid})
# ---------------------------------------------------------------------------

def _apply_nap_policy_patches(declaration_to_patch, current_declaration):
    # F5 WAF for NGINX policy updates
    policies = v5_6.MiscUtils.getDictKey(declaration_to_patch, 'declaration.http.policies')
    if policies is None:
        return current_declaration
    for policy in policies:
        current_declaration = v5_6.DeclarationPatcher.patchNAPPolicies(
            sourceDeclaration=current_declaration, patchedNAPPolicies=policy)
    return current_declaration


def _apply_certificate_patches(declaration_to_patch, current_declaration):
    # TLS certificate/key updates
    certificates = v5_6.MiscUtils.getDictKey(declaration_to_patch, 'declaration.certificates')
    if certificates is None:
        return current_declaration
    for certificate in certificates:
        current_declaration = v5_6.DeclarationPatcher.patchCertificates(
            sourceDeclaration=current_declaration, patchedCertificates=certificate)
    return current_declaration


def _apply_http_patches(declaration_to_patch, current_declaration):
    upstreams = v5_6.MiscUtils.getDictKey(declaration_to_patch, 'declaration.http.upstreams')
    if upstreams:
        for upstream in upstreams:
            current_declaration = v5_6.DeclarationPatcher.patchHttpUpstream(
                sourceDeclaration=current_declaration, patchedHttpUpstream=upstream)

    servers = v5_6.MiscUtils.getDictKey(declaration_to_patch, 'declaration.http.servers')
    if servers:
        for server in servers:
            current_declaration = v5_6.DeclarationPatcher.patchHttpServer(
                sourceDeclaration=current_declaration, patchedHttpServer=server)

    return current_declaration


def _apply_layer4_patches(declaration_to_patch, current_declaration):
    upstreams = v5_6.MiscUtils.getDictKey(declaration_to_patch, 'declaration.layer4.upstreams')
    if upstreams:
        for upstream in upstreams:
            current_declaration = v5_6.DeclarationPatcher.patchStreamUpstream(
                sourceDeclaration=current_declaration, patchedStreamUpstream=upstream)

    servers = v5_6.MiscUtils.getDictKey(declaration_to_patch, 'declaration.layer4.servers')
    if servers:
        for server in servers:
            current_declaration = v5_6.DeclarationPatcher.patchStreamServer(
                sourceDeclaration=current_declaration, patchedStreamServer=server)

    return current_declaration


def patch_config(declaration: ConfigDeclaration, configUid: str, apiversion: str):
    # Patch a declaration
    if configUid not in NcgRedis.declarationsList:
        return JSONResponse(
            status_code=404,
            content={'code': 404, 'details': {'message': f'declaration {configUid} not found'}},
            headers={'Content-Type': 'application/json'}
        )

    # The declaration sections to be patched
    declaration_to_patch = declaration.model_dump()

    # The currently applied declaration
    _, current_declaration = get_declaration(configUid=configUid)

    current_declaration = _apply_nap_policy_patches(declaration_to_patch, current_declaration)
    current_declaration = _apply_certificate_patches(declaration_to_patch, current_declaration)

    if 'declaration' in declaration_to_patch:
        current_declaration = _apply_http_patches(declaration_to_patch, current_declaration)
        current_declaration = _apply_layer4_patches(declaration_to_patch, current_declaration)

    # Apply the updated declaration
    config_declaration = ConfigDeclaration.model_validate_json(json.dumps(current_declaration))
    result = createconfig(declaration=config_declaration, apiversion=apiversion,
                          runfromautosync=True, configUid=configUid)

    # Return the updated declaration
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


# Gets the given declaration. Returns status_code and body
def get_declaration(configUid: str):
    cfg = NcgRedis.redis.get('ncg.declaration.' + configUid)
    if cfg is None:
        return 404, ""
    return 200, pickle.loads(cfg).dict()
