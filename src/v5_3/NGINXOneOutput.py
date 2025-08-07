"""
Output to NGINX One console
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
import v5_3.NGINXOneUtils

# pydantic models
from V5_3_NginxConfigDeclaration import *

# NGINX App Protect helper functions
# NGINX App Protect helper functions
import v5_3.NGINXOneNAPUtils

# NGINX Declarative API modules
from NcgConfig import NcgConfig
from NcgRedis import NcgRedis

def NGINXOneOutput(d, declaration: ConfigDeclaration, apiversion: str, b64HttpConf: str,
              b64StreamConf: str,configFiles = {}, auxFiles = {},
              runfromautosync: bool = False,
              configUid: str = ""):
    # NGINX One Console Staged Configuration publish

    nOneToken = v5_3.MiscUtils.getDictKey(d, 'output.nginxone.token')
    nOneConfigSyncGroup = v5_3.MiscUtils.getDictKey(d, 'output.nginxone.configsyncgroup')
    nOneNamespace = v5_3.MiscUtils.getDictKey(d, 'output.nginxone.namespace')

    nOneSynctime = v5_3.MiscUtils.getDictKey(d, 'output.nginxone.synctime')

    nOneUrlFromJson = v5_3.MiscUtils.getDictKey(d, 'output.nginxone.url')
    urlCheck = urlparse(nOneUrlFromJson)

    if urlCheck.scheme not in ['http', 'https'] or urlCheck.scheme == "" or urlCheck.netloc == "":
        return {"status_code": 400,
                "message": {"status_code": 400, "message": {"code": 400,
                                                            "content": f"invalid NGINX One URL {nOneUrlFromJson}"}},
                "headers": {'Content-Type': 'application/json'}}

    # DNS resolution check
    dnsOutcome, dnsReply = v5_3.MiscUtils.resolveFQDN(urlCheck.netloc)
    if not dnsOutcome:
        return {"status_code": 400,
                "message": {"status_code": 400, "message": {"code": 400,
                                                            "content": f"DNS resolution failed for {urlCheck.netloc}: {dnsReply}"}},
                "headers": {'Content-Type': 'application/json'}}

    nOneUrl = f"{urlCheck.scheme}://{urlCheck.netloc}"

    if nOneSynctime < 0:
        return {"status_code": 400,
                "message": {"status_code": 400, "message": {"code": 400, "content": "synctime must be >= 0"}},
                "headers": {'Content-Type': 'application/json'}}

    # Fetch NGINX App Protect WAF policies from source of truth if needed
    d_policies = v5_3.MiscUtils.getDictKey(d, 'output.nginxone.policies')
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

    d_certs = v5_3.MiscUtils.getDictKey(d, 'output.nginxone.certificates')
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

    # Add optional certificates specified under output.nginxone.certificates
    extensions_map = {'certificate': '.crt', 'key': '.key'}

    d_certificates = v5_3.MiscUtils.getDictKey(d, 'output.nginxone.certificates')
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

    ### / Add optional certificates specified under output.nginxone.certificates

    # NGINX main configuration file through template
    j2_env = Environment(loader=FileSystemLoader(NcgConfig.config['templates']['root_dir'] + '/' + apiversion),
                         trim_blocks=True, extensions=["jinja2_base64_filters.Base64Filters"])

    nginxMainConf = j2_env.get_template(NcgConfig.config['templates']['nginxmain']).render(
        nginxconf={'modules': v5_3.MiscUtils.getDictKey(d, 'output.nginxone.modules'),
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
    stagedConfig = {'conf_path': NcgConfig.config['nms']['config_dir'] + '/nginx.conf',
                    'configs': [ configFiles, auxFiles ]}

    currentBaseStagedConfig = NcgRedis.redis.get(f'ncg.basestagedconfig.{configUid}').decode(
        'utf-8') if NcgRedis.redis.get(f'ncg.basestagedconfig.{configUid}') else None
    newBaseStagedConfig = json.dumps(baseStagedConfig)

    if currentBaseStagedConfig is not None and newBaseStagedConfig == currentBaseStagedConfig:
        print(f'Declaration [{configUid}] not changed')
        return {"status_code": 200,
                "message": {"status_code": 200, "message": {"code": 200, "content": "no changes"}}}
    else:
        # Configuration objects have changed, publish to NGINX One needed
        print(
            f'Declaration [{configUid}] changed, publishing' if configUid else f'New declaration created, publishing')

        # Get the config sync group id nOneUrl: str, nOneTokenUsername: str, nameSpace: str, clusterName: str
        returnCode, igUid = v5_3.NGINXOneUtils.getConfigSyncGroupId(nOneUrl = nOneUrl, nOneToken = nOneToken,
                                                nameSpace = nOneNamespace, configSyncGroupName = nOneConfigSyncGroup)

        # Invalid config sync group
        if returnCode != 200:
            return {"status_code": 404,
                    "message": {"status_code": 404, "message": {"code": returnCode,
                                                                "content": igUid}},
                    "headers": {'Content-Type': 'application/json'}}

        ### NGINX App Protect policies support - commits policies to control plane

        # Check NGINX App Protect WAF policies configuration sanity
        status, description = v5_3.NGINXOneNAPUtils.checkDeclarationPolicies(d)

        if status != 200:
            return {"status_code": 422,
                    "message": {"status_code": status, "message": {"code": status, "content": description}},
                    "headers": {'Content-Type': 'application/json'}}

        # Provision NGINX App Protect WAF policies to NGINX One Console
        ppReply = v5_3.NGINXOneNAPUtils.provisionPolicies(
            nginxOneUrl = nOneUrl, nginxOneToken = nOneToken, nginxOneNamespace = nOneNamespace,  declaration=d)

        if ppReply.status_code >= 400:
            return {"status_code": ppReply.status_code,
                    "message": {"status_code": ppReply.status_code, "message": {"code": ppReply.status_code, "content": ppReply.content} }}


        napPolicies = json.loads(ppReply.body)
        provisionedNapPolicies = napPolicies['all_policy_names_and_versions']
        activePolicyUids = napPolicies['all_policy_active_names_and_uids']

        # Add NGINX App Protect policies as payloads[] in the full configuration to be published through NGINX One Console
        napPoliciesConfigPayloads = v5_3.NGINXOneNAPUtils.addNapPolicyPayloads(nginxOneUrl=nOneUrl,
                                                             nginxOneToken=nOneToken,
                                                             nginxOneNamespace=nOneNamespace,
                                                             activePolicyUids=activePolicyUids,
                                                             instanceGroupUid=igUid)

        stagedConfig['payloads'] = napPoliciesConfigPayloads

        ### / NGINX App Protect policies support

        ### Publish staged config to config sync group
        returnHttpCode = 422

        r = requests.put(url=f'{nOneUrl}/api/nginx/one/namespaces/{nOneNamespace}/config-sync-groups/{igUid}/config',
                          data=json.dumps(stagedConfig),
                          headers={'Content-Type': 'application/json', "Authorization": f"Bearer APIToken {nOneToken}"},
                          verify=False)

        if r.status_code not in [200, 202]:
            # Configuration publish failed
            return {"status_code": r.status_code,
                    "message": {"status_code": r.status_code, "message": r.text},
                    "headers": {'Content-Type': 'application/json'}}

        if r.status_code == 202:
            # Configuration has been submitted to NGINX One Console, fetch the deployment status - reply was HTTP/202
            publishResponse = json.loads(r.text)
            publication_id = publishResponse['object_id']

            # Wait for either NGINX One Cloud Console success or failure after pushing a staged config
            isPending = True
            while isPending:
                time.sleep(NcgConfig.config['nms']['staged_config_publish_waittime'])
                deploymentCheck = requests.get(url=f'{nOneUrl}/api/nginx/one/namespaces/{nOneNamespace}/config-sync-groups/{igUid}/publications/{publication_id}',
                                               headers={"Authorization": f"Bearer APIToken {nOneToken}"},
                                               verify=False)

                checkJson = json.loads(deploymentCheck.text)

                if not checkJson['status'] == 'pending':
                    isPending = False

            if checkJson['status'] == "failed":
                # Staged config publish to NGINX One failed
                jsonResponse = checkJson['status_reasons'][0]
                returnHttpCode = 422
            elif checkJson['status'] == "succeeded":
                jsonResponse = { "message": "Config successfully applied", "status": checkJson['status'] }
                returnHttpCode = 200

                # Remove NAP policy versions that are not currently deployed on any config sync group
                v5_3.NGINXOneNAPUtils.removeUndeployedPolicyVersions(nginxOneUrl = nOneUrl, nginxOneToken = nOneToken, nginxOneNamespace = nOneNamespace,  policyIds=napPolicies['policy_ids'])

        else:
            # Staged config publish to NGINX One succeeded - reply was HTTP/200
            jsonResponse = json.loads(r.text)
            returnHttpCode = 200

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

        # If deploying a new configuration in GitOps mode start autosync
        if nOneSynctime == 0:
            NcgRedis.declarationsList[configUid] = "static"
        elif not runfromautosync:
            # GitOps autosync
            print(f'Starting autosync for configUid {configUid} every {nOneSynctime} seconds')

            job = schedule.every(nOneSynctime).seconds.do(lambda: v5_3_CreateConfig.configautosync(configUid))
            # Keep track of GitOps configs, key is the threaded job
            NcgRedis.declarationsList[configUid] = job

            NcgRedis.redis.set(f'ncg.apiversion.{configUid}', apiversion)

        responseContent = {' code': returnHttpCode, 'content': jsonResponse, 'configUid': configUid}

        # Configuration push completed, update redis keys
        if configUid != "":
            NcgRedis.redis.set('ncg.status.' + configUid, json.dumps(responseContent))

            # if nmsSynctime > 0:
            # Updates status, declaration and basestagedconfig in redis
            NcgRedis.redis.set('ncg.declaration.' + configUid, pickle.dumps(declaration))
            NcgRedis.redis.set('ncg.declarationrendered.' + configUid, json.dumps(d))
            NcgRedis.redis.set('ncg.basestagedconfig.' + configUid, json.dumps(baseStagedConfig))

        return {"status_code": returnHttpCode,
            "message": {"status_code": returnHttpCode,
                        "message": responseContent},
            "headers": {'Content-Type': 'application/json'}
            }