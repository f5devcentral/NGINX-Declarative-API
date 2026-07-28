"""
OpenAPI schema parser support functions
"""

import json
from typing import Dict, Any, List, Optional


class OpenAPIParser:
    """
    Parser for OpenAPI / Swagger specification dictionaries.
    """
    httpMethods = ['GET', 'HEAD', 'POST', 'PUT', 'DELETE', 'CONNECT', 'OPTIONS', 'TRACE', 'PATCH']

    def __init__(self, openAPISchema: Dict[str, Any]):
        """
        Initialize OpenAPIParser.

        Args:
            openAPISchema (Dict[str, Any]): Parsed OpenAPI or Swagger specification dictionary.
        """
        self.openAPISchema = openAPISchema or {}

    def version(self) -> Optional[str]:
        """
        Retrieves the OpenAPI or Swagger specification version.

        Returns:
            Optional[str]: Version string if found, otherwise None.
        """
        if 'openapi' in self.openAPISchema:
            return self.openAPISchema['openapi']
        elif 'swagger' in self.openAPISchema:
            return self.openAPISchema['swagger']
        return None

    def info(self) -> Optional[Dict[str, Any]]:
        """
        Retrieves the specification info dictionary.

        Returns:
            Optional[Dict[str, Any]]: Info dictionary if found, otherwise None.
        """
        return self.openAPISchema.get('info')

    def servers(self) -> List[Dict[str, str]]:
        """
        Retrieves server definitions from the schema.

        Returns:
            List[Dict[str, str]]: List of server dictionaries containing 'url' and optional 'description'.
        """
        all_servers = []
        if 'servers' in self.openAPISchema and isinstance(self.openAPISchema['servers'], list):
            for server in self.openAPISchema['servers']:
                s = {'url': server.get('url', '')}
                if 'description' in server:
                    s['description'] = server['description']
                all_servers.append(s)
        return all_servers

    def _parse_parameter(self, qsParam: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Helper method to parse a single query string / path parameter dictionary.

        Args:
            qsParam (Dict[str, Any]): Parameter definition dictionary.

        Returns:
            Optional[Dict[str, Any]]: Cleaned parameter dictionary or None if 'name' missing.
        """
        if 'name' not in qsParam:
            return None

        param = {
            'name': qsParam['name'],
            'in': qsParam.get('in', ''),
            'description': qsParam.get('description', ''),
            'required': qsParam.get('required', False)
        }

        param_schema = {}
        if 'schema' in qsParam and isinstance(qsParam['schema'], dict):
            schema_obj = qsParam['schema']
            param_schema['type'] = schema_obj.get('type', '')
            param_schema['default'] = schema_obj.get('default', '')
            param_schema['enum'] = list(schema_obj.get('enum', [])) if 'enum' in schema_obj else []

        param['schema'] = param_schema
        return param

    def _parse_method(self, method: str, methodInfo: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Helper method to parse details and parameters for an HTTP method on a path.

        Args:
            method (str): HTTP method name (e.g. 'get').
            methodInfo (Dict[str, Any]): Method details dictionary.

        Returns:
            Optional[Dict[str, Any]]: Parsed method dictionary or None if method not supported.
        """
        if method.upper() not in self.httpMethods:
            return None

        m = {
            'method': method,
            'details': {
                'description': methodInfo.get('description', ''),
                'summary': methodInfo.get('summary', ''),
                'operationId': methodInfo.get('operationId', '')
            },
            'parameters': []
        }

        raw_params = methodInfo.get('parameters')
        if raw_params and isinstance(raw_params, list):
            for qsParam in raw_params:
                parsed_p = self._parse_parameter(qsParam)
                if parsed_p:
                    m['parameters'].append(parsed_p)

        return m

    def paths(self) -> List[Dict[str, Any]]:
        """
        Retrieves all path and method definitions from the schema.

        Returns:
            List[Dict[str, Any]]: List of path dictionaries containing 'path' and 'methods'.
        """
        all_paths = []
        raw_paths = self.openAPISchema.get('paths')

        if raw_params_dict := (raw_paths if isinstance(raw_paths, dict) else None):
            for path, path_obj in raw_params_dict.items():
                p = {
                    'path': path,
                    'methods': []
                }

                if isinstance(path_obj, dict):
                    for method, method_info in path_obj.items():
                        if isinstance(method_info, dict):
                            parsed_m = self._parse_method(method, method_info)
                            if parsed_m:
                                p['methods'].append(parsed_m)

                all_paths.append(p)

        return all_paths
