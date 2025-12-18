"""
Lightweight shim to satisfy `pygame.pkgdata` API using importlib.resources.
This module is inserted into `sys.modules['pygame.pkgdata']` before importing
`pygame` so that `pkg_resources` is not required and the deprecation warning is avoided.

It implements `resource_stream(package, resource)` and `resource_exists(package, resource)`
with semantics similar to `pkg_resources`.
"""
from importlib import resources
import io
import types

__all__ = ["resource_stream", "resource_exists"]


def resource_stream(package, resource):
    """Return a binary file-like object for the resource.

    `package` can be a module or a string module name acceptable to importlib.resources.
    """
    try:
        return resources.open_binary(package, resource)
    except Exception:
        # If open_binary fails, try to locate the resource via files()
        try:
            path = resources.files(package).joinpath(resource)
            return path.open('rb')
        except Exception:
            # Fallback: empty BytesIO to avoid crashes in pygame when resource missing
            return io.BytesIO(b"")


def resource_exists(package, resource):
    try:
        # Use the high-level API when possible
        return resources.is_resource(package, resource)
    except Exception:
        try:
            path = resources.files(package).joinpath(resource)
            return path.exists()
        except Exception:
            return False

# Expose as a module object so we can insert into sys.modules easily
_module = types.ModuleType('pygame.pkgdata')
_module.resource_stream = resource_stream
_module.resource_exists = resource_exists

# For convenience when someone imports the module directly
resource_stream.__module__ = 'pygame.pkgdata'
resource_exists.__module__ = 'pygame.pkgdata'

# Provide the module object for insertion
pygame_pkgdata_module = _module
