"""
API Gateway support functions
"""

import json

import v5_1.GitOps
import v5_1.MiscUtils
from v5_1.OpenAPIParser import OpenAPIParser

# pydantic models
from V5_1_NginxConfigDeclaration import *


# Builds the declarative JSON for the API Gateway configuration
# Return a tuple: status, description. If status = 200 things were successful
def createAPIGateway(locationDeclaration: dict, authProfiles: Authentication={}):
    apiGwDeclaration = {}

    if locationDeclaration['apigateway']['openapi_schema']:
        status, apiSchemaString = v5_1.GitOps.getObjectFromRepo(object=locationDeclaration['apigateway']['openapi_schema'],
                                                                authProfiles = authProfiles['server'] if 'server' in authProfiles else {}, base64Encode=False)

        if v5_1.MiscUtils.yaml_or_json(apiSchemaString['content']) == 'yaml':
            # YAML to JSON conversion
            apiSchemaString['content'] = v5_1.MiscUtils.yaml_to_json(apiSchemaString['content'])

        apiSchema = OpenAPIParser(json.loads(apiSchemaString['content']))

        apiGwDeclaration = {}
        apiGwDeclaration['location'] = locationDeclaration
        apiGwDeclaration['info'] = apiSchema.info()
        apiGwDeclaration['servers'] = apiSchema.servers()
        apiGwDeclaration['paths'] = apiSchema.paths()
        apiGwDeclaration['version'] = apiSchema.version()

    return 200, apiGwDeclaration, apiSchemaString['content']