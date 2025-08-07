"""
draping: Apply and remove decorators to the fumctions (both sync and async) on-fly
"""

import importlib.metadata

from .draping import decorate, redecorate, undecorate

_metadata = importlib.metadata.metadata("draping")
__version__ = _metadata["Version"]
__author__ = _metadata["Author-email"]
__license__ = _metadata["License"]

__all__ = [
"decorate", "redecorate", "undecorate",
]
