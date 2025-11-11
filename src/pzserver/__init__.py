"""
PzServer: responsible for managing user interactions with the Pz Server app
Catalog:
SpeczCatalog:
TrainingSet:
"""

from .catalog import Catalog, SpeczCatalog, TrainingSet
from .core import PzServer
from .pipeline import Pipeline

# Import version information
try:
    from ._version import __version__
except ImportError:
    __version__ = "unknown"


def get_version():
    """
    Get the version of the pzserver package.
    
    Returns:
        str: The version string of the package.
    """
    return __version__
