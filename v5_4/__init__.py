"""Legacy import-compatibility package for historical ``v5_4`` modules.

The codebase now ships ``v5_5`` implementations. This package preserves
``import v5_4.*`` paths used by tests and older integrations by exposing
shim modules that re-export from ``v5_5``.
"""

__all__ = [
    'DeclarationPatcher',
    'MiscUtils',
    'OpenAPIParser',
]
