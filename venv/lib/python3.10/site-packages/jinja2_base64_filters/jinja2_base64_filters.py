# coding: utf-8

"""Main module."""

from jinja2.ext import Extension
import base64


class Base64Filters(Extension):
    def __init__(self, environment):
        super(Base64Filters, self).__init__(environment)
        environment.filters["b64encode"] = base64encode
        environment.filters["b64decode"] = base64decode


def base64encode(string):
    """
    args:
        string (str)
    returns:
        string (str)
    """
    # b64encode take a byte-like object as input so we need to encode our string(str)
    # b64encode returns a byte-like object so we convert it to a str
    return base64.b64encode(string.encode()).decode()


def base64decode(string):
    """
    args:
        string (str)
    returns:
        string (str)
    """
    return base64.b64decode(string.encode()).decode()
