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

# Tolerates self-signed TLS certificates
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


def getuniqueid():
    return uuid.uuid4()


def configautosync(configUid):
    print("Autosyncing configuid [" + configUid + "]")

    declaration = pickle.loads(NcgRedis.redis.get('ncg.declaration.' + configUid))
    apiversion = NcgRedis.redis.get('ncg.apiversion.' + configUid).decode()

    createconfig(declaration=declaration, apiversion=apiversion, runfromautosync=True, configUid=configUid)


def createconfig(declaration: ConfigDeclaration, apiversion: str, runfromautosync: bool = False, configUid: str = ""):
    # Building NGINX configuration for the given declaration

    try:
        # Pydantic JSON validation
        ConfigDeclaration(**declaration.dict())
    except ValidationError as e:
        print(f'JSON declaration invalid {e}')

    d = declaration.dict()
    decltype = d['output']['type']

    if d['declaration']['http'] is not None:

        if d['declaration']['http']['snippet'] is not None:
            d['declaration']['http']['snippet'] = Contrib.GitOps.getObjectFromRepo(d['declaration']['http']['snippet'])

        # Check HTTP upstreams validity
        all_upstreams = []
        http = d['declaration']['http']
        for i in range(len(http['upstreams'])):

            upstream = http['upstreams'][i]

            if upstream['snippet'] is not None:
                d['declaration']['http']['upstreams'][i]['snippet'] = Contrib.GitOps.getObjectFromRepo(
                    upstream['snippet'])

            all_upstreams.append(http['upstreams'][i]['name'])

        for server in d['declaration']['http']['servers']:
            if server['snippet'] is not None:
                server['snippet'] = Contrib.GitOps.getObjectFromRepo(server['snippet'])

            for loc in server['locations']:
                if loc['snippet'] is not None:
                    loc['snippet'] = Contrib.GitOps.getObjectFromRepo(loc['snippet'])

                if 'upstream' in loc and loc['upstream'].split('://')[1] not in all_upstreams:
                    return JSONResponse(

                        status_code=422,
                        content={"code": 422, "details": "invalid HTTP upstream " + loc['upstream']}
                    )

        # Check HTTP rate_limit profiles validity
        all_ratelimits = []
        http = d['declaration']['http']
        if http['rate_limit'] is not None:
            for i in range(len(http['rate_limit'])):
                all_ratelimits.append(http['rate_limit'][i]['name'])

            for server in d['declaration']['http']['servers']:
                for loc in server['locations']:
                    if loc['rate_limit'] is not None:
                        if loc['rate_limit']['profile'] not in all_ratelimits:
                            return JSONResponse(
                                status_code=422,
                                content={"code": 422,
                                         "details": "invalid rate_limit profile " + loc['rate_limit']['profile']}
                            )

    if d['declaration']['layer4'] is not None:
        # Check Layer4/stream upstreams validity
        all_upstreams = []
        layer4 = d['declaration']['layer4']
        for i in range(len(layer4['upstreams'])):
            all_upstreams.append(layer4['upstreams'][i]['name'])

        for server in d['declaration']['layer4']['servers']:

            if server['snippet'] is not None:
                server['snippet'] = Contrib.GitOps.getObjectFromRepo(server['snippet'])

            if 'upstream' in server and server['upstream'] not in all_upstreams:
                return JSONResponse(
                    status_code=422,
                    content={"code": 422, "details": "invalid Layer4 upstream " + server['upstream']}
                )

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
            return JSONResponse(
                status_code=200,
                content=payload
            )
        else:
            try:
                r = requests.post(d['output']['http']['url'], data=json.dumps(payload),
                                  headers={'Content-Type': 'application/json'})
            except:
                headers = {'Content-Type': 'application/json'}
                content = {'message': d['output']['http']['url'] + ' unreachable'}

                return JSONResponse(
                    status_code=502,
                    content=content,
                    headers=headers
                )

            if "Content-Length" in r.headers:
                r.headers.pop("Content-Length")
            if "Server" in r.headers:
                r.headers.pop("Server")
            if "Date" in r.headers:
                r.headers.pop("Date")

            return JSONResponse(
                status_code=r.status_code,
                content=r.text,
                headers=r.headers
            )
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

        return Response(content=cmHttp + '\n---\n' + cmStream, headers={'Content-Type': 'application/x-yaml'})
    elif decltype.lower() == 'nms':
        # NGINX Management Suite Staged Configuration publish
        nmsUrl = d['output']['nms']['url']
        nmsUsername = d['output']['nms']['username']
        nmsPassword = d['output']['nms']['password']
        nmsInstanceGroup = d['output']['nms']['instancegroup']
        nmsSynctime = d['output']['nms']['synctime']

        auxFiles = {'files': [], 'rootDir': NcgConfig.config['nms']['config_dir']}

        # Check TLS items validity
        certs = d['output']['nms']['certificates']
        all_tls = {'certificate': {}, 'key': {}, 'chain': {}}
        for i in range(len(certs)):
            all_tls[certs[i]['type']][certs[i]['name']] = True

        if d['declaration']['http'] is not None:
            if d['declaration']['http']['servers'] is not None:
                for server in d['declaration']['http']['servers']:
                    if server['listen']['tls'] is not None:
                        cert_name = server['listen']['tls']['certificate']
                        if cert_name not in all_tls['certificate']:
                            return JSONResponse(
                                status_code=422,
                                content={"code": 422,
                                         "details": "invalid TLS certificate " + cert_name + " for server" + str(
                                             server['names'])}
                            )

                        cert_key = server['listen']['tls']['key']
                        if cert_key not in all_tls['key']:
                            return JSONResponse(
                                status_code=422,
                                content={"code": 422,
                                         "details": "invalid TLS key " + cert_key + " for server" + str(
                                             server['names'])}
                            )

                        if server['listen']['tls']['chain'] is not None:
                            cert_chain = server['listen']['tls']['chain']
                            if cert_chain not in all_tls['chain']:
                                return JSONResponse(
                                    status_code=422,
                                    content={"code": 422,
                                             "details": "invalid TLS chain " + cert_chain + " for server" + str(
                                                 server['names'])}
                                )

        # Adds optional certificates specified under output.nms.certificates
        extensions_map = {'certificate': '.crt', 'key': '.key', 'chain': '.chain'}
        for c in d['output']['nms']['certificates']:
            certContent = Contrib.GitOps.getObjectFromRepo(c['contents'])

            newAuxFile = {'contents': certContent, 'name': NcgConfig.config['nms']['certs_dir'] +
                                                           '/' + c['name'] + extensions_map[c['type']]}
            auxFiles['files'].append(newAuxFile)

        ### / Adds optional certificates specified under output.nms.certificates

        # NGINX App Protect policies - each policy supports multiple tagged versions
        all_policies = {'app_protect': []}
        for p in d['output']['nms']['policies']:

            # Iterates over all NGINX App Protect policies
            if p['type'] == 'app_protect':
                # Iterates over all policy versions
                for policyVersion in p['versions']:
                    policyBody = Contrib.GitOps.getObjectFromRepo(policyVersion['contents'])

                    # Create the NGINX App Protect policy on NMS
                    r = Contrib.NAPUtils.createPolicy(
                        nmsUrl = nmsUrl, nmsUsername = nmsUsername, nmsPassword = nmsPassword,
                        policyName = p['name'],
                        policyDisplayName = policyVersion['displayName'],
                        policyDescription = policyVersion['description'],
                        policyJson = policyBody
                    )

                    # Check for errors creating NGINX App Protect policy
                    if r.status_code != 201:
                        return JSONResponse(
                            status_code=r.status_code,
                            content={"code": r.status_code, "details": json.loads(r.text)}
                        )

                # Stores the policy name in the global dictionary of available policies
                all_policies[p['type']].append(p['name'])



        ### / NGINX App Protect policies - each policy supports multiple tagged versions

        # Check NGINX App Protect policies and log profiles validity
        if d['declaration']['http'] is not None:
            for server in d['declaration']['http']['servers']:

                # Check app_protect directives in server {}
                if server['app_protect'] is not None:
                    if server['app_protect']['policy'] not in all_policies['app_protect']:
                        return JSONResponse(
                            status_code=422,
                            content={"code": 422,
                                     "details": "Invalid NGINX App Protect policy " + server['app_protect']['policy']}
                        )

                    if 'log' in server['app_protect'] and server['app_protect']['log']['profile_name'] not in \
                            ['log_all', 'log_blocked', 'log_illegal', 'secops_dashboard']:
                        return JSONResponse(
                            status_code=422,
                            content={"code": 422,
                                     "details": "Invalid NGINX App Protect log profile " + server['app_protect']['log'][
                                         'profile_name']}
                        )

                # Check app_protect directives in server.location {}
                for logprofile in server['locations']:
                    if logprofile['app_protect'] is not None:
                        if logprofile['app_protect']['policy'] not in all_policies['app_protect']:
                            return JSONResponse(
                                status_code=422,
                                content={"code": 422,
                                         "details": "Invalid NGINX App Protect policy " + logprofile['app_protect'][
                                             'policy']}
                            )

                        if 'log' in logprofile['app_protect'] and logprofile['app_protect']['log'][
                            'profile_name'] not in ['log_all', 'log_blocked', 'log_illegal', 'secops_dashboard']:
                            return JSONResponse(
                                status_code=422,
                                content={"code": 422, "details": "Invalid NGINX App Protect log profile " +
                                                                 logprofile['app_protect']['log'][
                                                                     'profile_name']}
                            )

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

        redisBaseStagedConfig = NcgRedis.redis.get('ncg.basestagedconfig.' + configUid)

        if redisBaseStagedConfig is not None and json.dumps(baseStagedConfig) == redisBaseStagedConfig.decode('utf-8'):
            print(f'Staged config {configUid} not changed')
        else:
            # Configuration objects have changed, publish to NIM needed
            print(f'Staged config {configUid} changed, publishing to NMS')

            # Retrieve instance group uid
            ig = requests.get(url=nmsUrl + '/api/platform/v1/instance-groups', auth=(nmsUsername, nmsPassword),
                              verify=False)

            if ig.status_code != 200:
                return JSONResponse(
                    status_code=ig.status_code,
                    content={"code": ig.status_code, "details": json.loads(ig.text)}
                )

            # Get the instance group id
            igUid = ''
            igJson = json.loads(ig.text)
            for i in igJson['items']:
                if i['name'] == nmsInstanceGroup:
                    igUid = i['uid']

            # Invalid instance group
            if igUid == '':
                return JSONResponse(
                    status_code=404,
                    content={"code": 404, "details": f"instance group {nmsInstanceGroup} not found"},
                    headers={'Content-Type': 'application/json'}
                )

            # Staged configuration publish to NGINX Management Suite
            stagedConfigPayload = json.dumps(stagedConfig)

            # Publish staged config to instance group
            r = requests.post(url=nmsUrl + f"/api/platform/v1/instance-groups/{igUid}/config",
                              data=stagedConfigPayload,
                              headers={'Content-Type': 'application/json'},
                              auth=(nmsUsername, nmsPassword),
                              verify=False)

            if r.status_code != 202:
                return JSONResponse(
                    status_code=r.status_code,
                    content={"code": r.status_code, "details": r.text},
                    headers={'Content-Type': 'application/json'}
                )

            # Fetches the deployment status
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

                if configUid == "":
                    # No configuration is found, generate one
                    configUid = str(getuniqueid())

                    # Stores the staged config to redis
                    # Redis keys:
                    # ncg.declaration.[configUid] = original config declaration
                    # ncg.basestagedconfig.[configUid] = base staged configuration
                    # ncg.apiversion.[configUid] = ncg API version
                    # ncg.status.[configUid] = latest status

                    NcgRedis.redis.set('ncg.declaration.' + configUid, pickle.dumps(declaration))
                    NcgRedis.redis.set('ncg.basestagedconfig.' + configUid, json.dumps(baseStagedConfig))
                    NcgRedis.redis.set('ncg.apiversion.' + configUid, apiversion)

                # If deploying a new configuration in GitOps mode start autosync
                if nmsSynctime > 0 and runfromautosync == False:
                    # GitOps autosync
                    print(f'Starting autosync for configUid {configUid} every {nmsSynctime} seconds')

                    job = schedule.every(nmsSynctime).seconds.do(lambda: configautosync(configUid))

                    # Keep track of GitOps configs, key is the threaded job
                    NcgRedis.declarationsList[configUid] = job
                else:
                    # Keep track of non-GitOps configs, key is "static"
                    NcgRedis.declarationsList[configUid] = "static"

            responseContent = {"code": deploymentCheck.status_code, "details": jsonResponse, "configUid": configUid}

            # Configuration push completed, update redis keys
            if configUid != "":
                # Updates status, declaration and basestagedconfig in redis
                NcgRedis.redis.set('ncg.status.' + configUid, json.dumps(responseContent))
                NcgRedis.redis.set('ncg.declaration.' + configUid, pickle.dumps(declaration))
                NcgRedis.redis.set('ncg.basestagedconfig.' + configUid, json.dumps(baseStagedConfig))

            return JSONResponse(
                status_code=deploymentCheck.status_code,
                content=responseContent,
                headers={'Content-Type': 'application/json'}
            )

    else:
        return JSONResponse(
            status_code=422,
            content={"message": f"output type {decltype} unknown"}
        )


def putconfig(declaration: ConfigDeclaration, apiversion: str, runfromautosync: bool = False, configUid: str = ""):
    return JSONResponse(status_code=418,content={"message":"WORK IN PROGRESS"})