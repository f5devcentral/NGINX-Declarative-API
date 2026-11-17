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
    _HTTP_TOKEN_RE = re.compile(r"^[!#$%&'*+\-.^_`|~0-9A-Za-z]+$")
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

    @staticmethod
    def _default_swagger_scheme(host: str) -> str:
        """
        Determines a fallback HTTP scheme when a Swagger 2.0 definition omits 'schemes'.
        """
        port_str = None
        if host.startswith('['):
            if ']:' in host:
                port_str = host.rsplit(']:', 1)[1]
        elif ':' in host:
            port_str = host.rsplit(':', 1)[1]
        return 'http' if (port_str and port_str != '443') else 'https'

    def _swagger_servers(self) -> List[Dict[str, Any]]:
        """
        Synthesizes server entries from Swagger / OpenAPI 2.0 top-level
        'host', 'basePath', and 'schemes' fields.
        """
        raw_host = self.openAPISchema.get('host')
        host = raw_host.strip() if isinstance(raw_host, str) else ''

        raw_base_path = self.openAPISchema.get('basePath')
        base_path_str = raw_base_path.strip().strip('/') if isinstance(raw_base_path, str) else ''
        normalized_base_path = f"/{base_path_str}" if base_path_str else ''

        if host:
            raw_schemes = self.openAPISchema.get('schemes')
            http_schemes = [
                s.strip().lower() for s in raw_schemes
                if isinstance(s, str) and s.strip().lower() in ('http', 'https')
            ] if isinstance(raw_schemes, list) else []
            scheme = http_schemes[0] if http_schemes else self._default_swagger_scheme(host)
            return [{'url': f"{scheme}://{host}{normalized_base_path}"}]

        if normalized_base_path:
            return [{'url': normalized_base_path}]

        return []

    def servers(self) -> List[Dict[str, Any]]:
        """
        Retrieves server definitions from the schema.

        Supports OpenAPI 3.x 'servers' arrays as well as Swagger / OpenAPI 2.0
        top-level 'host', 'basePath', and 'schemes' fields.

        Returns:
            List[Dict[str, Any]]: List of server dictionaries containing resolved 'url' and optional fields.
        """
        all_servers = []
        if 'servers' in self.openAPISchema and isinstance(self.openAPISchema['servers'], list):
            for server in self.openAPISchema['servers']:
                if isinstance(server, dict):
                    all_servers.append(self._parse_server(server))
            if all_servers:
                return all_servers

        if 'swagger' in self.openAPISchema or 'host' in self.openAPISchema:
            return self._swagger_servers()

        return all_servers

    def _parse_parameter(self, qsParam: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Helper method to parse a single query string / path / header parameter dictionary.

        Supports both OpenAPI 3.x ('parameter.schema') and Swagger / OpenAPI 2.0
        (type/default/enum/items directly on the Parameter Object).

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

        param_schema: Dict[str, Any] = {}
        schema_source: Optional[Dict[str, Any]] = None
        if 'schema' in qsParam and isinstance(qsParam['schema'], dict):
            schema_source = qsParam['schema']
        elif any(k in qsParam for k in ('type', 'default', 'enum', 'items')):
            schema_source = qsParam

        if schema_source is not None:
            items_obj = schema_source.get('items') if isinstance(schema_source.get('items'), dict) else {}
            param_schema['type'] = schema_source.get('type', '')
            param_schema['default'] = (
                schema_source['default'] if 'default' in schema_source else items_obj.get('default', '')
            )
            raw_enum = schema_source['enum'] if 'enum' in schema_source else items_obj.get('enum')
            param_schema['enum'] = list(raw_enum) if isinstance(raw_enum, list) else []

        param['schema'] = param_schema
        return param

    def _effective_consumes(self, methodInfo: Dict[str, Any]) -> List[str]:
        """
        Returns the effective Swagger 2.0 'consumes' media types for an operation,
        with operation-level 'consumes' overriding global document-level 'consumes'.
        """
        if 'consumes' in methodInfo:
            raw_consumes = methodInfo.get('consumes')
        else:
            raw_consumes = self.openAPISchema.get('consumes')

        if not isinstance(raw_consumes, list):
            return []
        return [ct for ct in raw_consumes if isinstance(ct, str) and ct]

    @staticmethod
    def _merge_parameters(
        pathParameters: Optional[List[Dict[str, Any]]],
        methodParameters: Optional[List[Dict[str, Any]]],
    ) -> List[Dict[str, Any]]:
        """
        Merges path-level and operation-level parameters per OpenAPI rules,
        allowing operation parameters to override matching (name, in) pairs.
        """
        merged: List[Dict[str, Any]] = []
        seen = set()

        for p in (methodParameters or []):
            if isinstance(p, dict):
                merged.append(p)
                if 'name' in p:
                    seen.add((p.get('name'), str(p.get('in', '')).lower()))

        for p in (pathParameters or []):
            if isinstance(p, dict):
                key = (p.get('name'), str(p.get('in', '')).lower()) if 'name' in p else None
                if key is None or key not in seen:
                    merged.append(p)
                    if key is not None:
                        seen.add(key)

        return merged

    def _parse_method(
        self,
        method: str,
        methodInfo: Dict[str, Any],
        pathParameters: Optional[List[Dict[str, Any]]] = None,
        allow_additional: bool = False,
    ) -> Optional[Dict[str, Any]]:
        """
        Helper method to parse details and parameters for an HTTP method on a path.

        Args:
            method (str): HTTP method name (e.g. 'get' or an additionalOperations method).
            methodInfo (Dict[str, Any]): Method details dictionary.
            pathParameters (Optional[List[Dict[str, Any]]]): Optional path-item parameters.
            allow_additional (bool): When True, accept arbitrary valid HTTP method tokens from
                OAS 3.2 additionalOperations (excluding unsupported QUERY).

        Returns:
            Optional[Dict[str, Any]]: Parsed method dictionary or None if method not supported.
        """
        if not isinstance(method, str) or not method or method.upper() == 'QUERY':
            return None
        if allow_additional:
            if not self._HTTP_TOKEN_RE.match(method):
                return None
        elif method.upper() not in self.httpMethods:
            return None

        request_body = methodInfo.get('requestBody') if isinstance(methodInfo.get('requestBody'), dict) else {}

        m = {}
        m['method'] = method
        m['details'] = {}
        m['details']['description'] = methodInfo.get('description', '')
        m['details']['summary'] = methodInfo.get('summary', '')
        m['details']['operationId'] = methodInfo.get('operationId', '')
        m['details']['requestBodyRequired'] = bool(request_body.get('required', False))
        m['details']['requestBodyContentType'] = []
        m['details']['disallowedResponseCodes'] = self.httpStatusCodes.copy()
        m['parameters'] = []

        content_dict = request_body.get('content') if isinstance(request_body.get('content'), dict) else {}
        for rbct in list(content_dict.keys()):
            m['details']['requestBodyContentType'].append(rbct)

        # m['details']['disallowedResponseCodes'] holds the list of disallowed HTTP return codes
        responses = methodInfo.get('responses') if isinstance(methodInfo.get('responses'), dict) else {}
        for respCode in list(responses.keys()):
            resp_code_str = str(respCode)
            if resp_code_str.lower() == 'default':
                m['details']['responseCodeDefault'] = responses.get(respCode)
            else:
                if resp_code_str in m['details']['disallowedResponseCodes']:
                    m['details']['disallowedResponseCodes'].remove(resp_code_str)

        raw_params = self._merge_parameters(
            pathParameters if isinstance(pathParameters, list) else None,
            methodInfo.get('parameters') if isinstance(methodInfo.get('parameters'), list) else None,
        )

        # Swagger / OpenAPI 2.0 body enforcement: inspect in="body" parameters and consumes
        if not request_body:
            body_params = [
                p for p in raw_params
                if str(p.get('in', '')).lower() == 'body'
            ]
            if body_params:
                m['details']['requestBodyRequired'] = any(bool(bp.get('required', False)) for bp in body_params)
                for ct in self._effective_consumes(methodInfo):
                    if ct not in m['details']['requestBodyContentType']:
                        m['details']['requestBodyContentType'].append(ct)

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

                    path_parameters = path_obj.get('parameters') if isinstance(path_obj.get('parameters'), list) else None
                    seen_methods = set()

                    for method, method_info in path_obj.items():
                        if isinstance(method_info, dict):
                            parsed_m = self._parse_method(method, method_info, pathParameters=path_parameters)
                            if parsed_m:
                                p['methods'].append(parsed_m)
                                seen_methods.add(parsed_m['method'].upper())

                    # OAS 3.2 additionalOperations: Map[string, Operation Object]
                    additional_ops = path_obj.get('additionalOperations')
                    if isinstance(additional_ops, dict):
                        for add_method, add_method_info in additional_ops.items():
                            if isinstance(add_method, str) and isinstance(add_method_info, dict):
                                if add_method.upper() in seen_methods:
                                    continue
                                parsed_m = self._parse_method(
                                    add_method,
                                    add_method_info,
                                    pathParameters=path_parameters,
                                    allow_additional=True,
                                )
                                if parsed_m:
                                    p['methods'].append(parsed_m)
                                    seen_methods.add(parsed_m['method'].upper())

                all_paths.append(p)

        return all_paths
