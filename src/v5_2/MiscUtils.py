"""
Support functions
"""

import re
import json
import yaml
import uuid


def getDictKey(_dict: dict, key_lookup: str, separator='.'):
    """
        Searches for a nested key in a dictionary and returns its value, or None if nothing was found.
        key_lookup must be a string where each key is deparated by a given "separator" character, which by default is a dot
    """
    keys = key_lookup.split(separator)
    subdict = _dict

    for k in keys:
        subdict = subdict[k] if k in subdict else None
        if subdict is None:
          return None

    return subdict

"""
Jinja2 regexp filter
"""
def regex_replace(s, find, replace):
    return re.sub(find, replace, s)

"""
JSON/YAML detection
"""
def yaml_or_json(document: str):
    try:
        json.load(document)
        return 'json'
    except Exception:
        return 'yaml'

"""
YAML to JSON conversion
"""
def yaml_to_json(document: str):
    return json.dumps(yaml.safe_load(document))


"""
JSON TO YAML conversion
"""
def json_to_yaml(document: str):
    return yaml.dump(json.loads(document))


"""
Returns a unique ID
"""
def getuniqueid():
    return uuid.uuid4()