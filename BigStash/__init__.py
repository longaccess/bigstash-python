from .version import get_versions
__version__ = get_versions()['version']
del get_versions

from .auth import BigStashAuth
from .api import BigStashAPI
