"""
NGINX App Protect support functions
"""

import requests
import json
import base64

import v5_3.GitOps

from NcgConfig import NcgConfig

from fastapi.responses import Response, JSONResponse

available_log_profiles = ['log_all', 'log_blocked', 'log_illegal', 'secops_dashboard']


# Define (create/update) a NGINX App Protect policy on NMS.
# If policyUid is not empty a the policy update is performed
# Returns a tuple {response,policy_id,policy_version_id}. r.status_code is 201 if successful
def __definePolicyOnNGINXOne__(nginxOneUrl: str, nginxOneToken: str, nginxOneNamespace: str, policyJson: str):
    policyName = json.loads(policyJson)['policy']['name']

    # Payload for NGINX One Console
    # policyBody holds the base64-encoded policy JSON definition
    # Control plane-compiled policy bundles are supported. Create the NGINX App Protect policy on NGINX One Console
    # POST {nginxOneUrl}/api/nginx/one/namespaces/{nginxOneNamespace}/app-protect/policies
    # {
    #     "policy": "<BASE64>"
    # }
    policyCreationPayload = {}
    policyCreationPayload['policy'] = base64.b64encode(bytes(policyJson, 'utf-8')).decode('utf-8')

    # Retrieve the full policy list from NGINX One Console
    allExistingPolicies = __getAllPolicies__(nginxOneUrl = nginxOneUrl, nginxOneToken = nginxOneToken, nginxOneNamespace=nginxOneNamespace)

    # Retrieve the policy id for the policy being created
    polId = __getPolicyId__(json.loads(allExistingPolicies.text), policyName)

    r = ""
    if polId != "":
        # This is a new version for an existing policy
        r = requests.put(url=f"{nginxOneUrl}/api/nginx/one/namespaces/{nginxOneNamespace}/app-protect/policies/{polId}",
                          data=json.dumps(policyCreationPayload),
                          headers={'Content-Type': 'application/json',
                                   "Authorization": f"Bearer APIToken {nginxOneToken}"},
                          verify=False)
    else:
        # New policy creation
        r = requests.post(url=f"{nginxOneUrl}/api/nginx/one/namespaces/{nginxOneNamespace}/app-protect/policies",
            data=json.dumps(policyCreationPayload),
            headers={'Content-Type': 'application/json', "Authorization": f"Bearer APIToken {nginxOneToken}"},
            verify=False)


    rJson = json.loads(r.text)
    polId = rJson['object_id']
    policyVersionId = rJson['latest']['object_id']

    return r, polId, policyVersionId


# Retrieve security policies information
def __getAllPolicies__(nginxOneUrl: str, nginxOneToken: str, nginxOneNamespace: str):
    return requests.get(url=f"{nginxOneUrl}/api/nginx/one/namespaces/{nginxOneNamespace}/app-protect/policies?paginated=false",
                        headers={"Authorization": f"Bearer APIToken {nginxOneToken}"}, verify=False)


# Retrieve all versions for the given security policy id
def __getAllPolicyVersions__(nginxOneUrl: str, nginxOneToken: str, nginxOneNamespace: str, policyId: str):
    return requests.get(url=f"{nginxOneUrl}/api/nginx/one/namespaces/{nginxOneNamespace}/app-protect/policies/{policyId}/versions?paginated=false",
                        headers={"Authorization": f"Bearer APIToken {nginxOneToken}"}, verify=False)



# Return the policy ID for the given policyName. allPoliciesJSON is the JSON output from __getAllPolicies__
def __getPolicyId__(allPoliciesJSON: dict, policyName: str):
    if 'items' in allPoliciesJSON:
        for p in allPoliciesJSON['items']:
            if policyName == p['name']:
                return p['object_id']

    return ""


# Delete the given version for the given security policy
def __deletePolicyVersion__(nginxOneUrl: str, nginxOneToken: str, nginxOneNamespace: str, policyId: str, policyVersionId: str):
    return requests.delete(url=f'{nginxOneUrl}/api/nginx/one/namespaces/{nginxOneNamespace}/app-protect/policies/{policyId}/versions/{policyVersionId}',
        headers={"Authorization": f"Bearer APIToken {nginxOneToken}"}, verify=False)


