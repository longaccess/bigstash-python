import six
import collections
import os.path
from datetime import datetime
from BigStash import models
from cached_property import cached_property


class Manifest(models.ModelBase, collections.MutableMapping):
    """A dictionary that applies an arbitrary key-altering
       function before accessing the keys"""

    def __init__(self, files=[], title=None, *args, **kwargs):
        super(Manifest, self).__init__(
            size=0, base='', *args, **kwargs)
        self._store = dict()
        self.size = 0
        self.base = ''
        self._slots.append('title')
        self._title = title
        self._slots.append('files')
        self.update((f.path, f) for f in files)

    def __getitem__(self, key):
        return self._store[key]

    def __delitem__(self, key):
        del self._store[key]

    def __setitem__(self, key, value):
        if not isinstance(value, models.File):
            raise ValueError("Manifest values must be File objects")
        if key in self._store:
            raise ValueError("Manifest values can only be written once")
        self.size += value.size
        self.base = os.path.dirname(
            os.path.commonprefix([self.base, value.path]))
        self._store[key] = value

    def __iter__(self):
        return six.itervalues(self._store)

    def __len__(self):
        return len(self._store)

    @cached_property
    def title(self):
        if self.base:
            return os.path.basename(os.path.normpath(self.base))
        return 'upload-{}'.format(datetime.now().date().isoformat())

    @property
    def files(self):
        return list(six.itervalues(self._store))
