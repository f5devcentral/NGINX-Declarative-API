"""
NGINX One support utility functions
"""

import json
import requests
from typing import Tuple


def getConfigSyncGroupId(
    nOneUrl: str,
    nOneToken: str,
    nameSpace: str,
    configSyncGroupName: str
) -> Tuple[int, str]:
    """
    Fetches the Config Sync Group UID from NGINX One Console.

    Args:
        nOneUrl (str): Console base URL.
        nOneToken (str): API token.
        nameSpace (str): Target namespace.
        configSyncGroupName (str): Target config sync group name.

    Returns:
        Tuple[int, str]: Status code (200 on success) and config sync group UID string (or error description).
    """
    url = f'{nOneUrl}/api/nginx/one/namespaces/{nameSpace}/config-sync-groups?paginated=false'
    headers = {"Authorization": f"APIToken {nOneToken}"}

    try:
        cSyncGroup = requests.get(url=url, verify=False, headers=headers)
        status_code = cSyncGroup.status_code
        text = cSyncGroup.text
    except Exception as e:
        status_code = 502
        text = e

    if status_code != 200:
        if status_code == 401:
            return status_code, "NGINX One authentication failed"
        else:
            return cSyncGroup.status_code, f"Error fetching config sync group [{text}]"

    igJson = json.loads(text)
    for item in igJson.get('items', []):
        if item.get('name') == configSyncGroupName:
            return 200, item.get('object_id', '')

    return 404, f"config sync group [{configSyncGroupName}] not found"
