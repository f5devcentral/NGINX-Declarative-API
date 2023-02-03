"""
NGINX App Protect support functions
"""

import requests
import json
import numpy

import Contrib.GitOps

from fastapi.responses import Response, JSONResponse

available_log_profiles = ['log_all', 'log_blocked', 'log_illegal', 'secops_dashboard']


# Define (create/update) a NGINX App Protect policy on NMS.
# If policyUid is not empty a the policy update is performed
# Returns a tuple {status_code,text}. status_code is 201 if successful
def __definePolicyOnNMS__(nmsUrl: str, nmsUsername: str, nmsPassword: str, policyName: str, policyDisplayName: str,
                          policyDescription: str, policyJson: str, policyUid: str = ""):
    # policyBody holds the base64-encoded policy JSON definition
    # Control plane-compiled policy bundles are supported. Create the NGINX App Protect policy on NMS
    # POST https://{{nms_host}}/api/platform/v1/security/policies
    # {
    #     "metadata": {
    #         "name": "prod-policy",
    #         "displayName": "Production Policy - blocking",
    #         "description": "Production-ready policy - blocking"
    #     },
    #     "content": "<BASE64>"
    # }

    policyCreationPayload = {'metadata': {}}
    policyCreationPayload['metadata']['name'] = policyName
    policyCreationPayload['metadata']['displayName'] = policyDisplayName
    policyCreationPayload['metadata']['description'] = policyDescription
    policyCreationPayload['content'] = policyJson

    if policyUid != "":
        # Existing policy update
        r = requests.put(url=f"{nmsUrl}/api/platform/v1/security/policies/{policyUid}",
                         data=json.dumps(policyCreationPayload),
                         headers={'Content-Type': 'application/json'},
                         auth=(nmsUsername, nmsPassword),
                         verify=False)
    else:
        # New policy creation - first try to create it as a new revision for an existing policy
        # The response code is 201 if successful and 404 if there is no policy with the given name
        r = requests.post(url=f"{nmsUrl}/api/platform/v1/security/policies?isNewRevision=true",
                          data=json.dumps(policyCreationPayload),
                          headers={'Content-Type': 'application/json'},
                          auth=(nmsUsername, nmsPassword),
                          verify=False)

        # Check if this is a new policy with no existing versions. If this is true create its initial version
        if r.status_code == 404:
            r = requests.post(url=f"{nmsUrl}/api/platform/v1/security/policies",
                              data=json.dumps(policyCreationPayload),
                              headers={'Content-Type': 'application/json'},
                              auth=(nmsUsername, nmsPassword),
                              verify=False)

    return r


# Retrieve security policies information
def __getAllPolicies__(nmsUrl: str, nmsUsername: str, nmsPassword: str):
    return requests.get(url=f'{nmsUrl}/api/platform/v1/security/policies',
                        auth=(nmsUsername, nmsPassword), verify=False)


# Delete security policy from control plane
def __deletePolicy__(nmsUrl: str, nmsUsername: str, nmsPassword: str, policyUid: str):
    return requests.delete(url=f'{nmsUrl}/api/platform/v1/security/policies/{policyUid}',
                           auth=(nmsUsername, nmsPassword), verify=False)


# Check NAP policies names validity for the given declaration
# Return a tuple: status, description. If status = 200 checks were successful
def checkDeclarationPolicies(declaration: dict):
    # NGINX App Protect policies check - duplicated policy names

    # all policy names as defined in the declaration
    # { 'policyName': 'activeTag', ... }
    allPolicyNames = {}

    for policy in declaration['output']['nms']['policies']:
        #print(f"Found NAP Policy [{policy['name']}] active tag [{policy['active_tag']}]")

        if policy['name'] in allPolicyNames:
            return 422, f"Duplicated NGINX App Protect WAF policy [{policy['name']}]"

        allPolicyNames[policy['name']] = policy['active_tag']

        # Check policy releases for non-univoque tags
        allPolicyVersionTags = {}
        for policyVersion in policy['versions']:
            #print(f"--> Policy [{policy['name']}] tag [{policyVersion['tag']}]")
            if policyVersion['tag'] in allPolicyVersionTags:
                return 422, f"Duplicated NGINX App Protect WAF policy tag [{policyVersion['tag']}] " \
                            f"for policy [{policy['name']}]"

            allPolicyVersionTags[policyVersion['tag']] = "found"

        if policy['active_tag'] not in allPolicyVersionTags:
            return 422, f"Invalid active tag [{policy['active_tag']}] for policy [{policy['name']}]"

    # Check policy names referenced by the declaration inside HTTP servers[]: they must be valid
    if 'servers' in declaration['declaration']['http']:
        for httpServer in declaration['declaration']['http']['servers']:
            if 'app_protect' in httpServer:
                if 'policy' in httpServer['app_protect'] and httpServer['app_protect']['policy'] not in allPolicyNames:
                    return 422, f"Unknown NGINX App Protect WAF policy [{httpServer['app_protect']['policy']}] " \
                                f"referenced by HTTP server [{httpServer['name']}]"

                if 'log' in httpServer['app_protect'] and httpServer['app_protect']['log']['profile_name'] \
                        not in available_log_profiles:
                    return 422, f"Invalid NGINX App Protect WAF log profile " \
                                f"[{httpServer['app_protect']['log']['profile_name']}] referenced by HTTP server " \
                                f"[{httpServer['name']}]"

            # Check policy names referenced in HTTP servers[].locations[]
            for location in httpServer['locations']:
                if 'app_protect' in location:
                    if 'policy' in location['app_protect'] and location['app_protect']['policy'] not in allPolicyNames:
                        return 422, f"Unknown NGINX App Protect WAF policy [{location['app_protect']['policy']}] " \
                                    f"referenced by HTTP server [{httpServer['name']}] location [{location['uri']}]"

                    if 'log' in httpServer['app_protect'] and httpServer['app_protect']['log']['profile_name'] \
                            not in available_log_profiles:
                        return 422, f"Invalid NGINX App Protect WAF log profile " \
                                    f"[{httpServer['app_protect']['log']['profile_name']}] referenced by HTTP server " \
                                    f"[{httpServer['name']}] location [{location['uri']}]"

    return 200, ""


