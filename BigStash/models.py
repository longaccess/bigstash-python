import os.path
import six
from BigStash import filename
from BigStash.structures import ObjectList, CaseInsensitiveDict
from collections import Mapping

from datetime import timedelta, tzinfo
from datetime import datetime as dt


try:
    from datetime import timezone
    utc = timezone.utc
except ImportError as e:
    ZERO = timedelta(0)

    class UTC(tzinfo):
        """UTC"""

        def utcoffset(self, dt):
            return ZERO

        def tzname(self, dt):
            return "UTC"

        def dst(self, dt):
            return ZERO

    utc = UTC()


class ModelMeta(CaseInsensitiveDict):
    fields = [
        'content-type',
        'last-modified'
    ]

    defaults = {
        'content-type': 'application/json'
    }

    def _filter_fields(self, data):
        for k in self.fields:
            if k in data:
                yield (k, data[k])
            elif k in self.defaults:
                yield (k, self.defaults[k])

    def __init__(self, data=None, **kwargs):
        kw = {}
        if data is not None:
            kw = dict(self._filter_fields(data))
        kw.update(dict(self._filter_fields(kwargs)))
        super(ModelMeta, self).__init__(**kw)


class ModelBase(object):
    def __init__(self, meta=None, *args, **kwargs):
        self._slots = []
        self._meta = ModelMeta(meta or {})
        for key, value in six.iteritems(kwargs):
            if not key.startswith('_'):
                self._slots.append(key)
                setattr(self, key, value)

    def __repr__(self):
        meta = ""
        if len(self._meta) > 0:
            meta = repr(self._meta)

        s = ["{ " + super(ModelBase, self).__repr__()]
        for slot, value in self.items():
            r = "\n\t".join(repr(value).split("\n"))
            s.append("\t{} = {}".format(slot, r))
        return "\n".join(s) + "}" + meta

    def items(self):
        for slot in self._slots:
            yield (slot, getattr(self, slot))

    def get_meta(self, attr):
        return self._meta.get(attr, None)

    def update(self, patch, meta):
        for key in self._slots:
            if key in patch:
                setattr(self, key, patch[key])
        self._meta.update(meta)


class APIRoot(ModelBase):
    pass


class URLObject(ModelBase):
    _href_attr = 'href'

    def __unicode__(self):
        return "{}: {}".format(
            self.__class__.__name__, getattr(self, self._href_attr, 'n/a'))


class Archive(URLObject):
    def __init__(self, *args, **kwargs):
        super(Archive, self).__init__(*args, **kwargs)
        if hasattr(self, 'files') and self.files is not None:
            if not isinstance(self.files, ObjectList):
                self.files = ObjectList(File, [], self.files)


class Upload(URLObject):
    def __init__(self, *args, **kwargs):
        super(Upload, self).__init__(*args, **kwargs)
        if hasattr(self, 's3') and self.s3 is not None:
            self.s3 = BucketToken(**self.s3)
        if hasattr(self, 'archive') and self.archive is not None:
            if not isinstance(self.archive, Archive):
                if isinstance(self.archive, Mapping):
                    self.archive = Archive(**self.archive)
                else:
                    self.archive = Archive(url=self.archive)


class BucketToken(URLObject):
    pass


class User(URLObject):

    def __init__(self, *args, **kwargs):
        super(User, self).__init__(*args, **kwargs)
        if hasattr(self, 'archives') and self.archives is not None:
            self.archives = ObjectList(
                Archive, self.archives['results'], self.archives['next'])


class Notification(ModelBase):
    pass


class File(ModelBase):
    def __init__(self, *args, **kwargs):
        if 'last_modified' in kwargs:
            try:
                kwargs['last_modified'] = dt.fromtimestamp(
                    kwargs['last_modified'], tz=utc)
            except TypeError:
                pass
        super(File, self).__init__(*args, **kwargs)


class ManifestFile(File):
    def __init__(self, *args, **kwargs):
        self._base = kwargs.pop('base', '')
        super(ManifestFile, self).__init__(*args, **kwargs)
        self._slots.append('path')

    @property
    def path(self):
        return filename.toposix(
            os.path.relpath(self.original_path, self._base))
