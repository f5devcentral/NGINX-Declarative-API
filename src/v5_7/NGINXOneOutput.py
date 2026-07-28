"""
Output to NGINX One console
"""

import base64
import requests
import json
import pickle
import time
import schedule
from typing import Dict, Any, Tuple, Optional
from jinja2 import Environment, FileSystemLoader
from urllib.parse import urlparse

import V5_7_CreateConfig

import v5_7.APIGateway
import v5_7.DevPortal
import v5_7.DeclarationPatcher
import v5_7.GitOps
import v5_7.MiscUtils
import v5_7.NGINXOneUtils

# pydantic models
from V5_7_NginxConfigDeclaration import *

# F5 WAF for NGINX helper functions
import v5_7.NGINXOneNAPUtils

# NGINX Declarative API modules
from NcgConfig import NcgConfig
from NcgRedis import NcgRedis


def _validate_target_url_and_dns(d: dict) -> Tuple[Optional[dict], str, str, str, str, int]:
    """
    Validates URL scheme, hostname, DNS resolution, and synctime settings.

    Returns:
        Tuple[Optional[dict], str, str, str, str, int]:
        (Error response dict or None, nOneUrl, nOneToken, nOneConfigSyncGroup, nOneNamespace, nOneSynctime)
    """
    nOneToken = v5_7.MiscUtils.getDictKey(d, 'output.nginxone.token')
    nOneConfigSyncGroup = v5_7.MiscUtils.getDictKey(d, 'output.nginxone.configsyncgroup')
    nOneNamespace = v5_7.MiscUtils.getDictKey(d, 'output.nginxone.namespace')
    nOneSynctime = v5_7.MiscUtils.getDictKey(d, 'output.nginxone.synctime')
    nOneUrlFromJson = v5_7.MiscUtils.getDictKey(d, 'output.nginxone.url')

    urlCheck = urlparse(nOneUrlFromJson)
    if urlCheck.scheme not in ['http', 'https'] or urlCheck.scheme == "" or urlCheck.hostname == "":
        return ({
            "status_code": 400,
            "message": {"status_code": 400, "message": {"code": 400, "content": f"invalid NGINX One URL {nOneUrlFromJson}"}},
            "headers": {'Content-Type': 'application/json'}
        }, "", "", "", "", 0)

    dnsOutcome, dnsReply = v5_7.MiscUtils.resolveFQDN(urlCheck.hostname)
    if not dnsOutcome:
        return ({
            "status_code": 400,
            "message": {"status_code": 400, "message": {"code": 400, "content": f"DNS resolution failed for {urlCheck.hostname}: {dnsReply}"}},
            "headers": {'Content-Type': 'application/json'}
        }, "", "", "", "", 0)

    if nOneSynctime < 0:
        return ({
            "status_code": 400,
            "message": {"status_code": 400, "message": {"code": 400, "content": "synctime must be >= 0"}},
            "headers": {'Content-Type': 'application/json'}
        }, "", "", "", "", 0)

    nOneUrl = f"{urlCheck.scheme}://{urlCheck.netloc}"
    return None, nOneUrl, nOneToken, nOneConfigSyncGroup, nOneNamespace, nOneSynctime


def _fetch_remote_policy_versions(d: dict) -> Optional[dict]:
    """
    Fetches F5 WAF for NGINX policies from source of truth if defined.

    Returns:
        Optional[dict]: Error response dictionary if fetching fails, otherwise None.
    """
    d_policies = v5_7.MiscUtils.getDictKey(d, 'declaration.http.policies')
    if d_policies is not None:
        for policy in d_policies:
            if 'versions' in policy:
                for policyVersion in policy['versions']:
                    auth = d.get('declaration', {}).get('authentication', {})
                    status, content = v5_7.GitOps.getObjectFromRepo(object=policyVersion['contents'], authProfiles=auth)
                    if status != 200:
                        return {"status_code": 422, "message": {"status_code": status, "message": content}}
                    policyVersion['contents'] = content
    return None


