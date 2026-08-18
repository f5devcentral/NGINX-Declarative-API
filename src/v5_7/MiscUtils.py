"""
Support utility functions
"""

import re
import json
import yaml
import uuid
import socket
import base64
from typing import Any, Dict, Tuple, Optional


def getDictKey(_dict: dict, key_lookup: str, separator: str = '.') -> Optional[Any]:
    """
    Searches for a nested key in a dictionary and returns its value, or None if not found.

    Args:
        _dict (dict): Target dictionary to traverse.
        key_lookup (str): Dot-separated (or custom separator) key path string.
        separator (str, optional): Key path separator character. Defaults to '.'.

    Returns:
        Optional[Any]: The retrieved value if present, otherwise None.
    """
    keys = key_lookup.split(separator)
    subdict = _dict

    for k in keys:
        if isinstance(subdict, dict) and k in subdict:
            subdict = subdict[k]
        else:
            return None

    return subdict


def regex_replace(s: str, find: str, replace: str) -> str:
    """
    Jinja2 regex replacement filter function.

    Args:
        s (str): Source string.
        find (str): Regular expression pattern to search for.
        replace (str): Replacement string.

    Returns:
        str: Resulting string with pattern replaced.
    """
    return re.sub(find, replace, s)


def yaml_or_json(document: str) -> str:
    """
    Detects whether a given document string is JSON or YAML.

    Args:
        document (str): Target document content.

    Returns:
        str: 'json' if valid JSON, otherwise 'yaml'.
    """
    try:
        json.loads(document)
        return 'json'
    except Exception:
        return 'yaml'


def yaml_to_json(document: str) -> str:
    """
    Converts YAML document string to a JSON string.

    Args:
        document (str): Source YAML document content.

    Returns:
        str: Output JSON string.
    """
    return json.dumps(yaml.load(document, Loader=yaml.BaseLoader))


def json_to_yaml(document: str) -> str:
    """
    Converts JSON document string to a YAML string.

    Args:
        document (str): Source JSON document content.

    Returns:
        str: Output YAML string.
    """
    return yaml.dump(json.loads(document))


def getuniqueid() -> uuid.UUID:
    """
    Generates a unique UUID4 instance.

    Returns:
        uuid.UUID: Generated UUID.
    """
    return uuid.uuid4()


def resolveFQDN(fqdn: str) -> Tuple[bool, Any]:
    """
    Tests DNS resolution for a fully qualified domain name.

    Args:
        fqdn (str): Domain name to resolve.

    Returns:
        Tuple[bool, Any]: (True, IP address string) if successful, or (False, exception object) on failure.
    """
    try:
        return True, socket.gethostbyname(fqdn)
    except Exception as e:
        return False, e


def isBase64(s: str) -> bool:
    """
    Checks whether a string is base64 encoded.

    Args:
        s (str): Candidate string.

    Returns:
        bool: True if base64 encoded, False otherwise.
    """
    try:
        return base64.b64encode(base64.b64decode(s)) == bytes(s, "utf-8")
    except Exception:
        return False