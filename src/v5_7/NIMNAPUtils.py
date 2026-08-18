"""
F5 WAF for NGINX support functions (NGINX Instance Manager)
"""

import json
import requests
import base64
from typing import Tuple, Dict

import v5_7.GitOps
from fastapi.responses import JSONResponse

from AppLogger import AppLogger, get_logger


def __definePolicyOnNMS__(
    nmsUrl: str,
    nmsUsername: str,
    nmsPassword: str,
    policyName: str,
    policyDisplayName: str,
    policyDescription: str,
    policyJson: str,
    policyUid: str = ""
) -> requests.Response:
    """
    Creates or updates an F5 WAF for NGINX policy on NGINX Instance Manager.

    Args:
        nmsUrl (str): NMS base URL.
        nmsUsername (str): Username.
        nmsPassword (str): Password.
        policyName (str): Policy name.
        policyDisplayName (str): Display name.
        policyDescription (str): Description string.
        policyJson (str): Policy JSON string content.
        policyUid (str, optional): Policy UID if updating existing policy. Defaults to "".

    Returns:
        requests.Response: Response object from NMS.
    """
    policyCreationPayload = {
        'metadata': {
            'name': policyName,
            'displayName': policyDisplayName,
            'description': policyDescription
        },
        'content': policyJson
    }

    auth = (nmsUsername, nmsPassword)
    headers = {'Content-Type': 'application/json'}

    if policyUid != "":
        url = f"{nmsUrl}/api/platform/v1/security/policies/{policyUid}"
        return requests.put(url=url, data=json.dumps(policyCreationPayload), headers=headers, auth=auth, verify=False)

    url = f"{nmsUrl}/api/platform/v1/security/policies?isNewRevision=true"
    r = requests.post(url=url, data=json.dumps(policyCreationPayload), headers=headers, auth=auth, verify=False)

    if r.status_code == 404:
        url = f"{nmsUrl}/api/platform/v1/security/policies"
        r = requests.post(url=url, data=json.dumps(policyCreationPayload), headers=headers, auth=auth, verify=False)

    return r


def __getAllPolicies__(nmsUrl: str, nmsUsername: str, nmsPassword: str) -> requests.Response:
    """
    Retrieves all security policies from NGINX Instance Manager.

    Args:
        nmsUrl (str): Base URL.
        nmsUsername (str): Username.
        nmsPassword (str): Password.

    Returns:
        requests.Response: Response object.
    """
    url = f'{nmsUrl}/api/platform/v1/security/policies'
    return requests.get(url=url, auth=(nmsUsername, nmsPassword), verify=False)


def __deletePolicy__(nmsUrl: str, nmsUsername: str, nmsPassword: str, policyUid: str) -> requests.Response:
    """
    Deletes security policy by UID from NGINX Instance Manager.

    Args:
        nmsUrl (str): Base URL.
        nmsUsername (str): Username.
        nmsPassword (str): Password.
        policyUid (str): Target Policy UID.

    Returns:
        requests.Response: Response object.
    """
    url = f'{nmsUrl}/api/platform/v1/security/policies/{policyUid}'
    return requests.delete(url=url, auth=(nmsUsername, nmsPassword), verify=False)


def _validate_policy_declarations(policies: list) -> Tuple[int, str, Dict[str, str]]:
    """
    Validates policy name uniqueness and active tag validity.

    Args:
        policies (list): List of policy declarations.

    Returns:
        Tuple[int, str, Dict[str, str]]: (status_code, error_message, map_of_valid_policy_names)
    """
    all_policy_names = {}

    for policy in policies:
        name = policy.get('name')
        active_tag = policy.get('active_tag')

        if name and name in all_policy_names:
            return 422, f"Duplicated WAF policy [{name}]", {}

        all_policy_names[name] = active_tag

        all_version_tags = {}
        for version in policy.get('versions', []):
            tag = version.get('tag')
            if tag and tag in all_version_tags:
                return 422, f"Duplicated WAF policy tag [{tag}] for policy [{name}]", {}
            all_version_tags[tag] = "found"

        if active_tag and active_tag not in all_version_tags:
            return 422, f"Invalid active tag [{active_tag}] for policy [{name}]", {}

    return 200, "", all_policy_names


