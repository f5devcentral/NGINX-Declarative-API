"""
API Gateway Developer Portal support functions
"""

import json
import base64
import requests
from typing import Tuple, Any, Dict

# NGINX Declarative API modules
from NcgConfig import NcgConfig
import v5_7.GitOps
import v5_7.MiscUtils

# pydantic models
from V5_7_NginxConfigDeclaration import *


def buildDevPortal(openapischema: str) -> Tuple[int, Any]:
    """
    Submits OpenAPI schema to Developer Portal service and returns status and JSON response.

    Args:
        openapischema (str): OpenAPI schema content string.

    Returns:
        Tuple[int, Any]: HTTP status code and response JSON object (or empty string on failure).
    """
    try:
        host = NcgConfig.config['devportal']['host']
        port = NcgConfig.config['devportal']['port']
        uri = NcgConfig.config['devportal']['uri']
        url = f"http://{host}:{port}{uri}"

        response = requests.post(
            url,
            headers={'Content-Type': 'application/json'},
            data=openapischema
        )
        return response.status_code, json.loads(response.text)
    except Exception:
        return 400, ""


def createDevPortal(locationDeclaration: dict, authProfiles: Authentication = {}) -> Tuple[int, str]:
    """
    Builds the declarative JSON for the API Gateway Developer Portal.

    Args:
        locationDeclaration (dict): Location declaration dictionary.
        authProfiles (Authentication, optional): Authentication profiles object.

    Returns:
        Tuple[int, str]: Status code and base64-encoded Developer Portal HTML string.
    """
    status = 200
    devportalHTML = ""

    if locationDeclaration.get('apigateway', {}).get('openapi_schema'):
        server_auth = authProfiles['server'] if isinstance(authProfiles, dict) and 'server' in authProfiles else {}
        status, apiSchemaString = v5_7.GitOps.getObjectFromRepo(
            object=locationDeclaration['apigateway']['openapi_schema'],
            authProfiles=server_auth,
            base64Encode=False
        )

        content = apiSchemaString.get('content', '')
        if v5_7.MiscUtils.yaml_or_json(content) == 'yaml':
            schema_json = v5_7.MiscUtils.yaml_to_json(content)
            status, devportalJSON = buildDevPortal(openapischema=schema_json)
        else:
            status, devportalJSON = buildDevPortal(openapischema=content)

        if status == 200 and isinstance(devportalJSON, dict) and 'devportal' in devportalJSON:
            devportalHTML = base64.b64encode(bytes(devportalJSON['devportal'], 'utf-8')).decode('utf-8')
        else:
            devportalHTML = ""

    return status, devportalHTML