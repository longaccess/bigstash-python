from __future__ import unicode_literals, print_function
import os
import hashlib
import logging
import collections
import os.path
from datetime import datetime
from cached_property import cached_property
from functools import partial
from BigStash import filename, models
from six.moves import filter, map
from itertools import starmap, chain


log = logging.getLogger('bigstash.manifest')


class Manifest(models.ModelBase, collections.MutableMapping):
    def __init__(self, files=None, title=None, *args, **kwargs):
        super(Manifest, self).__init__(
            size=0, *args, **kwargs)
        self._base = None
        self._slots.append('source')
        self._store = dict()
        self._slots.append('title')
        self._title = title
        self._slots.append('files')
        for i, f in enumerate(files, start=1):
            self[i] = f

    def __getitem__(self, key):
        return models.ManifestFile(
            base=self._base, id=key, **dict(self._store[key].items()))

    def __delitem__(self, key):
        del self._store[key]

    def __setitem__(self, key, value):
        if not isinstance(value, models.File):
            raise ValueError("Manifest values must be File objects")
        if key in self._store:
            raise ValueError("Manifest values can only be written once")
        self.size += value.size
        if self._base is None:
            self._base = value.original_path
        self._base = os.path.dirname(
            os.path.commonprefix([self._base, value.original_path]))
        self._store[key] = value

    def __iter__(self):
        for k in self._store.keys():
            yield self[k]

    def __len__(self):
        return len(self._store)

    @property
    def base(self):
        return filename.toposix(self._base)

    @property
    def source(self):
        return {'prefix': self._base}

    @cached_property
    def title(self):
        if self._title:
            return self._title
        elif self.base and self.base != '/':
            return os.path.basename(os.path.normpath(self.base))
        else:
            return 'upload-{}'.format(datetime.now().date().isoformat())

    @property
    def files(self):
        return list(self)

    @classmethod
    def from_paths(cls, paths, title=''):
        errors = []

        def ignored(path, reason, *args):
            log.debug("Ignoring {}: {}".format(path, reason))

        def invalid(path, reason, *args):
            errors.append((path, reason))
            log.debug("Invalid file {}: {}".format(path, reason))

        def _include_file(path):
            if not os.path.exists(path):
                return invalid(path, "File doesn't exist")

            return not any(chain(
                starmap(partial(ignored, path), filename.should_ignore(path)),
                starmap(partial(invalid, path), filename.is_invalid(path))))

        def _walk_dirs(paths):
            for path in paths:
                if os.path.isdir(path):
                    for r, _, files in os.walk(path):
                        absfiles = (os.path.abspath(os.path.join(r, p))
                                    for p in files)
                        for p in filter(_include_file, absfiles):
                            yield p
                else:
                    path = os.path.abspath(path)
                    if _include_file(path):
                        yield path

        def _tofile(path):
            return models.File(
                original_path=path, size=os.path.getsize(path),
                last_modified=os.path.getmtime(path),
                md5=hashlib.md5(open(path, 'rb').read()).hexdigest())

        files = map(_tofile, map(os.path.abspath, _walk_dirs(paths)))

        return (cls(title=title, files=files), errors)
