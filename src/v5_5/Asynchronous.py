""""
Asynchronous declarations support
"""
import json
import pickle

import v5_4.MiscUtils
from NcgRedis import NcgRedis

# pydantic models
from V5_4_NginxConfigDeclaration import ConfigDeclaration

#
# Check if the incoming request is asynchronous
#
def checkIfAsynch(declaration: ConfigDeclaration, method: str, apiVersion: str, configUid: str):
    djson = declaration.model_dump()

    if djson['output']['synchronous']:
        # Synchronous declaration, normal processing
        return None, None

    # Asynchronous declaration, submit to FIFO queue
    submissionUid = str(v5_4.MiscUtils.getuniqueid())
    submissionPayload = {'declaration': declaration, 'method': method, 'configUid': configUid, "apiVersion": apiVersion, "submissionUid": submissionUid}
    NcgRedis.asyncQueue.put(submissionPayload)

    response = {}
    response['code'] = 202
    response['message'] = f'Declaration submitted'
    response['configUid'] = configUid
    response['submissionUid'] = submissionUid

    NcgRedis.redis.set(f'ncg.async.submission.{submissionUid}', json.dumps(response))

    return 202, response