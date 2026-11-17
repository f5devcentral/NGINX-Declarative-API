"""
Tests for v5_5/OpenAPIParser.py

The v5_6 implementation is identical, so a single test suite covers both.
"""
import pytest

import v5_5.OpenAPIParser as oap_module
import v5_6.OpenAPIParser as oap_v56_module
import v5_7.OpenAPIParser as oap_v57_module

OpenAPIParser = oap_module.OpenAPIParser
OpenAPIParser_v56 = oap_v56_module.OpenAPIParser
OpenAPIParser_v57 = oap_v57_module.OpenAPIParser


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

OPENAPI_3_SCHEMA = {
    'openapi': '3.0.0',
    'info': {'title': 'Test API', 'version': '1.0.0'},
    'servers': [
        {'url': 'https://api.example.com', 'description': 'Production'},
        {'url': 'https://staging.example.com'},
    ],
    'paths': {
        '/users': {
            'get': {
                'summary': 'List users',
                'description': 'Returns all users',
                'operationId': 'listUsers',
                'parameters': [
                    {
                        'name': 'limit',
                        'in': 'query',
                        'description': 'Max results',
                        'required': False,
                        'schema': {'type': 'integer', 'default': '20'},
                    }
                ],
            },
            'post': {
                'summary': 'Create user',
                'description': 'Creates a new user',
                'operationId': 'createUser',
            },
        },
        '/users/{id}': {
            'get': {
                'summary': 'Get user',
                'description': 'Returns a single user',
                'operationId': 'getUser',
            },
            'delete': {
                'summary': 'Delete user',
                'description': 'Deletes a user',
                'operationId': 'deleteUser',
            },
        },
    },
}

SWAGGER_2_SCHEMA = {
    'swagger': '2.0',
    'info': {'title': 'Old API', 'version': '0.1'},
    'paths': {},
}

MINIMAL_SCHEMA = {}


# ---------------------------------------------------------------------------
# version()
# ---------------------------------------------------------------------------

class TestVersion:
    def test_openapi_3(self):
        parser = OpenAPIParser(OPENAPI_3_SCHEMA)
        assert parser.version() == '3.0.0'

    def test_swagger_2(self):
        parser = OpenAPIParser(SWAGGER_2_SCHEMA)
        assert parser.version() == '2.0'

    def test_no_version_returns_none(self):
        parser = OpenAPIParser(MINIMAL_SCHEMA)
        assert parser.version() is None

    def test_v56_version(self):
        parser = OpenAPIParser_v56(OPENAPI_3_SCHEMA)
        assert parser.version() == '3.0.0'


# ---------------------------------------------------------------------------
# info()
# ---------------------------------------------------------------------------

class TestInfo:
    def test_returns_info_block(self):
        parser = OpenAPIParser(OPENAPI_3_SCHEMA)
        info = parser.info()
        assert info['title'] == 'Test API'
        assert info['version'] == '1.0.0'

    def test_no_info_returns_none(self):
        parser = OpenAPIParser(MINIMAL_SCHEMA)
        assert parser.info() is None

    def test_v56_info(self):
        parser = OpenAPIParser_v56(SWAGGER_2_SCHEMA)
        assert parser.info()['title'] == 'Old API'


# ---------------------------------------------------------------------------
# servers()
# ---------------------------------------------------------------------------

class TestServers:
    def test_returns_all_servers(self):
        parser = OpenAPIParser(OPENAPI_3_SCHEMA)
        servers = parser.servers()
        assert len(servers) == 2

    def test_server_url_present(self):
        parser = OpenAPIParser(OPENAPI_3_SCHEMA)
        urls = [s['url'] for s in parser.servers()]
        assert 'https://api.example.com' in urls

    def test_server_description_present_when_defined(self):
        parser = OpenAPIParser(OPENAPI_3_SCHEMA)
        prod = next(s for s in parser.servers() if s['url'] == 'https://api.example.com')
        assert prod.get('description') == 'Production'

    def test_server_no_description_when_absent(self):
        parser = OpenAPIParser(OPENAPI_3_SCHEMA)
        staging = next(s for s in parser.servers() if s['url'] == 'https://staging.example.com')
        assert 'description' not in staging

    def test_no_servers_returns_empty_list(self):
        parser = OpenAPIParser(MINIMAL_SCHEMA)
        assert parser.servers() == []

    def test_v56_servers(self):
        parser = OpenAPIParser_v56(OPENAPI_3_SCHEMA)
        assert len(parser.servers()) == 2


# ---------------------------------------------------------------------------
# paths()
# ---------------------------------------------------------------------------

