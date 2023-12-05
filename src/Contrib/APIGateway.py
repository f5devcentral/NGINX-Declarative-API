"""
API Gateway support functions
"""

import json
import Contrib.GitOps
from Contrib.OpenAPIParser import OpenAPIParser


# Check NAP policies names validity for the given declaration
# Return a tuple: status, description. If status = 200 checks were successful
def createAPIGateway(declaration: dict):
    if 'openapi_schema' in declaration:
        status, apiSchemaString = Contrib.GitOps.getObjectFromRepo(content=declaration['openapi_schema'],base64Encode=False)
        apiSchema = OpenAPIParser(json.loads(apiSchemaString))

        servers = apiSchema.servers()
        paths = apiSchema.paths()

        print(f"Servers: {servers}")
        print(f"Paths: {paths}")

    return 200, ""