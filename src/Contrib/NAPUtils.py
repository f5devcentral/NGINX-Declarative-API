"""
NGINX App Protect support functions
"""

import requests
import json

from fastapi.responses import Response, JSONResponse


# Creates a NGINX App Protect policy on NMS
# Returns a tuple {status_code,text}. status_code is 201 if successful
def createPolicy(nmsUrl: str, nmsUsername: str, nmsPassword: str, policyName: str, policyDisplayName: str,
                 policyDescription: str, policyJson: str):

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

    r = requests.post(url=f"{nmsUrl}/api/platform/v1/security/policies?isNewRevision=true",
                      data=json.dumps(policyCreationPayload),
                      headers={'Content-Type': 'application/json'},
                      auth=(nmsUsername, nmsPassword),
                      verify=False)

    # Check if this is a new policy with no existing versions. If so we POST the initial version
    # If policy exists we get a HTTP/201 and a new version is added to the policy
    if r.status_code == 404:
        r = requests.post(url=f"{nmsUrl}/api/platform/v1/security/policies",
                          data=json.dumps(policyCreationPayload),
                          headers={'Content-Type': 'application/json'},
                          auth=(nmsUsername, nmsPassword),
                          verify=False)

    return r
