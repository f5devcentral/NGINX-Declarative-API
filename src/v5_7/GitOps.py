"""
GitOps support functions
"""

import base64
import requests
from typing import Tuple, Dict, Any
from requests import ReadTimeout, HTTPError, Timeout, ConnectionError, ConnectTimeout

import v5_7.MiscUtils

# pydantic models
from V5_7_NginxConfigDeclaration import *


def __fetchfromsourceoftruth__(url: str, headers: dict = {}) -> Tuple[int, str]:
    """
    Fetches content from an external source of truth URL.

    Args:
        url (str): Target HTTP/HTTPS URL.
        headers (dict, optional): Request HTTP headers.

    Returns:
        Tuple[int, str]: Status code and response text or error message.
    """
    try:
        reply = requests.get(url=url, headers=headers, verify=False)
    except (ConnectTimeout, HTTPError, ReadTimeout, Timeout, ConnectionError):
        return 408, f"URL {url} unreachable"

    return reply.status_code, reply.text


def _build_auth_headers(object_item: dict, authProfiles: dict) -> dict:
    """
    Constructs authorization headers for fetching content from external repositories.

    Args:
        object_item (dict): Object definition containing authentication requirements.
        authProfiles (dict): Available authentication profiles.

    Returns:
        dict: Headers dictionary populated with Authorization or custom header details.
    """
    headers = {}
    if not (authProfiles and 'server' in authProfiles and object_item.get('authentication')):
        return headers

    target_profile_name = object_item['authentication'][0].get('profile')
    for authP in authProfiles['server']:
        if target_profile_name == authP.get('name'):
            auth_type = authP.get('type', '').lower()
            if auth_type == 'token':
                token_data = authP.get('token', {})
                auth_token = token_data.get('token', '')
                token_type = token_data.get('type', '').lower()

                if token_type == 'bearer':
                    headers['Authorization'] = f"Bearer {auth_token}"
                elif token_type == 'basic':
                    username = token_data.get('username', '')
                    encoded_pwd = token_data.get('password', '')
                    password = base64.b64decode(encoded_pwd).decode('utf-8')
                    basic_credentials = f"{username}:{password}"
                    b64_creds = base64.b64encode(basic_credentials.encode('utf-8')).decode('utf-8')
                    headers['Authorization'] = f"Basic {b64_creds}"
                elif token_type == 'header':
                    header_location = token_data.get('location', '')
                    headers[header_location] = auth_token

    return headers


def getObjectFromRepo(
    object: ObjectFromSourceOfTruth,
    authProfiles: Authentication = {},
    base64Encode: bool = True
) -> Tuple[int, Any]:
    """
    Fetches object content from repository if URL is provided, or decodes content directly.

    Args:
        object (ObjectFromSourceOfTruth): Target object containing content location or data.
        authProfiles (Authentication, optional): Authentication profiles object.
        base64Encode (bool, optional): Whether to base64 encode result. Defaults to True.

    Returns:
        Tuple[int, Any]: Status code and updated object dictionary.
    """
    status_code = 200
    response = object

    if object:
        content_str = object.get('content', '')
        if content_str.lower().startswith(("http://", "https://")):
            headers = _build_auth_headers(object, authProfiles)
            status_code, fetchedContent = __fetchfromsourceoftruth__(url=content_str, headers=headers)

            if status_code == 200:
                if base64Encode:
                    fetchedContent = base64.b64encode(bytes(fetchedContent, 'utf-8')).decode('utf-8')
                else:
                    fetchedContent = bytes(fetchedContent, 'utf-8').decode("utf-8")
            else:
                fetchedContent = f"Error fetching {content_str}"

            response['content'] = fetchedContent
        else:
            if not base64Encode:
                if v5_7.MiscUtils.isBase64(content_str):
                    response['content'] = base64.b64decode(content_str).decode()
                else:
                    response['content'] = content_str

    return status_code, response