def _validate_log_profile_declarations(profiles: list) -> Tuple[int, str, Dict[str, str]]:
    """
    Validates WAF log profile name uniqueness.

    Args:
        profiles (list): List of profile declarations.

    Returns:
        Tuple[int, str, Dict[str, str]]: (status_code, error_message, map_of_valid_profile_names)
    """
    all_profile_names = []

    for p in profiles:
        if p.get('type') == "app_protect":
            name = p.get('app_protect').get("name")

            if name and name in all_profile_names:
                return 422, f"Duplicated WAF log profile [{name}]", {}

        all_profile_names.append(name)

    return 200, "", all_profile_names


def _validate_server_and_location_policies(servers: list, all_policy_names: dict, all_log_profile_names: dict) -> Tuple[int, str]:
    """
    Validates policy and log profile references inside servers and locations.

    Args:
        servers (list): List of HTTP server definitions.
        all_policy_names (dict): Dict of valid policy names.

    Returns:
        Tuple[int, str]: (status_code, error_message)
    """
    available_log_profiles = ['secops_dashboard', 'log_grpc_illegal', 'log_f5_arcsight', 'log_f5_splunk', 'log_all',
                              'log_blocked', 'log_illegal', 'log_grpc_all', 'log_grpc_blocked'] + all_log_profile_names

    valid_policy_keys = ', '.join(all_policy_names.keys())
    valid_log_keys = ', '.join(available_log_profiles)

    for httpServer in servers:
        app_protect = httpServer.get('app_protect', {})
        if app_protect:
            pol = app_protect.get('policy')
            if pol and pol not in all_policy_names:
                return 422, f"Unknown WAF policy [{pol}] referenced by HTTP server [{httpServer.get('name')}] it must be one of [{valid_policy_keys}]"

            log_prof = app_protect.get('log', {}).get('profile_name')
            if log_prof and log_prof not in available_log_profiles:
                return 422, f"Invalid WAF log profile [{log_prof}] referenced by HTTP server [{httpServer.get('name')}] it must be one of [{valid_log_keys}]"

        for location in httpServer.get('locations', []):
            loc_protect = location.get('app_protect', {})
            if loc_protect:
                loc_pol = loc_protect.get('policy')
                if loc_pol and loc_pol not in all_policy_names:
                    return 422, f"Unknown WAF policy [{loc_pol}] referenced by HTTP server [{httpServer.get('name')}] location [{location.get('uri')}] it must be one of [{valid_policy_keys}]"

                if app_protect and app_protect.get('log', {}).get('profile_name') and app_protect['log']['profile_name'] not in available_log_profiles:
                    return 422, f"Invalid WAF log profile [{app_protect['log']['profile_name']}] referenced by HTTP server [{httpServer.get('name')}] location [{location.get('uri')}] it must be one of [{valid_log_keys}]"

    return 200, ""



def _validate_server_and_location_log_profiles(servers: list, all_log_profile_names: dict) -> Tuple[int, str]:
    """
    Validates policy and log profile references inside servers and locations.

    Args:
        servers (list): List of HTTP server definitions.
        all_policy_names (dict): Dict of valid policy names.

    Returns:
        Tuple[int, str]: (status_code, error_message)
    """
    available_log_profiles = ['secops_dashboard', 'log_grpc_illegal', 'log_f5_arcsight', 'log_f5_splunk', 'log_all',
                              'log_blocked', 'log_illegal', 'log_grpc_all', 'log_grpc_blocked'] + all_log_profile_names

    valid_log_keys = ', '.join(available_log_profiles)

    for httpServer in servers:
        app_protect = httpServer.get('app_protect', {})
        if app_protect:
            log_prof = app_protect.get('log', {}).get('profile_name')
            if log_prof and log_prof not in available_log_profiles:
                return 422, f"Invalid WAF log profile [{log_prof}] referenced by HTTP server [{httpServer.get('name')}] it must be one of [{valid_log_keys}]"

        for location in httpServer.get('locations', []):
            loc_protect = location.get('app_protect', {})
            if loc_protect:
                if app_protect and app_protect.get('log', {}).get('profile_name') and app_protect['log']['profile_name'] not in available_log_profiles:
                    return 422, f"Invalid WAF log profile [{app_protect['log']['profile_name']}] referenced by HTTP server [{httpServer.get('name')}] location [{location.get('uri')}] it must be one of [{valid_log_keys}]"

    return 200, ""


