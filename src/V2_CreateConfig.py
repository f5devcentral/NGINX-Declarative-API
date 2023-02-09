"""
Configuration creation based on jinja2 templates
"""

import base64
import requests
import json
import time
import uuid
import schedule
import pickle

from jinja2 import Environment, FileSystemLoader
from fastapi.responses import Response, JSONResponse
from pydantic import ValidationError
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from datetime import datetime

# pydantic models
from V2_NginxConfigDeclaration import *

# NGINX Declarative API modules
from NcgConfig import NcgConfig
from NcgRedis import NcgRedis

# NGINX App Protect helper functions
import Contrib.NAPUtils
import Contrib.GitOps
import Contrib.NIMUtils
import Contrib.DeclarationPatcher

# Tolerates self-signed TLS certificates
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


def getuniqueid():
    return uuid.uuid4()


def configautosync(configUid):
    print("Autosyncing configuid [" + configUid + "]")

    declaration = ''
    declFromRedis = NcgRedis.redis.get(f'ncg.declaration.{configUid}')

    if declFromRedis is not None:
        declaration = pickle.loads(declFromRedis)
    apiversion = NcgRedis.redis.get(f'ncg.apiversion.{configUid}').decode()

    createconfig(declaration=declaration, apiversion=apiversion, runfromautosync=True, configUid=configUid)