# Check NAP policies names validity for the given declaration
# Return a tuple: status, description. If status = 200 checks were successful
def checkDeclarationPolicies(declaration: dict):
    # NGINX App Protect policies check - duplicated policy names

    # all policy names as defined in the declaration
    # { 'policyName': 'activeTag', ... }
    allPolicyNames = {}

    if 'policies' not in declaration['output']['nginxone']:
        return 200, ""

    for policy in declaration['output']['nginxone']['policies']:
        # print(f"Found NAP Policy [{policy['name']}] active tag [{policy['active_tag']}]")

        if policy['name'] and policy['name'] in allPolicyNames:
            return 422, f"Duplicated NGINX App Protect WAF policy [{policy['name']}]"

        allPolicyNames[policy['name']] = policy['active_tag']

        # Check policy releases for non-univoque tags
        allPolicyVersionTags = {}
        for policyVersion in policy['versions']:
            if policyVersion['tag'] and policyVersion['tag'] in allPolicyVersionTags:
                return 422, f"Duplicated NGINX App Protect WAF policy tag [{policyVersion['tag']}] " \
                            f"for policy [{policy['name']}]"

            allPolicyVersionTags[policyVersion['tag']] = "found"

        if policy['active_tag'] and policy['active_tag'] not in allPolicyVersionTags:
            return 422, f"Invalid active tag [{policy['active_tag']}] for policy [{policy['name']}]"

    # Check policy names referenced by the declaration inside HTTP servers[]: they must be valid
    if 'http' in declaration['declaration'] and 'servers' in declaration['declaration']['http']:
        for httpServer in declaration['declaration']['http']['servers']:
            if 'app_protect' in httpServer:
                if 'policy' in httpServer['app_protect'] and httpServer['app_protect']['policy'] \
                        and httpServer['app_protect']['policy'] not in allPolicyNames:
                    return 422, f"Unknown NGINX App Protect WAF policy [{httpServer['app_protect']['policy']}] " \
                                f"referenced by HTTP server [{httpServer['name']}]"

                if 'log' in httpServer['app_protect'] \
                        and 'profile_name' in httpServer['app_protect']['log'] \
                        and httpServer['app_protect']['log']['profile_name'] \
                        and httpServer['app_protect']['log']['profile_name'] \
                        not in available_log_profiles:
                    return 422, f"Invalid NGINX App Protect WAF log profile " \
                                f"[{httpServer['app_protect']['log']['profile_name']}] referenced by HTTP server " \
                                f"[{httpServer['name']}]"

            # Check policy names referenced in HTTP servers[].locations[]
            for location in httpServer['locations']:
                if 'app_protect' in location:
                    if 'policy' in location['app_protect'] and location['app_protect']['policy'] \
                            and location['app_protect']['policy'] not in allPolicyNames:
                        return 422, f"Unknown NGINX App Protect WAF policy [{location['app_protect']['policy']}] " \
                                    f"referenced by HTTP server [{httpServer['name']}] location [{location['uri']}]"

                    if 'log' in httpServer['app_protect'] and httpServer['app_protect']['log'] \
                            and httpServer['app_protect']['log']['profile_name'] \
                            and httpServer['app_protect']['log']['profile_name'] \
                            not in available_log_profiles:
                        return 422, f"Invalid NGINX App Protect WAF log profile " \
                                    f"[{httpServer['app_protect']['log']['profile_name']}] referenced by HTTP server " \
                                    f"[{httpServer['name']}] location [{location['uri']}]"

    return 200, ""


