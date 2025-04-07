""""
Asynchronous declarations support
"""

import pickle

import v5_3.MiscUtils
from NcgRedis import NcgRedis

# pydantic models
from V5_3_NginxConfigDeclaration import ConfigDeclaration

#
# Check if the incoming request is asynchronous
#
def checkIfAsynch(declaration: ConfigDeclaration, method: str, apiVersion: str):
    djson = declaration.model_dump();

    if djson['output']['synchronous']:
        # Synchronous declaration, normal processing
        return None, None

    # Asynchronous declaration, submit to FIFO queue
    configUid = str(v5_3.MiscUtils.getuniqueid())
    submissionPayload = {'declaration': declaration, 'method': method, 'configUid': configUid, "apiVersion": apiVersion}
    NcgRedis.asyncQueue.put(submissionPayload)

    response = {}
    response['code'] = 202
    response['message'] = f'Declaration submitted'
    response['configUid'] = configUid

    NcgRedis.redis.set(f'ncg.asynch.declaration.{configUid}', pickle.dumps(declaration))
    NcgRedis.redis.set(f'ncg.asynch.apiversion.{configUid}', apiVersion)

    return 202, response