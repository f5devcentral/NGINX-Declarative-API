"""
NGINX Instance Manager support functions
"""

import requests
import json

import v4_0.GitOps

from fastapi.responses import Response, JSONResponse


# Fetch an instance group UID from NGINX Instance Manager
# Return None if not found
def getNIMInstanceGroupUid(nmsUrl: str, nmsUsername: str, nmsPassword: str, instanceGroupName: str):
    # Retrieve instance group uid
    ig = requests.get(url=f'{nmsUrl}/api/platform/v1/instance-groups', auth=(nmsUsername, nmsPassword),
                      verify=False)

    if ig.status_code != 200:
        return None

    # Get the instance group id
    igUid = None
    igJson = json.loads(ig.text)
    for i in igJson['items']:
        if i['name'] == instanceGroupName:
            igUid = i['uid']

    return igUid
