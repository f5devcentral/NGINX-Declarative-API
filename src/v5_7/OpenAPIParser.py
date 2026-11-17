"""
OpenAPI schema parser support functions
"""

import re
from typing import Dict, Any, List, Optional


class OpenAPIParser:
    """
    Parser for OpenAPI / Swagger specification dictionaries.
    """
    httpMethods = ['GET', 'HEAD', 'POST', 'PUT', 'DELETE', 'CONNECT', 'OPTIONS', 'TRACE', 'PATCH']
    httpStatusCodes = [
    #    "000",
    #    "100", "101", "102", "103",
    #    "200", "201", "202", "203", "204", "205", "206", "207", "208", "218", "226",
        "300", "301", "302", "303", "304", "305", "306", "307", "308",
        "400",
    #   "401",
        "402",
    #   "403",
        "404", "405", "406", "407", "408", "409",
        "410", "411", "412", "413", "414", "415", "416", "417", "418", "419",
        "420", "421", "422", "423", "424", "425", "426", "428",
    #   "429",
        "430",
        "431", "440", "444", "449", "450", "451", "460", "463", "464",
        "494", "495", "496", "497", "498",
        "500", "501", "502", "503", "504", "505", "506", "507", "508", "509",
        "510", "511", "520", "521", "522", "523", "524", "525", "526", "527",
        "529", "530", "540", "561", "598", "599",
    ]

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

    @staticmethod
    def _resolve_server_url(url: str, variables: Optional[Dict[str, Any]] = None) -> str:
        """
        Resolves server variable placeholders {var} in a server URL using their default values.

        Args:
            url (str): The raw server URL template.
            variables (Optional[Dict[str, Any]]): Dictionary of Server Variable Objects.

        Returns:
            str: The resolved URL with variables substituted.
        """
        if not url:
            return ""
        if not variables or not isinstance(variables, dict):
            return url

        def _replace_var(match: re.Match) -> str:
            var_name = match.group(1).strip()
            if var_name in variables and isinstance(variables[var_name], dict):
                var_obj = variables[var_name]
                if 'default' in var_obj and var_obj['default'] is not None:
                    return str(var_obj['default'])
                if 'enum' in var_obj and isinstance(var_obj['enum'], list) and var_obj['enum']:
                    return str(var_obj['enum'][0])
            return match.group(0)

        return re.sub(r'\{([^{}]+)\}', _replace_var, url)

    def _parse_server(self, server: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parses a single server definition and resolves server variables if present.

        Args:
            server (Dict[str, Any]): Server definition dictionary.

        Returns:
            Dict[str, Any]: Parsed server dictionary with resolved 'url' and optional fields.
        """
        raw_url = server.get('url', '')
        variables = server.get('variables') if isinstance(server.get('variables'), dict) else None
        resolved_url = self._resolve_server_url(raw_url, variables)
        s: Dict[str, Any] = {'url': resolved_url}
        if 'name' in server:
            s['name'] = server['name']
        if 'description' in server:
            s['description'] = server['description']
        if variables:
            s['variables'] = variables
        return s

    def servers(self) -> List[Dict[str, Any]]:
        """
        Retrieves server definitions from the schema.

        Returns:
            List[Dict[str, Any]]: List of server dictionaries containing resolved 'url' and optional 'description'.
        """
        all_servers = []
        if 'servers' in self.openAPISchema and isinstance(self.openAPISchema['servers'], list):
            for server in self.openAPISchema['servers']:
                if isinstance(server, dict):
                    all_servers.append(self._parse_server(server))
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

        m = {}
        m['method'] = method
        m['details'] = {}
        m['details']['description'] = methodInfo.get('description', '')
        m['details']['summary'] = methodInfo.get('summary', '')
        m['details']['operationId'] = methodInfo.get('operationId', '')
        m['details']['requestBodyRequired'] = methodInfo.get('requestBody', {}).get('required', False)
        m['details']['requestBodyContentType'] = []
        m['details']['disallowedResponseCodes'] = self.httpStatusCodes.copy()
        m['parameters'] = []

        for rbct in list(methodInfo.get('requestBody', {}).get('content', {}).keys()):
            m['details']['requestBodyContentType'].append(rbct)

        # m['details']['disallowedResponseCodes'] holds the list of disallowed HTTP return codes
        for respCode in list(methodInfo.get('responses', {}).keys()):
            if respCode.lower() == 'default':
                m['details']['responseCodeDefault'] = methodInfo.get('responses', {}).get('default')
            else:
                if respCode in m['details']['disallowedResponseCodes']:
                    m['details']['disallowedResponseCodes'].remove(respCode)

        raw_params = methodInfo.get('parameters')
        if raw_params and isinstance(raw_params, list):
            for qsParam in raw_params:
                parsed_p = self._parse_parameter(qsParam)
                if parsed_p:
                    m['parameters'].append(parsed_p)

        if 'servers' in methodInfo and isinstance(methodInfo['servers'], list):
            m['servers'] = [
                self._parse_server(s) for s in methodInfo['servers'] if isinstance(s, dict)
            ]

        return m

    def paths(self) -> List[Dict[str, Any]]:
        """
        Retrieves all path and method definitions from the schema.

        Returns:
            List[Dict[str, Any]]: List of path dictionaries containing 'path', 'methods', and optional 'servers'.
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
                    if 'servers' in path_obj and isinstance(path_obj['servers'], list):
                        p['servers'] = [
                            self._parse_server(s) for s in path_obj['servers'] if isinstance(s, dict)
                        ]

                    for method, method_info in path_obj.items():
                        if isinstance(method_info, dict):
                            parsed_m = self._parse_method(method, method_info)
                            if parsed_m:
                                p['methods'].append(parsed_m)

                all_paths.append(p)

        return all_paths
