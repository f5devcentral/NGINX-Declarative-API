"""
API Gateway Developer Portal support functions
"""

import json
import requests
import base64

# NGINX Declarative API modules
from NcgConfig import NcgConfig
import v4_1.GitOps
import v4_1.MiscUtils


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
def createDevPortal(locationDeclaration: dict):
    if locationDeclaration['apigateway']['openapi_schema']:
        status, apiSchemaString = v4_1.GitOps.getObjectFromRepo(
            content=locationDeclaration['apigateway']['openapi_schema'], base64Encode=False)

        if v4_1.MiscUtils.yaml_or_json(apiSchemaString) == 'yaml':
            # YAML to JSON conversion
            apiSchemaString = v4_1.MiscUtils.yaml_to_json(apiSchemaString)

        status, devportalJSON = buildDevPortal(openapischema=apiSchemaString)
        if status == 200:
            devportalHTML = base64.b64encode(bytes(devportalJSON['devportal'], 'utf-8')).decode('utf-8')
        else:
            devportalHTML = ""

    return status, devportalHTML