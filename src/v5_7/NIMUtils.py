"""
NGINX Instance Manager support utility functions
"""

import json
from collections import namedtuple

import requests
from typing import Tuple, Optional


def getNIMInstanceGroupUid(
    nmsUrl: str,
    nmsUsername: str,
    nmsPassword: str,
    instanceGroupName: str
) -> Tuple[int,str]:
    """
    Fetches an instance group UID from NGINX Instance Manager (NMS).

    Args:
        nmsUrl (str): NMS base URL.
        nmsUsername (str): Username.
        nmsPassword (str): Password.
        instanceGroupName (str): Target instance group name.

    Returns:
        Optional[str]: Instance group UID string if found, otherwise None.
    """
    url = f'{nmsUrl}/api/platform/v1/instance-groups?limit=100'
    auth = (nmsUsername, nmsPassword)

    try:
        ig = requests.get(url=url, auth=auth, verify=False)
        status_code = ig.status_code
        text = ig.text
    except Exception as e:
        status_code = 502
        text = e

    if status_code != 200:
        if status_code == 401:
            return status_code, "NGINX Instance Manager authentication failed"
        else:
            return status_code, f"Error fetching instance group [{text}]"

    igJson = json.loads(text)
    for item in igJson.get('items', []):
        if item.get('name') == instanceGroupName:
            return 200, item.get('uid','')

    return 404, f"instance group [{instanceGroupName}] not found"
