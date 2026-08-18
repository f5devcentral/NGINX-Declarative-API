"""
F5 WAF for NGINX support functions (NGINX One Console)
"""

import json
import base64
import requests
from typing import Tuple, Dict

import v5_7.GitOps
from fastapi.responses import JSONResponse


def __definePolicyOnNGINXOne__(
    nginxOneUrl: str,
    nginxOneToken: str,
    nginxOneNamespace: str,
    policyJson: str
) -> requests.Response:
    """
    Creates or updates an F5 WAF for NGINX policy on NGINX One Console.

    Args:
        nginxOneUrl (str): NGINX One console base URL.
        nginxOneToken (str): Authentication API token.
        nginxOneNamespace (str): Namespace name.
        policyJson (str): Policy JSON string.

    Returns:
        requests.Response: Response object from NGINX One API call.
    """
    policy_name = json.loads(policyJson)['policy']['name']

    policyCreationPayload = {
        'policy': base64.b64encode(bytes(policyJson, 'utf-8')).decode('utf-8')
    }

    allExistingPolicies = __getAllPolicies__(
        nginxOneUrl=nginxOneUrl,
        nginxOneToken=nginxOneToken,
        nginxOneNamespace=nginxOneNamespace
    )
    polId = __getPolicyId__(json.loads(allExistingPolicies.text), policy_name)

    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'APIToken {nginxOneToken}'
    }

    if polId != "":
        url = f"{nginxOneUrl}/api/nginx/one/namespaces/{nginxOneNamespace}/app-protect/policies/{polId}"
        return requests.put(url=url, data=json.dumps(policyCreationPayload), headers=headers, verify=False)
    else:
        url = f"{nginxOneUrl}/api/nginx/one/namespaces/{nginxOneNamespace}/app-protect/policies"
        return requests.post(url=url, data=json.dumps(policyCreationPayload), headers=headers, verify=False)


def __getAllPolicies__(nginxOneUrl: str, nginxOneToken: str, nginxOneNamespace: str) -> requests.Response:
    """
    Retrieves all security policies from NGINX One Console.

    Args:
        nginxOneUrl (str): Base URL.
        nginxOneToken (str): API Token.
        nginxOneNamespace (str): Target namespace.

    Returns:
        requests.Response: HTTP response object.
    """
    url = f"{nginxOneUrl}/api/nginx/one/namespaces/{nginxOneNamespace}/app-protect/policies?paginated=false"
    headers = {"Authorization": f"APIToken {nginxOneToken}"}
    return requests.get(url=url, headers=headers, verify=False)


def __getPolicyId__(allPoliciesJSON: dict, policyName: str) -> str:
    """
    Retrieves policy ID for a given policy name from full policy list JSON.

    Args:
        allPoliciesJSON (dict): Parsed JSON dictionary of all policies.
        policyName (str): Name of target policy.

    Returns:
        str: Policy object ID if found, otherwise empty string.
    """
    if isinstance(allPoliciesJSON, dict) and 'items' in allPoliciesJSON:
        for p in allPoliciesJSON['items']:
            if policyName == p.get('name'):
                return p.get('object_id', '')
    return ""


def __deletePolicy__(nginxOneUrl: str, nginxOneToken: str, nginxOneNamespace: str, policyUids: list) -> requests.Response:
    """
    Deletes specified security policies from NGINX One Console.

    Args:
        nginxOneUrl (str): Base URL.
        nginxOneToken (str): API token.
        nginxOneNamespace (str): Namespace name.
        policyUids (list): List of policy object IDs to delete.

    Returns:
        requests.Response: Response object from PATCH delete operation.
    """
    jsonPayload = [{'object_id': polId, 'action': 'delete'} for polId in policyUids]
    url = f'{nginxOneUrl}/api/nginx/one/namespaces/{nginxOneNamespace}/app-protect/policies'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'APIToken {nginxOneToken}'
    }
    return requests.patch(url=url, headers=headers, verify=False, data=json.dumps(jsonPayload))