def _validate_tls_declarations(d: dict) -> Optional[dict]:
    """
    Validates TLS certificates and keys referenced by servers and ACME issuers.

    Returns:
        Optional[dict]: Error response dictionary if validation fails, otherwise None.
    """
    all_tls = {'certificate': {}, 'key': {}}
    d_certs = v5_7.MiscUtils.getDictKey(d, 'declaration.certificates')
    if d_certs is not None:
        for cert in d_certs:
            if cert.get('name'):
                all_tls[cert['type']][cert['name']] = True

    d_servers = v5_7.MiscUtils.getDictKey(d, 'declaration.http.servers')
    if d_servers is not None:
        for server in d_servers:
            listen = server.get('listen')
            if listen is not None and 'tls' in listen:
                cert_name = v5_7.MiscUtils.getDictKey(server, 'listen.tls.certificate')
                if cert_name and cert_name not in all_tls['certificate']:
                    return {
                        "status_code": 422,
                        "message": {
                            "status_code": 422,
                            "message": {"code": 422, "content": f"invalid TLS certificate [{cert_name}] for server [{server.get('names')}] must be one of [{','.join(all_tls['certificate'])}]"}}
                    }

                cert_key = v5_7.MiscUtils.getDictKey(server, 'listen.tls.key')
                if cert_key and cert_key not in all_tls['key']:
                    return {
                        "status_code": 422,
                        "message": {
                            "status_code": 422,
                            "message": {"code": 422, "content": f"invalid TLS key [{cert_key}] for server [{server.get('names')}] must be one of [{','.join(all_tls['key'])}]"}}
                    }

                trusted_cert_name = v5_7.MiscUtils.getDictKey(server, 'listen.tls.trusted_ca_certificates')
                if trusted_cert_name and trusted_cert_name not in all_tls['certificate']:
                    return {
                        "status_code": 422,
                        "message": {
                            "status_code": 422,
                            "message": {"code": 422, "content": f"invalid trusted CA certificate [{trusted_cert_name}] for server [{server.get('names')}] must be one of [{','.join(all_tls['certificate'])}]"}}
                    }

    d_acmeissuers = v5_7.MiscUtils.getDictKey(d, 'declaration.http.acme_issuers')
    if d_acmeissuers is not None:
        for issuer in d_acmeissuers:
            cert_name = issuer.get('ssl_trusted_certificate')
            if cert_name and cert_name not in all_tls['certificate']:
                return {
                    "status_code": 422,
                    "message": {
                        "status_code": 422,
                        "message": {"code": 422, "content": f"invalid TLS certificate [{cert_name}] for ACME issuer [{issuer.get('name')}] must be one of [{','.join(all_tls['certificate'])}]"}}
                }

    return None


def _build_rendered_config_files(
    d: dict,
    apiversion: str,
    b64HttpConf: str,
    b64StreamConf: str,
    configFiles: dict,
    auxFiles: dict
) -> Tuple[Optional[dict], dict, dict]:
    """
    Renders templates and constructs base staged configuration structures.

    Returns:
        Tuple[Optional[dict], dict, dict]: Error response if cert fetch fails, baseStagedConfig, stagedConfig
    """
    extensions_map = {'certificate': '.crt', 'key': '.key'}
    d_certificates = v5_7.MiscUtils.getDictKey(d, 'declaration.certificates')
    if d_certificates is not None:
        for c in d_certificates:
            auth = d.get('declaration', {}).get('authentication', {})
            status, certContent = v5_7.GitOps.getObjectFromRepo(object=c['contents'], authProfiles=auth)
            if status != 200:
                return {"status_code": 422, "message": {"status_code": status, "message": {"code": status, "content": certContent}}}, {}, {}

            certs_dir = NcgConfig.config['nms']['certs_dir']
            newAuxFile = {
                'contents': certContent['content'],
                'name': f"{certs_dir}/{c['name']}{extensions_map[c['type']]}"
            }
            auxFiles['files'].append(newAuxFile)

    template_path = f"{NcgConfig.config['templates']['root_dir']}/{apiversion}"
    j2_env = Environment(
        loader=FileSystemLoader(template_path),
        trim_blocks=True,
        extensions=["jinja2_base64_filters.Base64Filters"]
    )

    nginxMainConf = j2_env.get_template(NcgConfig.config['templates']['nginxmain']).render(
        nginxconf={
            'mainhttpfile': NcgConfig.config['nms']['staged_config_http_filename'],
            'mainstreamfile': NcgConfig.config['nms']['staged_config_stream_filename'],
            'modules': v5_7.MiscUtils.getDictKey(d, 'output.nginxone.modules'),
            'license': v5_7.MiscUtils.getDictKey(d, 'output.license')
        },
        d={'http': v5_7.MiscUtils.getDictKey(d, 'declaration.http')}
    )
    b64NginxMain = str(base64.urlsafe_b64encode(nginxMainConf.encode("utf-8")), "utf-8")

    licenseJwtFile = j2_env.get_template(NcgConfig.config['templates']['license']).render(
        nginxconf={'license': v5_7.MiscUtils.getDictKey(d, 'output.license')}
    )
    b64licenseJwtFile = str(base64.urlsafe_b64encode(licenseJwtFile.encode("utf-8")), "utf-8")

    mimetypes_path = f"{template_path}/{NcgConfig.config['templates']['mimetypes']}"
    with open(mimetypes_path, 'r') as f:
        nginxMimeTypes = f.read()

    b64NginxMimeTypes = str(base64.urlsafe_b64encode(nginxMimeTypes.encode("utf-8")), "utf-8")
    config_dir = NcgConfig.config['nms']['config_dir']

    auxFiles['files'].append({'contents': b64NginxMimeTypes, 'name': f"{config_dir}/mime.types"})
    configFiles['files'].append({'contents': b64NginxMain, 'name': f"{config_dir}/nginx.conf"})
    configFiles['files'].append({'contents': b64HttpConf, 'name': f"{config_dir}/{NcgConfig.config['nms']['staged_config_http_filename']}"})
    configFiles['files'].append({'contents': b64StreamConf, 'name': f"{config_dir}/{NcgConfig.config['nms']['staged_config_stream_filename']}"})

    if v5_7.MiscUtils.getDictKey(d, 'output.license.token') != "":
        configFiles['files'].append({'contents': b64licenseJwtFile, 'name': f"{config_dir}/license.jwt"})

    baseStagedConfig = {'aux': [{'files': configFiles}]}
    stagedConfig = {
        'conf_path': f"{config_dir}/nginx.conf",
        'configs': [configFiles, auxFiles]
    }

    return None, baseStagedConfig, stagedConfig


