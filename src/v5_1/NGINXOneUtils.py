"""
NGINX One support functions
"""

import requests
import json


# Fetch a cluster ID from NGINX One
# Return None if not found
def getClusterId(nOneUrl: str, nOneToken: str, nameSpace: str, configSyncGroupName: str):
    # Retrieve instance group uid
    cluster = requests.get(url=f'{nOneUrl}/api/nginx/one/namespaces/{nameSpace}/clusters',
                      verify=False, headers = {"Authorization": f"Bearer APIToken {nOneToken}"})

    if cluster.status_code != 200:
        return cluster.status_code, "NGINX One authorization failed"

    # Get the instance group id
    igUid = None
    igJson = json.loads(cluster.text)
    for i in igJson['items']:
        if i['name'] == configSyncGroupName:
            igUid = i['object_id']

    if igUid is None:
        return 404, f"config sync group [{configSyncGroupName}] not found"

    return 200, igUid
