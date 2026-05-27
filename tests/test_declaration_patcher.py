"""
Tests for v5_5/DeclarationPatcher.py and v5_4/DeclarationPatcher.py

Each patcher function follows a consistent contract:
  - add:    name not yet present → appended
  - update: name already present, len > 1 → replaced
  - delete: name already present, len == 1 (name-only dict) → removed
"""
import copy
import pytest

import v5_5.DeclarationPatcher as patcher_v55
import v5_4.DeclarationPatcher as patcher_v54


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _decl_with_http_servers(*servers):
    return {'declaration': {'http': {'servers': list(servers)}}}

def _decl_with_http_upstreams(*upstreams):
    return {'declaration': {'http': {'upstreams': list(upstreams)}}}

def _decl_with_layer4_servers(*servers):
    return {'declaration': {'layer4': {'servers': list(servers)}}}

def _decl_with_layer4_upstreams(*upstreams):
    return {'declaration': {'layer4': {'upstreams': list(upstreams)}}}

def _decl_with_nms_policies(*policies):
    return {'output': {'nms': {'policies': list(policies)}}}

def _decl_with_nms_certificates(*certs):
    return {'output': {'nms': {'certificates': list(certs)}}}


# ---------------------------------------------------------------------------
# patchHttpServer
# ---------------------------------------------------------------------------

class TestPatchHttpServer:
    def test_add_to_empty_declaration(self):
        result = patcher_v55.patchHttpServer({}, {'name': 'srv1', 'listen': '80'})
        assert len(result['declaration']['http']['servers']) == 1
        assert result['declaration']['http']['servers'][0]['name'] == 'srv1'

    def test_add_new_server(self):
        decl = _decl_with_http_servers({'name': 'existing', 'listen': '80'})
        result = patcher_v55.patchHttpServer(decl, {'name': 'new', 'listen': '443'})
        names = [s['name'] for s in result['declaration']['http']['servers']]
        assert 'existing' in names
        assert 'new' in names

    def test_update_existing_server(self):
        decl = _decl_with_http_servers({'name': 'srv1', 'listen': '80'})
        result = patcher_v55.patchHttpServer(decl, {'name': 'srv1', 'listen': '443'})
        servers = result['declaration']['http']['servers']
        assert len(servers) == 1
        assert servers[0]['listen'] == '443'

    def test_delete_server_by_name_only(self):
        decl = _decl_with_http_servers({'name': 'srv1', 'listen': '80'}, {'name': 'srv2', 'listen': '443'})
        result = patcher_v55.patchHttpServer(decl, {'name': 'srv1'})
        names = [s['name'] for s in result['declaration']['http']['servers']]
        assert 'srv1' not in names
        assert 'srv2' in names

    def test_v54_add_server(self):
        result = patcher_v54.patchHttpServer({}, {'name': 'srv1', 'listen': '80'})
        assert result['declaration']['http']['servers'][0]['name'] == 'srv1'


class TestPatchHttpUpstream:
    def test_add_upstream(self):
        result = patcher_v55.patchHttpUpstream({}, {'name': 'up1', 'origin': []})
        assert result['declaration']['http']['upstreams'][0]['name'] == 'up1'

    def test_update_upstream(self):
        decl = _decl_with_http_upstreams({'name': 'up1', 'origin': ['10.0.0.1']})
        result = patcher_v55.patchHttpUpstream(decl, {'name': 'up1', 'origin': ['10.0.0.2']})
        assert result['declaration']['http']['upstreams'][0]['origin'] == ['10.0.0.2']

    def test_delete_upstream(self):
        decl = _decl_with_http_upstreams({'name': 'up1', 'origin': []}, {'name': 'up2', 'origin': []})
        result = patcher_v55.patchHttpUpstream(decl, {'name': 'up1'})
        names = [u['name'] for u in result['declaration']['http']['upstreams']]
        assert 'up1' not in names
        assert 'up2' in names

    def test_v54_add_upstream(self):
        result = patcher_v54.patchHttpUpstream({}, {'name': 'up1', 'origin': []})
        assert result['declaration']['http']['upstreams'][0]['name'] == 'up1'