def checkDeclarationPolicies(declaration: dict) -> Tuple[int, str]:
    """
    Validates WAF policies defined inside the declaration dictionary.

    Args:
        declaration (dict): Declaration object.

    Returns:
        Tuple[int, str]: Status code (200 on success) and error description string.
    """
    decl_http = (declaration.get('declaration', {}) or {}).get('http')
    if not decl_http or 'policies' not in decl_http:
        return 200, ""

    status, msg, all_policy_names = _validate_policy_declarations(decl_http['policies'])
    if status != 200:
        return status, msg

    status, msg, all_log_profile_names = _validate_log_profile_declarations(decl_http['log_profiles'])
    if status != 200:
        return status, msg

    servers = decl_http.get('servers')
    if servers:
        status, msg = _validate_server_and_location_policies(servers, all_policy_names=all_policy_names, all_log_profile_names=all_log_profile_names)
        if status != 200:
            return status, msg

    return 200, ""


def checkLogProfiles(declaration: dict) -> Tuple[int, str]:
    """
    Validates WAF log profiles defined inside the declaration dictionary.

    Args:
        declaration (dict): Declaration object.

    Returns:
        Tuple[int, str]: Status code (200 on success) and error description string.
    """
    decl_http = (declaration.get('declaration', {}) or {}).get('http')
    if not decl_http or 'log_profiles' not in decl_http:
        return 200, ""

    status, msg, all_policy_names = _validate_log_profile_declarations(decl_http['log_profiles'])
    if status != 200:
        return status, msg

    servers = decl_http.get('servers')
    if servers:
        status, msg = _validate_server_and_location_log_profiles(servers, all_policy_names)
        if status != 200:
            return status, msg

    return 200, ""


def provisionPolicies(
    nmsUrl: str,
    nmsUsername: str,
    nmsPassword: str,
    declaration: dict
) -> JSONResponse:
    """
    Creates/updates F5 WAF policies on NGINX Instance Manager for a given declaration.

    Args:
        nmsUrl (str): NGINX Instance Manager URL.
        nmsUsername (str): Username.
        nmsPassword (str): Password.
        declaration (dict): Configuration declaration dict.

    Returns:
        JSONResponse: Status code and policy version mappings.
    """
    all_policy_names_and_versions = {}
    all_policy_active_names_and_uids = {}

    policies = (declaration.get('declaration', {}) or {}).get('http', {}).get('policies')
    if policies:
        for p in policies:
            policy_name = p.get('name')
            if policy_name and p.get('type') == 'app_protect':
                policy_active_tag = p.get('active_tag')

                for policyVersion in p.get('versions', []):
                    status, policyBody = v5_7.GitOps.getObjectFromRepo(policyVersion['contents'])

                    if status != 200:
                        return JSONResponse(
                            status_code=422,
                            content={"code": status, "details": policyBody['content']}
                        )

                    r = __definePolicyOnNMS__(
                        nmsUrl=nmsUrl, nmsUsername=nmsUsername, nmsPassword=nmsPassword,
                        policyName=policy_name,
                        policyDisplayName=policyVersion.get('displayName', ''),
                        policyDescription=policyVersion.get('description', ''),
                        policyJson=policyBody['content']
                    )

                    if r.status_code != 201:
                        return JSONResponse(
                            status_code=r.status_code,
                            content={"code": r.status_code, "details": json.loads(r.text)}
                        )

                    if policy_name not in all_policy_names_and_versions:
                        all_policy_names_and_versions[policy_name] = []

                    uid = json.loads(r.text)['metadata']['uid']
                    tag = policyVersion['tag']

                    if policy_active_tag == tag:
                        all_policy_active_names_and_uids[policy_name] = uid

                    all_policy_names_and_versions[policy_name].append({'tag': tag, 'uid': uid})

    return JSONResponse(
        status_code=200,
        content={
            "all_policy_names_and_versions": all_policy_names_and_versions,
            "all_policy_active_names_and_uids": all_policy_active_names_and_uids
        }
    )


