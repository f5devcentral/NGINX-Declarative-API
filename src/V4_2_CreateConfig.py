"""
Configuration creation based on jinja2 templates
"""

import base64
import json
import pickle
import time
import uuid
import hashlib
from datetime import datetime
from urllib.parse import urlparse

import requests
import schedule
from fastapi.responses import Response, JSONResponse
from jinja2 import Environment, FileSystemLoader
from pydantic import ValidationError
from requests.packages.urllib3.exceptions import InsecureRequestWarning

import v4_2.APIGateway
import v4_2.DevPortal
import v4_2.DeclarationPatcher
import v4_2.GitOps
import v4_2.MiscUtils

# NGINX App Protect helper functions
import v4_2.NAPUtils
import v4_2.NIMUtils

# NGINX Declarative API modules
from NcgConfig import NcgConfig
from NcgRedis import NcgRedis

# pydantic models
from V4_2_NginxConfigDeclaration import *

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

    # NGINX configuration files for staged config
    configFiles = {'files': [], 'rootDir': NcgConfig.config['nms']['config_dir']}

    # NGINX auxiliary files for staged config
    auxFiles = {'files': [], 'rootDir': NcgConfig.config['nms']['config_dir']}

    try:
        # Pydantic JSON validation
        ConfigDeclaration(**declaration.model_dump())
    except ValidationError as e:
        print(f'Invalid declaration {e}')

    d = declaration.model_dump()
    decltype = d['output']['type']

    j2_env = Environment(loader=FileSystemLoader(NcgConfig.config['templates']['root_dir'] + '/' + apiversion),
                         trim_blocks=True, extensions=["jinja2_base64_filters.Base64Filters"])
    j2_env.filters['regex_replace'] = v4_2.MiscUtils.regex_replace

    if 'http' in d['declaration']:
        if 'snippet' in d['declaration']['http']:
            status, snippet = v4_2.GitOps.getObjectFromRepo(object = d['declaration']['http']['snippet'], authProfiles = d['declaration']['http']['authentication'])

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
                    status, snippet = v4_2.GitOps.getObjectFromRepo(object = upstream['snippet'], authProfiles = d['declaration']['http']['authentication'])

                    if status != 200:
                        return {"status_code": 422, "message": {"status_code": status, "message": snippet}}

                    d['declaration']['http']['upstreams'][i]['snippet'] = snippet

                all_upstreams.append(http['upstreams'][i]['name'])

        # Check HTTP rate_limit profiles validity
        all_ratelimits = []
        http = d['declaration']['http']

        d_rate_limit = v4_2.MiscUtils.getDictKey(d, 'declaration.http.rate_limit')
        if d_rate_limit is not None:
            for i in range(len(d_rate_limit)):
                all_ratelimits.append(d_rate_limit[i]['name'])

        # Check authentication profiles validity and creates authentication config files

        # List of all auth client & server profile names
        all_auth_client_profiles = []
        all_auth_server_profiles = []

        d_auth_profiles = v4_2.MiscUtils.getDictKey(d, 'declaration.http.authentication')
        if d_auth_profiles is not None:
            if 'client' in d_auth_profiles:
                # Render all client authentication profiles

                auth_client_profiles = d_auth_profiles['client']
                for i in range(len(auth_client_profiles)):
                    auth_profile = auth_client_profiles[i]

                    match auth_profile['type']:
                        case 'jwt':
                            # Add the rendered authentication configuration snippet as a config file in the staged configuration - jwt template
                            templateName = NcgConfig.config['templates']['auth_client_root']+"/jwt.tmpl"
                            renderedClientAuthProfile = j2_env.get_template(templateName).render(
                                authprofile=auth_profile, ncgconfig=NcgConfig.config)

                            b64renderedClientAuthProfile = base64.b64encode(bytes(renderedClientAuthProfile, 'utf-8')).decode('utf-8')
                            configFileName = NcgConfig.config['nms']['auth_client_dir'] + '/'+auth_profile['name'].replace(' ','_')+".conf"
                            authProfileConfigFile = {'contents': b64renderedClientAuthProfile,
                                              'name': configFileName }

                            all_auth_client_profiles.append(auth_profile['name'])
                            auxFiles['files'].append(authProfileConfigFile)

                            # Add the rendered authentication configuration snippet as a config file in the staged configuration - jwks template
                            templateName = NcgConfig.config['templates']['auth_client_root']+"/jwks.tmpl"
                            renderedClientAuthProfile = j2_env.get_template(templateName).render(
                                authprofile=auth_profile, ncgconfig=NcgConfig.config)

                            b64renderedClientAuthProfile = base64.b64encode(bytes(renderedClientAuthProfile, 'utf-8')).decode('utf-8')
                            configFileName = NcgConfig.config['nms']['auth_client_dir'] + '/jwks_'+auth_profile['name'].replace(' ','_')+".conf"
                            authProfileConfigFile = {'contents': b64renderedClientAuthProfile,
                                              'name': configFileName }

                            all_auth_client_profiles.append(auth_profile['name'])
                            auxFiles['files'].append(authProfileConfigFile)

                        case 'mtls':
                            # Add the rendered authentication configuration snippet as a config file in the staged configuration - mTLS template
                            templateName = NcgConfig.config['templates']['auth_client_root'] + "/mtls.tmpl"
                            renderedClientAuthProfile = j2_env.get_template(templateName).render(
                                authprofile=auth_profile, ncgconfig=NcgConfig.config)

                            b64renderedClientAuthProfile = base64.b64encode(
                                bytes(renderedClientAuthProfile, 'utf-8')).decode('utf-8')
                            configFileName = NcgConfig.config['nms']['auth_client_dir'] + '/' + auth_profile[
                                'name'].replace(' ', '_') + ".conf"
                            authProfileConfigFile = {'contents': b64renderedClientAuthProfile,
                                                     'name': configFileName}

                            all_auth_client_profiles.append(auth_profile['name'])
                            auxFiles['files'].append(authProfileConfigFile)

            if 'server' in d_auth_profiles:
                # Render all server authentication profiles

                auth_server_profiles = d_auth_profiles['server']
                for i in range(len(auth_server_profiles)):
                    auth_profile = auth_server_profiles[i]

                    match auth_profile['type']:
                        case 'token':
                            # Add the rendered authentication configuration snippet as a config file in the staged configuration - token template
                            templateName = NcgConfig.config['templates']['auth_server_root']+"/token.tmpl"
                            renderedServerAuthProfile = j2_env.get_template(templateName).render(
                                authprofile=auth_profile, ncgconfig=NcgConfig.config)

                            b64renderedServerAuthProfile = base64.b64encode(bytes(renderedServerAuthProfile, 'utf-8')).decode('utf-8')
                            configFileName = NcgConfig.config['nms']['auth_server_dir'] + '/'+auth_profile['name'].replace(' ','_')+".conf"
                            authProfileConfigFile = {'contents': b64renderedServerAuthProfile,
                                              'name': configFileName }

                            all_auth_server_profiles.append(auth_profile['name'])
                            auxFiles['files'].append(authProfileConfigFile)

                        case 'mtls':
                            # Add the rendered authentication configuration snippet as a config file in the staged configuration - mTLS template
                            templateName = NcgConfig.config['templates']['auth_server_root'] + "/mtls.tmpl"
                            renderedServerAuthProfile = j2_env.get_template(templateName).render(
                                authprofile=auth_profile, ncgconfig=NcgConfig.config)

                            b64renderedServerAuthProfile = base64.b64encode(
                                bytes(renderedServerAuthProfile, 'utf-8')).decode('utf-8')
                            configFileName = NcgConfig.config['nms']['auth_server_dir'] + '/' + auth_profile[
                                'name'].replace(' ', '_') + ".conf"
                            authProfileConfigFile = {'contents': b64renderedServerAuthProfile,
                                                     'name': configFileName}

                            all_auth_server_profiles.append(auth_profile['name'])
                            auxFiles['files'].append(authProfileConfigFile)


        # Check authorization profiles validity and creates authorization config files

        # List of all authorization client profile names
        all_authz_client_profiles = []

        d_authz_profiles = v4_2.MiscUtils.getDictKey(d, 'declaration.http.authorization')
        if d_authz_profiles is not None:
            # Render all client authorization profiles

            for i in range(len(d_authz_profiles)):
                authz_profile = d_authz_profiles[i]

                match authz_profile['type']:
                    case 'jwt':
                        # Add the rendered authorization configuration snippet as a config file in the staged configuration - jwt authZ maps template
                        templateName = NcgConfig.config['templates']['authz_client_root']+"/jwt-authz-map.tmpl"
                        renderedClientAuthZProfile = j2_env.get_template(templateName).render(
                            authprofile=authz_profile, ncgconfig=NcgConfig.config)

                        b64renderedClientAuthProfile = base64.b64encode(bytes(renderedClientAuthZProfile, 'utf-8')).decode('utf-8')
                        configFileName = NcgConfig.config['nms']['authz_client_dir'] + '/'+authz_profile['name'].replace(' ','_')+".maps.conf"
                        authProfileConfigFile = {'contents': b64renderedClientAuthProfile,
                                          'name': configFileName }

                        all_authz_client_profiles.append(authz_profile['name'])
                        auxFiles['files'].append(authProfileConfigFile)

                        # Add the rendered authorization configuration snippet as a config file in the staged configuration - jwt template
                        templateName = NcgConfig.config['templates']['authz_client_root'] + "/jwt.tmpl"
                        renderedClientAuthZProfile = j2_env.get_template(templateName).render(
                            authprofile=authz_profile, ncgconfig=NcgConfig.config)

                        b64renderedClientAuthProfile = base64.b64encode(bytes(renderedClientAuthZProfile, 'utf-8')).decode(
                            'utf-8')
                        configFileName = NcgConfig.config['nms']['authz_client_dir'] + '/' + authz_profile['name'].replace(' ',
                                                                                                                           '_') + ".conf"
                        authProfileConfigFile = {'contents': b64renderedClientAuthProfile,
                                                 'name': configFileName}

                        all_authz_client_profiles.append(authz_profile['name'])
                        auxFiles['files'].append(authProfileConfigFile)

        # NGINX Javascript profiles
        all_njs_profiles = []
        d_njs_files = v4_2.MiscUtils.getDictKey(d, 'declaration.http.njs_profiles')
        if d_njs_files is not None:
            for i in range(len(d_njs_files)):
                njs_file = d_njs_files[i]
                njs_filename = njs_file['name'].replace(' ','_')

                status, content = v4_2.GitOps.getObjectFromRepo(object=njs_file['file'],
                                                                authProfiles=d['declaration']['http'][
                                                                    'authentication'])

                if status != 200:
                    return {"status_code": 422, "message": {"status_code": status, "message": content}}

                njsAuxFile = {'contents': content['content'],
                              'name': NcgConfig.config['nms']['njs_dir'] + '/' + njs_filename + '.js'}
                auxFiles['files'].append(njsAuxFile)
                all_njs_profiles.append(njs_filename)

        # HTTP level Javascript hooks
        d_http_njs_hooks = v4_2.MiscUtils.getDictKey(d, 'declaration.http.njs')
        if d_http_njs_hooks is not None:
            for i in range(len(d_http_njs_hooks)):
                if d_http_njs_hooks[i]['profile'] not in all_njs_profiles:
                    return {"status_code": 422,
                            "message": {"status_code": status, "message":
                                {"code": status,
                                 "content": f"invalid njs profile [{d_http_njs_hooks[i]['profile']}] in HTTP declaration, must be one of {all_njs_profiles}"}}}

        # Parse HTTP servers
        d_servers = v4_2.MiscUtils.getDictKey(d, 'declaration.http.servers')
        if d_servers is not None:
            for server in d_servers:
                serverSnippet = ''

                # Server level Javascript hooks
                if server['njs']:
                    for i in range(len(server['njs'])):
                        if server['njs'][i]['profile'] not in all_njs_profiles:
                            return {"status_code": 422,
                                    "message": {"status_code": status, "message":
                                        {"code": status,
                                         "content": f"invalid njs profile [{server['njs'][i]['profile']}] in server [{server['name']}], must be one of {all_njs_profiles}"}}}

                # Server client authentication name validity check
                if 'authentication' in server and server['authentication']:
                    serverAuthClientProfiles = server['authentication']['client']

                    for authClientProfile in serverAuthClientProfiles:
                        if authClientProfile['profile'] not in all_auth_client_profiles:
                            return {"status_code": 422,
                                    "message": {"status_code": status, "message":
                                        {"code": status,
                                         "content": f"invalid client authentication profile [{authClientProfile['profile']}] in server [{server['name']}] must be one of {all_auth_client_profiles}"}}}

                # Location client authorization name validity check
                if 'authorization' in server and server['authorization']:
                    if server['authorization']['profile'] and server['authorization']['profile'] not in all_authz_client_profiles:
                        return {"status_code": 422,
                                "message": {"status_code": status, "message":
                                    {"code": status,
                                     "content": f"invalid client authorization profile [{server['authorization']['profile']}] in server [{server['name']}] must be one of {all_authz_client_profiles}"}}}

                if server['snippet']:
                    status, serverSnippet = v4_2.GitOps.getObjectFromRepo(object = server['snippet'], authProfiles = d['declaration']['http']['authentication'], base64Encode = False)

                    if status != 200:
                        return {"status_code": 422, "message": {"status_code": status, "message": serverSnippet}}

                    serverSnippet = serverSnippet['content']

                for loc in server['locations']:

                    # Location level Javascript hooks
                    if loc['njs']:
                        for i in range(len(loc['njs'])):
                            if loc['njs'][i]['profile'] not in all_njs_profiles:
                                return {"status_code": 422,
                                        "message": {"status_code": status, "message":
                                            {"code": status,
                                             "content": f"invalid njs profile [{loc['njs'][i]['profile']}] in location [{loc['uri']}], must be one of {all_njs_profiles}"}}}

                    if loc['snippet']:
                        status, snippet = v4_2.GitOps.getObjectFromRepo(object = loc['snippet'], authProfiles = d['declaration']['http']['authentication'])

                        if status != 200:
                            return {"status_code": 422, "message": {"status_code": status, "message": snippet}}

                        loc['snippet'] = snippet

                    # Location upstream name validity check
                    if 'upstream' in loc and loc['upstream'] and urlparse(loc['upstream']).netloc not in all_upstreams:
                        return {"status_code": 422,
                                "message": {"status_code": status, "message":
                                    {"code": status, "content": f"invalid HTTP upstream [{loc['upstream']}]"}}}

                    # Location client authentication name validity check
                    if 'authentication' in loc and loc['authentication']:
                        locAuthClientProfiles = loc['authentication']['client']

                        for authClientProfile in locAuthClientProfiles:
                            if authClientProfile['profile'] not in all_auth_client_profiles:
                                return {"status_code": 422,
                                        "message": {"status_code": status, "message":
                                            {"code": status, "content": f"invalid client authentication profile [{authClientProfile['profile']}] in location [{loc['uri']}] must be one of {all_auth_client_profiles}"}}}

                    # Location client authorization name validity check
                    if 'authorization' in loc and loc['authorization']:
                        if loc['authorization']['profile'] and loc['authorization']['profile'] not in all_authz_client_profiles:
                            return {"status_code": 422,
                                    "message": {"status_code": status, "message":
                                        {"code": status, "content": f"invalid client authorization profile [{loc['authorization']['profile']}] in location [{loc['uri']}] must be one of {all_authz_client_profiles}"}}}

                    # Location server authentication name validity check
                    if 'authentication' in loc and loc['authentication']:
                        locAuthServerProfiles = loc['authentication']['server']

                        for authServerProfile in locAuthServerProfiles:
                            if authServerProfile['profile'] not in all_auth_server_profiles:
                                return {"status_code": 422,
                                        "message": {"status_code": status, "message":
                                            {"code": status, "content": f"invalid server authentication profile [{authServerProfile['profile']}] in location [{loc['uri']}]"}}}

                    # API Gateway provisioning
                    if loc['apigateway'] and loc['apigateway']['api_gateway'] and loc['apigateway']['api_gateway']['enabled'] and loc['apigateway']['api_gateway']['enabled'] == True:
                        openApiAuthProfile = loc['apigateway']['openapi_schema']['authentication']
                        if openApiAuthProfile and openApiAuthProfile[0]['profile'] not in all_auth_server_profiles:
                            return {"status_code": 422,
                                    "message": {"status_code": status, "message":
                                        {"code": status,
                                         "content": f"invalid server authentication profile [{openApiAuthProfile[0]['profile']}] for OpenAPI schema [{loc['apigateway']['openapi_schema']['content']}]"}}}

                        status, apiGatewayConfigDeclaration = v4_2.APIGateway.createAPIGateway(locationDeclaration = loc, authProfiles = d['declaration']['http']['authentication'])

                        # API Gateway configuration template rendering
                        if apiGatewayConfigDeclaration:
                            apiGatewaySnippet = j2_env.get_template(NcgConfig.config['templates']['apigwconf']).render(
                                declaration=apiGatewayConfigDeclaration, ncgconfig=NcgConfig.config)
                            apiGatewaySnippetb64 = base64.b64encode(bytes(apiGatewaySnippet, 'utf-8')).decode('utf-8')

                            newAuxFile = {'contents': apiGatewaySnippetb64, 'name': NcgConfig.config['nms']['apigw_dir'] +
                                                                            loc['uri'] + ".conf" }
                            auxFiles['files'].append(newAuxFile)

                    # API Gateway Developer portal provisioning
                    if loc['apigateway'] and loc['apigateway']['developer_portal'] and 'enabled' in loc['apigateway']['developer_portal'] and loc['apigateway']['developer_portal']['enabled'] == True:

                        status, devPortalHTML = v4_2.DevPortal.createDevPortal(locationDeclaration = loc, authProfiles = d['declaration']['http']['authentication'])

                        if status != 200:
                            return {"status_code": 412,
                                    "message": {"status_code": status, "message":
                                        {"code": status, "content": f"Developer Portal creation failed for {loc['uri']}"}}}

                        ### Add optional API Developer portal HTML files
                        # devPortalHTML
                        newAuxFile = {'contents': devPortalHTML, 'name': NcgConfig.config['nms']['devportal_dir'] +
                                                                           loc['apigateway']['developer_portal']['uri']}
                        auxFiles['files'].append(newAuxFile)

                        ### / Add optional API Developer portal HTML files

                    if loc['rate_limit'] is not None:
                        if 'profile' in loc['rate_limit'] and loc['rate_limit']['profile'] and loc['rate_limit'][
                            'profile'] not in all_ratelimits:
                            return {"status_code": 422,
                                    "message": {
                                        "status_code": status,
                                        "message":
                                            {"code": status,
                                             "content":
                                                 f"invalid rate_limit profile [{loc['rate_limit']['profile']}]"}}}

            server['snippet']['content'] = base64.b64encode(bytes(serverSnippet, 'utf-8')).decode('utf-8')

    if 'layer4' in d['declaration']:
        # Check Layer4/stream upstreams validity
        all_upstreams = []

        d_upstreams = v4_2.MiscUtils.getDictKey(d, 'declaration.layer4.upstreams')
        if d_upstreams is not None:
            for i in range(len(d_upstreams)):
                all_upstreams.append(d_upstreams[i]['name'])

        d_servers = v4_2.MiscUtils.getDictKey(d, 'declaration.layer4.servers')
        if d_servers is not None:
            for server in d_servers:

                if server['snippet']:
                    status, snippet = v4_2.GitOps.getObjectFromRepo(object = server['snippet'], authProfiles = d['declaration']['http']['authentication'])

                    if status != 200:
                        return {"status_code": 422, "message": {"status_code": status, "message": snippet}}

                    server['snippet'] = snippet

                if 'upstream' in server and server['upstream'] and server['upstream'] not in all_upstreams:
                    return {"status_code": 422,
                            "message": {
                                "status_code": status,
                                "message":
                                    {"code": status, "content": f"invalid Layer4 upstream {server['upstream']}"}}}

    # HTTP configuration template rendering
    httpConf = j2_env.get_template(NcgConfig.config['templates']['httpconf']).render(
        declaration=d['declaration']['http'], ncgconfig=NcgConfig.config) if 'http' in d['declaration'] else ''

    # Stream configuration template rendering
    streamConf = j2_env.get_template(NcgConfig.config['templates']['streamconf']).render(
        declaration=d['declaration']['layer4'], ncgconfig=NcgConfig.config) if 'layer4' in d['declaration'] else ''

    b64HttpConf = str(base64.b64encode(httpConf.encode("utf-8")), "utf-8")
    b64StreamConf = str(base64.b64encode(streamConf.encode("utf-8")), "utf-8")

    if decltype.lower() == "plaintext":
        # Plaintext output
        return httpConf + streamConf

    elif decltype.lower() == "json" or decltype.lower() == 'http':
        # JSON-wrapped b64-encoded output
        payload = {"http_config": f"{b64HttpConf}", "stream_config": f"{b64StreamConf}"}

        if decltype.lower() == "json":
            # JSON output
            return {"status_code": 200, "message": {"status_code": 200, "message": payload}}
        else:
            # HTTP POST output
            try:
                r = requests.post(d['output']['http']['url'], data=json.dumps(payload),
                                  headers={'Content-Type': 'application/json'})
            except:
                headers = {'Content-Type': 'application/json'}
                content = {'message': d['output']['http']['url'] + ' unreachable'}

                return {"status_code": 502, "message": {"status_code": 502, "message": content}, "headers": headers}

            r.headers.pop("Content-Length") if "Content-Length" in r.headers else ''
            r.headers.pop("Server") if "Server" in r.headers else ''
            r.headers.pop("Date") if "Date" in r.headers else ''
            r.headers.pop("Content-Type") if "Content-Type" in r.headers else ''

            r.headers['Content-Type'] = 'application/json'

            return {"status_code": r.status_code, "message": {"code": r.status_code, "content": r.text},
                    "headers": r.headers}

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
        # NGINX Instance Manager Staged Configuration publish

        nmsUsername = v4_2.MiscUtils.getDictKey(d, 'output.nms.username')
        nmsPassword = v4_2.MiscUtils.getDictKey(d, 'output.nms.password')
        nmsInstanceGroup = v4_2.MiscUtils.getDictKey(d, 'output.nms.instancegroup')
        nmsSynctime = v4_2.MiscUtils.getDictKey(d, 'output.nms.synctime')

        nmsUrlFromJson = v4_2.MiscUtils.getDictKey(d, 'output.nms.url')
        urlCheck = urlparse(nmsUrlFromJson)

        if urlCheck.scheme not in ['http', 'https'] or urlCheck.scheme == "" or urlCheck.netloc == "":
            return {"status_code": 400,
                    "message": {"status_code": 400, "message": {"code": 400,
                                                                "content": f"invalid NGINX Management Suite URL {nmsUrlFromJson}"}},
                    "headers": {'Content-Type': 'application/json'}}

        nmsUrl = f"{urlCheck.scheme}://{urlCheck.netloc}"

        if nmsSynctime < 0:
            return {"status_code": 400,
                    "message": {"status_code": 400, "message": {"code": 400, "content": "synctime must be >= 0"}},
                    "headers": {'Content-Type': 'application/json'}}

        # Fetch NGINX App Protect WAF policies from source of truth if needed
        d_policies = v4_2.MiscUtils.getDictKey(d, 'output.nms.policies')
        if d_policies is not None:
            for policy in d_policies:
                if 'versions' in policy:
                    for policyVersion in policy['versions']:
                        status, content = v4_2.GitOps.getObjectFromRepo(object = policyVersion['contents'], authProfiles = d['declaration']['http']['authentication'])

                        if status != 200:
                            return {"status_code": 422, "message": {"status_code": status, "message": content}}

                        policyVersion['contents'] = content

        # Check TLS items validity
        all_tls = {'certificate': {}, 'key': {}}

        d_certs = v4_2.MiscUtils.getDictKey(d, 'output.nms.certificates')
        if d_certs is not None:
            for i in range(len(d_certs)):
                if d_certs[i]['name']:
                    all_tls[d_certs[i]['type']][d_certs[i]['name']] = True

        d_servers = v4_2.MiscUtils.getDictKey(d, 'declaration.http.servers')
        if d_servers is not None:
            for server in d_servers:
                if server['listen'] is not None:
                    if 'tls' in server['listen']:
                        cert_name = v4_2.MiscUtils.getDictKey(server, 'listen.tls.certificate')
                        if cert_name and cert_name not in all_tls['certificate']:
                            return {"status_code": 422,
                                    "message": {
                                        "status_code": 422,
                                        "message": {"code": 422,
                                                    "content": "invalid TLS certificate " +
                                                               cert_name + " for server" + str(
                                                        server['names'])}
                                    }}

                        cert_key = v4_2.MiscUtils.getDictKey(server, 'listen.tls.key')
                        if cert_key and cert_key not in all_tls['key']:
                            return {"status_code": 422,
                                    "message": {
                                        "status_code": 422,
                                        "message": {"code": 422,
                                                    "content": "invalid TLS key " + cert_key + " for server" + str(
                                                        server['names'])}
                                    }}

                        trusted_cert_name = v4_2.MiscUtils.getDictKey(server, 'listen.tls.trusted_ca_certificates')
                        if trusted_cert_name and trusted_cert_name not in all_tls['certificate']:
                            return {"status_code": 422,
                                    "message": {
                                        "status_code": 422,
                                        "message": {"code": 422,
                                                    "content": "invalid trusted CA certificate " +
                                                               trusted_cert_name + " for server" + str(server['names'])}
                                    }}

                        if v4_2.MiscUtils.getDictKey(server, 'listen.tls.mtls.enabled') in ['optional_no_ca'] \
                                and 'ocsp' in server['listen']['tls']:
                            return {"status_code": 422,
                                    "message": {
                                        "status_code": 422,
                                        "message": {"code": 422,
                                                    "content": "OCSP is incompatible with 'optional_no_ca' client "
                                                               "mTLS verification for server" + str(
                                                        server['names'])}
                                    }}

                        client_cert_name = v4_2.MiscUtils.getDictKey(server, 'listen.tls.mtls.client_certificates')
                        if client_cert_name and client_cert_name not in all_tls['certificate']:
                            return {"status_code": 422,
                                    "message": {
                                        "status_code": 422,
                                        "message": {"code": 422,
                                                    "content": f"invalid mTLS client certificates [{client_cert_name}] for server {str(server['names'])}"}
                                    }}

        # Add optional certificates specified under output.nms.certificates
        extensions_map = {'certificate': '.crt', 'key': '.key'}

        d_certificates = v4_2.MiscUtils.getDictKey(d, 'output.nms.certificates')
        if d_certificates is not None:
            for c in d_certificates:
                status, certContent = v4_2.GitOps.getObjectFromRepo(object = c['contents'], authProfiles = d['declaration']['http']['authentication'])

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
            nginxconf={'modules': v4_2.MiscUtils.getDictKey(d, 'output.nms.modules')})

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

        # Append config files to staged configuration
        configFiles['files'].append(filesNginxMain)
        configFiles['files'].append(filesHttpConf)
        configFiles['files'].append(filesStreamConf)

        # Staged config
        baseStagedConfig = {'auxFiles': auxFiles, 'configFiles': configFiles}
        stagedConfig = {'auxFiles': auxFiles, 'configFiles': configFiles,
                        'updateTime': datetime.utcnow().isoformat()[:-3] + 'Z',
                        'ignoreConflict': True, 'validateConfig': False}

        currentBaseStagedConfig = NcgRedis.redis.get(f'ncg.basestagedconfig.{configUid}').decode('utf-8') if NcgRedis.redis.get(f'ncg.basestagedconfig.{configUid}') else None
        newBaseStagedConfig = json.dumps(baseStagedConfig)

        if currentBaseStagedConfig is not None and newBaseStagedConfig == currentBaseStagedConfig:
            print(f'Declaration [{configUid}] not changed')
            return {"status_code": 200,
                    "message": {"status_code": 200, "message": {"code": 200, "content": "no changes"}}}
        else:
            # Configuration objects have changed, publish to NIM needed
            print(f'Declaration [{configUid}] changed, publishing to NIM' if configUid else f'New declaration created, publishing to NIM')

            # Retrieve instance group uid
            try:
                ig = requests.get(url=f'{nmsUrl}/api/platform/v1/instance-groups', auth=(nmsUsername, nmsPassword),
                                  verify=False)
            except Exception as e:
                return {"status_code": 400,
                        "message": {"status_code": 400,
                                    "message": {"code": 400, "content": f"Can't connect to {nmsUrl}"}}}

            if ig.status_code != 200:
                try:
                    return {"status_code": ig.status_code,
                            "message": {"status_code": ig.status_code,
                                        "message": {"code": ig.status_code, "content": json.loads(ig.text)}}}
                except:
                    return {"status_code": ig.status_code,
                            "message": {"status_code": ig.status_code,
                                        "message": {"code": ig.status_code, "content": ig.text}}}

            # Get the instance group id
            igUid = v4_2.NIMUtils.getNIMInstanceGroupUid(nmsUrl=nmsUrl, nmsUsername=nmsUsername,
                                                            nmsPassword=nmsPassword, instanceGroupName=nmsInstanceGroup)

            # Invalid instance group
            if igUid is None:
                return {"status_code": 404,
                        "message": {"status_code": 404, "message": {"code": 404,
                                                                    "content": f"instance group {nmsInstanceGroup} not found"}},
                        "headers": {'Content-Type': 'application/json'}}

            ### NGINX App Protect policies support - commits policies to control plane

            # Check NGINX App Protect WAF policies configuration sanity
            status, description = v4_2.NAPUtils.checkDeclarationPolicies(d)

            if status != 200:
                return {"status_code": 422, "message": {"status_code": status, "message": {"code": status,"content": description}},
                        "headers": {'Content-Type': 'application/json'}}

            # Provision NGINX App Protect WAF policies to NGINX Instance Manager
            provisionedNapPolicies, activePolicyUids = v4_2.NAPUtils.provisionPolicies(
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
                doWeHavePolicies = v4_2.NAPUtils.makePolicyActive(nmsUrl=nmsUrl, nmsUsername=nmsUsername,
                                                                     nmsPassword=nmsPassword,
                                                                     activePolicyUids=activePolicyUids,
                                                                     instanceGroupUid=igUid)

                if doWeHavePolicies:
                    # Clean up NGINX App Protect WAF policies not used anymore
                    # and not defined in the declaration just pushed
                    time.sleep(NcgConfig.config['nms']['staged_config_publish_waittime'])
                    v4_2.NAPUtils.cleanPolicyLeftovers(nmsUrl=nmsUrl, nmsUsername=nmsUsername,
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
    declarationToPatch = declaration.model_dump()

    # The currently applied declaration
    status_code, currentDeclaration = get_declaration(configUid=configUid)

    # Handle policy updates
    d_policies = v4_2.MiscUtils.getDictKey(declarationToPatch, 'output.nms.policies')
    if d_policies is not None:
        # NGINX App Protect WAF policy updates
        for p in d_policies:
            currentDeclaration = v4_2.DeclarationPatcher.patchNAPPolicies(
                sourceDeclaration=currentDeclaration, patchedNAPPolicies=p)

    # Handle certificate updates
    d_certificates = v4_2.MiscUtils.getDictKey(declarationToPatch, 'output.nms.certificates')
    if d_certificates is not None:
        # TLS certificate/key updates
        for p in d_certificates:
            currentDeclaration = v4_2.DeclarationPatcher.patchCertificates(
                sourceDeclaration=currentDeclaration, patchedCertificates=p)

    # Handle declaration updates
    if 'declaration' in declarationToPatch:
        # HTTP
        d_upstreams = v4_2.MiscUtils.getDictKey(declarationToPatch, 'declaration.http.upstreams')
        if d_upstreams:
            # HTTP upstream patch
            for u in d_upstreams:
                currentDeclaration = v4_2.DeclarationPatcher.patchHttpUpstream(
                    sourceDeclaration=currentDeclaration, patchedHttpUpstream=u)

        d_servers = v4_2.MiscUtils.getDictKey(declarationToPatch, 'declaration.http.servers')
        if d_servers:
            # HTTP servers patch
            for s in d_servers:
                currentDeclaration = v4_2.DeclarationPatcher.patchHttpServer(
                    sourceDeclaration=currentDeclaration, patchedHttpServer=s)

        # Stream / Layer4
        d_upstreams = v4_2.MiscUtils.getDictKey(declarationToPatch, 'declaration.layer4.upstreams')
        if d_upstreams:
            # Stream upstream patch
            for u in d_upstreams:
                currentDeclaration = v4_2.DeclarationPatcher.patchStreamUpstream(
                    sourceDeclaration=currentDeclaration, patchedStreamUpstream=u)

        d_servers = v4_2.MiscUtils.getDictKey(declarationToPatch, 'declaration.layer4.servers')
        if d_servers:
            # Stream servers patch
            for s in d_servers:
                currentDeclaration = v4_2.DeclarationPatcher.patchStreamServer(
                    sourceDeclaration=currentDeclaration, patchedStreamServer=s)

    # Apply the updated declaration
    configDeclaration = ConfigDeclaration.model_validate_json(json.dumps(currentDeclaration))

    r = createconfig(declaration=configDeclaration, apiversion=apiversion,
                     runfromautosync=True, configUid=configUid)

    # Return the updated declaration
    message = r['message']

    if r['status_code'] != 200:
        currentDeclaration = {}
        # message = f'declaration {configUid} update failed';

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