# Create the given declarative configuration
# Return a JSON string:
# { "status_code": nnn, "headers": {}, "message": {} }
def createconfig(declaration: ConfigDeclaration, apiversion: str, runfromautosync: bool = False, configUid: str = ""):
    # Building NGINX configuration for the given declaration

    try:
        # Pydantic JSON validation
        ConfigDeclaration(**declaration.dict())
    except ValidationError as e:
        print(f'Invalid declaration {e}')

    d = declaration.dict()
    decltype = d['output']['type']

    if 'http' in d['declaration']:
        if 'snippet' in d['declaration']['http']:
            status, snippet = Contrib.GitOps.getObjectFromRepo(d['declaration']['http']['snippet'])

            if status != 200:
                return {"status_code": 422, "message": {"status_code": status, "message": snippet}}

            d['declaration']['http']['snippet'] = snippet

        # Check HTTP upstreams validity
        all_upstreams = []
        http = d['declaration']['http']

        if 'upstreams' in http:
            for i in range(len(http['upstreams'])):

                upstream = http['upstreams'][i]

                if upstream['snippet']:
                    status, snippet = Contrib.GitOps.getObjectFromRepo(upstream['snippet'])

                    if status != 200:
                        return {"status_code": 422, "message": {"status_code": status, "message": snippet}}

                    d['declaration']['http']['upstreams'][i]['snippet'] = snippet

                all_upstreams.append(http['upstreams'][i]['name'])

        if 'servers' in d['declaration']['http']:
            for server in d['declaration']['http']['servers']:
                if server['snippet']:
                    status, snippet = Contrib.GitOps.getObjectFromRepo(server['snippet'])

                    if status != 200:
                        return {"status_code": 422, "message": {"status_code": status, "message": snippet}}

                    server['snippet'] = snippet

                for loc in server['locations']:
                    if loc['snippet']:
                        status, snippet = Contrib.GitOps.getObjectFromRepo(loc['snippet'])

                        if status != 200:
                            return {"status_code": 422, "message": {"status_code": status, "message": snippet}}

                        loc['snippet'] = snippet

                    if 'upstream' in loc and loc['upstream'] and loc['upstream'].split('://')[1] not in all_upstreams:
                        print(f"INVALID UPSTREAM {loc['upstream']}")
                        return {"status_code": 422,
                                "message": {"status_code": status,
                                                                "message": "invalid HTTP upstream ["
                                                                           + loc['upstream'] + "]"}}

        # Check HTTP rate_limit profiles validity
        all_ratelimits = []
        http = d['declaration']['http']

        if 'rate_limit' in http:
            if http['rate_limit']:
                for i in range(len(http['rate_limit'])):
                    all_ratelimits.append(http['rate_limit'][i]['name'])

                for server in d['declaration']['http']['servers']:
                    for loc in server['locations']:
                        if loc['rate_limit'] != "":
                            if loc['rate_limit']['profile'] and loc['rate_limit']['profile'] not in all_ratelimits:
                                return {"status_code": 422,
                                        "message": {
                                            "status_code": status,
                                            "message": f"invalid rate_limit profile {loc['rate_limit']['profile']}"}}

    if 'layer4' in d['declaration']:
        # Check Layer4/stream upstreams validity
        all_upstreams = []

        layer4 = d['declaration']['layer4']

        if 'upstreams' in layer4:
            for i in range(len(layer4['upstreams'])):
                all_upstreams.append(layer4['upstreams'][i]['name'])

        if 'servers' in d['declaration']['layer4']:
            for server in d['declaration']['layer4']['servers']:

                if server['snippet']:
                    status, snippet = Contrib.GitOps.getObjectFromRepo(server['snippet'])

                    if status != 200:
                        return {"status_code": 422, "message": {"status_code": status, "message": snippet}}

                    server['snippet'] = snippet

                if 'upstream' in server and server['upstream'] and server['upstream'] not in all_upstreams:
                    return {"status_code": 422,
                            "message": {
                                "status_code": status,
                                "message": f"invalid Layer4 upstream {server['upstream']}"}}

    j2_env = Environment(loader=FileSystemLoader(NcgConfig.config['templates']['root_dir'] + '/' + apiversion),
                         trim_blocks=True, extensions=["jinja2_base64_filters.Base64Filters"])

    httpConf = j2_env.get_template(NcgConfig.config['templates']['httpconf']).render(
        declaration=d['declaration']['http'], ncgconfig=NcgConfig.config)
    streamConf = j2_env.get_template(NcgConfig.config['templates']['streamconf']).render(
        declaration=d['declaration']['layer4'], ncgconfig=NcgConfig.config)

    b64HttpConf = str(base64.urlsafe_b64encode(httpConf.encode("utf-8")), "utf-8")
    b64StreamConf = str(base64.urlsafe_b64encode(streamConf.encode("utf-8")), "utf-8")

    if decltype.lower() == "plaintext":
        # Plaintext output
        return httpConf + streamConf

    elif decltype.lower() == "json" or decltype.lower() == 'http':
        # JSON-wrapped b64-encoded output
        payload = {"http_config": f"{b64HttpConf}", "stream_config": f"{b64StreamConf}"}

        if decltype.lower() == "json":
            return {"status_code": 200, "message": payload}
        else:
            try:
                r = requests.post(d['output']['http']['url'], data=json.dumps(payload),
                                  headers={'Content-Type': 'application/json'})
            except:
                headers = {'Content-Type': 'application/json'}
                content = {'message': d['output']['http']['url'] + ' unreachable'}

                return {"status_code": 502, "message": {"status_code": 502, "message": content}, "headers": headers}

            if "Content-Length" in r.headers:
                r.headers.pop("Content-Length")
            if "Server" in r.headers:
                r.headers.pop("Server")
            if "Date" in r.headers:
                r.headers.pop("Date")

            return {"status_code": r.status_code, "message":
                {"status_code": r.status_code, "message": r.text}, "headers": r.headers}

    elif decltype.lower() == 'configmap':
        # Kubernetes ConfigMap output
        cmHttp = j2_env.get_template(NcgConfig.config['templates']['configmap']).render(nginxconfig=httpConf,
                                                                                        name=d['output']['configmap'][
                                                                                                 'name'] + '.http',
                                                                                        filename=
                                                                                        d['output']['configmap'][
                                                                                            'filename'] + '.http',
                                                                                        namespace=
                                                                                        d['output']['configmap'][
                                                                                            'namespace'])
        cmStream = j2_env.get_template(NcgConfig.config['templates']['configmap']).render(nginxconfig=streamConf,
                                                                                          name=d['output']['configmap'][
                                                                                                   'name'] + '.stream',
                                                                                          filename=
                                                                                          d['output']['configmap'][
                                                                                              'filename'] + '.stream',
                                                                                          namespace=
                                                                                          d['output']['configmap'][
                                                                                              'namespace'])

        return {"status_code": 422, "message": f"{cmHttp}\n---\n{cmStream}",
                "headers": {'Content-Type': 'application/x-yaml'}}

    elif decltype.lower() == 'nms':
        # NGINX Management Suite Staged Configuration publish
        nmsUrl = d['output']['nms']['url']
        nmsUsername = d['output']['nms']['username']
        nmsPassword = d['output']['nms']['password']
        nmsInstanceGroup = d['output']['nms']['instancegroup']
        nmsSynctime = d['output']['nms']['synctime']

        auxFiles = {'files': [], 'rootDir': NcgConfig.config['nms']['config_dir']}

        # Fetch NGINX App Protect WAF policies from source of truth if needed
        if 'policies' in d['output']['nms']:
            for policy in d['output']['nms']['policies']:
                if 'versions' in policy:
                    for policyVersion in policy['versions']:
                        status, content = Contrib.GitOps.getObjectFromRepo(policyVersion['contents'])

                        if status != 200:
                            return {"status_code": 422, "message": {"status_code": status, "message": content}}

                        policyVersion['contents'] = content

        # Check TLS items validity
        all_tls = {'certificate': {}, 'key': {}, 'chain': {}}

        if 'certificates' in d['output']['nms']:
            certs = d['output']['nms']['certificates']
            for i in range(len(certs)):
                if certs[i]['name']:
                    all_tls[certs[i]['type']][certs[i]['name']] = True

        if 'http' in d['declaration']:
            if 'servers' in d['declaration']['http']:
                for server in d['declaration']['http']['servers']:
                    if 'tls' in server['listen']:
                        if 'certificate' in server['listen']['tls']:
                            cert_name = server['listen']['tls']['certificate']
                            if cert_name and cert_name not in all_tls['certificate']:
                                return {"status_code": 422,
                                        "message": {
                                            "status_code": 422,
                                            "message": "invalid TLS certificate " + cert_name + " for server" + str(
                                                server['names'])}
                                        }

                        if 'key' in server['listen']['tls']:
                            cert_key = server['listen']['tls']['key']
                            if cert_key and cert_key not in all_tls['key']:
                                return {"status_code": 422,
                                        "message": {
                                            "status_code": 422,
                                            "message": "invalid TLS key " + cert_key + " for server" + str(
                                                server['names'])}
                                        }

                        if 'chain' in server['listen']['tls']:
                            cert_chain = server['listen']['tls']['chain']
                            if cert_chain and cert_chain not in all_tls['chain']:
                                return {"status_code": 422,
                                        "message": {
                                            "status_code": 422,
                                            "message": "invalid TLS chain " + cert_chain + " for server" + str(
                                                server['names'])}
                                        }

        # Adds optional certificates specified under output.nms.certificates
        extensions_map = {'certificate': '.crt', 'key': '.key', 'chain': '.chain'}

        if 'certificates' in d['output']['nms']:
            for c in d['output']['nms']['certificates']:
                status, certContent = Contrib.GitOps.getObjectFromRepo(c['contents'])

                if status != 200:
                    return {"status_code": 422, "message": {"status_code": status, "message": certContent}}

                newAuxFile = {'contents': certContent, 'name': NcgConfig.config['nms']['certs_dir'] +
                                                               '/' + c['name'] + extensions_map[c['type']]}
                auxFiles['files'].append(newAuxFile)

        ### / Adds optional certificates specified under output.nms.certificates

        # NGINX main configuration file through template
        j2_env = Environment(loader=FileSystemLoader(NcgConfig.config['templates']['root_dir'] + '/' + apiversion),
                             trim_blocks=True, extensions=["jinja2_base64_filters.Base64Filters"])

        nginxMainConf = j2_env.get_template(NcgConfig.config['templates']['nginxmain']).render(
            nginxconf={'modules': d['output']['nms']['modules']})

        # Base64-encoded NGINX main configuration (/etc/nginx/nginx.conf)
        b64NginxMain = str(base64.urlsafe_b64encode(nginxMainConf.encode("utf-8")), "utf-8")

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
        filesHttpConf = {'contents': b64HttpConf,
                         'name': NcgConfig.config['nms']['config_dir'] + '/' + NcgConfig.config['nms'][
                             'staged_config_http_filename']}
        filesStreamConf = {'contents': b64StreamConf,
                           'name': NcgConfig.config['nms']['config_dir'] + '/' + NcgConfig.config['nms'][
                               'staged_config_stream_filename']}

        configFiles = {'files': [], 'rootDir': NcgConfig.config['nms']['config_dir']}
        configFiles['files'].append(filesNginxMain)
        configFiles['files'].append(filesHttpConf)
        configFiles['files'].append(filesStreamConf)

        # Staged config
        baseStagedConfig = {'auxFiles': auxFiles, 'configFiles': configFiles}
        stagedConfig = {'auxFiles': auxFiles, 'configFiles': configFiles,
                        'updateTime': datetime.utcnow().isoformat()[:-3] + 'Z',
                        'ignoreConflict': True, 'validateConfig': False}

        redisDeclarationRendered = NcgRedis.redis.get(f'ncg.declarationrendered.{configUid}')

        if redisDeclarationRendered is not None and json.dumps(d) == redisDeclarationRendered.decode('utf-8'):
            print(f'Configuration [{configUid}] not changed')
            return {"status_code": 200, "message": {"status_code": 200, "message": "no changes"}}
        else:
            # Configuration objects have changed, publish to NIM needed
            print(f'Configuration [{configUid}] changed, publishing to NMS')

            # Retrieve instance group uid
            ig = requests.get(url=f'{nmsUrl}/api/platform/v1/instance-groups', auth=(nmsUsername, nmsPassword),
                              verify=False)

            if ig.status_code != 200:
                return {"status_code": ig.status_code, "message":
                    {"status_code": ig.status_code, "message": json.loads(ig.text)}}

            # Get the instance group id
            igUid = Contrib.NIMUtils.getNIMInstanceGroupUid(nmsUrl=nmsUrl, nmsUsername=nmsUsername,
                                                            nmsPassword=nmsPassword, instanceGroupName=nmsInstanceGroup)

            # Invalid instance group
            if igUid is None:
                return {"status_code": 404,
                        "message": {"status_code": 404, "message": f"instance group {nmsInstanceGroup} not found"},
                        "headers": {'Content-Type': 'application/json'}}

            ### NGINX App Protect policies support - commits policies to control plane

            # Check NGINX App Protect WAF policies configuration sanity
            status, description = Contrib.NAPUtils.checkDeclarationPolicies(d)

            if status != 200:
                return {"status_code": 422, "message": {"status_code": status, "message": description}}

            # Provision NGINX App Protect WAF policies to NGINX Management Suite
            provisionedNapPolicies, activePolicyUids = Contrib.NAPUtils.provisionPolicies(
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
            time.sleep(NcgConfig.config['nms']['staged_config_publish_waittime'])
            deploymentCheck = requests.get(url=nmsUrl + publishResponse['links']['rel'],
                                           auth=(nmsUsername, nmsPassword),
                                           verify=False)

            checkJson = json.loads(deploymentCheck.text)

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
                    configUid = str(getuniqueid())

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
                doWeHavePolicies = Contrib.NAPUtils.makePolicyActive(nmsUrl=nmsUrl, nmsUsername=nmsUsername, nmsPassword=nmsPassword,
                                                  activePolicyUids=activePolicyUids, instanceGroupUid=igUid)

                if doWeHavePolicies:
                    # Clean up NGINX App Protect WAF policies not used anymore
                    # and not defined in the declaration just pushed
                    time.sleep(NcgConfig.config['nms']['staged_config_publish_waittime'])
                    Contrib.NAPUtils.cleanPolicyLeftovers(nmsUrl=nmsUrl, nmsUsername=nmsUsername,
                                                          nmsPassword=nmsPassword,
                                                          currentPolicies=provisionedNapPolicies)

                # If deploying a new configuration in GitOps mode start autosync
                if nmsSynctime == 0:
                    NcgRedis.declarationsList[configUid] = "static"
                elif not runfromautosync:
                    # GitOps autosync
                    print(f'Starting autosync for configUid {configUid} every {nmsSynctime} seconds')

                    job = schedule.every(nmsSynctime).seconds.do(lambda: configautosync(configUid))
                    # Keep track of GitOps configs, key is the threaded job
                    NcgRedis.declarationsList[configUid] = job

                    NcgRedis.redis.set(f'ncg.apiversion.{configUid}', apiversion)
                    # NcgRedis.redis.set(f'ncg.declaration.{configUid}', pickle.dumps(declaration))
                    # NcgRedis.redis.set(f'ncg.declarationrendered.{configUid}', json.dumps(d))
                    # NcgRedis.redis.set(f'ncg.basestagedconfig.{configUid}', json.dumps(baseStagedConfig))

            responseContent = {'code': deploymentCheck.status_code, 'content': jsonResponse, 'configUid': configUid}

            # Configuration push completed, update redis keys
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

    else:
        return {"status_code": 422, "message": {"status_code": 422, "message": f"output type {decltype} unknown"}}


def patch_config(declaration: ConfigDeclaration, configUid: str, apiversion: str):
    # Patch a declaration
    if configUid not in NcgRedis.declarationsList:
        return JSONResponse(
            status_code=404,
            content={'code': 404, 'details': {'message': f'declaration {configUid} not found'}},
            headers={'Content-Type': 'application/json'}
        )

    # The declaration sections to be patched
    declarationToPatch = declaration.dict()

    # The currently applied declaration
    status_code, currentDeclaration = get_declaration(configUid=configUid)

    # Handles declaration updates
    if 'declaration' in declarationToPatch:
        # HTTP
        if 'http' in declarationToPatch['declaration']:
            if 'upstreams' in declarationToPatch['declaration']['http']:
                # HTTPu pstream patch
                for u in declarationToPatch['declaration']['http']['upstreams']:
                    # print(f"Patching HTTP upstream [{u['name']}]")
                    currentDeclaration = Contrib.DeclarationPatcher.patchHttpUpstream(
                        sourceDeclaration=currentDeclaration, patchedHttpUpstream=u)

            if 'servers' in declarationToPatch['declaration']['http']:
                # HTTP servers patch
                for s in declarationToPatch['declaration']['http']['servers']:
                    # print(f"Patching HTTP server [{s['name']}]")
                    currentDeclaration = Contrib.DeclarationPatcher.patchHttpServer(
                        sourceDeclaration=currentDeclaration, patchedHttpServer=s)

        # Stream / Layer4
        if 'layer4' in declarationToPatch['declaration']:
            if 'upstreams' in declarationToPatch['declaration']['layer4']:
                # Stream upstream patch
                for u in declarationToPatch['declaration']['layer4']['upstreams']:
                    # print(f"Patching Stream upstream [{u['name']}]")
                    currentDeclaration = Contrib.DeclarationPatcher.patchStreamUpstream(
                        sourceDeclaration=currentDeclaration, patchedStreamUpstream=u)

            if 'servers' in declarationToPatch['declaration']['layer4']:
                # Stream servers patch
                for s in declarationToPatch['declaration']['layer4']['servers']:
                    # print(f"Patching Stream server [{s['name']}]")
                    currentDeclaration = Contrib.DeclarationPatcher.patchStreamServer(
                        sourceDeclaration=currentDeclaration, patchedStreamServer=s)

    # Apply the updated declaration
    configDeclaration = ConfigDeclaration.parse_raw(json.dumps(currentDeclaration))

    r = createconfig(declaration=configDeclaration, apiversion=apiversion,
                     runfromautosync=True, configUid=configUid)

    # Return the updated declaration
    message = r['message']

    if r['status_code'] != 200:
        currentDeclaration = {}
        #message = f'declaration {configUid} update failed';

    responseContent = {'code': r['status_code'], 'details': {'message': message},
                       'declaration': currentDeclaration, 'configUid': configUid}

    return JSONResponse(
        status_code=r['status_code'],
        content=responseContent,
        headers={'Content-Type': 'application/json'}
    )


# Gets the given declaration. Returns status_code and body
def get_declaration(configUid: str):
    cfg = NcgRedis.redis.get('ncg.declaration.' + configUid)

    if cfg is None:
        return 404, ""

    return 200, pickle.loads(cfg).dict()
