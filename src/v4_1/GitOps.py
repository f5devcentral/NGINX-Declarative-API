"""
GitOps support functions
"""

import base64
import requests

from requests import ReadTimeout, HTTPError, Timeout, ConnectionError, ConnectTimeout
from typing import List

# pydantic models
from V4_1_NginxConfigDeclaration import *


# Fetches a URL content
def __fetchfromsourceoftruth__(url, headers = {} ):
    # Object is fetched from external repository
    try:
        reply = requests.get(url = url, headers = headers, verify=False)
    except (ConnectTimeout, HTTPError, ReadTimeout, Timeout, ConnectionError):
        return 408, "URL " + url + " unreachable"

    return reply.status_code, reply.text


# If content starts with http(s):// fetches the object and return it b64-encoded by default.
# base64Encode to be set to False to disable b64 encoding
# Returns the status original content otherwise.
# Return is a tuple: status_code, content
def getObjectFromRepo(object: ObjectFromSourceOfTruth, authProfiles: Authentication={}, base64Encode: bool=True):
    status_code = 200
    response = object

    if object:
        if object['content'].lower().startswith(("http://","https://")):
            # Object is fetched from external repository
            headers = {}

            # Set server authentication if needed
            if authProfiles and 'server' in authProfiles:
                for authP in authProfiles['server']:
                    if object['authentication'][0]['profile'] == authP['name']:
                        # Sets up authentication
                        if authP['type'].lower() == 'token':
                            authToken = authP['token']['token']
                            authTokenType = authP['token']['type']
                            authTokenLocation = authP['token']['location']

                            if authTokenType.lower() == 'bearer':
                                headers['Authorization'] = f"Bearer {authToken}"
                            elif authTokenType.lower() == 'header':
                                headers[authTokenLocation] = authToken

            status_code, fetchedContent = __fetchfromsourceoftruth__(url = object['content'], headers = headers)

            if status_code == 200:
                if base64Encode == True:
                    fetchedContent = base64.b64encode(bytes(fetchedContent, 'utf-8')).decode('utf-8')
                else:
                    fetchedContent = bytes(fetchedContent, 'utf-8').decode("utf-8")

            response['content'] = fetchedContent

    return status_code, response