# ---------------------------------------------------------------------------
# patchStreamServer (layer4)
# ---------------------------------------------------------------------------

class TestPatchStreamServer:
    def test_add_to_empty(self):
        result = patcher_v55.patchStreamServer({}, {'name': 'l4srv', 'listen': '3306'})
        assert result['declaration']['layer4']['servers'][0]['name'] == 'l4srv'

    def test_add_new_server(self):
        decl = _decl_with_layer4_servers({'name': 'existing', 'listen': '3306'})
        result = patcher_v55.patchStreamServer(decl, {'name': 'new', 'listen': '5432'})
        names = [s['name'] for s in result['declaration']['layer4']['servers']]
        assert set(names) == {'existing', 'new'}

    def test_update_server(self):
        decl = _decl_with_layer4_servers({'name': 'srv', 'listen': '3306'})
        result = patcher_v55.patchStreamServer(decl, {'name': 'srv', 'listen': '5432'})
        assert result['declaration']['layer4']['servers'][0]['listen'] == '5432'

    def test_delete_server(self):
        decl = _decl_with_layer4_servers({'name': 'srv1', 'listen': '3306'}, {'name': 'srv2', 'listen': '5432'})
        result = patcher_v55.patchStreamServer(decl, {'name': 'srv1'})
        names = [s['name'] for s in result['declaration']['layer4']['servers']]
        assert 'srv1' not in names
        assert 'srv2' in names

    def test_v54_add_server(self):
        result = patcher_v54.patchStreamServer({}, {'name': 'l4srv', 'listen': '3306'})
        assert result['declaration']['layer4']['servers'][0]['name'] == 'l4srv'


class TestPatchStreamUpstream:
    def test_add_upstream(self):
        result = patcher_v55.patchStreamUpstream({}, {'name': 'l4up', 'origin': []})
        assert result['declaration']['layer4']['upstreams'][0]['name'] == 'l4up'

    def test_update_upstream(self):
        decl = _decl_with_layer4_upstreams({'name': 'l4up', 'origin': ['10.0.0.1']})
        result = patcher_v55.patchStreamUpstream(decl, {'name': 'l4up', 'origin': ['10.0.0.2']})
        assert result['declaration']['layer4']['upstreams'][0]['origin'] == ['10.0.0.2']

    def test_delete_upstream(self):
        decl = _decl_with_layer4_upstreams({'name': 'u1', 'origin': []}, {'name': 'u2', 'origin': []})
        result = patcher_v55.patchStreamUpstream(decl, {'name': 'u1'})
        names = [u['name'] for u in result['declaration']['layer4']['upstreams']]
        assert 'u1' not in names
        assert 'u2' in names


# ---------------------------------------------------------------------------
# patchNAPPolicies
# ---------------------------------------------------------------------------

