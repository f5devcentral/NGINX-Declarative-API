"""
Support utility functions
"""

import re
import json
import yaml
import uuid
import socket
import base64
import ipaddress
from typing import Any, Tuple, Optional, Literal


PortMode = Literal["none", "optional", "optional_no_wildcard", "required"]
FQDN_REGEX = re.compile(
    r"^(?=.{1,253}$)"
    r"(?:(?!-)[A-Za-z0-9-]{1,63}(?<!-)\.)+"
    r"(?!-)(?!\d+$)[A-Za-z0-9-]{2,63}(?<!-)$"
)

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


def _is_valid_port(port_str: str) -> bool:
    if not port_str.isascii() or not port_str.isdigit():
        return False
    if len(port_str) > 1 and port_str.startswith("0"):
        return False
    return 1 <= int(port_str) <= 65535
def _is_valid_address(host: str, allow_wildcard: bool = False) -> bool:
    if allow_wildcard and host == "*":
        return True
    # 1. Check IPv4 or IPv6
    try:
        ipaddress.ip_address(host)
        return True
    except ValueError:
        pass
    # 2. Check FQDN (with IDN / Punycode support)
    candidate = host[:-1] if host.endswith(".") else host
    if not candidate:
        return False
    try:
        ascii_host = candidate.encode("idna").decode("ascii")
    except UnicodeError:
        return False
    return bool(FQDN_REGEX.match(ascii_host))
def validate_host(v: str, port_mode: PortMode = "optional") -> bool:
    allow_wildcard = port_mode in ("optional", "required")
    # 1. Handle bracketed IPv6: [2001:db8::1] or [2001:db8::1]:8080
    if v.startswith("["):
        if v.endswith("]"):
            if port_mode == "required":
                return False
            host = v[1:-1]
        elif "]:" in v:
            if port_mode == "none":
                return False
            host, port_str = v[1:].rsplit("]:", 1)
            if not _is_valid_port(port_str):
                return False
        else:
            return False
        try:
            ipaddress.IPv6Address(host)
            return True
        except ValueError:
            return False
    # 2. Handle unbracketed input containing colon(s)
    if ":" in v:
        # When port is forbidden or optional, check if `v` is a raw IPv6 address first
        if port_mode in ("none", "optional", "optional_no_wildcard"):
            try:
                ipaddress.IPv6Address(v)
                return True
            except ValueError:
                if port_mode == "none":
                    return False
        # Otherwise, split the last ":port" segment (empty host like ":8080" is rejected)
        host, port_str = v.rsplit(":", 1)
        if not _is_valid_port(port_str):
            return False
        return _is_valid_address(host, allow_wildcard=allow_wildcard)
    # 3. Handle unbracketed input without colons
    if port_mode == "required":
        # Host is empty and only the mandatory port is specified (e.g. "8080")
        return _is_valid_port(v)
    if port_mode in ("optional", "optional_no_wildcard"):
        # Can be empty (""), a bare port ("8080"), "*" (if allowed), or a valid address
        if v == "" or _is_valid_port(v):
            return True
    return _is_valid_address(v, allow_wildcard=allow_wildcard)