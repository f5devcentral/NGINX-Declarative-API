"""
Asynchronous declarations support
"""

import json
import pickle
from typing import Optional, Tuple, Dict, Any

import v5_7.MiscUtils
from NcgRedis import NcgRedis

# pydantic models
from V5_7_NginxConfigDeclaration import ConfigDeclaration


def checkIfAsynch(
    declaration: ConfigDeclaration,
    method: str,
    apiVersion: str,
    configUid: str
) -> Tuple[Optional[int], Optional[Dict[str, Any]]]:
    """
    Check if the incoming request is asynchronous. If asynchronous, submits payload to FIFO queue.

    Args:
        declaration (ConfigDeclaration): The configuration declaration model instance.
        method (str): HTTP method.
        apiVersion (str): API version string.
        configUid (str): Unique configuration identifier.

    Returns:
        Tuple[Optional[int], Optional[Dict[str, Any]]]: Tuple of (status_code, response_dict),
        or (None, None) if synchronous processing is required.
    """
    djson = declaration.model_dump()

    if djson.get('output', {}).get('synchronous'):
        # Synchronous declaration, normal processing
        return None, None

    # Asynchronous declaration, submit to FIFO queue
    submissionUid = str(v5_7.MiscUtils.getuniqueid())
    submissionPayload = {
        'declaration': declaration,
        'method': method,
        'configUid': configUid,
        'apiVersion': apiVersion,
        'submissionUid': submissionUid
    }
    NcgRedis.asyncQueue.put(submissionPayload)

    response = {
        'code': 202,
        'message': 'Declaration submitted',
        'configUid': configUid,
        'submissionUid': submissionUid
    }

    NcgRedis.redis.set(f'ncg.async.submission.{submissionUid}', json.dumps(response))

    return 202, response