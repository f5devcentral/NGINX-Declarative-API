"""
Unit tests for v5.7 API Gateway upstreams and OpenAPI servers specification support.
"""
import base64
import json
import os
import pytest

from NcgConfig import NcgConfig
import V5_7_CreateConfig
from V5_7_ConfigBuilder import ConfigBuildContext, build_config_files

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))


@pytest.fixture(autouse=True)
def setup_ncg_config():
    NcgConfig._instance = None
    NcgConfig(os.path.join(REPO_ROOT, "etc", "config.yaml"))
    NcgConfig.config['templates']['root_dir'] = os.path.join(REPO_ROOT, 'templates')


def _build_test_declaration(
    openapi_schema: dict,
    server_url: str = "https://fallback.example.com",
    with_resolver: bool = False,
) -> dict:
    b64_schema = base64.b64encode(json.dumps(openapi_schema).encode()).decode()
    decl = {
        'output': {'type': 'nms'},
        'declaration': {
            'http': {
                'servers': [
                    {
                        'name': 'test_apigw',
                        'names': ['test_apigw.example.com'],
                        'resolver': 'Google' if with_resolver else '',
                        'log': None,
                        'locations': [
                            {
                                'uri': '/gw',
                                'log': None,
                                'apigateway': {
                                    'api_gateway': {
                                        'enabled': True,
                                        'strip_uri': True,
                                        'server_url': server_url,
                                    },
                                    'openapi_schema': {
                                        'content': b64_schema,
                                    },
                                },
                            }
                        ],
                    }
                ]
            }
        },
    }
    if with_resolver:
        decl['declaration']['resolvers'] = [
            {
                'name': 'Google',
                'address': '8.8.8.8',
                'ipv4': True,
                'ipv6': False,
                'timeout': '30s',
            }
        ]
    return decl


