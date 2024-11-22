"""
OpenAPI schema parser support functions
"""

import json

class OpenAPIParser:
    httpMethods = ['GET', 'HEAD', 'POST', 'PUT', 'DELETE', 'CONNECT', 'OPTIONS', 'TRACE', 'PATCH']

    def __init__(self, openAPISchema):
        self.openAPISchema = openAPISchema

    def version(self):
        if 'openapi' in self.openAPISchema:
            return self.openAPISchema['openapi']
        elif 'swagger' in self.openAPISchema:
            return self.openAPISchema['swagger']

        return None

    def info(self):
        return self.openAPISchema['info']

    def servers(self):
        self.allServers = []

        # Loop over OpenAPI schema servers
        if 'servers' in self.openAPISchema:
            for server in self.openAPISchema['servers']:
                urlName = server['url']
                self.s = {}
                self.s['url'] = urlName

                if 'description' in server:
                    self.s['description'] = server['description']

                self.allServers.append(self.s)

        return self.allServers

    def paths(self):
        self.allPaths = []

        # Loop over OpenAPI schema paths
        if 'paths' in self.openAPISchema:
            for path in self.openAPISchema['paths'].keys():
                #print(f"- {path}")
                self.p = {}
                self.p['path'] = path
                self.p['methods'] = []

                # Loop over path HTTP methods found in schema
                for method in self.openAPISchema['paths'][path].keys():
                    methodInfo = self.openAPISchema['paths'][path][method]

                    if method.upper() in self.httpMethods:
                        self.m = {}
                        self.m['method'] = method
                        self.m['details'] = {}

                        if 'description' in methodInfo and methodInfo['description']:
                            self.m['details']['description'] = methodInfo['description']
                        if 'operationId' in methodInfo and methodInfo['operationId']:
                            self.m['details']['operationId'] = methodInfo['operationId']

                        self.p['methods'].append(self.m)

                self.allPaths.append(self.p)

        return self.allPaths