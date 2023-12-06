"""
API Gateway support functions
"""

import json
import base64

import Contrib.GitOps
from Contrib.OpenAPIParser import OpenAPIParser


# Builds the declarative JSON for the API Gateway configuration
# Return a tuple: status, description. If status = 200 things were successful
def createAPIGateway(locationDeclaration: dict):
    apiGwDeclaration = {}

    if locationDeclaration['apigateway']['openapi_schema']:
        status, apiSchemaString = Contrib.GitOps.getObjectFromRepo(content=locationDeclaration['apigateway']['openapi_schema'], base64Encode=False)
        apiSchema = OpenAPIParser(json.loads(apiSchemaString))

        version = apiSchema.version()
        info = apiSchema.info()
        servers = apiSchema.servers()
        paths = apiSchema.paths()

        print(f"OpenAPI version: {version}")
        print(f"Info {info}")
        print(f"Servers: {servers}")
        print(f"Paths: {paths}")

        apiGwDeclaration = {}
        apiGwDeclaration['location'] = locationDeclaration
        apiGwDeclaration['info'] = info
        apiGwDeclaration['servers'] = servers
        apiGwDeclaration['paths'] = paths

    return 200, apiGwDeclaration