def _poll_publication_status(
    nOneUrl: str,
    nOneNamespace: str,
    igUid: str,
    publication_id: str,
    nOneToken: str
) -> Tuple[int, dict]:
    """
    Polls NGINX One Console for deployment completion status after HTTP 202 response.

    Returns:
        Tuple[int, dict]: HTTP status code and response body dictionary.
    """
    headers = {"Authorization": f"Bearer APIToken {nOneToken}"}
    url = f'{nOneUrl}/api/nginx/one/namespaces/{nOneNamespace}/config-sync-groups/{igUid}/publications/{publication_id}'

    isPending = True
    checkJson = {}
    while isPending:
        time.sleep(NcgConfig.config['nms']['staged_config_publish_waittime'])
        deploymentCheck = requests.get(url=url, headers=headers, verify=False)
        checkJson = json.loads(deploymentCheck.text)
        if checkJson.get('status') != 'pending':
            isPending = False

    if checkJson.get('status') == "failed":
        return 422, checkJson.get('status_reasons', [{}])[0]
    elif checkJson.get('status') == "succeeded":
        return 200, {"message": "Config successfully applied", "status": checkJson.get('status')}

    return 422, checkJson


def _persist_redis_state_and_schedule_autosync(
    configUid: str,
    declaration: ConfigDeclaration,
    d: dict,
    baseStagedConfig: dict,
    apiversion: str,
    nOneSynctime: int,
    runfromautosync: bool
) -> str:
    """
    Stores declaration state in Redis and sets up scheduled autosync if enabled.

    Returns:
        str: Active configUid.
    """
    if not runfromautosync:
        configUid = str(v5_7.MiscUtils.getuniqueid())
        NcgRedis.redis.set(f'ncg.declaration.{configUid}', pickle.dumps(declaration))
        NcgRedis.redis.set(f'ncg.declarationrendered.{configUid}', json.dumps(d))
        NcgRedis.redis.set(f'ncg.basestagedconfig.{configUid}', json.dumps(baseStagedConfig))
        NcgRedis.redis.set(f'ncg.apiversion.{configUid}', apiversion)

    if nOneSynctime == 0:
        NcgRedis.declarationsList[configUid] = "static"
    elif not runfromautosync:
        print(f'Starting autosync for configUid {configUid} every {nOneSynctime} seconds')
        job = schedule.every(nOneSynctime).seconds.do(lambda: V5_7_CreateConfig.configautosync(configUid))
        NcgRedis.declarationsList[configUid] = job
        NcgRedis.redis.set(f'ncg.apiversion.{configUid}', apiversion)

    return configUid


