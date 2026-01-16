"""
API Gateway Developer Portal support functions
"""

import json
import requests
import base64

# NGINX Declarative API modules
from NcgConfig import NcgConfig
import v5_4.GitOps
import v5_4.MiscUtils

# pydantic models
from V5_4_NginxConfigDeclaration import *

def buildDevPortal(openapischema):
    try:
        response = requests.post(f"http://{NcgConfig.config['devportal']['host']}:"
                                 f"{NcgConfig.config['devportal']['port']}{NcgConfig.config['devportal']['uri']}",
                                 headers={'Content-Type': 'application/json'}, data=openapischema)
    except Exception as e:
        return 400, ""

    return response.status_code, json.loads(response.text)


# Builds the declarative JSON for the API Gateway configuration
# Return a tuple: status, description. If status = 200 things were successful
def createDevPortal(locationDeclaration: dict, authProfiles: Authentication={}):
    if locationDeclaration['apigateway']['openapi_schema']:
        status, apiSchemaString = v5_4.GitOps.getObjectFromRepo(
            object = locationDeclaration['apigateway']['openapi_schema'], authProfiles = authProfiles['server'] if 'server' in authProfiles else {}, base64Encode = False)

        if v5_4.MiscUtils.yaml_or_json(apiSchemaString['content']) == 'yaml':
            # YAML to JSON conversion
            status, devportalJSON = buildDevPortal(openapischema = v5_4.MiscUtils.yaml_to_json(apiSchemaString['content']))
        else:
            status, devportalJSON = buildDevPortal(openapischema = apiSchemaString['content'])

        if status == 200:
            devportalHTML = base64.b64encode(bytes(devportalJSON['devportal'], 'utf-8')).decode('utf-8')
        else:
            devportalHTML = ""

    return status, devportalHTML