class TestV57ApiGatewayServers:
    def test_root_servers_multiple_entries(self):
        schema = {
            'openapi': '3.0.0',
            'info': {'title': 'Root Multi-Servers API', 'version': '1.0.0'},
            'servers': [
                {'url': 'https://srv1.example.com'},
                {'url': 'https://srv2.example.com'},
                {'url': 'https://srv3.example.com:8443'},
            ],
            'paths': {
                '/items': {'get': {'summary': 'List items'}},
            },
        }
        decl = _build_test_declaration(schema)
        ctx = ConfigBuildContext(decl, 'v5.7')
        err = build_config_files(ctx)
        assert err is None

        upstreams_file = next(f for f in ctx.configFiles['files'] if 'upstream' in f['name'].lower())
        content = base64.b64decode(upstreams_file['contents']).decode()

        assert 'upstream apigw_test_apigw_gw {' in content
        assert 'zone apigw_test_apigw_gw 64k;' in content
        assert 'server srv1.example.com:443;' in content
        assert 'server srv2.example.com:443;' in content
        assert 'server srv3.example.com:8443;' in content

    def test_per_path_servers_override(self):
        schema = {
            'openapi': '3.0.0',
            'info': {'title': 'Per-Path Servers API', 'version': '1.0.0'},
            'servers': [
                {'url': 'https://default.example.com'},
            ],
            'paths': {
                '/standard': {
                    'get': {'summary': 'Standard path'},
                },
                '/dedicated': {
                    'servers': [
                        {'url': 'https://dedicated1.example.com'},
                        {'url': 'https://dedicated2.example.com'},
                    ],
                    'get': {'summary': 'Dedicated path'},
                },
            },
        }
        decl = _build_test_declaration(schema)
        ctx = ConfigBuildContext(decl, 'v5.7')
        err = build_config_files(ctx)
        assert err is None

        upstreams_file = next(f for f in ctx.configFiles['files'] if 'upstream' in f['name'].lower())
        upstreams_content = base64.b64decode(upstreams_file['contents']).decode()

        # Both the default upstream and the dedicated path upstream must exist
        assert 'upstream apigw_test_apigw_gw {' in upstreams_content
        assert 'zone apigw_test_apigw_gw 64k;' in upstreams_content
        assert 'server default.example.com:443;' in upstreams_content

        assert 'upstream apigw_test_apigw_gw_dedicated {' in upstreams_content
        assert 'zone apigw_test_apigw_gw_dedicated 64k;' in upstreams_content
        assert 'server dedicated1.example.com:443;' in upstreams_content
        assert 'server dedicated2.example.com:443;' in upstreams_content

        # Location file routing checks
        location_file = next(
            f for f in ctx.configFiles['files']
            if 'apigateway' in f['name'].lower() and 'upstreams' not in f['name'].lower() and 'maps' not in f['name'].lower()
        )
        location_content = base64.b64decode(location_file['contents']).decode()

        assert 'proxy_pass https://apigw_test_apigw_gw$uri$is_args$args;' in location_content
        assert 'proxy_pass https://apigw_test_apigw_gw_dedicated$uri$is_args$args;' in location_content

    def test_open_meteo_path_only_servers_overrides_server_url(self):
        schema = {
            'openapi': '3.0.0',
            'info': {'title': 'Open-Meteo APIs', 'version': '1.0'},
            'paths': {
                '/v1/forecast': {
                    'servers': [
                        {'url': 'https://api.open-meteo.com'},
                        {'url': 'https://customer-api.open-meteo.com'},
                    ],
                    'get': {'summary': '7 day weather forecast for coordinates'},
                },
            },
        }
        decl = _build_test_declaration(schema, server_url='https://fallback.open-meteo.com', with_resolver=True)
        ctx = ConfigBuildContext(decl, 'v5.7')
        err = build_config_files(ctx)
        assert err is None

        upstreams_file = next(f for f in ctx.configFiles['files'] if 'upstream' in f['name'].lower())
        upstreams_content = base64.b64decode(upstreams_file['contents']).decode()

        assert 'upstream apigw_test_apigw_gw_v1_forecast {' in upstreams_content
        assert 'zone apigw_test_apigw_gw_v1_forecast 64k;' in upstreams_content
        assert 'server api.open-meteo.com:443 resolve;' in upstreams_content
        assert 'server customer-api.open-meteo.com:443 resolve;' in upstreams_content
        assert 'fallback.open-meteo.com' not in upstreams_content

        location_file = next(
            f for f in ctx.configFiles['files']
            if 'apigateway' in f['name'].lower() and 'upstreams' not in f['name'].lower() and 'maps' not in f['name'].lower()
        )
        location_content = base64.b64decode(location_file['contents']).decode()
        assert 'proxy_pass https://apigw_test_apigw_gw_v1_forecast$uri$is_args$args;' in location_content

    def test_server_variables_substitution(self):
        schema = {
            'openapi': '3.0.0',
            'info': {'title': 'Variables API', 'version': '1.0.0'},
            'servers': [
                {
                    'url': 'https://{env}.api.example.com:{port}/{version}',
                    'variables': {
                        'env': {'default': 'prod'},
                        'port': {'default': '8443'},
                        'version': {'default': 'v1'},
                    },
                },
            ],
            'paths': {
                '/status': {
                    'get': {'summary': 'Status path'},
                },
                '/data': {
                    'servers': [
                        {
                            'url': 'https://{region}.data.example.com:{port}',
                            'variables': {
                                'region': {'default': 'us-east'},
                                'port': {'default': '9443'},
                            },
                        },
                    ],
                    'get': {'summary': 'Data path'},
                },
            },
        }
        decl = _build_test_declaration(schema)
        ctx = ConfigBuildContext(decl, 'v5.7')
        err = build_config_files(ctx)
        assert err is None

        upstreams_file = next(f for f in ctx.configFiles['files'] if 'upstream' in f['name'].lower())
        upstreams_content = base64.b64decode(upstreams_file['contents']).decode()

        # Root server resolved variables
        assert 'upstream apigw_test_apigw_gw {' in upstreams_content
        assert 'zone apigw_test_apigw_gw 64k;' in upstreams_content
        assert 'server prod.api.example.com:8443;' in upstreams_content

        # Dedicated path upstream resolved variables
        assert 'upstream apigw_test_apigw_gw_data {' in upstreams_content
        assert 'zone apigw_test_apigw_gw_data 64k;' in upstreams_content
        assert 'server us-east.data.example.com:9443;' in upstreams_content

        location_file = next(
            f for f in ctx.configFiles['files']
            if 'apigateway' in f['name'].lower() and 'upstreams' not in f['name'].lower() and 'maps' not in f['name'].lower()
        )
        location_content = base64.b64decode(location_file['contents']).decode()
        assert 'proxy_pass https://apigw_test_apigw_gw/v1$uri$is_args$args;' in location_content
        assert 'proxy_pass https://apigw_test_apigw_gw_data$uri$is_args$args;' in location_content

    def test_operation_level_servers_single_and_multi_method(self):
        schema = {
            'openapi': '3.0.0',
            'info': {'title': 'Operation Servers API', 'version': '1.0.0'},
            'servers': [{'url': 'https://server1.example.com'}],
            'paths': {
                '/single': {
                    'get': {
                        'summary': 'Single method override',
                        'servers': [{'url': 'https://server2.example.com'}],
                    },
                },
                '/users': {
                    'get': {
                        'summary': 'Read users',
                        'servers': [{'url': 'https://read.example.com/v2'}],
                    },
                    'post': {
                        'summary': 'Write users',
                    },
                },
            },
        }
        decl = _build_test_declaration(schema)
        ctx = ConfigBuildContext(decl, 'v5.7')
        err = build_config_files(ctx)
        assert err is None

        upstreams_file = next(f for f in ctx.configFiles['files'] if 'upstream' in f['name'].lower())
        upstreams_content = base64.b64decode(upstreams_file['contents']).decode()
        assert 'upstream apigw_test_apigw_gw {' in upstreams_content
        assert 'server server1.example.com:443;' in upstreams_content
        assert 'upstream apigw_test_apigw_gw_single_get {' in upstreams_content
        assert 'server server2.example.com:443;' in upstreams_content
        assert 'upstream apigw_test_apigw_gw_users_get {' in upstreams_content
        assert 'server read.example.com:443;' in upstreams_content

        maps_file = next(f for f in ctx.configFiles['files'] if 'maps' in f['name'].lower())
        maps_content = base64.b64decode(maps_file['contents']).decode()
        assert 'map $request_method $apigw_upstream_' in maps_content
        assert '"GET" "apigw_test_apigw_gw_users_get";' in maps_content
        assert '"POST" "apigw_test_apigw_gw";' in maps_content

        location_file = next(
            f for f in ctx.configFiles['files']
            if 'apigateway' in f['name'].lower() and 'upstreams' not in f['name'].lower() and 'maps' not in f['name'].lower()
        )
        location_content = base64.b64decode(location_file['contents']).decode()
        assert 'proxy_pass https://apigw_test_apigw_gw_single_get$uri$is_args$args;' in location_content
        assert 'proxy_pass $apigw_scheme_' in location_content

    def test_relative_server_urls_and_unresolved_variable_error(self):
        schema_rel = {
            'openapi': '3.0.0',
            'info': {'title': 'Relative Servers API', 'version': '1.0.0'},
            'servers': [{'url': '/v1'}],
            'paths': {
                '/ping': {'get': {'summary': 'Ping'}},
                '/dot': {'servers': [{'url': '.'}], 'get': {'summary': 'Dot'}},
            },
        }
        decl = _build_test_declaration(schema_rel, server_url='https://api.example.com')
        ctx = ConfigBuildContext(decl, 'v5.7')
        err = build_config_files(ctx)
        assert err is None

        location_file = next(
            f for f in ctx.configFiles['files']
            if 'apigateway' in f['name'].lower() and 'upstreams' not in f['name'].lower() and 'maps' not in f['name'].lower()
        )
        location_content = base64.b64decode(location_file['contents']).decode()
        assert 'proxy_pass https://apigw_test_apigw_gw/v1$uri$is_args$args;' in location_content
        assert 'proxy_pass https://apigw_test_apigw_gw_dot$uri$is_args$args;' in location_content

        schema_bad = {
            'openapi': '3.0.0',
            'info': {'title': 'Bad Var API', 'version': '1.0.0'},
            'servers': [{'url': 'https://{missing_var}.example.com'}],
            'paths': {'/ping': {'get': {'summary': 'Ping'}}},
        }
        ctx_bad = ConfigBuildContext(_build_test_declaration(schema_bad), 'v5.7')
        err_bad = build_config_files(ctx_bad)
        assert err_bad is not None
        assert err_bad['status_code'] == 422