class TestPatchNAPPolicies:
    BASE_POLICY = {
        'type': 'app_protect',
        'name': 'my-policy',
        'active_tag': 'v1',
        'versions': [{'tag': 'v1', 'contents': {'content': 'http://example.com/policy.json'}}],
    }

    def test_missing_output_returns_unchanged(self):
        decl = {'declaration': {}}
        result = patcher_v55.patchNAPPolicies(decl, self.BASE_POLICY)
        assert result == decl

    def test_missing_nms_returns_unchanged(self):
        decl = {'output': {}}
        result = patcher_v55.patchNAPPolicies(decl, self.BASE_POLICY)
        assert result == decl

    def test_missing_policies_returns_unchanged(self):
        decl = {'output': {'nms': {}}}
        result = patcher_v55.patchNAPPolicies(decl, self.BASE_POLICY)
        assert result == decl

    def test_add_policy(self):
        decl = _decl_with_nms_policies()
        new_policy = copy.deepcopy(self.BASE_POLICY)
        result = patcher_v55.patchNAPPolicies(decl, new_policy)
        assert len(result['output']['nms']['policies']) == 1
        assert result['output']['nms']['policies'][0]['name'] == 'my-policy'

    def test_update_existing_policy(self):
        old_policy = {'type': 'app_protect', 'name': 'my-policy', 'active_tag': 'v1',
                      'versions': [{'tag': 'v1', 'contents': {'content': 'old'}}]}
        decl = _decl_with_nms_policies(old_policy)
        updated = copy.deepcopy(self.BASE_POLICY)
        updated['active_tag'] = 'v2'
        result = patcher_v55.patchNAPPolicies(decl, updated)
        policies = result['output']['nms']['policies']
        assert len(policies) == 1
        assert policies[0]['active_tag'] == 'v2'

    def test_delete_policy_empty_versions(self):
        existing = copy.deepcopy(self.BASE_POLICY)
        decl = _decl_with_nms_policies(existing)
        delete_req = {'type': 'app_protect', 'name': 'my-policy', 'active_tag': '', 'versions': []}
        result = patcher_v55.patchNAPPolicies(decl, delete_req)
        assert result['output']['nms']['policies'] == []

    def test_v54_add_policy(self):
        decl = _decl_with_nms_policies()
        result = patcher_v54.patchNAPPolicies(decl, copy.deepcopy(self.BASE_POLICY))
        assert result['output']['nms']['policies'][0]['name'] == 'my-policy'


# ---------------------------------------------------------------------------
# patchCertificates
# ---------------------------------------------------------------------------

class TestPatchCertificates:
    BASE_CERT = {'type': 'certificate', 'name': 'my-cert', 'contents': {'content': 'CERTDATA'}}

    def test_missing_output_returns_unchanged(self):
        decl = {}
        result = patcher_v55.patchCertificates(decl, self.BASE_CERT)
        assert result == decl

    def test_missing_nms_returns_unchanged(self):
        decl = {'output': {}}
        result = patcher_v55.patchCertificates(decl, self.BASE_CERT)
        assert result == decl

    def test_missing_certificates_returns_unchanged(self):
        decl = {'output': {'nms': {}}}
        result = patcher_v55.patchCertificates(decl, self.BASE_CERT)
        assert result == decl

    def test_add_certificate(self):
        decl = _decl_with_nms_certificates()
        result = patcher_v55.patchCertificates(decl, copy.deepcopy(self.BASE_CERT))
        assert len(result['output']['nms']['certificates']) == 1
        assert result['output']['nms']['certificates'][0]['name'] == 'my-cert'

    def test_update_certificate(self):
        old = {'type': 'certificate', 'name': 'my-cert', 'contents': {'content': 'OLD'}}
        decl = _decl_with_nms_certificates(old)
        updated = {'type': 'certificate', 'name': 'my-cert', 'contents': {'content': 'NEW'}}
        result = patcher_v55.patchCertificates(decl, updated)
        assert result['output']['nms']['certificates'][0]['contents']['content'] == 'NEW'

    def test_delete_certificate_when_existing_has_empty_contents(self):
        # When the EXISTING cert has empty contents, patching it causes deletion (not appended).
        existing_empty = {'type': 'certificate', 'name': 'my-cert', 'contents': {}}
        decl = _decl_with_nms_certificates(
            existing_empty,
            {'type': 'key', 'name': 'other-key', 'contents': {'content': 'KEY'}},
        )
        patch = {'type': 'certificate', 'name': 'my-cert', 'contents': {'content': 'NEW'}}
        result = patcher_v55.patchCertificates(decl, patch)
        names = [c['name'] for c in result['output']['nms']['certificates']]
        assert 'my-cert' not in names
        assert 'other-key' in names

    def test_v54_add_certificate(self):
        decl = _decl_with_nms_certificates()
        result = patcher_v54.patchCertificates(decl, copy.deepcopy(self.BASE_CERT))
        assert result['output']['nms']['certificates'][0]['name'] == 'my-cert'
