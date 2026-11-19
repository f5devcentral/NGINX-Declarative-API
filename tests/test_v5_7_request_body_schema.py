"""Tests for v5.7 API Gateway OpenAPI request body schema enforcement."""

import base64
import copy
import json
import os
import shutil
import subprocess
import sys
import tempfile

import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
SRC_DIR = os.path.join(REPO_ROOT, 'src')
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from NcgConfig import NcgConfig  # noqa: E402
from V5_7_ConfigBuilder import (  # noqa: E402
    ConfigBuildContext,
    _render_main_configs,
    build_config_files,
)
from v5_7.NGINXOneOutput import (  # noqa: E402
    _build_rendered_config_files as n1_build_rendered_config_files,
)
from v5_7.NIMOutput import (  # noqa: E402
    _build_rendered_config_files as nim_build_rendered_config_files,
)
from v5_7.OpenAPIParser import OpenAPIParser  # noqa: E402


@pytest.fixture(autouse=True)
def setup_ncg_config():
    NcgConfig._instance = None
    NcgConfig(os.path.join(REPO_ROOT, 'etc', 'config.yaml'))
    NcgConfig.config['templates']['root_dir'] = os.path.join(REPO_ROOT, 'templates')


def _build_test_declaration(
    openapi_schema: dict,
    server_url: str = 'https://backend.example.com',
    enforce_bodies: bool = True,
    modules=None,
    output_type: str = 'nms',
) -> dict:
    b64_schema = base64.b64encode(json.dumps(openapi_schema).encode('utf-8')).decode('utf-8')
    out_cfg = {'type': output_type}
    if modules is not None:
        out_cfg['nms'] = {'modules': list(modules)}
    return {
        'output': out_cfg,
        'declaration': {
            'http': {
                'servers': [
                    {
                        'name': 'test_apigw',
                        'names': ['test_apigw.example.com'],
                        'resolver': '',
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
                                        'enforce_bodies': enforce_bodies,
                                        'enforce_response_codes': True,
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


def _decode_b64(text: str) -> str:
    return base64.urlsafe_b64decode(text.encode('utf-8')).decode('utf-8')


def _find_file(container: dict, predicate) -> dict:
    return next(f for f in container['files'] if predicate(f))


# ---------------------------------------------------------------------------
# OpenAPIParser requestBodySchemas & schema_defs tests
# ---------------------------------------------------------------------------


class TestOpenAPIParserRequestBodySchemas:
    def test_oas30_inline_and_ref_and_request_body_ref(self):
        doc = {
            'openapi': '3.0.3',
            'components': {
                'schemas': {
                    'Address': {
                        'type': 'object',
                        'required': ['city'],
                        'properties': {'city': {'type': 'string'}},
                    },
                    'User': {
                        'type': 'object',
                        'required': ['name'],
                        'properties': {
                            'name': {'type': 'string'},
                            'address': {'$ref': '#/components/schemas/Address'},
                        },
                    },
                },
                'requestBodies': {
                    'UserBody': {
                        'required': True,
                        'content': {
                            'application/json': {
                                'schema': {'$ref': '#/components/schemas/User'}
                            }
                        },
                    }
                },
            },
            'paths': {
                '/users': {
                    'post': {
                        'requestBody': {'$ref': '#/components/requestBodies/UserBody'},
                        'responses': {'201': {'description': 'Created'}},
                    }
                },
                '/items': {
                    'put': {
                        'requestBody': {
                            'required': False,
                            'content': {
                                'application/json': {
                                    'schema': {
                                        'type': 'object',
                                        'properties': {'qty': {'type': 'integer'}},
                                    }
                                }
                            },
                        },
                        'responses': {'200': {'description': 'OK'}},
                    }
                },
                '/health': {
                    'get': {'responses': {'200': {'description': 'OK'}}}
                },
            },
        }

        parser = OpenAPIParser(doc)
        parsed_paths = parser.paths()
        by_path = {p['path']: p for p in parsed_paths}

        post_details = by_path['/users']['methods'][0]['details']
        assert post_details['requestBodyRequired'] is True
        assert post_details['requestBodyContentType'] == ['application/json']
        assert post_details['requestBodySchemas'] == {
            'application/json': {'$ref': '#/components/schemas/User'}
        }

        put_details = by_path['/items']['methods'][0]['details']
        assert put_details['requestBodyRequired'] is False
        assert put_details['requestBodySchemas']['application/json']['type'] == 'object'

        get_details = by_path['/health']['methods'][0]['details']
        assert get_details['requestBodySchemas'] == {}

        schema_defs = parser.request_body_schema_defs(parsed_paths)
        assert '#/components/schemas/User' in schema_defs
        assert '#/components/schemas/Address' in schema_defs
        assert schema_defs['#/components/schemas/Address']['required'] == ['city']

    def test_oas31_defs_boolean_schemas_type_array_and_cyclic_ref(self):
        doc = {
            'openapi': '3.1.0',
            '$defs': {
                'Node': {
                    'type': 'object',
                    'required': ['id'],
                    'properties': {
                        'id': {'type': ['string', 'integer']},
                        'next': {'$ref': '#/$defs/Node'},
                    },
                    'additionalProperties': False,
                }
            },
            'paths': {
                '/tree': {
                    'post': {
                        'requestBody': {
                            'required': True,
                            'content': {
                                'application/json': {
                                    'schema': {
                                        'type': 'object',
                                        'properties': {
                                            'root': {'$ref': '#/$defs/Node'},
                                            'tuple': {
                                                'type': 'array',
                                                'prefixItems': [
                                                    {'type': 'string'},
                                                    {'type': 'number'},
                                                ],
                                                'items': False,
                                            },
                                        },
                                    }
                                }
                            },
                        },
                        'responses': {'200': {'description': 'OK'}},
                    }
                }
            },
        }

        parser = OpenAPIParser(doc)
        parsed_paths = parser.paths()
        schema_defs = parser.request_body_schema_defs(parsed_paths)

        assert '#/$defs/Node' in schema_defs
        assert parsed_paths[0]['methods'][0]['details']['requestBodySchemas']['application/json']['properties']['tuple']['items'] is False

    def test_swagger2_body_parameter_consumes_and_unresolved_ref(self):
        doc = {
            'swagger': '2.0',
            'host': 'api.example.com',
            'basePath': '/v2',
            'consumes': ['application/json'],
            'definitions': {
                'Order': {
                    'type': 'object',
                    'required': ['sku'],
                    'properties': {'sku': {'type': 'string'}},
                }
            },
            'paths': {
                '/orders': {
                    'post': {
                        'parameters': [
                            {
                                'name': 'body',
                                'in': 'body',
                                'required': True,
                                'schema': {'$ref': '#/definitions/Order'},
                            }
                        ],
                        'responses': {'200': {'description': 'OK'}},
                    }
                },
                '/wild': {
                    'post': {
                        'consumes': [],
                        'parameters': [
                            {
                                'name': 'body',
                                'in': 'body',
                                'required': True,
                                'schema': {'type': 'object', 'required': ['x']},
                            }
                        ],
                        'responses': {'200': {'description': 'OK'}},
                    }
                },
                '/dangling': {
                    'post': {
                        'parameters': [
                            {
                                'name': 'body',
                                'in': 'body',
                                'required': True,
                                'schema': {'$ref': '#/definitions/DoesNotExist'},
                            }
                        ],
                        'responses': {'200': {'description': 'OK'}},
                    }
                },
            },
        }

        parser = OpenAPIParser(doc)
        parsed_paths = parser.paths()
        by_path = {p['path']: p for p in parsed_paths}

        orders_details = by_path['/orders']['methods'][0]['details']
        assert orders_details['requestBodySchemas'] == {
            'application/json': {'$ref': '#/definitions/Order'}
        }

        # Wild path inherits root consumes ['application/json'] in _effective_consumes if empty?
        # Ensure at least fallback '*/*' or inherited consumes holds the schema safely.
        wild_details = by_path['/wild']['methods'][0]['details']
        assert wild_details['requestBodySchemas']

        # Dangling $ref is skipped cleanly rather than emitting broken rules
        dangling_details = by_path['/dangling']['methods'][0]['details']
        assert dangling_details['requestBodySchemas'] == {}

        # Swagger 2.0 with omitted consumes anywhere defaults to */*
        no_consumes_doc = {
            'swagger': '2.0',
            'paths': {
                '/any': {
                    'post': {
                        'parameters': [
                            {
                                'name': 'body',
                                'in': 'body',
                                'required': True,
                                'schema': {'type': 'object', 'properties': {'a': {'type': 'string'}}},
                            }
                        ],
                        'responses': {'200': {'description': 'OK'}},
                    }
                }
            },
        }
        p2 = OpenAPIParser(no_consumes_doc)
        assert p2.paths()[0]['methods'][0]['details']['requestBodySchemas'] == {
            '*/*': {'type': 'object', 'properties': {'a': {'type': 'string'}}}
        }


# ---------------------------------------------------------------------------
# ConfigBuilder + Template + Output tests
# ---------------------------------------------------------------------------


class TestConfigRenderingAndModuleWiring:
    def _sample_oas(self) -> dict:
        return {
            'openapi': '3.0.3',
            'components': {
                'schemas': {
                    'Pet': {
                        'type': 'object',
                        'required': ['name', 'age'],
                        'properties': {
                            'name': {'type': 'string', 'minLength': 2},
                            'age': {'type': 'integer', 'minimum': 0},
                        },
                        'additionalProperties': False,
                    }
                }
            },
            'paths': {
                '/pets': {
                    'get': {'responses': {'200': {'description': 'OK'}}},
                    'post': {
                        'requestBody': {
                            'required': True,
                            'content': {
                                'application/json': {
                                    'schema': {'$ref': '#/components/schemas/Pet'}
                                }
                            },
                        },
                        'responses': {'201': {'description': 'Created'}},
                    },
                },
                '/ping': {
                    'get': {'responses': {'200': {'description': 'Pong'}}}
                },
            },
        }

    def test_end_to_end_nginx_configs_and_js_rendered(self):
        decl = _build_test_declaration(self._sample_oas(), enforce_bodies=True, modules=[])
        ctx = ConfigBuildContext(decl, 'v5.7')
        err = build_config_files(ctx)
        assert err is None

        b64_http, b64_stream = _render_main_configs(ctx)
        http_conf = _decode_b64(b64_http)

        # NJS module generated in auxFiles
        njs_file = _find_file(ctx.auxFiles, lambda f: f['name'].startswith('/etc/nginx/njs/apigw_body_'))
        njs_src = _decode_b64(njs_file['contents'])
        assert 'export default {' in njs_src
        assert 'validate_req_body_0_pets' in njs_src
        assert '"#/components/schemas/Pet"' in njs_src

        # http.conf declares js_path / js_import
        assert 'js_path "/etc/nginx/njs";' in http_conf
        assert 'js_import apigw_body_test_apigw_example_com_gw from apigw_body_test_apigw_example_com_gw.js;' in http_conf

        # Server block includes _proxy*.conf at server {} level
        server_conf = _decode_b64(
            _find_file(ctx.configFiles, lambda f: f['name'] == '/etc/nginx/servers/http/test_apigw.conf')['contents']
        )
        assert 'include "/etc/nginx/apigateway/test_apigw.example.com/gw_proxy*.conf";' in server_conf

        # Main apigateway location conf uses js_content for /pets and direct proxy_pass for /ping
        apigw_conf = _decode_b64(
            _find_file(
                ctx.configFiles,
                lambda f: '/etc/nginx/apigateway/' in f['name'] and '_proxy' not in f['name'],
            )['contents']
        )
        assert 'client_body_in_single_buffer on;' in apigw_conf
        assert 'js_content apigw_body_test_apigw_example_com_gw.validate_req_body_0_pets;' in apigw_conf
        assert 'location = /gw/ping {' in apigw_conf

        # Server-level named internal proxy location rendered in _proxy.conf
        proxy_conf = _decode_b64(
            _find_file(ctx.configFiles, lambda f: f['name'].endswith('_proxy.conf'))['contents']
        )
        assert 'location @apigw_proxy_test_apigw_example_com_gw_0_pets {' in proxy_conf
        assert 'rewrite ^/gw/(.*)$ /$1 break;' in proxy_conf
        assert 'proxy_intercept_errors on;' in proxy_conf
        assert 'proxy_pass https://apigw_test_apigw_gw$uri$is_args$args;' in proxy_conf

        # Both NIMOutput and NGINXOneOutput auto-inject ngx_http_js_module without duplicating
        for builder in (nim_build_rendered_config_files, n1_build_rendered_config_files):
            err_out, _, staged = builder(
                copy.deepcopy(decl),
                'v5.7',
                b64_http,
                b64_stream,
                copy.deepcopy(ctx.configFiles),
                copy.deepcopy(ctx.auxFiles),
            )
            assert err_out is None
            cfg_container = staged['configFiles'] if 'configFiles' in staged else staged['configs'][0]
            nginx_conf = _decode_b64(
                _find_file(cfg_container, lambda f: f['name'].endswith('/nginx.conf'))['contents']
            )
            assert nginx_conf.count('load_module modules/ngx_http_js_module.so;') == 1

            # Already specified -> no duplicate
            decl_with_mod = _build_test_declaration(
                self._sample_oas(),
                enforce_bodies=True,
                modules=['ngx_http_js_module'],
            )
            err_out2, _, staged2 = builder(
                decl_with_mod,
                'v5.7',
                b64_http,
                b64_stream,
                copy.deepcopy(ctx.configFiles),
                copy.deepcopy(ctx.auxFiles),
            )
            assert err_out2 is None
            cfg_container2 = staged2['configFiles'] if 'configFiles' in staged2 else staged2['configs'][0]
            nginx_conf2 = _decode_b64(
                _find_file(cfg_container2, lambda f: f['name'].endswith('/nginx.conf'))['contents']
            )
            assert nginx_conf2.count('load_module modules/ngx_http_js_module.so;') == 1

    def test_enforce_bodies_false_skips_njs_validation(self):
        decl = _build_test_declaration(self._sample_oas(), enforce_bodies=False, modules=[])
        ctx = ConfigBuildContext(decl, 'v5.7')
        err = build_config_files(ctx)
        assert err is None

        b64_http, b64_stream = _render_main_configs(ctx)
        http_conf = _decode_b64(b64_http)

        server_conf = _decode_b64(
            _find_file(ctx.configFiles, lambda f: f['name'] == '/etc/nginx/servers/http/test_apigw.conf')['contents']
        )

        assert not any('apigw_body_' in f['name'] for f in ctx.auxFiles['files'])
        assert not any('_proxy.conf' in f['name'] for f in ctx.configFiles['files'])
        assert 'js_import' not in http_conf
        assert '_proxy*.conf' not in server_conf

        _, _, staged = nim_build_rendered_config_files(
            decl, 'v5.7', b64_http, b64_stream, ctx.configFiles, ctx.auxFiles
        )
        nginx_conf = _decode_b64(
            _find_file(staged['configFiles'], lambda f: f['name'].endswith('/nginx.conf'))['contents']
        )
        assert 'ngx_http_js_module' not in nginx_conf


# ---------------------------------------------------------------------------
# Node.js runtime execution of rendered njs schema validator
# ---------------------------------------------------------------------------


def _run_validator_cases(openapi_schema: dict, cases: list) -> list:
    """Renders the njs validator via ConfigBuilder and executes cases under Node."""
    node_bin = shutil.which('node')
    if not node_bin:
        pytest.skip('node binary not available in PATH')

    decl = _build_test_declaration(openapi_schema, enforce_bodies=True)
    ctx = ConfigBuildContext(decl, 'v5.7')
    err = build_config_files(ctx)
    assert err is None

    njs_file = _find_file(ctx.auxFiles, lambda f: f['name'].startswith('/etc/nginx/njs/apigw_body_'))
    njs_src = _decode_b64(njs_file['contents'])

    runner_js = f"""
import mod from './validator.mjs';

const validator = mod.default || mod;
const cases = {json.dumps(cases)};
const results = [];

for (const tc of cases) {{
  const res = {{ name: tc.name, status: null, body: null, redirect: null, headersOut: {{}} }};
  const r = {{
    method: tc.method || 'POST',
    headersIn: tc.headers || {{}},
    requestText: tc.body !== undefined ? tc.body : '',
    variables: {{}},
    headersOut: res.headersOut,
    return(code, body) {{
      res.status = code;
      res.body = body || null;
    }},
    internalRedirect(loc) {{
      res.redirect = loc;
    }},
  }};
  const fn = validator[tc.func || 'validate_req_body_0_test'];
  if (typeof fn !== 'function') {{
    throw new Error('Missing validator function: ' + (tc.func || 'validate_req_body_0_test'));
  }}
  fn(r);
  results.push(res);
}}

process.stdout.write(JSON.stringify(results));
"""
    with tempfile.TemporaryDirectory() as tmpdir:
        validator_path = os.path.join(tmpdir, 'validator.mjs')
        runner_path = os.path.join(tmpdir, 'runner.mjs')
        with open(validator_path, 'w', encoding='utf-8') as f:
            f.write(njs_src)
        with open(runner_path, 'w', encoding='utf-8') as f:
            f.write(runner_js)
        proc = subprocess.run(
            [node_bin, runner_path],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
    assert proc.returncode == 0, f'Node failed:\nSTDOUT: {proc.stdout}\nSTDERR: {proc.stderr}'
    return json.loads(proc.stdout)


class TestRenderedValidatorRuntime:
    def test_comprehensive_json_schema_and_oas_keywords(self):
        schema_doc = {
            'openapi': '3.1.0',
            'components': {
                'schemas': {
                    'TreeNode': {
                        'type': 'object',
                        'required': ['value'],
                        'properties': {
                            'value': {'type': 'integer', 'minimum': 1},
                            'child': {'$ref': '#/components/schemas/TreeNode'},
                        },
                        'additionalProperties': False,
                    }
                }
            },
            'paths': {
                '/complex': {
                    'get': {'responses': {'200': {'description': 'OK'}}},
                    'post': {
                        'requestBody': {
                            'required': True,
                            'content': {
                                'application/json': {
                                    'schema': {
                                        'type': 'object',
                                        'required': ['id', 'serverId', 'name', 'score', 'tags', 'kind'],
                                        'properties': {
                                            'id': {'type': 'string', 'format': 'uuid'},
                                            # readOnly must NOT be required in request bodies per OAS
                                            'serverId': {'type': 'string', 'readOnly': True},
                                            'name': {'type': 'string', 'minLength': 2, 'maxLength': 10, 'pattern': '^[A-Za-z0-9_]+$'},
                                            'nick': {'type': 'string', 'nullable': True},
                                            'email': {'type': 'string', 'format': 'email'},
                                            'createdDate': {'type': 'string', 'format': 'date'},
                                            'createdAt': {'type': 'string', 'format': 'date-time'},
                                            'ip4': {'type': 'string', 'format': 'ipv4'},
                                            'ip6': {'type': 'string', 'format': 'ipv6'},
                                            'homepage': {'type': 'string', 'format': 'uri'},
                                            'score': {
                                                'type': 'number',
                                                'exclusiveMinimum': 0,
                                                'maximum': 10,
                                                'multipleOf': 0.1,
                                            },
                                            'tags': {
                                                'type': 'array',
                                                'items': {'type': 'string'},
                                                'minItems': 1,
                                                'maxItems': 3,
                                                'uniqueItems': True,
                                            },
                                            'tuple': {
                                                'type': 'array',
                                                'prefixItems': [
                                                    {'type': 'string'},
                                                    {'type': 'integer'},
                                                ],
                                                'items': False,
                                            },
                                            'kind': {'enum': ['A', 'B']},
                                            'version': {'const': 2},
                                            'tree': {'$ref': '#/components/schemas/TreeNode'},
                                            'choice': {
                                                'oneOf': [
                                                    {'type': 'object', 'required': ['a'], 'properties': {'a': {'type': 'string'}}},
                                                    {'type': 'object', 'required': ['b'], 'properties': {'b': {'type': 'integer'}}},
                                                ]
                                            },
                                            'country': {'type': 'string'},
                                            'postalCode': {'type': 'string'},
                                        },
                                        'patternProperties': {
                                            '^x-': {'type': 'string'}
                                        },
                                        'additionalProperties': False,
                                        'propertyNames': {'pattern': '^[a-zA-Z0-9_-]+$'},
                                        'dependentRequired': {
                                            'postalCode': ['country']
                                        },
                                        'if': {
                                            'properties': {'country': {'const': 'US'}},
                                            'required': ['country'],
                                        },
                                        'then': {
                                            'required': ['postalCode'],
                                        },
                                    }
                                },
                                '*+json': {
                                    'schema': {
                                        'type': 'object',
                                        'required': ['title'],
                                        'properties': {'title': {'type': 'string'}},
                                    }
                                },
                            },
                        },
                        'responses': {'200': {'description': 'OK'}},
                    },
                },
                '/optional': {
                    'post': {
                        'requestBody': {
                            'required': False,
                            'content': {
                                'application/json': {
                                    'schema': {
                                        'type': 'object',
                                        'required': ['flag'],
                                        'properties': {'flag': {'type': 'boolean'}},
                                    }
                                }
                            },
                        },
                        'responses': {'200': {'description': 'OK'}},
                    }
                },
                '/form-and-text': {
                    'post': {
                        'requestBody': {
                            'required': True,
                            'content': {
                                'application/x-www-form-urlencoded': {
                                    'schema': {
                                        'type': 'object',
                                        'required': ['count', 'active'],
                                        'properties': {
                                            'count': {'type': 'integer', 'minimum': 1},
                                            'active': {'type': 'boolean'},
                                        },
                                    }
                                },
                                'text/plain': {
                                    'schema': {'type': 'string', 'minLength': 3, 'pattern': '^hi'}
                                },
                            },
                        },
                        'responses': {'200': {'description': 'OK'}},
                    }
                },
            },
        }

        valid_payload = {
            'id': '550e8400-e29b-41d4-a716-446655440000',
            'name': 'Alice_1',
            'nick': None,
            'email': 'alice@example.com',
            'createdDate': '2026-05-01',
            'createdAt': '2026-05-01T12:30:00Z',
            'ip4': '192.168.1.10',
            'ip6': '2001:db8::1',
            'homepage': 'https://example.com/docs',
            'score': 0.3,
            'tags': ['alpha', 'beta'],
            'tuple': ['ok', 42],
            'kind': 'A',
            'version': 2,
            'tree': {'value': 1, 'child': {'value': 2}},
            'choice': {'a': 'yes'},
            'country': 'US',
            'postalCode': '94105',
            'x-trace': 'abc',
        }

        def _mut(**updates):
            d = copy.deepcopy(valid_payload)
            for k, v in updates.items():
                if v is None and k in d and k != 'nick':
                    del d[k]
                else:
                    d[k] = v
            return json.dumps(d)

        cases = [
            {
                'name': 'get_passes_through_to_internal_redirect',
                'func': 'validate_req_body_0_complex',
                'method': 'GET',
                'headers': {},
                'body': '',
            },
            {
                'name': 'valid_complex_json_with_charset',
                'func': 'validate_req_body_0_complex',
                'method': 'POST',
                'headers': {'Content-Type': 'application/json; charset=utf-8'},
                'body': json.dumps(valid_payload),
            },
            {
                'name': 'required_missing_fails',
                'func': 'validate_req_body_0_complex',
                'method': 'POST',
                'headers': {'Content-Type': 'application/json'},
                'body': _mut(name=None),
            },
            {
                'name': 'bad_uuid_format_fails',
                'func': 'validate_req_body_0_complex',
                'method': 'POST',
                'headers': {'Content-Type': 'application/json'},
                'body': _mut(id='not-a-uuid'),
            },
            {
                'name': 'exclusive_minimum_zero_fails',
                'func': 'validate_req_body_0_complex',
                'method': 'POST',
                'headers': {'Content-Type': 'application/json'},
                'body': _mut(score=0),
            },
            {
                'name': 'multiple_of_mismatch_fails',
                'func': 'validate_req_body_0_complex',
                'method': 'POST',
                'headers': {'Content-Type': 'application/json'},
                'body': _mut(score=0.35),
            },
            {
                'name': 'unique_items_violation_fails',
                'func': 'validate_req_body_0_complex',
                'method': 'POST',
                'headers': {'Content-Type': 'application/json'},
                'body': _mut(tags=['dup', 'dup']),
            },
            {
                'name': 'tuple_extra_item_fails',
                'func': 'validate_req_body_0_complex',
                'method': 'POST',
                'headers': {'Content-Type': 'application/json'},
                'body': _mut(tuple=['ok', 42, 'extra']),
            },
            {
                'name': 'oneof_both_matched_fails',
                'func': 'validate_req_body_0_complex',
                'method': 'POST',
                'headers': {'Content-Type': 'application/json'},
                'body': _mut(choice={'a': 'x', 'b': 1}),
            },
            {
                'name': 'cyclic_ref_nested_invalid_fails',
                'func': 'validate_req_body_0_complex',
                'method': 'POST',
                'headers': {'Content-Type': 'application/json'},
                'body': _mut(tree={'value': 1, 'child': {'value': 0}}),
            },
            {
                'name': 'additional_property_rejected',
                'func': 'validate_req_body_0_complex',
                'method': 'POST',
                'headers': {'Content-Type': 'application/json'},
                'body': _mut(unexpected='nope'),
            },
            {
                'name': 'if_then_country_us_requires_postal',
                'func': 'validate_req_body_0_complex',
                'method': 'POST',
                'headers': {'Content-Type': 'application/json'},
                'body': _mut(postalCode=None),
            },
            {
                'name': 'malformed_json_fails_400',
                'func': 'validate_req_body_0_complex',
                'method': 'POST',
                'headers': {'Content-Type': 'application/json'},
                'body': '{"broken": ',
            },
            {
                'name': 'empty_required_body_fails_400',
                'func': 'validate_req_body_0_complex',
                'method': 'POST',
                'headers': {'Content-Type': 'application/json'},
                'body': '',
            },
            {
                'name': 'structured_suffix_plus_json_valid',
                'func': 'validate_req_body_0_complex',
                'method': 'POST',
                'headers': {'Content-Type': 'application/problem+json'},
                'body': json.dumps({'title': 'Bad Gateway'}),
            },
            {
                'name': 'structured_suffix_plus_json_invalid',
                'func': 'validate_req_body_0_complex',
                'method': 'POST',
                'headers': {'Content-Type': 'application/problem+json'},
                'body': json.dumps({'detail': 'missing title'}),
            },
            {
                'name': 'optional_empty_body_passes',
                'func': 'validate_req_body_1_optional',
                'method': 'POST',
                'headers': {'Content-Type': 'application/json'},
                'body': '',
            },
            {
                'name': 'optional_nonempty_invalid_body_fails',
                'func': 'validate_req_body_1_optional',
                'method': 'POST',
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'flag': 'not-bool'}),
            },
            {
                'name': 'form_urlencoded_valid_coerced',
                'func': 'validate_req_body_2_form_and_text',
                'method': 'POST',
                'headers': {'Content-Type': 'application/x-www-form-urlencoded'},
                'body': 'count=5&active=true',
            },
            {
                'name': 'form_urlencoded_invalid_integer_fails',
                'func': 'validate_req_body_2_form_and_text',
                'method': 'POST',
                'headers': {'Content-Type': 'application/x-www-form-urlencoded'},
                'body': 'count=0&active=true',
            },
            {
                'name': 'text_plain_valid',
                'func': 'validate_req_body_2_form_and_text',
                'method': 'POST',
                'headers': {'Content-Type': 'text/plain'},
                'body': 'hi there',
            },
            {
                'name': 'text_plain_pattern_fails',
                'func': 'validate_req_body_2_form_and_text',
                'method': 'POST',
                'headers': {'Content-Type': 'text/plain'},
                'body': 'bye there',
            },
        ]

        results = {r['name']: r for r in _run_validator_cases(schema_doc, cases)}

        expected_pass = [
            'get_passes_through_to_internal_redirect',
            'valid_complex_json_with_charset',
            'structured_suffix_plus_json_valid',
            'optional_empty_body_passes',
            'form_urlencoded_valid_coerced',
            'text_plain_valid',
        ]
        for name in expected_pass:
            assert results[name]['status'] is None, f"{name} unexpectedly failed: {results[name]}"
            assert results[name]['redirect'].startswith('@apigw_proxy_'), name

        for tc in cases:
            if tc['name'] not in expected_pass:
                assert results[tc['name']]['status'] == 400, f"{tc['name']} unexpectedly passed: {results[tc['name']]}"
                assert results[tc['name']]['redirect'] is None, tc['name']
                assert results[tc['name']]['headersOut'].get('Content-Type') == 'application/json'
                err_payload = json.loads(results[tc['name']]['body'])
                assert err_payload['code'] == 400
                assert isinstance(err_payload['message'], str) and len(err_payload['message']) > 0
