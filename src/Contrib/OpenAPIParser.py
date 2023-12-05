"""
OpenAPI schema parser support functions
"""

import json

class OpenAPIParser:
    httpMethods = ['GET', 'HEAD', 'POST', 'PUT', 'DELETE', 'CONNECT', 'OPTIONS', 'TRACE', 'PATCH']

    def __init__(self, openAPISchema):
        self.openAPISchema = openAPISchema

    def servers(self):
        self.allServers = {}

        # Loop over OpenAPI schema servers
        for server in self.openAPISchema['servers']:
            urlName = server['url']
            self.allServers[urlName] = {}

            if 'description' in server:
                self.allServers[urlName]['description'] = server['description']

        return self.allServers

    def paths(self):
        self.allPaths = {}

        # Loop over OpenAPI schema paths
        for path in self.openAPISchema['paths'].keys():
            print(f"- {path}")
            self.allPaths[path] = {}

            # Loop over path HTTP methods found in schema
            for method in self.openAPISchema['paths'][path].keys():
                methodInfo = self.openAPISchema['paths'][path][method]

                if method.upper() in self.httpMethods:
                    print(f"  - {method} - {methodInfo['description'] if 'description' in methodInfo else ''}")
                    self.allPaths[path][method] = {}

                    if 'description' in methodInfo and methodInfo['description']:
                        self.allPaths[path][method]['description'] = methodInfo['description']
                    if 'operationId' in methodInfo and methodInfo['operationId']:
                        self.allPaths[path][method]['operationId'] = methodInfo['operationId']

        return self.allPaths