# For the given declaration creates/updates NGINX App Protect WAF policies on NGINX Instance Manager
# making sure that they are in sync with what is defined in the JSON declaration
# Returns a JSON with status code
def provisionPolicies(nginxOneUrl: str, nginxOneToken: str, nginxOneNamespace: str, declaration: dict):
    # NGINX App Protect policies - each policy supports multiple tagged versions

    # Policy names and all tag/uid pairs
    # {'prod-policy': [{'tag': 'v1', 'uid': 'ebcf9c7e-0930-450d-8108-7cad30e59661'},
    #                 {'tag': 'v2', 'uid': 'd18c2eb7-814e-4e4d-90fc-54014eef199e'}],
    # 'staging-policy': [{'tag': 'block', 'uid': '9794faa7-5b6c-4ce5-9e68-946f04766bb4'},
    #                    {'tag': 'xss-ok', 'uid': '7b4b850a-ff9e-42a0-85d0-850171474224'}]}
    all_policy_names_and_versions = {}

    # Policy names and active tag uids
    # { 'prod-policy': 'ebcf9c7e-0930-450d-8108-7cad30e59661',
    # 'staging-policy': '7b4b850a-ff9e-42a0-85d0-850171474224' }
    all_policy_active_names_and_uids = {}

    # Policy ID and policy version IDs being created
    createdPolicyIds = []

    for p in declaration['output']['nginxone']['policies']:
        policy_name = p['name']
        if policy_name:
            policy_active_tag = p['active_tag']

            # Iterates over all NGINX App Protect policies
            if p['type'] == 'app_protect':
                # Create all policy versions
                for policyVersion in p['versions']:
                    status, policyBody = v5_3.GitOps.getObjectFromRepo(policyVersion['contents'],base64Encode=False)

                    if status != 200:
                        return JSONResponse(
                            status_code=422,
                            content={"code": status,
                                     "details": policyBody['content']}
                        )

                    # Create the NGINX App Protect policy on NGINX One Console
                    r,polId,polVersionId = __definePolicyOnNGINXOne__(
                        nginxOneUrl=nginxOneUrl, nginxOneToken=nginxOneToken, nginxOneNamespace=nginxOneNamespace,
                        policyJson=policyBody['content']
                    )

                    # Check for errors creating NGINX App Protect policy
                    if r.status_code != 201:
                        return JSONResponse(
                            status_code=r.status_code,
                            content={"code": r.status_code, "details": json.loads(r.text)}
                        )
                    else:
                        # Policy was created, retrieve metadata.uid for each policy version
                        if policy_name not in all_policy_names_and_versions:
                            all_policy_names_and_versions[policy_name] = []

                        # Stores the policy version
                        uid = json.loads(r.text)['latest']['object_id']
                        tag = policyVersion['tag']

                        if policy_active_tag == tag:
                            all_policy_active_names_and_uids[policy_name] = uid

                        all_policy_names_and_versions[policy_name].append({'tag': tag, 'uid': uid})

                        createdPolicyIds.append(polId)


    return JSONResponse(status_code=200, content={"all_policy_names_and_versions": all_policy_names_and_versions,
                                                  "all_policy_active_names_and_uids": all_policy_active_names_and_uids,
                                                  "policy_ids": list(set(createdPolicyIds))})


# Publish a NGINX App Protect WAF policy building a "payloads" entry for NGINX One Console
# This will be injected into the PUT payload for https://{tenant_cname}.console.ves.volterra.io/api/nginx/one/namespaces/{namespace}/instances/{instanceObjectID}/config
# activePolicyUids is a dict { "policy_name": "active_uid", [...] }
# Return the policy "payloads" array having this format:
# {
#
#     "type": "nap_policy_version",
#     "object_id": "pv_ID",
#     "paths":
#
#     [
#         "/etc/nms/policyname.tgz
#     ]
# },
#
def addNapPolicyPayloads(nginxOneUrl: str, nginxOneToken: str, nginxOneNamespace: str, activePolicyUids: dict, instanceGroupUid: str):
    payloadsArray = []

    for policyName in activePolicyUids:
        body = {}
        body['type'] = "nap_policy_version"
        body['object_id'] = activePolicyUids[policyName]
        body['paths'] = []
        body['paths'].append(NcgConfig.config['nms']['nap_policies_dir_pum'] + '/' + policyName + '.tgz')

        payloadsArray.append(body)

    return payloadsArray


# Delete all policy versions not currently deployed to any config sync group
def removeUndeployedPolicyVersions(nginxOneUrl: str, nginxOneToken: str, nginxOneNamespace: str, policyIds: []):
    for p in policyIds:

        r = __getAllPolicyVersions__(nginxOneUrl=nginxOneUrl, nginxOneToken=nginxOneToken, nginxOneNamespace=nginxOneNamespace, policyId=p)

        if r.status_code == 200:
            j = json.loads(r.text)

            if 'items' in j:
                for policyVersion in j['items']:
                    if not 'deployments' in policyVersion:
                        # Policy version is not currently deployed, remove it
                        __deletePolicyVersion__(nginxOneUrl=nginxOneUrl, nginxOneToken=nginxOneToken,
                            nginxOneNamespace=nginxOneNamespace, policyId=p, policyVersionId=policyVersion['object_id'])