def _validate_policy_declarations(policies: list) -> Tuple[int, str, Dict[str, str]]:
    """
    Validates policy uniqueness, tag uniqueness, and active tag presence.

    Args:
        policies (list): List of policy declarations.

    Returns:
        Tuple[int, str, Dict[str, str]]: (status, error_message, map_of_valid_policy_names_to_active_tags)
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
    Validates referenced policies and log profile names in HTTP servers and locations.

    Args:
        servers (list): List of HTTP server definitions.
        all_policy_names (dict): Dict of defined valid policy names.

    Returns:
        Tuple[int, str]: (status_code, error_message)
    """
    available_log_profiles = ['log_all', 'log_blocked', 'log_illegal', 'secops_dashboard'] + all_log_profile_names

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
                    return 422, f"Invalid WAF log profile [{app_protect['log']['profile_name']}] referenced by HTTP server [{httpServer.get('name')}] location [{location.get('uri')}]"

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
    Check NAP policies validity for the given declaration.

    Args:
        declaration (dict): Full configuration declaration dict.

    Returns:
        Tuple[int, str]: Status code (200 on success) and error description message.
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


def provisionPolicies(nginxOneUrl: str, nginxOneToken: str, nginxOneNamespace: str, declaration: dict) -> JSONResponse:
    """
    Provisions F5 WAF for NGINX policies to NGINX One console for a given declaration.

    Args:
        nginxOneUrl (str): Console URL.
        nginxOneToken (str): Auth token.
        nginxOneNamespace (str): Namespace.
        declaration (dict): Declaration object.

    Returns:
        JSONResponse: JSON response containing status and policy version mapping details.
    """
    all_policy_names_and_versions = {}
    all_policy_active_names_and_uids = {}

    http_decl = (declaration.get('declaration', {}) or {}).get('http', {})
    policies = http_decl.get('policies', {}) if http_decl else []
    if policies:
        for p in policies:
            policy_name = p.get('name')
            if policy_name and p.get('type') == 'app_protect':
                policy_active_tag = p.get('active_tag')

                allPoliciesJSON = __getAllPolicies__(
                    nginxOneUrl=nginxOneUrl,
                    nginxOneToken=nginxOneToken,
                    nginxOneNamespace=nginxOneNamespace
                )
                polId = __getPolicyId__(json.loads(allPoliciesJSON.text), policy_name)
                if polId != "":
                    __deletePolicy__(
                        nginxOneUrl=nginxOneUrl,
                        nginxOneToken=nginxOneToken,
                        nginxOneNamespace=nginxOneNamespace,
                        policyUids=[polId]
                    )

                for policyVersion in p.get('versions', []):
                    status, policyBody = v5_7.GitOps.getObjectFromRepo(policyVersion['contents'], base64Encode=False)

                    if status != 200:
                        return JSONResponse(
                            status_code=422,
                            content={"code": status, "details": policyBody['content']}
                        )

                    r = __definePolicyOnNGINXOne__(
                        nginxOneUrl=nginxOneUrl,
                        nginxOneToken=nginxOneToken,
                        nginxOneNamespace=nginxOneNamespace,
                        policyJson=policyBody['content']
                    )

                    if r.status_code != 201:
                        return JSONResponse(
                            status_code=r.status_code,
                            content={"code": r.status_code, "details": json.loads(r.text)}
                        )

                    if policy_name not in all_policy_names_and_versions:
                        all_policy_names_and_versions[policy_name] = []

                    uid = json.loads(r.text)['latest']['object_id']
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
    nginxOneUrl: str,
    nginxOneToken: str,
    nginxOneNamespace: str,
    activePolicyUids: dict,
    instanceGroupUid: str
) -> bool:
    """
    Publishes an F5 WAF for NGINX policy, marking it active.

    Args:
        nginxOneUrl (str): Console URL.
        nginxOneToken (str): API Token.
        nginxOneNamespace (str): Namespace.
        activePolicyUids (dict): Dict of policy_name to active_uid.
        instanceGroupUid (str): Target instance group UID.

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
        url = f'{nginxOneUrl}/api/platform/v1/security/publish'
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'APIToken {nginxOneToken}'
        }
        requests.post(url=url, data=json.dumps(body), headers=headers, verify=False)

    return doWeHavePolicies


def provisionLogProfiles(
    nginxOneUrl: str,
    nginxOneToken: str,
    nginxOneNamespace: str,
    declaration: dict
) -> Tuple [bool, str, str, JSONResponse]:
    """
    Creates/updates F5 WAF log profiles on NGINX One Console for a given declaration.

    Args:
        nginxOneUrl (str): NGINX One Console URL.
        nginxOneToken (str): Authentication token.
        nginxOneNamespace (str): Namespace.
        declaration (dict): Configuration declaration dict.

    Returns:
        bool: Success status
        str: if bool is False, log profile name that triggered the error, "" otherwise
        str: the NGINX One console reply
        JSONResponse: an array of {logprofilename, id}
    """

    allN1Cprofiles = __get_all_WAFLogProfiles__(nginxOneUrl=nginxOneUrl, nginxOneToken=nginxOneToken, nginxOneNamespace=nginxOneNamespace)
    allLogProfilesWithUIDs = []

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
                        profileEscape = {"from": esc_from[i], "to": esc_to[i]}
                        profileJson['content']['escaping_characters'].append(profileEscape)

                success, profileName, nimReply = __writeWAFLogProfile__(
                nginxOneUrl=nginxOneUrl,
                nginxOneToken=nginxOneToken, nginxOneNamespace=nginxOneNamespace, logProfileName=profileName, logProfileJson=profileJson, allN1Cprofiles=allN1Cprofiles)

                if not success:
                    return success, profileName, nimReply, allLogProfilesWithUIDs

                allLogProfilesWithUIDs_item = {}
                allLogProfilesWithUIDs_item['name'] = profileName
                allLogProfilesWithUIDs_item['uid'] = json.loads(nimReply).get('object_id')
                allLogProfilesWithUIDs.append(allLogProfilesWithUIDs_item)

    return True, "", "", allLogProfilesWithUIDs


def __writeWAFLogProfile__(
    nginxOneUrl: str,
    nginxOneToken: str,
    nginxOneNamespace: str,
    logProfileName: str,
    logProfileJson: dict,
    allN1Cprofiles: dict
) -> Tuple [bool, str, str]:
    """
    Writes F5 WAF log profile to NGINX One Console.

    Args:
        nginxOneUrl (str): NGINX One Console URL.
        nginxOneToken (str): Authentication token.
        nginxOneNamespace (str): Namespace.
        logProfileName (str): Log profile name.
        logProfileJson (dict): Log profile JSON.

   Returns:
        bool: Success status
        str: log profile name that triggered the error
        str: the NGINX One Console reply payload
    """

    logProfileUid = __get_WAFLogProfile_id__(logProfileName=logProfileName,allN1Cprofiles=allN1Cprofiles)

    logProfileCreationPayload_old = {
        'metadata': {
            'name': logProfileName
        },
        'content': base64.b64encode(bytes(json.dumps(logProfileJson), 'utf-8')).decode('utf-8')
    }

    logProfileCreationPayload = {
        'name': logProfileName,
        'config': base64.b64encode(bytes(json.dumps(logProfileJson), 'utf-8')).decode('utf-8')
    }

    baseUrl = f'{nginxOneUrl}/api/nginx/one/namespaces/{nginxOneNamespace}/app-protect/log-profiles'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'APIToken {nginxOneToken}'
    }

    if logProfileUid:
        # Update existing WAF log profile
        url = f'{baseUrl}/{logProfileUid}'
        reply = requests.put(url=url, data=json.dumps(logProfileCreationPayload), headers=headers, verify=False)

        if reply.status_code != 200:
            return False, logProfileName, reply.text
    else:
        # Create new WAF log profile
        reply = requests.post(url=baseUrl, data=json.dumps(logProfileCreationPayload), headers=headers, verify=False)

        if reply.status_code != 201:
            return False, logProfileName, reply.text

    # WAF log profile successfully committed
    return True, logProfileName, reply.text


def __get_WAFLogProfile_id__(
    logProfileName: str,
    allN1Cprofiles: dict
) -> str:
    for n1cprofile in allN1Cprofiles.get('items'):
        if n1cprofile.get('name') == logProfileName:
            return n1cprofile.get('object_id')

    return None


def __get_all_WAFLogProfiles__(
    nginxOneUrl: str,
    nginxOneToken: str,
    nginxOneNamespace: str
) -> dict:
    """
    Gets all WAF log profiles from NGINX One Console.

    Args:
        nginxOneUrl (str): NGINX One Console URL.
        nginxOneToken (str): Authentication token.
        nginxOneNamespace (str): Namespace.

   Returns:
        dict: log profiles json list
    """
    url = f"{nginxOneUrl}/api/nginx/one/namespaces/{nginxOneNamespace}/app-protect/log-profiles?paginated=false"

    headers = {
        'Authorization': f'APIToken {nginxOneToken}'
    }
    r = requests.get(url=url, headers=headers, verify=False)

    if r.status_code != 200:
        return {"count": 0,"items":[]}

    return json.loads(r.text)