"""
GitOps support functions
"""

import base64
import requests

from fastapi.responses import JSONResponse
from requests import ReadTimeout, HTTPError, Timeout, ConnectionError


# Fetches a URL content
def __fetchfromsourceoftruth__(url):
    # Policy must be fetched from external repository
    try:
        reply = requests.get(url=url, verify=False)
    except (ConnectTimeout, HTTPError, ReadTimeout, Timeout, ConnectionError):
        return 503, "URL " + url + " unreachable"

    return reply.status_code, reply.text


# If content starts with http(s):// fetches the object and return it b64-encoded
# Returns the original content otherwise
def getObjectFromRepo(content: str):
    if content.lower().startswith("http://") or content.lower().startswith("https://"):
        # Policy is fetched from external repository
        status_code, content = __fetchfromsourceoftruth__(content)

        if status_code != 200:
            return JSONResponse(
                status_code=422,
                content={"code": 422,
                         "details": "Invalid request " + content + " HTTP code " + str(
                             status_code)}
            )

        content = base64.b64encode(bytes(content, 'utf-8')).decode('utf-8')

    return content