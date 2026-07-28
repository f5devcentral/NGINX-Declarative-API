"""
NGINX Instance Manager support utility functions
"""

import json
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

    ig = requests.get(url=url, auth=auth, verify=False)
    if ig.status_code != 200:
        if ig.status_code == 401:
            return ig.status_code, "NGINX Instance Manager authentication failed"
        else:
            return ig.status_code, f"Error fetching instance group [{ig.text}]"

    igJson = json.loads(ig.text)
    for item in igJson.get('items', []):
        if item.get('name') == instanceGroupName:
            return 200, item.get('uid')

    return 404, f"instance group [{instanceGroupName}] not found"