def makePolicyActive(
    nmsUrl: str,
    nmsUsername: str,
    nmsPassword: str,
    activePolicyUids: dict,
    instanceGroupUid: str
) -> bool:
    """
    Publishes an F5 WAF policy making it active on NMS.

    Args:
        nmsUrl (str): NGINX Instance Manager Base URL.
        nmsUsername (str): Username.
        nmsPassword (str): Password.
        activePolicyUids (dict): Policy name to active UID dict.
        instanceGroupUid (str): Instance group UID.

    Returns:
        bool: True if at least one policy was published, False otherwise.
    """
    doWeHavePolicies = False

    for policyName, activeUid in activePolicyUids.items():
        body = {
            "publications": [
                {
                    "policyContent": {
                        "name": f'{policyName}',
                        "uid": f'{activeUid}'
                    },
                    "instanceGroups": [
                        f'{instanceGroupUid}'
                    ]
                }
            ]
        }

        doWeHavePolicies = True
        url = f'{nmsUrl}/api/platform/v1/security/publish'
        auth = (nmsUsername, nmsPassword)
        headers = {'Content-Type': 'application/json'}
        requests.post(url=url, auth=auth, data=json.dumps(body), headers=headers, verify=False)

    return doWeHavePolicies


def cleanPolicyLeftovers(nmsUrl: str, nmsUsername: str, nmsPassword: str, currentPolicies: dict) -> None:
    """
    Removes unused/leftover F5 WAF policies from NGINX Instance Manager.

    Args:
        nmsUrl (str): NGINX Instance Manager Base URL.
        nmsUsername (str): Username.
        nmsPassword (str): Password.
        currentPolicies (dict): Currently active policies map.
    """
    allNMSPolicies = __getAllPolicies__(nmsUrl=nmsUrl, nmsUsername=nmsUsername, nmsPassword=nmsPassword)
    allNMSPoliciesJson = json.loads(allNMSPolicies.text)

    allUidsOnNMS = []
    for p in allNMSPoliciesJson.get('items', []):
        if p.get('metadata', {}).get('name') in currentPolicies:
            allUidsOnNMS.append(p['metadata']['uid'])

    allCurrentPoliciesUIDs = []
    for policyName, tags in currentPolicies.items():
        if policyName:
            for tag in tags:
                allCurrentPoliciesUIDs.append(tag['uid'])

    uidsToRemove = list(set(allUidsOnNMS) - set(allCurrentPoliciesUIDs))

    for uid in uidsToRemove:
        __deletePolicy__(nmsUrl=nmsUrl, nmsUsername=nmsUsername, nmsPassword=nmsPassword, policyUid=uid)


