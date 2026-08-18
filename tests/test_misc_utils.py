"""
Tests for v5_5/MiscUtils.py and v5_6/MiscUtils.py

Covers pure utility functions that have no external service dependencies.
"""
import io
import base64
import json
import uuid
import pytest

import v5_5.MiscUtils as utils_v55
import v5_6.MiscUtils as utils_v56


# ---------------------------------------------------------------------------
# getDictKey
# ---------------------------------------------------------------------------

class TestGetDictKey:
    def test_top_level_key(self):
        d = {'a': 1}
        assert utils_v55.getDictKey(d, 'a') == 1

    def test_nested_key(self):
        d = {'a': {'b': {'c': 42}}}
        assert utils_v55.getDictKey(d, 'a.b.c') == 42

    def test_missing_key_returns_none(self):
        d = {'a': {'b': 1}}
        assert utils_v55.getDictKey(d, 'a.x') is None

    def test_missing_top_level_returns_none(self):
        d = {'a': 1}
        assert utils_v55.getDictKey(d, 'z') is None

    def test_custom_separator(self):
        d = {'a': {'b': 99}}
        assert utils_v55.getDictKey(d, 'a/b', separator='/') == 99

    def test_empty_dict(self):
        assert utils_v55.getDictKey({}, 'a.b') is None

    # v5_6 has the same implementation
    def test_v56_nested_key(self):
        d = {'x': {'y': 'hello'}}
        assert utils_v56.getDictKey(d, 'x.y') == 'hello'


# ---------------------------------------------------------------------------
# regex_replace
# ---------------------------------------------------------------------------

class TestRegexReplace:
    def test_simple_replace(self):
        assert utils_v55.regex_replace('hello world', r'world', 'there') == 'hello there'

    def test_pattern_replace(self):
        assert utils_v55.regex_replace('abc123def', r'\d+', 'NUM') == 'abcNUMdef'

    def test_no_match(self):
        assert utils_v55.regex_replace('hello', r'xyz', 'ABC') == 'hello'

    def test_replace_all_occurrences(self):
        result = utils_v55.regex_replace('aXbXcX', r'X', '-')
        assert result == 'a-b-c-'

    def test_v56_regex_replace(self):
        assert utils_v56.regex_replace('foo bar', r'\s', '_') == 'foo_bar'


# ---------------------------------------------------------------------------
# yaml_or_json  (accepts a file-like object due to json.load usage)
# ---------------------------------------------------------------------------

class TestYamlOrJson:
    def test_detects_json(self):
        doc = io.StringIO('{"key": "value"}')
        assert utils_v55.yaml_or_json(doc) == 'json'

    def test_detects_yaml(self):
        doc = io.StringIO('key: value\n')
        assert utils_v55.yaml_or_json(doc) == 'yaml'

    def test_empty_object_json(self):
        doc = io.StringIO('{}')
        assert utils_v55.yaml_or_json(doc) == 'json'

    def test_v56_detects_json(self):
        doc = io.StringIO('{"a": 1}')
        assert utils_v56.yaml_or_json(doc) == 'json'

    def test_v56_detects_yaml(self):
        doc = io.StringIO('a: 1\n')
        assert utils_v56.yaml_or_json(doc) == 'yaml'


# ---------------------------------------------------------------------------
# yaml_to_json
# ---------------------------------------------------------------------------

class TestYamlToJson:
    def test_simple_mapping(self):
        yaml_input = 'name: nginx\nversion: "1.0"'
        result = json.loads(utils_v55.yaml_to_json(yaml_input))
        assert result['name'] == 'nginx'
        assert result['version'] == '1.0'

    def test_nested_mapping(self):
        yaml_input = 'outer:\n  inner: value'
        result = json.loads(utils_v55.yaml_to_json(yaml_input))
        assert result['outer']['inner'] == 'value'

    def test_list(self):
        yaml_input = 'items:\n  - one\n  - two'
        result = json.loads(utils_v55.yaml_to_json(yaml_input))
        assert result['items'] == ['one', 'two']

    def test_v56_yaml_to_json(self):
        result = json.loads(utils_v56.yaml_to_json('key: val'))
        assert result['key'] == 'val'


# ---------------------------------------------------------------------------
# json_to_yaml
# ---------------------------------------------------------------------------

class TestJsonToYaml:
    def test_simple_object(self):
        import yaml
        result = utils_v55.json_to_yaml('{"name": "nginx"}')
        parsed = yaml.safe_load(result)
        assert parsed['name'] == 'nginx'

    def test_nested_object(self):
        import yaml
        result = utils_v55.json_to_yaml('{"a": {"b": 1}}')
        parsed = yaml.safe_load(result)
        assert parsed['a']['b'] == 1

    def test_v56_json_to_yaml(self):
        import yaml
        result = utils_v56.json_to_yaml('{"x": "y"}')
        parsed = yaml.safe_load(result)
        assert parsed['x'] == 'y'


# ---------------------------------------------------------------------------
# getuniqueid
# ---------------------------------------------------------------------------

class TestGetUniqueId:
    def test_returns_uuid(self):
        result = utils_v55.getuniqueid()
        # Should be a valid UUID
        assert isinstance(result, uuid.UUID)

    def test_returns_unique_values(self):
        ids = {utils_v55.getuniqueid() for _ in range(100)}
        assert len(ids) == 100

    def test_v56_returns_uuid(self):
        result = utils_v56.getuniqueid()
        assert isinstance(result, uuid.UUID)


# ---------------------------------------------------------------------------
# resolveFQDN
# ---------------------------------------------------------------------------

class TestResolveFQDN:
    def test_invalid_fqdn_returns_false(self):
        ok, _ = utils_v55.resolveFQDN('this.domain.does.not.exist.invalid')
        assert ok is False

    def test_v56_invalid_fqdn(self):
        ok, _ = utils_v56.resolveFQDN('this.domain.does.not.exist.invalid')
        assert ok is False


# ---------------------------------------------------------------------------
# isBase64  (v5_5 only)
# ---------------------------------------------------------------------------

class TestIsBase64:
    def test_valid_base64(self):
        encoded = base64.b64encode(b'hello world').decode('utf-8')
        assert utils_v55.isBase64(encoded) is True

    def test_not_base64(self):
        assert utils_v55.isBase64('this is not base64!!!') is False

    def test_empty_string(self):
        # base64.b64encode(b'') == b'' and base64.b64decode(b'') == b''
        # bytes('', 'utf-8') == b'' so empty string is technically valid base64
        assert utils_v55.isBase64('') is True

    def test_json_string_not_base64(self):
        assert utils_v55.isBase64('{"key": "value"}') is False
