"""
NGINX One support functions
"""

import requests
import json


# Fetch a cluster ID from NGINX One
# Return None if not found
def getClusterId(nOneUrl: str, nOneToken: str, nameSpace: str, clusterName: str):
    # Retrieve instance group uid
    print(f"URL {nOneUrl} namespace {nameSpace} cluster {clusterName} token {nOneToken}")

    cluster = requests.get(url=f'{nOneUrl}/api/nginx/one/namespaces/{nameSpace}/clusters',
                      verify=False, headers = {"Authorization": f"Bearer {nOneToken}"})

    if cluster.status_code != 200:
        return cluster.status_code, "NGINX One authorization failed"

    # Get the instance group id
    igUid = None
    igJson = json.loads(cluster.text)
    for i in igJson['items']:
        if i['name'] == clusterName:
            igUid = i['object_id']

    if igUid is None:
        return 404, f"cluster {clusterName} not found"

    return 200, igUid