def provisionLogProfiles(
    nmsUrl: str,
    nmsUsername: str,
    nmsPassword: str,
    declaration: dict
) -> Tuple [bool, str, str]:
    """
    Creates/updates F5 WAF log profiles on NGINX Instance Manager for a given declaration.

    Args:
        nmsUrl (str): NGINX Instance Manager URL.
        nmsUsername (str): Username.
        nmsPassword (str): Password.
        declaration (dict): Configuration declaration dict.

    Returns:
        bool: Success status
        str: if bool is False, log profile name that triggered the error
    """

    http_decl = (declaration.get('declaration', {}) or {}).get('http', {})
    log_profiles = http_decl.get('log_profiles', {}) if http_decl else []
    if log_profiles:
        for p in log_profiles:
            if p.get('type') == 'app_protect':
                waflogprofile = p.get('app_protect')
                profileName = waflogprofile.get('name')
                profileJson = {}
                profileJson['filter'] = {}
                profileJson['filter']['request_type'] = waflogprofile.get('type')
                profileJson['content'] = {}

                parm = waflogprofile.get('format')
                if parm: profileJson['content']['format'] = parm
                parm = waflogprofile.get('format_string')
                if parm: profileJson['content']['format_string'] = parm
                parm = waflogprofile.get('max_message_size')
                if parm: profileJson['content']['max_message_size'] = parm
                parm = waflogprofile.get('max_request_size')
                if parm: profileJson['content']['max_request_size'] = parm
                parm = waflogprofile.get('list_prefix')
                if parm: profileJson['content']['list_prefix'] = parm
                parm = waflogprofile.get('list_delimiter')
                if parm: profileJson['content']['list_delimiter'] = parm
                parm = waflogprofile.get('list_suffix')
                if parm: profileJson['content']['list_suffix'] = parm

                esc_from = waflogprofile.get('escaping_characters_from', '')
                esc_to = waflogprofile.get('escaping_characters_to', '')

                if esc_from and esc_to:
                    profileJson['content']['escaping_characters'] = []

                    for i in range(len(esc_from)):
                        profileEscape = {"from": esc_from[i], "to": esc_to[i] }
                        profileJson['content']['escaping_characters'].append(profileEscape)

                success, profileName, nimReply = __writeWAFLogProfile__(
                nmsUrl=nmsUrl,
                nmsUsername=nmsUsername, nmsPassword=nmsPassword, logProfileName=profileName, logProfileJson=profileJson)

                if not success:
                    return success, profileName, nimReply

    return True, "", ""


def __writeWAFLogProfile__(
    nmsUrl: str,
    nmsUsername: str,
    nmsPassword: str,
    logProfileName: str,
    logProfileJson: dict
) -> Tuple [bool, str, str]:
    """
    Writes F5 WAF log profile to NGINX Instance Manager.

    Args:
        nmsUrl (str): NGINX Instance Manager Base URL.
        nmsUsername (str): Username.
        nmsPassword (str): Password.
        logProfileName (str): Log profile name.
        logProfileJson (dict): Log profile JSON.

   Returns:
        bool: Success status
        str: if bool is False, log profile name that triggered the error
        str: the NGINX Instance Manager reply payload
    """
    logger = get_logger()

    url = f'{nmsUrl}/api/platform/v1/security/logprofiles'
    auth = (nmsUsername, nmsPassword)
    headers = {'Content-Type': 'application/json'}
    r = requests.get(url=f'{url}/{logProfileName}', auth=auth, headers=headers, verify=False)

    if r.status_code not in (200,404):
        return False, "", ""

    logProfileCreationPayload = {
        'metadata': {
            'name': logProfileName
        },
        'content': base64.b64encode(bytes(json.dumps(logProfileJson), 'utf-8')).decode('utf-8')
    }

    if r.status_code == 200:
        # Update existing WAF log profile
        logProfileUid = json.loads(r.text)['metadata']['uid']
        reply = requests.put(url=f'{url}/{logProfileUid}', auth=auth, data=json.dumps(logProfileCreationPayload), headers=headers, verify=False)

        if reply.status_code not in (200,412):
            return False, logProfileName, reply.text

        if reply.status_code == 412:
            logger.warning(
                f"WAF log profile update [{logProfileName}] code [{json.loads(reply.text).get('code')}] - {json.loads(reply.text).get('message')}")
    else:
        # Create new WAF log profile
        reply = requests.post(url=f'{url}', auth=auth, data=json.dumps(logProfileCreationPayload), headers=headers, verify=False)

        if reply.status_code != 201:
            return False, logProfileName, reply.text

    # WAF log profile successfully committed
    return True, "", ""