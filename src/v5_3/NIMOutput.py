"""
Output to NGINX Instance Manager
"""

import base64
import requests
import json
import pickle
import time
import schedule

from jinja2 import Environment, FileSystemLoader
from urllib.parse import urlparse
from datetime import datetime

import V5_3_CreateConfig

import v5_3.APIGateway
import v5_3.DevPortal
import v5_3.DeclarationPatcher
import v5_3.GitOps
import v5_3.MiscUtils
import v5_3.NIMOutput
import v5_3.NIMUtils

# pydantic models
from V5_3_NginxConfigDeclaration import *

# NGINX App Protect helper functions
import v5_3.NAPUtils

# NGINX Declarative API modules
from NcgConfig import NcgConfig
from NcgRedis import NcgRedis

def NIMOutput(d, declaration: ConfigDeclaration, apiversion: str, b64HttpConf: str,
              b64StreamConf: str,configFiles = {}, auxFiles = {},
              runfromautosync: bool = False,
              configUid: str = ""):
    # NGINX Instance Manager Staged Configuration publish

    nmsUsername = v5_3.MiscUtils.getDictKey(d, 'output.nms.username')
    nmsPassword = v5_3.MiscUtils.getDictKey(d, 'output.nms.password')
    nmsInstanceGroup = v5_3.MiscUtils.getDictKey(d, 'output.nms.instancegroup')
    nmsSynctime = v5_3.MiscUtils.getDictKey(d, 'output.nms.synctime')

    nmsUrlFromJson = v5_3.MiscUtils.getDictKey(d, 'output.nms.url')
    urlCheck = urlparse(nmsUrlFromJson)

    if urlCheck.scheme not in ['http', 'https'] or urlCheck.scheme == "" or urlCheck.netloc == "":
        return {"status_code": 400,
                "message": {"status_code": 400, "message": {"code": 400,
                                                            "content": f"invalid NGINX Instance Manager URL {nmsUrlFromJson}"}},
                "headers": {'Content-Type': 'application/json'}}

    # DNS resolution check
    dnsOutcome, dnsReply = v5_3.MiscUtils.resolveFQDN(urlCheck.netloc)
    if not dnsOutcome:
        return {"status_code": 400,
                "message": {"status_code": 400, "message": {"code": 400,
                                                            "content": f"DNS resolution failed for {urlCheck.netloc}: {dnsReply}"}},
                "headers": {'Content-Type': 'application/json'}}

    nmsUrl = f"{urlCheck.scheme}://{urlCheck.netloc}"

    if nmsSynctime < 0:
        return {"status_code": 400,
                "message": {"status_code": 400, "message": {"code": 400, "content": "synctime must be >= 0"}},
                "headers": {'Content-Type': 'application/json'}}

    # Fetch NGINX App Protect WAF policies from source of truth if needed
    d_policies = v5_3.MiscUtils.getDictKey(d, 'output.nms.policies')
    if d_policies is not None:
        for policy in d_policies:
            if 'versions' in policy:
                for policyVersion in policy['versions']:
                    status, content = v5_3.GitOps.getObjectFromRepo(object=policyVersion['contents'],
                                                                    authProfiles=d['declaration']['http'][
                                                                        'authentication'])

                    if status != 200:
                        return {"status_code": 422, "message": {"status_code": status, "message": content}}

                    policyVersion['contents'] = content

    # Check TLS items validity
    all_tls = {'certificate': {}, 'key': {}}

    d_certs = v5_3.MiscUtils.getDictKey(d, 'output.nms.certificates')
    if d_certs is not None:
        for i in range(len(d_certs)):
            if d_certs[i]['name']:
                all_tls[d_certs[i]['type']][d_certs[i]['name']] = True

    d_servers = v5_3.MiscUtils.getDictKey(d, 'declaration.http.servers')
    if d_servers is not None:
        for server in d_servers:
            if server['listen'] is not None:
                if 'tls' in server['listen']:
                    cert_name = v5_3.MiscUtils.getDictKey(server, 'listen.tls.certificate')
                    if cert_name and cert_name not in all_tls['certificate']:
                        return {"status_code": 422,
                                "message": {
                                    "status_code": 422,
                                    "message": {"code": 422,
                                                "content": "invalid TLS certificate " +
                                                           cert_name + " for server" + str(
                                                    server['names'])}
                                }}

                    cert_key = v5_3.MiscUtils.getDictKey(server, 'listen.tls.key')
                    if cert_key and cert_key not in all_tls['key']:
                        return {"status_code": 422,
                                "message": {
                                    "status_code": 422,
                                    "message": {"code": 422,
                                                "content": "invalid TLS key " + cert_key + " for server" + str(
                                                    server['names'])}
                                }}

                    trusted_cert_name = v5_3.MiscUtils.getDictKey(server, 'listen.tls.trusted_ca_certificates')
                    if trusted_cert_name and trusted_cert_name not in all_tls['certificate']:
                        return {"status_code": 422,
                                "message": {
                                    "status_code": 422,
                                    "message": {"code": 422,
                                                "content": "invalid trusted CA certificate " +
                                                           trusted_cert_name + " for server" + str(server['names'])}
                                }}

    # Add optional certificates specified under output.nms.certificates
    extensions_map = {'certificate': '.crt', 'key': '.key'}

    d_certificates = v5_3.MiscUtils.getDictKey(d, 'output.nms.certificates')
    if d_certificates is not None:
        for c in d_certificates:
            status, certContent = v5_3.GitOps.getObjectFromRepo(object=c['contents'],
                                                                authProfiles=d['declaration']['http']['authentication'])

            if status != 200:
                return {"status_code": 422,
                        "message": {"status_code": status, "message": {"code": status, "content": certContent}}}

            newAuxFile = {'contents': certContent['content'], 'name': NcgConfig.config['nms']['certs_dir'] +
                                                                      '/' + c['name'] + extensions_map[c['type']]}
            auxFiles['files'].append(newAuxFile)

    ### / Add optional certificates specified under output.nms.certificates

    # NGINX main configuration file through template
    j2_env = Environment(loader=FileSystemLoader(NcgConfig.config['templates']['root_dir'] + '/' + apiversion),
                         trim_blocks=True, extensions=["jinja2_base64_filters.Base64Filters"])

    nginxMainConf = j2_env.get_template(NcgConfig.config['templates']['nginxmain']).render(
        nginxconf={'modules': v5_3.MiscUtils.getDictKey(d, 'output.nms.modules'),
                   'license': v5_3.MiscUtils.getDictKey(d, 'output.license')})

    # Base64-encoded NGINX main configuration (/etc/nginx/nginx.conf)
    b64NginxMain = str(base64.urlsafe_b64encode(nginxMainConf.encode("utf-8")), "utf-8")

    # NGINX License file
    licenseJwtFile = j2_env.get_template(NcgConfig.config['templates']['license']).render(
        nginxconf={'license': v5_3.MiscUtils.getDictKey(d, 'output.license')})

    # Base64-encoded license file (/etc/nginx/license.jwt)
    b64licenseJwtFile = str(base64.urlsafe_b64encode(licenseJwtFile.encode("utf-8")), "utf-8")

    # Base64-encoded NGINX mime.types (/etc/nginx/mime.types)
    f = open(NcgConfig.config['templates']['root_dir'] + '/' + apiversion + '/' + NcgConfig.config['templates'][
        'mimetypes'], 'r')
    nginxMimeTypes = f.read()
    f.close()

    b64NginxMimeTypes = str(base64.urlsafe_b64encode(nginxMimeTypes.encode("utf-8")), "utf-8")
    filesMimeType = {'contents': b64NginxMimeTypes, 'name': NcgConfig.config['nms']['config_dir'] + '/mime.types'}
    auxFiles['files'].append(filesMimeType)

    # Base64-encoded NGINX HTTP service configuration
    filesNginxMain = {'contents': b64NginxMain, 'name': NcgConfig.config['nms']['config_dir'] + '/nginx.conf'}
    filesLicenseFile = {'contents': b64licenseJwtFile, 'name': NcgConfig.config['nms']['config_dir'] + '/license.jwt'}
    filesHttpConf = {'contents': b64HttpConf,
                     'name': NcgConfig.config['nms']['config_dir'] + '/' + NcgConfig.config['nms'][
                         'staged_config_http_filename']}
    filesStreamConf = {'contents': b64StreamConf,
                       'name': NcgConfig.config['nms']['config_dir'] + '/' + NcgConfig.config['nms'][
                           'staged_config_stream_filename']}

    # Append config files to staged configuration
    configFiles['files'].append(filesNginxMain)
    configFiles['files'].append(filesHttpConf)
    configFiles['files'].append(filesStreamConf)

    # If no R33+ license token was specified in the JSON declaration, it is assumed a token already exists
    # on the NGINX instances and it won't be overwritten
    if v5_3.MiscUtils.getDictKey(d, 'output.license.token') != "":
        configFiles['files'].append(filesLicenseFile)

    # Staged config
    baseStagedConfig = {'auxFiles': auxFiles, 'configFiles': configFiles}
    stagedConfig = {'auxFiles': auxFiles, 'configFiles': configFiles,
                    'updateTime': datetime.utcnow().isoformat()[:-3] + 'Z',
                    'ignoreConflict': True, 'validateConfig': False}

    currentBaseStagedConfig = NcgRedis.redis.get(f'ncg.basestagedconfig.{configUid}').decode(
        'utf-8') if NcgRedis.redis.get(f'ncg.basestagedconfig.{configUid}') else None
    newBaseStagedConfig = json.dumps(baseStagedConfig)

    if currentBaseStagedConfig is not None and newBaseStagedConfig == currentBaseStagedConfig:
        print(f'Declaration [{configUid}] not changed')
        return {"status_code": 200,
                "message": {"status_code": 200, "message": {"code": 200, "content": "no changes"}}}
    else:
        # Configuration objects have changed, publish to NIM needed
        print(
            f'Declaration [{configUid}] changed, publishing' if configUid else f'New declaration created, publishing')

        # Get the instance group id
        igUid = v5_3.NIMUtils.getNIMInstanceGroupUid(nmsUrl=nmsUrl, nmsUsername=nmsUsername,
                                                     nmsPassword=nmsPassword, instanceGroupName=nmsInstanceGroup)

        # Invalid instance group
        if igUid is None:
            return {"status_code": 404,
                    "message": {"status_code": 404, "message": {"code": 404,
                                                                "content": f"instance group {nmsInstanceGroup} not found"}},
                    "headers": {'Content-Type': 'application/json'}}

        ### NGINX App Protect policies support - commits policies to control plane

        # Check NGINX App Protect WAF policies configuration sanity
        status, description = v5_3.NAPUtils.checkDeclarationPolicies(d)

        if status != 200:
            return {"status_code": 422,
                    "message": {"status_code": status, "message": {"code": status, "content": description}},
                    "headers": {'Content-Type': 'application/json'}}

        # Provision NGINX App Protect WAF policies to NGINX Instance Manager
        provisionedNapPolicies, activePolicyUids = v5_3.NAPUtils.provisionPolicies(
            nmsUrl=nmsUrl, nmsUsername=nmsUsername, nmsPassword=nmsPassword, declaration=d)

        ### / NGINX App Protect policies support

        ### Publish staged config to instance group
        r = requests.post(url=nmsUrl + f"/api/platform/v1/instance-groups/{igUid}/config",
                          data=json.dumps(stagedConfig),
                          headers={'Content-Type': 'application/json'},
                          auth=(nmsUsername, nmsPassword),
                          verify=False)

        if r.status_code != 202:
            # Configuration push failed
            return {"status_code": r.status_code,
                    "message": {"status_code": r.status_code, "message": r.text},
                    "headers": {'Content-Type': 'application/json'}}

        # Fetch the deployment status
        publishResponse = json.loads(r.text)

        # Wait for either NIM success or failure after pushing a staged config
        isPending = True
        while isPending:
            time.sleep(NcgConfig.config['nms']['staged_config_publish_waittime'])
            deploymentCheck = requests.get(url=nmsUrl + publishResponse['links']['rel'],
                                           auth=(nmsUsername, nmsPassword),
                                           verify=False)

            checkJson = json.loads(deploymentCheck.text)

            if not checkJson['details']['pending']:
                isPending = False

        if len(checkJson['details']['failure']) > 0:
            # Staged config publish to NIM failed
            jsonResponse = checkJson['details']['failure'][0]
            deploymentCheck.status_code = 422
        else:
            # Staged config publish to NIM succeeded
            jsonResponse = json.loads(deploymentCheck.text)

            # if nmsSynctime > 0 and runfromautosync == False:
            if runfromautosync == False:
                # No configuration is found, generate one
                configUid = str(v5_3.MiscUtils.getuniqueid())

                # Stores the staged config to redis
                # Redis keys:
                # ncg.declaration.[configUid] = original config declaration
                # ncg.declarationrendered.[configUid] = original config declaration - rendered
                # ncg.basestagedconfig.[configUid] = base staged configuration
                # ncg.apiversion.[configUid] = ncg API version
                # ncg.status.[configUid] = latest status

                NcgRedis.redis.set(f'ncg.declaration.{configUid}', pickle.dumps(declaration))
                NcgRedis.redis.set(f'ncg.declarationrendered.{configUid}', json.dumps(d))
                NcgRedis.redis.set(f'ncg.basestagedconfig.{configUid}', json.dumps(baseStagedConfig))
                NcgRedis.redis.set(f'ncg.apiversion.{configUid}', apiversion)

            # Makes NGINX App Protect policies active
            doWeHavePolicies = v5_3.NAPUtils.makePolicyActive(nmsUrl=nmsUrl, nmsUsername=nmsUsername,
                                                              nmsPassword=nmsPassword,
                                                              activePolicyUids=activePolicyUids,
                                                              instanceGroupUid=igUid)

            if doWeHavePolicies:
                # Clean up NGINX App Protect WAF policies not used anymore
                # and not defined in the declaration just pushed
                time.sleep(NcgConfig.config['nms']['staged_config_publish_waittime'])
                v5_3.NAPUtils.cleanPolicyLeftovers(nmsUrl=nmsUrl, nmsUsername=nmsUsername,
                                                   nmsPassword=nmsPassword,
                                                   currentPolicies=provisionedNapPolicies)

            # If deploying a new configuration in GitOps mode start autosync
            if nmsSynctime == 0:
                NcgRedis.declarationsList[configUid] = "static"
            elif not runfromautosync:
                # GitOps autosync
                print(f'Starting autosync for configUid {configUid} every {nmsSynctime} seconds')

                job = schedule.every(nmsSynctime).seconds.do(lambda: v5_3_CreateConfig.configautosync(configUid))
                # Keep track of GitOps configs, key is the threaded job
                NcgRedis.declarationsList[configUid] = job

                NcgRedis.redis.set(f'ncg.apiversion.{configUid}', apiversion)

        responseContent = {'code': deploymentCheck.status_code, 'content': jsonResponse, 'configUid': configUid}

        # Configuration push completed, update redis keys
        if configUid != "":
            NcgRedis.redis.set('ncg.status.' + configUid, json.dumps(responseContent))

            # if nmsSynctime > 0:
            # Updates status, declaration and basestagedconfig in redis
            NcgRedis.redis.set('ncg.declaration.' + configUid, pickle.dumps(declaration))
            NcgRedis.redis.set('ncg.declarationrendered.' + configUid, json.dumps(d))
            NcgRedis.redis.set('ncg.basestagedconfig.' + configUid, json.dumps(baseStagedConfig))

        return {"status_code": deploymentCheck.status_code,
            "message": {"status_code": deploymentCheck.status_code,
                        "message": responseContent},
            "headers": {'Content-Type': 'application/json'}
            }