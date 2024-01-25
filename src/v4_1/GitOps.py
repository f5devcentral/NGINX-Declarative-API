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
def __fetchfromsourceoftruth__(url):
    # Object is fetched from external repository
    try:
        reply = requests.get(url=url, verify=False)
    except (ConnectTimeout, HTTPError, ReadTimeout, Timeout, ConnectionError):
        return 408, "URL " + url + " unreachable"

    return reply.status_code, reply.text


# If content starts with http(s):// fetches the object and return it b64-encoded by default.
# base64Encode to be set to False to disable b64 encoding
# Returns the status original content otherwise.
# Return is a tuple: status_code, content
def getObjectFromRepo(object: ObjectFromSourceOfTruth, authProfiles: List[LocationAuthServer]=[], base64Encode: bool=True):
    status_code = 200
    content = ""

    print("=> SOURCE OF TRUTH")
    print(f"- object: {object['authentication'] if 'authentication' in object else 'NONE'}")
    print(f"- auth  : {authProfiles}")

    if object:
        if object['content'].lower().startswith("http://") or object['content'].lower().startswith("https://"):
            # Object is fetched from external repository

            # Set server authentication if needed

            status_code, content = __fetchfromsourceoftruth__(object['content'])

            if status_code == 200:
                if base64Encode == True:
                    content = base64.b64encode(bytes(content, 'utf-8')).decode('utf-8')
                else:
                    content = bytes(content, 'utf-8').decode("utf-8")

    return status_code, content