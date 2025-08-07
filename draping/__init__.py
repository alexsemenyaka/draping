

"""
draping: Apply and remove decorators to the fumctions (both sync and async) on-fly
"""

import importlib.metadata

_metadata = importlib.metadata.metadata("draping")
__version__ = _metadata["Version"]
__author__ = _metadata["Author-email"]
__license__ = _metadata["License"]

__all__ = [
]
