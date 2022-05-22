"""
Configuration creation based on jinja2 templates
"""

import base64
import requests
import json
import time

from jinja2 import Environment, FileSystemLoader
from fastapi.responses import Response, JSONResponse
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from datetime import datetime

# pydantic models
from NginxConfigDeclaration import *

# NGINX Configuration Generator modules
from NcgConfig import NcgConfig

# Tolerates self-signed TLS certificates
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


def createconfig(declaration: ConfigDeclaration, decltype: str):
    # Building NGINX configuration for declaration.json()
    d = declaration.dict()

    j2_env = Environment(loader=FileSystemLoader(NcgConfig.config['templates']['root_dir']), trim_blocks=True)
    httpConf = j2_env.get_template(NcgConfig.config['templates']['httpconf']).render(
        declaration=d['declaration']['http'])
    streamConf = j2_env.get_template(NcgConfig.config['templates']['streamconf']).render(
        declaration=d['declaration']['layer4'])

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
                                                                                        'name']+'.http',
                                                                                    filename=d['output']['configmap'][
                                                                                        'filename']+'.http',
                                                                                    namespace=d['output']['configmap'][
                                                                                        'namespace'])
        cmStream = j2_env.get_template(NcgConfig.config['templates']['configmap']).render(nginxconfig=streamConf,
                                                                                        name=d['output']['configmap'][
                                                                                            'name']+'.stream',
                                                                                        filename=
                                                                                        d['output']['configmap'][
                                                                                            'filename']+'.stream',
                                                                                        namespace=
                                                                                        d['output']['configmap'][
                                                                                            'namespace'])

        return Response(content=cmHttp+'\n---\n'+cmStream, headers={'Content-Type': 'application/x-yaml'})
    elif decltype.lower() == 'nms':
        # NGINX Management Suite Staged Configuration publish

        # Base64-encoded NGINX main configuration (/etc/nginx/nginx.conf)
        f = open(NcgConfig.config['templates']['root_dir'] + '/' + NcgConfig.config['templates']['nginxmain'], 'r')
        nginxMainConf = f.read()
        f.close()
        b64NginxMain = str(base64.urlsafe_b64encode(nginxMainConf.encode("utf-8")), "utf-8")

        # Base64-encoded NGINX mime.types (/etc/nginx/mime.types)
        f = open(NcgConfig.config['templates']['root_dir'] + '/' + NcgConfig.config['templates']['mimetypes'], 'r')
        nginxMimeTypes = f.read()
        f.close()
        b64NginxMimeTypes = str(base64.urlsafe_b64encode(nginxMimeTypes.encode("utf-8")), "utf-8")

        filesMimeType = {'contents': b64NginxMimeTypes, 'name': NcgConfig.config['nms']['config_dir'] + '/mime.types'}

        auxFiles = {'files': [], 'rootDir': NcgConfig.config['nms']['config_dir']}
        auxFiles['files'].append(filesMimeType)

        # Adds optional auxfiles specified under output.nms.auxfiles
        for dAuxFile in d['output']['nms']['auxfiles']:
            newAuxFile = {'contents': dAuxFile['contents'], 'name': dAuxFile['name']}
            auxFiles['files'].append(newAuxFile)

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

        stagedConfig = {'auxFiles': auxFiles, 'configFiles': configFiles,
                        'updateTime': datetime.utcnow().isoformat()[:-3] + 'Z',
                        'ignoreConflict': True, 'validateConfig': False}

        nmsUrl = d['output']['nms']['url']
        nmsUsername = d['output']['nms']['username']
        nmsPassword = d['output']['nms']['password']
        nmsInstanceGroup = d['output']['nms']['instancegroup']

        # Retrieve instance group uid
        ig = requests.get(url=nmsUrl + '/api/platform/v1/instance-groups', auth=(nmsUsername, nmsPassword),
                          verify=False)

        if ig.status_code != 200:
            return JSONResponse(
                status_code=ig.status_code,
                content=ig.text,
                headers=ig.headers
            )

        igUid = ''
        igJson = json.loads(ig.text)
        for i in igJson['items']:
            if i['name'] == nmsInstanceGroup:
                igUid = i['uid']

        # Invalid instance group
        if igUid == '':
            return JSONResponse(
                status_code=404,
                content={"message": f"instance group {nmsInstanceGroup} not found"},
                headers={'Content-Type': 'application/json'}
            )

        # Staged configuration publish to NGINX Management Suite
        r = requests.post(url=nmsUrl + f"/api/platform/v1/instance-groups/{igUid}/config",
                          data=json.dumps(stagedConfig),
                          headers={'Content-Type': 'application/json'},
                          auth=(nmsUsername, nmsPassword),
                          verify=False)

        publishResponse = json.loads(r.text)

        if r.status_code != 202:
            return JSONResponse(
                status_code=r.status_code,
                content=json.loads(r.text),
                headers=r.headers
            )

        # Fetches the deployment status
        time.sleep(5)
        deploymentCheck = requests.get(url=nmsUrl + publishResponse['links']['rel'], auth=(nmsUsername, nmsPassword),
                                       verify=False)

        checkJson = json.loads(deploymentCheck.text)

        if len(checkJson['details']['failure']) != 0:
            responseBody = json.dumps(checkJson['details']['failure'][0])
        else:
            responseBody = r.text

        if "Content-Length" in r.headers:
            r.headers.pop("Content-Length")
        if "Server" in r.headers:
            r.headers.pop("Server")
        if "Date" in r.headers:
            r.headers.pop("Date")

        return JSONResponse(
            status_code=r.status_code,
            content=json.loads(responseBody),
            headers=r.headers
        )

    else:
        return JSONResponse(
            status_code=422,
            content={"message": f"output type {decltype} unknown"}
        )
