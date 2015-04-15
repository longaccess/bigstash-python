from __future__ import unicode_literals, print_function
import os
import hashlib
import logging
from functools import partial
from BigStash import filename, models
from BigStash.manifest import Manifest
from six.moves import filter, map
from itertools import starmap, chain


log = logging.getLogger('bigstash.upload')


class Upload(object):

    def __init__(self, api=None):
        if not api:
            raise TypeError("You must provide a BigStash API instance")
        self.api = api

    def archive(self, paths=[], title=''):
        if not paths:
            raise TypeError("You must provide at least a file path")

        errors = []

        def ignored(path, reason, *args):
            log.debug("Ignoring {}: {}".format(path, reason))

        def invalid(path, reason, *args):
            errors.append(path)
            log.debug("Invalid file {}: {}".format(path, reason))

        def _include_file(path):
            p = os.path.basename(path)
            return not any(chain(
                starmap(partial(ignored, path), filename.should_ignore(p)),
                starmap(partial(invalid, path), filename.is_invalid(p))))

        def _walk_dirs(paths):
            for path in paths:
                if os.path.isdir(path):
                    for r, _, files in os.walk(path):
                        for p in filter(_include_file, files):
                            yield os.path.join(r, p)
                elif _include_file(path):
                    yield path

        def _mkfile(path):
            return models.File(
                path=path,
                size=os.path.getsize(path),
                last_modified=os.path.getmtime(path),
                md5=hashlib.md5(open(path, 'rb').read()).hexdigest())

        files = (_mkfile(p) for p in map(os.path.abspath, _walk_dirs(paths)))

        manifest = Manifest(title=title, files=files)

        upload = None
        if not errors:
            archive = self.api.CreateArchive(
                title=manifest.title, size=manifest.size)
            upload = self.api.CreateUpload(archive=archive, manifest=manifest)
        return (upload, errors)
