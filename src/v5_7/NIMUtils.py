"""
NGINX Instance Manager support utility functions
"""

import json
from collections import namedtuple

import requests
from typing import Tuple, Optional
from AppLogger import AppLogger, get_logger


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
    logger = get_logger()

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
            uid = item.get('uid','')
            logger.debug(f"Found instance group [{instanceGroupName}] with uid [{uid}] NIM [{nmsUrl}]")
            return 200, uid

    return 404, f"instance group [{instanceGroupName}] not found"
