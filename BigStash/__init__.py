from .version import get_versions
__version__ = get_versions()['version']
del get_versions

from .auth import BigStashAuth
from .api import BigStashAPI
from .conf import BigStashAPISettings
from .error import BigStashError

__all__ = ['__version__', 'BigStashAuth', 'BigStashAPI',
           'BigStashAPISettings', 'BigStashError']