def NGINXOneOutput(
    d: dict,
    declaration: ConfigDeclaration,
    apiversion: str,
    b64HttpConf: str,
    b64StreamConf: str,
    configFiles: dict = {},
    auxFiles: dict = {},
    runfromautosync: bool = False,
    configUid: str = ""
) -> dict:
    """
    Main entry point for publishing staged configuration to NGINX One Console.

    Returns:
        dict: Response payload containing status_code, message, and headers.
    """
    err, nOneUrl, nOneToken, nOneConfigSyncGroup, nOneNamespace, nOneSynctime = _validate_target_url_and_dns(d)
    if err:
        return err

    err = _fetch_remote_policy_versions(d)
    if err:
        return err

    err = _validate_tls_declarations(d)
    if err:
        return err

    err, baseStagedConfig, stagedConfig = _build_rendered_config_files(
        d, apiversion, b64HttpConf, b64StreamConf, configFiles, auxFiles
    )
    if err:
        return err

    currentBaseStagedConfig = NcgRedis.redis.get(f'ncg.basestagedconfig.{configUid}').decode('utf-8') \
        if NcgRedis.redis.get(f'ncg.basestagedconfig.{configUid}') else None
    newBaseStagedConfig = json.dumps(baseStagedConfig)

    if currentBaseStagedConfig is not None and newBaseStagedConfig == currentBaseStagedConfig:
        print(f'Declaration [{configUid}] not changed')
        return {"status_code": 200, "message": {"status_code": 200, "message": {"code": 200, "content": "no changes"}}}

    print(f'Declaration [{configUid}] changed, publishing' if configUid else 'New declaration created, publishing')

    returnCode, igUid = v5_7.NGINXOneUtils.getConfigSyncGroupId(
        nOneUrl=nOneUrl, nOneToken=nOneToken, nameSpace=nOneNamespace, configSyncGroupName=nOneConfigSyncGroup
    )
    if returnCode != 200:
        return {
            "status_code": 404,
            "message": {"status_code": 404, "message": {"code": returnCode, "content": igUid}},
            "headers": {'Content-Type': 'application/json'}
        }

    status, description = v5_7.NGINXOneNAPUtils.checkDeclarationPolicies(d)
    if status != 200:
        return {
            "status_code": 422,
            "message": {"status_code": status, "message": {"code": status, "content": description}},
            "headers": {'Content-Type': 'application/json'}
        }

    ppReply = v5_7.NGINXOneNAPUtils.provisionPolicies(
        nginxOneUrl=nOneUrl, nginxOneToken=nOneToken, nginxOneNamespace=nOneNamespace, declaration=d
    )
    if ppReply.status_code >= 400:
        return {
            "status_code": ppReply.status_code,
            "message": {"status_code": ppReply.status_code, "message": {"code": ppReply.status_code, "content": json.loads(ppReply.body)['details']}}
        }

    napPolicies = json.loads(ppReply.body)
    activePolicyUids = napPolicies['all_policy_active_names_and_uids']

    url = f'{nOneUrl}/api/nginx/one/namespaces/{nOneNamespace}/config-sync-groups/{igUid}/config'
    headers = {'Content-Type': 'application/json', "Authorization": f"Bearer APIToken {nOneToken}"}
    r = requests.put(url=url, data=json.dumps(stagedConfig), headers=headers, verify=False)

    if r.status_code not in [200, 202]:
        return {
            "status_code": r.status_code,
            "message": {"status_code": r.status_code, "message": r.text},
            "headers": {'Content-Type': 'application/json'}
        }

    if r.status_code == 202:
        publishResponse = json.loads(r.text)
        publication_id = publishResponse['object_id']
        returnHttpCode, jsonResponse = _poll_publication_status(nOneUrl, nOneNamespace, igUid, publication_id, nOneToken)
    else:
        jsonResponse = json.loads(r.text)
        returnHttpCode = 200

    configUid = _persist_redis_state_and_schedule_autosync(
        configUid, declaration, d, baseStagedConfig, apiversion, nOneSynctime, runfromautosync
    )

    doWeHavePolicies = v5_7.NGINXOneNAPUtils.makePolicyActive(
        nginxOneUrl=nOneUrl, nginxOneToken=nOneToken, nginxOneNamespace=nOneNamespace,
        activePolicyUids=activePolicyUids, instanceGroupUid=igUid
    )
    if doWeHavePolicies:
        time.sleep(NcgConfig.config['nms']['staged_config_publish_waittime'])

    responseContent = {' code': returnHttpCode, 'content': jsonResponse, 'configUid': configUid}

    if configUid != "":
        NcgRedis.redis.set(f'ncg.status.{configUid}', json.dumps(responseContent))
        NcgRedis.redis.set(f'ncg.declaration.{configUid}', pickle.dumps(declaration))
        NcgRedis.redis.set(f'ncg.declarationrendered.{configUid}', json.dumps(d))
        NcgRedis.redis.set(f'ncg.basestagedconfig.{configUid}', json.dumps(baseStagedConfig))

    return {
        "status_code": returnHttpCode,
        "message": {"status_code": returnHttpCode, "message": responseContent},
        "headers": {'Content-Type': 'application/json'}
    }