# For the given declaration creates/updates NGINX App Protect WAF policies on NGINX Management Suite
# making sure that they are in sync with what is defined in the JSON declaration
# Returns a tuple with two dictionaries: all_policy_names_and_versions, all_policy_active_names_and_uids
def provisionPolicies(nmsUrl: str, nmsUsername: str, nmsPassword: str, declaration: dict):
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

    for p in declaration['output']['nms']['policies']:
        policy_name = p['name']
        policy_active_tag = p['active_tag']

        # Iterates over all NGINX App Protect policies
        if p['type'] == 'app_protect':
            # Iterates over all policy versions
            for policyVersion in p['versions']:
                status, policyBody = Contrib.GitOps.getObjectFromRepo(policyVersion['contents'])

                if status != 200:
                    return JSONResponse(
                        status_code=422,
                        content={"code": status,
                                 "details": policyBody}
                    )

                # Create the NGINX App Protect policy on NMS
                r = __definePolicyOnNMS__(
                    nmsUrl=nmsUrl, nmsUsername=nmsUsername, nmsPassword=nmsPassword,
                    policyName=policy_name,
                    policyDisplayName=policyVersion['displayName'],
                    policyDescription=policyVersion['description'],
                    policyJson=policyBody
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
                        #print(f"=> Stored policy {policy_name}")
                        all_policy_names_and_versions[policy_name] = []

                    # Stores the policy version
                    uid = json.loads(r.text)['metadata']['uid']
                    tag = policyVersion['tag']

                    if policy_active_tag == tag:
                        all_policy_active_names_and_uids[policy_name] = uid

                    all_policy_names_and_versions[policy_name].append({'tag': tag, 'uid': uid})
                    #print(f"=> Stored policy [{policy_name}] tag [{tag}] uid [{uid}]")

    #print(f"=> All provisioned policies {all_policy_names_and_versions}")
    #print(f"=> All active uids {all_policy_active_names_and_uids}")

    return all_policy_names_and_versions, all_policy_active_names_and_uids


# Publish a NGINX App Protect WAF policy making it active
# activePolicyUids is a dict { "policy_name": "active_uid", [...] }
def makePolicyActive(nmsUrl: str, nmsUsername: str, nmsPassword: str, activePolicyUids: dict, instanceGroupUid: str):
    for policyName in activePolicyUids:
        body = {
            "publications": [
                {
                    "policyContent": {
                        "name": f'{policyName}',
                        "uid": f'{activePolicyUids[policyName]}'
                    },
                    "instanceGroups": [
                        f'{instanceGroupUid}'
                    ]
                }
            ]
        }

        #print(f"=> Activating policy [{policyName}] [{activePolicyUids[policyName]}]")

        requests.post(url=f'{nmsUrl}/api/platform/v1/security/publish', auth=(nmsUsername, nmsPassword),
                      data=json.dumps(body), headers={'Content-Type': 'application/json'}, verify=False)

    return


# For the given declaration creates/updates NGINX App Protect WAF policies on NGINX Management Suite
# making sure that they are in sync with what is defined in the JSON declaration
# Returns a tuple: status, response payload
def cleanPolicyLeftovers(nmsUrl: str, nmsUsername: str, nmsPassword: str, currentPolicies: dict):
    # Fetch all policies currently defined on the control plane
    allNMSPolicies = __getAllPolicies__(nmsUrl=nmsUrl, nmsUsername=nmsUsername, nmsPassword=nmsPassword)
    allNMSPoliciesJson = json.loads(allNMSPolicies.text)

    # Build a list of all uids for policies currently available on the control plane whose names match
    # currentPolicies (policies that have just been pushed to data plane)
    allUidsOnNMS = []
    for p in allNMSPoliciesJson['items']:
        #print(f"==> {p['metadata']['uid']}")
        if p['metadata']['name'] in currentPolicies:
            allUidsOnNMS.append(p['metadata']['uid'])

    allCurrentPoliciesUIDs = []
    for policyName in currentPolicies:
        #print(f"Found policy {policyName} => {currentPolicies[policyName]}")
        for tag in currentPolicies[policyName]:
            allCurrentPoliciesUIDs.append(tag['uid'])

    #print(f"{len(allUidsOnNMS)} NMS UIDS {allUidsOnNMS}")
    #print(f"{len(allCurrentPoliciesUIDs)} NEW UIDS {allCurrentPoliciesUIDs}")

    uidsToRemove = numpy.setdiff1d(allUidsOnNMS, allCurrentPoliciesUIDs)

    #print(f"{len(uidsToRemove)} Policy UIDs to remove {uidsToRemove}")

    for uid in uidsToRemove:
        #print(f"=> Deleting policy {uid}")
        __deletePolicy__(nmsUrl=nmsUrl, nmsUsername=nmsUsername, nmsPassword=nmsPassword, policyUid=uid)


    return