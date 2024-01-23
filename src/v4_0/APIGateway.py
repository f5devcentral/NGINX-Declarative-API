"""
API Gateway support functions
"""

import json
import base64

import v4_0.GitOps
import v4_0.MiscUtils
from v4_0.OpenAPIParser import OpenAPIParser


# Builds the declarative JSON for the API Gateway configuration
# Return a tuple: status, description. If status = 200 things were successful
def createAPIGateway(locationDeclaration: dict):
    apiGwDeclaration = {}

    if locationDeclaration['apigateway']['openapi_schema']:
        status, apiSchemaString = v4_0.GitOps.getObjectFromRepo(content=locationDeclaration['apigateway']['openapi_schema'], base64Encode=False)

        if v4_0.MiscUtils.yaml_or_json(apiSchemaString) == 'yaml':
            # YAML to JSON conversion
            apiSchemaString = v4_0.MiscUtils.yaml_to_json(apiSchemaString)

        apiSchema = OpenAPIParser(json.loads(apiSchemaString))

        apiGwDeclaration = {}
        apiGwDeclaration['location'] = locationDeclaration
        apiGwDeclaration['info'] = apiSchema.info()
        apiGwDeclaration['servers'] = apiSchema.servers()
        apiGwDeclaration['paths'] = apiSchema.paths()
        apiGwDeclaration['version'] = apiSchema.version()

    return 200, apiGwDeclaration