class TestPaths:
    def test_returns_all_paths(self):
        parser = OpenAPIParser(OPENAPI_3_SCHEMA)
        paths = parser.paths()
        path_uris = [p['path'] for p in paths]
        assert '/users' in path_uris
        assert '/users/{id}' in path_uris

    def test_methods_populated(self):
        parser = OpenAPIParser(OPENAPI_3_SCHEMA)
        users_path = next(p for p in parser.paths() if p['path'] == '/users')
        methods = [m['method'] for m in users_path['methods']]
        assert 'get' in methods
        assert 'post' in methods

    def test_method_details(self):
        parser = OpenAPIParser(OPENAPI_3_SCHEMA)
        users_path = next(p for p in parser.paths() if p['path'] == '/users')
        get_method = next(m for m in users_path['methods'] if m['method'] == 'get')
        assert get_method['details']['summary'] == 'List users'
        assert get_method['details']['operationId'] == 'listUsers'

    def test_query_parameters_parsed(self):
        parser = OpenAPIParser(OPENAPI_3_SCHEMA)
        users_path = next(p for p in parser.paths() if p['path'] == '/users')
        get_method = next(m for m in users_path['methods'] if m['method'] == 'get')
        assert len(get_method['parameters']) == 1
        assert get_method['parameters'][0]['name'] == 'limit'
        assert get_method['parameters'][0]['in'] == 'query'

    def test_parameter_schema_parsed(self):
        parser = OpenAPIParser(OPENAPI_3_SCHEMA)
        users_path = next(p for p in parser.paths() if p['path'] == '/users')
        get_method = next(m for m in users_path['methods'] if m['method'] == 'get')
        schema = get_method['parameters'][0]['schema']
        assert schema['type'] == 'integer'
        assert schema['default'] == '20'

    def test_no_paths_returns_empty_list(self):
        parser = OpenAPIParser(MINIMAL_SCHEMA)
        assert parser.paths() == []

    def test_non_http_keys_ignored(self):
        # 'summary' at path level is not a valid HTTP method and should be ignored
        schema = {
            'paths': {
                '/health': {
                    'summary': 'health check path',
                    'get': {'description': 'ping', 'summary': 'health', 'operationId': 'healthCheck'},
                }
            }
        }
        parser = OpenAPIParser(schema)
        paths = parser.paths()
        health = next(p for p in paths if p['path'] == '/health')
        methods = [m['method'] for m in health['methods']]
        assert 'get' in methods
        assert 'summary' not in methods

    def test_v56_paths(self):
        parser = OpenAPIParser_v56(OPENAPI_3_SCHEMA)
        paths = parser.paths()
        assert any(p['path'] == '/users' for p in paths)


# ---------------------------------------------------------------------------
# v5.7 servers and variables tests
# ---------------------------------------------------------------------------

class TestOpenAPIServersV57:
    def test_v57_servers_variables_substitution(self):
        schema = {
            'openapi': '3.0.0',
            'servers': [
                {
                    'name': 'Production',
                    'url': 'https://{username}.server.com:{port}/{version}',
                    'description': 'Main server',
                    'variables': {
                        'username': {'default': 'demo', 'description': 'Username'},
                        'port': {'default': '8443', 'enum': ['8443', '443']},
                        'version': {'default': 'v1'},
                    },
                },
                {'url': 'https://secondary.server.com'},
            ],
        }
        parser = OpenAPIParser_v57(schema)
        servers = parser.servers()
        assert len(servers) == 2
        assert servers[0]['name'] == 'Production'
        assert servers[0]['url'] == 'https://demo.server.com:8443/v1'
        assert servers[0]['description'] == 'Main server'
        assert servers[1]['url'] == 'https://secondary.server.com'

    def test_v57_paths_servers(self):
        schema = {
            'openapi': '3.0.0',
            'paths': {
                '/items': {
                    'servers': [
                        {'url': 'https://items1.server.com'},
                        {
                            'url': 'https://{region}.items2.server.com',
                            'variables': {'region': {'default': 'us-west'}},
                        },
                    ],
                    'get': {'summary': 'List items'},
                },
                '/status': {
                    'get': {'summary': 'Status check'},
                },
            },
        }
        parser = OpenAPIParser_v57(schema)
        paths = parser.paths()
        items_p = next(p for p in paths if p['path'] == '/items')
        status_p = next(p for p in paths if p['path'] == '/status')

        assert 'servers' in items_p
        assert len(items_p['servers']) == 2
        assert items_p['servers'][0]['url'] == 'https://items1.server.com'
        assert items_p['servers'][1]['url'] == 'https://us-west.items2.server.com'

        assert 'servers' not in status_p

    def test_v57_operation_servers(self):
        schema = {
            'openapi': '3.0.0',
            'servers': [{'url': 'https://server1.com'}],
            'paths': {
                '/users': {
                    'get': {
                        'summary': 'List users',
                        'servers': [
                            {
                                'url': 'https://{region}.server2.com',
                                'variables': {'region': {'default': 'eu'}},
                            }
                        ],
                    },
                    'post': {'summary': 'Create user'},
                },
            },
        }
        parser = OpenAPIParser_v57(schema)
        paths = parser.paths()
        users_p = next(p for p in paths if p['path'] == '/users')
        get_m = next(m for m in users_p['methods'] if m['method'] == 'get')
        post_m = next(m for m in users_p['methods'] if m['method'] == 'post')

        assert 'servers' in get_m
        assert get_m['servers'][0]['url'] == 'https://eu.server2.com'
        assert 'servers' not in post_m
