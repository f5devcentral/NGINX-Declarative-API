"""
NGINX One support functions
"""

import requests
import json


# Fetch a cluster ID from NGINX One
# Return None if not found
def getConfigSyncGroupId(nOneUrl: str, nOneToken: str, nameSpace: str, configSyncGroupName: str):
    # Retrieve config sync group uid
    cSyncGroup = requests.get(url=f'{nOneUrl}/api/nginx/one/namespaces/{nameSpace}/clusters',
                      verify=False, headers = {"Authorization": f"Bearer APIToken {nOneToken}"})

    if cSyncGroup.status_code != 200:
        if cSyncGroup.status_code == 401:
            return cSyncGroup.status_code, "NGINX One authentication failed"
        else:
            return cSyncGroup.status_code, f"Error fetching config sync group uid: {cSyncGroup.text}"

    # Get the instance group id
    igUid = None
    igJson = json.loads(cSyncGroup.text)
    for i in igJson['items']:
        if i['name'] == configSyncGroupName:
            igUid = i['object_id']

    if igUid is None:
        return 404, f"config sync group [{configSyncGroupName}] not found"

    return 200, igUid
