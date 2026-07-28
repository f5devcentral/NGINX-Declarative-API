"""
Output to NGINX Instance Manager (NIM)
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
from datetime import datetime

import V5_7_CreateConfig

import v5_7.APIGateway
import v5_7.DevPortal
import v5_7.DeclarationPatcher
import v5_7.GitOps
import v5_7.MiscUtils
import v5_7.NIMOutput
import v5_7.NIMUtils

# pydantic models
from V5_7_NginxConfigDeclaration import *

# F5 WAF for NGINX helper functions
import v5_7.NIMNAPUtils

# NGINX Declarative API modules
from NcgConfig import NcgConfig
from NcgRedis import NcgRedis


def _validate_target_url_and_dns(d: dict) -> Tuple[Optional[dict], str, str, str, str, int]:
    """
    Validates NMS URL, DNS resolution, and synctime settings.

    Returns:
        Tuple[Optional[dict], str, str, str, str, int]:
        (Error response dict or None, nmsUrl, nmsUsername, nmsPassword, nmsInstanceGroup, nmsSynctime)
    """
    nmsUsername = v5_7.MiscUtils.getDictKey(d, 'output.nms.username')
    nmsPassword = v5_7.MiscUtils.getDictKey(d, 'output.nms.password')
    nmsInstanceGroup = v5_7.MiscUtils.getDictKey(d, 'output.nms.instancegroup')
    nmsSynctime = v5_7.MiscUtils.getDictKey(d, 'output.nms.synctime')
    nmsUrlFromJson = v5_7.MiscUtils.getDictKey(d, 'output.nms.url')

    urlCheck = urlparse(nmsUrlFromJson)
    if urlCheck.scheme not in ['http', 'https'] or urlCheck.scheme == "" or urlCheck.hostname == "":
        return ({
            "status_code": 400,
            "message": {"status_code": 400, "message": {"code": 400, "content": f"invalid NGINX Instance Manager URL {nmsUrlFromJson}"}},
            "headers": {'Content-Type': 'application/json'}
        }, "", "", "", "", 0)

    dnsOutcome, dnsReply = v5_7.MiscUtils.resolveFQDN(urlCheck.hostname)
    if not dnsOutcome:
        return ({
            "status_code": 400,
            "message": {"status_code": 400, "message": {"code": 400, "content": f"DNS resolution failed for {urlCheck.hostname}: {dnsReply}"}},
            "headers": {'Content-Type': 'application/json'}
        }, "", "", "", "", 0)

    if nmsSynctime < 0:
        return ({
            "status_code": 400,
            "message": {"status_code": 400, "message": {"code": 400, "content": "synctime must be >= 0"}},
            "headers": {'Content-Type': 'application/json'}
        }, "", "", "", "", 0)

    nmsUrl = f"{urlCheck.scheme}://{urlCheck.netloc}"
    return None, nmsUrl, nmsUsername, nmsPassword, nmsInstanceGroup, nmsSynctime


def _fetch_remote_policy_versions(d: dict) -> Optional[dict]:
    """
    Fetches F5 WAF for NGINX policies from source of truth if defined.

    Returns:
        Optional[dict]: Error response dict if fetch fails, otherwise None.
    """
    d_policies = v5_7.MiscUtils.getDictKey(d, 'output.declaration.http.policies')
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
    Renders templates and builds baseStagedConfig and stagedConfig for NMS.

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
            'modules': v5_7.MiscUtils.getDictKey(d, 'output.nms.modules'),
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

    baseStagedConfig = {'auxFiles': auxFiles, 'configFiles': configFiles}
    stagedConfig = {
        'auxFiles': auxFiles,
        'configFiles': configFiles,
        'updateTime': datetime.utcnow().isoformat()[:-3] + 'Z',
        'ignoreConflict': True,
        'validateConfig': False
    }

    return None, baseStagedConfig, stagedConfig


def _poll_publication_status(
    nmsUrl: str,
    rel_link: str,
    nmsUsername: str,
    nmsPassword: str
) -> Tuple[int, dict]:
    """
    Polls NMS deployment status until complete.

    Returns:
        Tuple[int, dict]: Status code and response details dict.
    """
    isPending = True
    jsonResponse = {}
    deployment_status_code = 200

    while isPending:
        time.sleep(NcgConfig.config['nms']['staged_config_publish_waittime'])
        deploymentCheck = requests.get(
            url=f"{nmsUrl}{rel_link}",
            auth=(nmsUsername, nmsPassword),
            verify=False
        )

        checkJson = json.loads(deploymentCheck.text)
        if deploymentCheck.status_code == 404:
            jsonResponse = {"message": f"deployment not found at {rel_link}"}
            isPending = False

        if 'details' in checkJson and not checkJson['details'].get('pending'):
            isPending = False

    if 'details' not in checkJson or len(checkJson['details'].get('failure', [])) > 0:
        jsonResponse = checkJson['details']['failure'][0] if 'details' in checkJson else jsonResponse
        deployment_status_code = 422
    else:
        jsonResponse = json.loads(deploymentCheck.text)
        deployment_status_code = deploymentCheck.status_code

    return deployment_status_code, jsonResponse


def _persist_redis_state_and_schedule_autosync(
    configUid: str,
    declaration: ConfigDeclaration,
    d: dict,
    baseStagedConfig: dict,
    apiversion: str,
    nmsSynctime: int,
    runfromautosync: bool
) -> str:
    """
    Stores state in Redis and sets up scheduled autosync if enabled.

    Returns:
        str: Active configUid.
    """
    if not runfromautosync:
        configUid = str(v5_7.MiscUtils.getuniqueid())
        NcgRedis.redis.set(f'ncg.declaration.{configUid}', pickle.dumps(declaration))
        NcgRedis.redis.set(f'ncg.declarationrendered.{configUid}', json.dumps(d))
        NcgRedis.redis.set(f'ncg.basestagedconfig.{configUid}', json.dumps(baseStagedConfig))
        NcgRedis.redis.set(f'ncg.apiversion.{configUid}', apiversion)

    if nmsSynctime == 0:
        NcgRedis.declarationsList[configUid] = "static"
    elif not runfromautosync:
        print(f'Starting autosync for configUid {configUid} every {nmsSynctime} seconds')
        job = schedule.every(nmsSynctime).seconds.do(lambda: V5_7_CreateConfig.configautosync(configUid))
        NcgRedis.declarationsList[configUid] = job
        NcgRedis.redis.set(f'ncg.apiversion.{configUid}', apiversion)

    return configUid


def NIMOutput(
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
    Main entry point for publishing staged configuration to NGINX Instance Manager.

    Returns:
        dict: Response payload dictionary containing status_code, message, and headers.
    """
    err, nmsUrl, nmsUsername, nmsPassword, nmsInstanceGroup, nmsSynctime = _validate_target_url_and_dns(d)
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

    returnCode, igUid = v5_7.NIMUtils.getNIMInstanceGroupUid(
        nmsUrl=nmsUrl, nmsUsername=nmsUsername, nmsPassword=nmsPassword, instanceGroupName=nmsInstanceGroup
    )
    if returnCode != 200:
        return {
            "status_code": 404,
            "message": {"status_code": 404, "message": {"code": returnCode, "content": igUid}},
            "headers": {'Content-Type': 'application/json'}
        }

    status, description = v5_7.NIMNAPUtils.checkDeclarationPolicies(d)
    if status != 200:
        return {
            "status_code": 422,
            "message": {"status_code": status, "message": {"code": status, "content": description}},
            "headers": {'Content-Type': 'application/json'}
        }

    ppReply = v5_7.NIMNAPUtils.provisionPolicies(
        nmsUrl=nmsUrl, nmsUsername=nmsUsername, nmsPassword=nmsPassword, declaration=d
    )
    if ppReply.status_code >= 400:
        return {
            "status_code": ppReply.status_code,
            "message": {"status_code": ppReply.status_code, "message": {"code": ppReply.status_code, "content": json.loads(ppReply.body)['details']}}
        }

    napPolicies = json.loads(ppReply.body)
    provisionedNapPolicies = napPolicies['all_policy_names_and_versions']
    activePolicyUids = napPolicies['all_policy_active_names_and_uids']

    url = f"{nmsUrl}/api/platform/v1/instance-groups/{igUid}/config"
    r = requests.post(
        url=url,
        data=json.dumps(stagedConfig),
        headers={'Content-Type': 'application/json'},
        auth=(nmsUsername, nmsPassword),
        verify=False
    )

    if r.status_code != 202:
        return {
            "status_code": r.status_code,
            "message": {"status_code": r.status_code, "message": r.text},
            "headers": {'Content-Type': 'application/json'}
        }

    publishResponse = json.loads(r.text)
    rel_link = publishResponse['links']['rel']

    deployment_status_code, jsonResponse = _poll_publication_status(nmsUrl, rel_link, nmsUsername, nmsPassword)

    if deployment_status_code == 200:
        configUid = _persist_redis_state_and_schedule_autosync(
            configUid, declaration, d, baseStagedConfig, apiversion, nmsSynctime, runfromautosync
        )

        doWeHavePolicies = v5_7.NIMNAPUtils.makePolicyActive(
            nmsUrl=nmsUrl, nmsUsername=nmsUsername, nmsPassword=nmsPassword,
            activePolicyUids=activePolicyUids, instanceGroupUid=igUid
        )

        if doWeHavePolicies:
            time.sleep(NcgConfig.config['nms']['staged_config_publish_waittime'])
            v5_7.NIMNAPUtils.cleanPolicyLeftovers(
                nmsUrl=nmsUrl, nmsUsername=nmsUsername, nmsPassword=nmsPassword,
                currentPolicies=provisionedNapPolicies
            )

    responseContent = {'code': deployment_status_code, 'content': jsonResponse, 'configUid': configUid}

    if configUid != "":
        NcgRedis.redis.set(f'ncg.status.{configUid}', json.dumps(responseContent))
        NcgRedis.redis.set(f'ncg.declaration.{configUid}', pickle.dumps(declaration))
        NcgRedis.redis.set(f'ncg.declarationrendered.{configUid}', json.dumps(d))
        NcgRedis.redis.set(f'ncg.basestagedconfig.{configUid}', json.dumps(baseStagedConfig))

    return {
        "status_code": deployment_status_code,
        "message": {"status_code": deployment_status_code, "message": responseContent},
        "headers": {'Content-Type': 'application/json'}
    }