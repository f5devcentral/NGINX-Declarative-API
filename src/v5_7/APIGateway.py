"""
API Gateway support functions
"""

import json
from typing import Dict, Tuple, Any

import v5_7.GitOps
import v5_7.MiscUtils
from v5_7.OpenAPIParser import OpenAPIParser

# pydantic models
from V5_7_NginxConfigDeclaration import *


def _fetch_and_parse_openapi_schema(
    openapi_schema_obj: Dict[str, Any],
    auth_profiles: Dict[str, Any]
) -> Tuple[int, Any, Dict[str, Any]]:
    """
    Fetches the OpenAPI schema object from GitOps repo and converts YAML to JSON if needed.

    Args:
        openapi_schema_obj (dict): The OpenAPI schema object declaration.
        auth_profiles (dict): Authentication profiles dictionary.

    Returns:
        Tuple[int, Any, dict]: Status code, parsed OpenAPIParser instance or empty string, and raw content dictionary.
    """
    server_auth = auth_profiles['server'] if isinstance(auth_profiles, dict) and 'server' in auth_profiles else {}
    status, api_schema_string = v5_7.GitOps.getObjectFromRepo(
        object=openapi_schema_obj,
        authProfiles=server_auth,
        base64Encode=False
    )

    if status != 200:
        return status, "", api_schema_string

    content = api_schema_string.get('content', '')
    if v5_7.MiscUtils.yaml_or_json(content) == 'yaml':
        content = v5_7.MiscUtils.yaml_to_json(content)
        api_schema_string['content'] = content

    parsed_schema = OpenAPIParser(json.loads(content))
    return 200, parsed_schema, api_schema_string


def createAPIGateway(locationDeclaration: dict, authProfiles: Authentication = {}) -> Tuple[int, dict, str]:
    """
    Builds the declarative JSON for the API Gateway configuration.

    Args:
        locationDeclaration (dict): The location declaration object.
        authProfiles (Authentication, optional): Authentication profiles object.

    Returns:
        Tuple[int, dict, str]: Status code, API gateway declaration dict, and raw schema content string.
    """
    apiGwDeclaration = {}
    raw_schema_content = ""

    if locationDeclaration.get('apigateway', {}).get('openapi_schema'):
        status, apiSchema, schema_obj = _fetch_and_parse_openapi_schema(
            locationDeclaration['apigateway']['openapi_schema'],
            authProfiles
        )

        if status != 200:
            return status, "", ""

        raw_schema_content = schema_obj.get('content', '')
        apiGwDeclaration = {
            'location': locationDeclaration,
            'info': apiSchema.info(),
            'servers': apiSchema.servers(),
            'paths': apiSchema.paths(),
            'version': apiSchema.version()
        }

    return 200, apiGwDeclaration, raw_schema_content