"""
Configuration creation based on jinja2 templates
"""

import base64
import json
import pickle
from urllib.parse import urlparse

import requests
import schedule
from fastapi.responses import Response, JSONResponse
from jinja2 import Environment, FileSystemLoader
from pydantic import ValidationError
from requests.packages.urllib3.exceptions import InsecureRequestWarning

import v5_3.APIGateway
import v5_3.DevPortal
import v5_3.DeclarationPatcher
import v5_3.GitOps
import v5_3.MiscUtils
import v5_3.NIMOutput
import v5_3.NGINXOneOutput

# NGINX App Protect helper functions
import v5_3.NAPUtils
import v5_3.NIMUtils

# NGINX Declarative API modules
from NcgConfig import NcgConfig
from NcgRedis import NcgRedis

# pydantic models
from V5_3_NginxConfigDeclaration import *

# Tolerates self-signed TLS certificates
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


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
    configFiles = {'files': []}

    # NGINX auxiliary files for staged config
    auxFiles = {'files': []}

    # Extra manifests to be returned to the caller
    extraOutputManifests = []

    try:
        # Pydantic JSON validation
        ConfigDeclaration(**declaration.model_dump())
    except ValidationError as e:
        print(f'Invalid declaration {e}')

    d = declaration.model_dump()
    decltype = d['output']['type']

    j2_env = Environment(loader=FileSystemLoader(NcgConfig.config['templates']['root_dir'] + '/' + apiversion),
                         trim_blocks=True, extensions=["jinja2_base64_filters.Base64Filters"])
    j2_env.filters['regex_replace'] = v5_3.MiscUtils.regex_replace

    # Check resolver profiles validity and creates resolver config files
    if 'resolvers' in d['declaration']:
        all_resolver_profiles = []

        d_resolver_profiles = v5_3.MiscUtils.getDictKey(d, 'declaration.resolvers')
        if d_resolver_profiles is not None:
            # Render all resolver profiles
            for i in range(len(d_resolver_profiles)):
                resolver_profile = d_resolver_profiles[i]

                # Add the rendered resolver configuration snippet as a config file in the staged configuration
                templateName = NcgConfig.config['templates']['resolver']
                renderedResolverProfile = j2_env.get_template(templateName).render(
                    resolverprofile=resolver_profile, ncgconfig=NcgConfig.config)

                b64renderedResolverProfile = base64.b64encode(bytes(renderedResolverProfile, 'utf-8')).decode(
                    'utf-8')
                configFileName = NcgConfig.config['nms']['resolver_dir'] + '/' + resolver_profile['name'].replace(' ',
                                                                                                                  '_') + ".conf"
                resolverProfileConfigFile = {'contents': b64renderedResolverProfile,
                                             'name': configFileName}

                all_resolver_profiles.append(resolver_profile['name'])
                auxFiles['files'].append(resolverProfileConfigFile)

    if 'http' in d['declaration']:
        if 'snippet' in d['declaration']['http']:
            status, snippet = v5_3.GitOps.getObjectFromRepo(object = d['declaration']['http']['snippet'], authProfiles = d['declaration']['http']['authentication'])

            if status != 200:
                return {"status_code": 422, "message": {"status_code": status, "message": snippet}}

            d['declaration']['http']['snippet'] = snippet

        # Check HTTP upstreams validity
        all_upstreams = []
        http = d['declaration']['http']

        if 'upstreams' in http:
            for i in range(len(http['upstreams'])):
                upstream = http['upstreams'][i]

                if upstream['resolver'] and upstream['resolver']  not in all_resolver_profiles:
                    return {"status_code": 422,
                            "message": {"status_code": status, "message":
                                {"code": status,
                                 "content": f"invalid resolver profile [{upstream['resolver']}] in HTTP upstream [{upstream['name']}], must be one of {all_resolver_profiles}"}}}

                if upstream['snippet']:
                    status, snippet = v5_3.GitOps.getObjectFromRepo(object = upstream['snippet'], authProfiles = d['declaration']['http']['authentication'])

                    if status != 200:
                        return {"status_code": 422, "message": {"status_code": status, "message": snippet}}

                    d['declaration']['http']['upstreams'][i]['snippet'] = snippet

                # Add the rendered upstream configuration snippet as a config file in the staged configuration
                templateName = NcgConfig.config['templates']['upstream_http']
                renderedUpstreamProfile = j2_env.get_template(templateName).render(
                    u=upstream, ncgconfig=NcgConfig.config)

                b64renderedUpstreamProfile = base64.b64encode(bytes(renderedUpstreamProfile, 'utf-8')).decode(
                    'utf-8')
                configFileName = NcgConfig.config['nms']['upstream_http_dir'] + '/' + upstream['name'].replace(' ', '_') + ".conf"
                upstreamProfileConfigFile = {'contents': b64renderedUpstreamProfile,
                                         'name': configFileName}

                auxFiles['files'].append(upstreamProfileConfigFile)
                all_upstreams.append(http['upstreams'][i]['name'])

        http = d['declaration']['http']

        # Check HTTP rate_limit profiles validity
        all_ratelimits = []

        d_rate_limit = v5_3.MiscUtils.getDictKey(d, 'declaration.http.rate_limit')
        if d_rate_limit is not None:
            for i in range(len(d_rate_limit)):
                all_ratelimits.append(d_rate_limit[i]['name'])

        # Check HTTP cache profiles validity
        all_cache_profiles = []

        d_cache_profiles = v5_3.MiscUtils.getDictKey(d, 'declaration.http.cache')
        if d_cache_profiles is not None:
            for i in range(len(d_cache_profiles)):
                all_cache_profiles.append(d_cache_profiles[i]['name'])

        # Check authentication profiles validity and creates authentication config files

        # List of all auth client & server profile names
        all_auth_client_profiles = []
        all_auth_server_profiles = []

        d_auth_profiles = v5_3.MiscUtils.getDictKey(d, 'declaration.http.authentication')
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

        d_authz_profiles = v5_3.MiscUtils.getDictKey(d, 'declaration.http.authorization')
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
        d_njs_files = v5_3.MiscUtils.getDictKey(d, 'declaration.http.njs_profiles')
        if d_njs_files is not None:
            for i in range(len(d_njs_files)):
                njs_file = d_njs_files[i]
                njs_filename = njs_file['name'].replace(' ','_')

                status, content = v5_3.GitOps.getObjectFromRepo(object=njs_file['file'],
                                                                authProfiles=d['declaration']['http'][
                                                                    'authentication'])

                if status != 200:
                    return {"status_code": 422, "message": {"status_code": status, "message": content}}

                njsAuxFile = {'contents': content['content'],
                              'name': NcgConfig.config['nms']['njs_dir'] + '/' + njs_filename + '.js'}
                auxFiles['files'].append(njsAuxFile)
                all_njs_profiles.append(njs_filename)

        # HTTP level Javascript hooks
        d_http_njs_hooks = v5_3.MiscUtils.getDictKey(d, 'declaration.http.njs')
        if d_http_njs_hooks is not None:
            for i in range(len(d_http_njs_hooks)):
                if d_http_njs_hooks[i]['profile'] not in all_njs_profiles:
                    return {"status_code": 422,
                            "message": {"status_code": status, "message":
                                {"code": status,
                                 "content": f"invalid njs profile [{d_http_njs_hooks[i]['profile']}] in HTTP declaration, must be one of {all_njs_profiles}"}}}

        # Parse HTTP servers
        d_servers = v5_3.MiscUtils.getDictKey(d, 'declaration.http.servers')
        if d_servers is not None:
            for server in d_servers:
                serverSnippet = ''

                # Server level resolver name validity check
                if server['resolver']:
                    if server['resolver'] not in all_resolver_profiles:
                        return {"status_code": 422,
                                    "message": {"status_code": status, "message":
                                        {"code": status,
                                         "content": f"invalid resolver profile [{server['resolver']}] in HTTP server [{server['name']}], must be one of {all_resolver_profiles}"}}}

                # Server level cache profile name validity
                if server['cache']:
                    if server['cache']['profile'] not in all_cache_profiles and server['cache']['profile'] != "":
                        return {"status_code": 422,
                                    "message": {"status_code": status, "message":
                                        {"code": status,
                                         "content": f"invalid cache profile [{server['cache']['profile']}] in HTTP server [{server['name']}], must be one of {all_cache_profiles}"}}}

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

                # Server client authorization name validity check
                if 'authorization' in server and server['authorization']:
                    if server['authorization']['profile'] and server['authorization']['profile'] not in all_authz_client_profiles:
                        return {"status_code": 422,
                                "message": {"status_code": status, "message":
                                    {"code": status,
                                     "content": f"invalid client authorization profile [{server['authorization']['profile']}] in server [{server['name']}] must be one of {all_authz_client_profiles}"}}}

                # mTLS client authentication name validity check
                if 'authentication' in server['listen']['tls']:
                    if 'client' in server['listen']['tls']['authentication']:
                        tlsAuthProfiles = server['listen']['tls']['authentication']['client']
                        for mtlsClientProfile in tlsAuthProfiles:
                            if mtlsClientProfile['profile'] not in all_auth_client_profiles:
                                return {"status_code": 422,
                                        "message": {"status_code": status, "message":
                                            {"code": status,
                                             "content": f"invalid client authentication profile [{mtlsClientProfile['profile']}] in server [{server['name']}] must be one of {all_auth_client_profiles}"}}}

                if server['snippet']:
                    status, serverSnippet = v5_3.GitOps.getObjectFromRepo(object = server['snippet'], authProfiles = d['declaration']['http']['authentication'], base64Encode = False)

                    if status != 200:
                        return {"status_code": 422, "message": {"status_code": status, "message": serverSnippet}}

                    serverSnippet = serverSnippet['content']

                # Create HTTP server configuration file
                httpServerConf = j2_env.get_template(NcgConfig.config['templates']['server_http']).render(declaration=d['declaration']['http'], s=server, ncgconfig=NcgConfig.config)
                httpServerConfb64 = base64.b64encode(bytes(httpServerConf, 'utf-8')).decode('utf-8')
                newHttpServerAuxFile = {'contents': httpServerConfb64, 'name': NcgConfig.config['nms']['server_http_dir'] +
                                                                        '/' + server['name'].replace(' ', '_') + ".conf"}
                auxFiles['files'].append(newHttpServerAuxFile)

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
                        status, snippet = v5_3.GitOps.getObjectFromRepo(object = loc['snippet'], authProfiles = d['declaration']['http']['authentication'])

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

                    # API Gateway visualization integrations
                    apiGwVisibilityIntegrations = {}

                    if loc['apigateway'] and loc['apigateway']['visibility']:
                        visibility_integrations = loc['apigateway']['visibility']
                        for i in range(len(visibility_integrations)):
                            vis = visibility_integrations[i]

                            if vis['enabled'] == True:
                                apiGwVisibilityIntegrations[ vis['type'] ] = True

                                if vis['type'].lower() == 'moesif':
                                    # Moesif integration

                                    # Add the rendered Moesif visibility configuration snippet as a config file in the staged configuration - HTTP context
                                    templateName = NcgConfig.config['templates'][
                                                       'visibility_root'] + "/moesif/http.tmpl"
                                    renderedMoesifHTTP = j2_env.get_template(templateName).render(
                                        vis=vis, loc=loc, ncgconfig=NcgConfig.config)

                                    b64renderedMoesifHTTP = base64.b64encode(
                                        bytes(renderedMoesifHTTP, 'utf-8')).decode(
                                        'utf-8')
                                    moesifHTTPConfigFile = {'contents': b64renderedMoesifHTTP,
                                                            'name': NcgConfig.config['nms'][
                                                                        'visibility_dir'] +
                                                                    loc['uri'] + "-moesif-http.conf"}

                                    auxFiles['files'].append(moesifHTTPConfigFile)

                                    # Add the rendered Moesif visibility configuration snippet as a config file in the staged configuration - server context
                                    templateName = NcgConfig.config['templates'][
                                                       'visibility_root'] + "/moesif/server.tmpl"
                                    renderedMoesifServer = j2_env.get_template(templateName).render(
                                        vis=vis, loc=loc, ncgconfig=NcgConfig.config)

                                    b64renderedMoesifServer = base64.b64encode(
                                        bytes(renderedMoesifServer, 'utf-8')).decode(
                                        'utf-8')
                                    moesifServerConfigFile = {'contents': b64renderedMoesifServer,
                                                              'name': NcgConfig.config['nms'][
                                                                          'visibility_dir'] +
                                                                      loc['uri'] + "-moesif-server.conf"}

                                    auxFiles['files'].append(moesifServerConfigFile)

                    # API Gateway provisioning
                    if loc['apigateway'] and loc['apigateway']['api_gateway'] and loc['apigateway']['api_gateway']['enabled'] and loc['apigateway']['api_gateway']['enabled'] == True:
                        openApiAuthProfile = loc['apigateway']['openapi_schema']['authentication']
                        if openApiAuthProfile and openApiAuthProfile[0]['profile'] not in all_auth_server_profiles:
                            return {"status_code": 422,
                                    "message": {"status_code": status, "message":
                                        {"code": status,
                                         "content": f"invalid server authentication profile [{openApiAuthProfile[0]['profile']}] for OpenAPI schema [{loc['apigateway']['openapi_schema']['content']}]"}}}

                        status, apiGatewayConfigDeclaration, openAPISchemaJSON = v5_3.APIGateway.createAPIGateway(locationDeclaration = loc, authProfiles = loc['apigateway']['openapi_schema']['authentication'])

                        # API Gateway configuration template rendering
                        if apiGatewayConfigDeclaration:
                            apiGatewaySnippet = j2_env.get_template(NcgConfig.config['templates']['apigwconf']).render(
                                declaration=apiGatewayConfigDeclaration, enabledVisibility=apiGwVisibilityIntegrations, ncgconfig=NcgConfig.config)
                            apiGatewaySnippetb64 = base64.b64encode(bytes(apiGatewaySnippet, 'utf-8')).decode('utf-8')

                            newAuxFile = {'contents': apiGatewaySnippetb64, 'name': NcgConfig.config['nms']['apigw_dir'] +
                                                                            '/' + server['names'][0] +
                                                                            loc['uri'] + ".conf" }
                            auxFiles['files'].append(newAuxFile)

                    # API Gateway Developer portal provisioning
                    if loc['apigateway'] and loc['apigateway']['developer_portal'] and 'enabled' in loc['apigateway']['developer_portal'] and loc['apigateway']['developer_portal']['enabled'] == True:

                        if loc['apigateway']['developer_portal']['type'].lower() == 'redocly':
                            ### Redocly developer portal - Add optional API Developer portal HTML files
                            status, devPortalHTML = v5_3.DevPortal.createDevPortal(locationDeclaration=loc,
                                                                                   authProfiles=
                                                                                   d['declaration']['http'][
                                                                                       'authentication'])

                            if status != 200:
                                return {"status_code": 412,
                                        "message": {"status_code": status, "message":
                                            {"code": status,
                                             "content": f"Developer Portal creation failed for {loc['uri']}"}}}

                            newAuxFile = {'contents': devPortalHTML, 'name': NcgConfig.config['nms']['devportal_dir'] +
                                                                               loc['apigateway']['developer_portal']['redocly']['uri']}
                            auxFiles['files'].append(newAuxFile)

                            ### / Redocly developer portal - Add optional API Developer portal HTML files
                        elif loc['apigateway']['developer_portal']['type'].lower() == 'backstage':
                            ### Backstage developer portal - Create Kubernetes Backstage manifest
                            backstageManifest = j2_env.get_template(f"{NcgConfig.config['templates']['devportal_root']}/backstage.tmpl").render(
                                declaration=loc['apigateway']['developer_portal']['backstage'], openAPISchema = v5_3.MiscUtils.json_to_yaml(openAPISchemaJSON), ncgconfig=NcgConfig.config)

                            extraOutputManifests.append(backstageManifest)
                            ### / Backstage developer portal - Create Kubernetes Backstage manifest

                    # Check location-level rate limit profile name validity
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

                    # Check location-level cache profile name validity
                    if loc['cache'] is not None:
                        if 'profile' in loc['cache'] and loc['cache']['profile'] and loc['cache'][
                                    'profile'] not in all_cache_profiles and loc['cache'][
                                    'profile'] != "":
                            return {"status_code": 422,
                                    "message": {
                                        "status_code": status,
                                        "message":
                                            {"code": status,
                                             "content":
                                                 f"invalid cache profile [{loc['cache']['profile']}]"}}}

            server['snippet']['content'] = base64.b64encode(bytes(serverSnippet, 'utf-8')).decode('utf-8')

    if 'layer4' in d['declaration']:
        # Check Layer4/stream upstreams validity
        all_upstreams = []

        d_upstreams = v5_3.MiscUtils.getDictKey(d, 'declaration.layer4.upstreams')
        if d_upstreams is not None:
            for i in range(len(d_upstreams)):
                upstream = d_upstreams[i]

                if upstream['resolver'] and upstream['resolver']  not in all_resolver_profiles:
                    return {"status_code": 422,
                            "message": {"status_code": status, "message":
                                {"code": status,
                                 "content": f"invalid resolver profile [{upstream['resolver']}] in stream upstream [{upstream['name']}], must be one of {all_resolver_profiles}"}}}

                if upstream['snippet']:
                    status, snippet = v5_3.GitOps.getObjectFromRepo(object = upstream['snippet'], authProfiles = d['declaration']['http']['authentication'])

                    if status != 200:
                        return {"status_code": 422, "message": {"status_code": status, "message": snippet}}

                    d['declaration']['layer4']['upstreams'][i]['snippet'] = snippet

                # Add the rendered upstream configuration snippet as a config file in the staged configuration
                templateName = NcgConfig.config['templates']['upstream_stream']
                renderedUpstreamProfile = j2_env.get_template(templateName).render(
                    u=upstream, ncgconfig=NcgConfig.config)

                b64renderedUpstreamProfile = base64.b64encode(bytes(renderedUpstreamProfile, 'utf-8')).decode(
                    'utf-8')
                configFileName = NcgConfig.config['nms']['upstream_stream_dir'] + '/' + upstream['name'].replace(' ', '_') + ".conf"
                upstreamProfileConfigFile = {'contents': b64renderedUpstreamProfile,
                                         'name': configFileName}

                auxFiles['files'].append(upstreamProfileConfigFile)

                all_upstreams.append(d_upstreams[i]['name'])

        d_servers = v5_3.MiscUtils.getDictKey(d, 'declaration.layer4.servers')
        if d_servers is not None:
            for server in d_servers:

                # Server level resolver name validity check
                if server['resolver']:
                    if server['resolver'] not in all_resolver_profiles:
                        return {"status_code": 422,
                                    "message": {"status_code": status, "message":
                                        {"code": status,
                                         "content": f"invalid resolver profile [{server['resolver'] }] in stream server [{server['name']}], must be one of {all_resolver_profiles}"}}}

                if server['snippet']:
                    status, snippet = v5_3.GitOps.getObjectFromRepo(object = server['snippet'], authProfiles = d['declaration']['http']['authentication'])

                    if status != 200:
                        return {"status_code": 422, "message": {"status_code": status, "message": snippet}}

                    server['snippet'] = snippet

                if 'upstream' in server and server['upstream'] and server['upstream'] not in all_upstreams:
                    return {"status_code": 422,
                            "message": {
                                "status_code": status,
                                "message":
                                    {"code": status, "content": f"invalid Layer4 upstream {server['upstream']}"}}}

                # Create Stream server configuration file
                streamServerConf = j2_env.get_template(NcgConfig.config['templates']['server_stream']).render(s=server, ncgconfig=NcgConfig.config)
                streamServerConfb64 = base64.b64encode(bytes(streamServerConf, 'utf-8')).decode('utf-8')
                newStreamServerAuxFile = {'contents': streamServerConfb64, 'name': NcgConfig.config['nms']['server_stream_dir'] +
                                                                        '/' + server['name'].replace(' ', '_') + ".conf"}
                auxFiles['files'].append(newStreamServerAuxFile)

    # HTTP configuration template rendering
    httpConf = j2_env.get_template(NcgConfig.config['templates']['httpconf']).render(
        declaration=d['declaration']['http'], ncgconfig=NcgConfig.config) if 'http' in d['declaration'] else ''

    # Stream configuration template rendering
    streamConf = j2_env.get_template(NcgConfig.config['templates']['streamconf']).render(
        declaration=d['declaration']['layer4'], ncgconfig=NcgConfig.config) if 'layer4' in d['declaration'] else ''

    b64HttpConf = str(base64.b64encode(httpConf.encode("utf-8")), "utf-8")
    b64StreamConf = str(base64.b64encode(streamConf.encode("utf-8")), "utf-8")

    if decltype.lower() == 'nms':
        # Output to NGINX Instance Manager

        # NGINX configuration files for staged config
        configFiles['rootDir'] = NcgConfig.config['nms']['config_dir']

        # NGINX auxiliary files for staged config
        auxFiles['rootDir'] = NcgConfig.config['nms']['config_dir']

        finalReply = v5_3.NIMOutput.NIMOutput(d = d, declaration = declaration, apiversion = apiversion,
                                 b64HttpConf = b64HttpConf, b64StreamConf = b64StreamConf,
                                 configFiles = configFiles,
                                 auxFiles = auxFiles,
                                 runfromautosync = runfromautosync, configUid = configUid )

        if finalReply['status_code'] == 200:
            if len(extraOutputManifests) > 0:
                finalReply['message']['message']['content']['manifests'] = extraOutputManifests

        return finalReply

    elif decltype.lower() == 'nginxone':
        # Output to NGINX One Console

        # NGINX configuration files for staged config
        configFiles['name'] = NcgConfig.config['nms']['config_dir']

        # NGINX auxiliary files for staged config
        auxFiles['name'] = NcgConfig.config['nms']['config_dir']

        finalReply =  v5_3.NGINXOneOutput.NGINXOneOutput(d = d, declaration = declaration, apiversion = apiversion,
                                 b64HttpConf = b64HttpConf, b64StreamConf = b64StreamConf,
                                 configFiles = configFiles,
                                 auxFiles = auxFiles,
                                 runfromautosync = runfromautosync, configUid = configUid )

        if finalReply['status_code'] == 200:
            if len(extraOutputManifests) > 0:
                finalReply['message']['message']['content']['manifests'] = extraOutputManifests

        return finalReply
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
    d_policies = v5_3.MiscUtils.getDictKey(declarationToPatch, 'output.nms.policies')
    if d_policies is not None:
        # NGINX App Protect WAF policy updates
        for p in d_policies:
            currentDeclaration = v5_3.DeclarationPatcher.patchNAPPolicies(
                sourceDeclaration=currentDeclaration, patchedNAPPolicies=p)

    # Handle certificate updates
    d_certificates = v5_3.MiscUtils.getDictKey(declarationToPatch, 'output.nms.certificates')
    if d_certificates is not None:
        # TLS certificate/key updates
        for p in d_certificates:
            currentDeclaration = v5_3.DeclarationPatcher.patchCertificates(
                sourceDeclaration=currentDeclaration, patchedCertificates=p)

    # Handle declaration updates
    if 'declaration' in declarationToPatch:
        # HTTP
        d_upstreams = v5_3.MiscUtils.getDictKey(declarationToPatch, 'declaration.http.upstreams')
        if d_upstreams:
            # HTTP upstream patch
            for u in d_upstreams:
                currentDeclaration = v5_3.DeclarationPatcher.patchHttpUpstream(
                    sourceDeclaration=currentDeclaration, patchedHttpUpstream=u)

        d_servers = v5_3.MiscUtils.getDictKey(declarationToPatch, 'declaration.http.servers')
        if d_servers:
            # HTTP servers patch
            for s in d_servers:
                currentDeclaration = v5_3.DeclarationPatcher.patchHttpServer(
                    sourceDeclaration=currentDeclaration, patchedHttpServer=s)

        # Stream / Layer4
        d_upstreams = v5_3.MiscUtils.getDictKey(declarationToPatch, 'declaration.layer4.upstreams')
        if d_upstreams:
            # Stream upstream patch
            for u in d_upstreams:
                currentDeclaration = v5_3.DeclarationPatcher.patchStreamUpstream(
                    sourceDeclaration=currentDeclaration, patchedStreamUpstream=u)

        d_servers = v5_3.MiscUtils.getDictKey(declarationToPatch, 'declaration.layer4.servers')
        if d_servers:
            # Stream servers patch
            for s in d_servers:
                currentDeclaration = v5_3.DeclarationPatcher.patchStreamServer(
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