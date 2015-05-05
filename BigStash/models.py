import os.path
import six
from BigStash import filename
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


class ModelBase(object):
    def __init__(self, *args, **kwargs):
        self._slots = []
        for key, value in six.iteritems(kwargs):
            self._slots.append(key)
            setattr(self, key, value)

    def __repr__(self):
        s = ["{ " + super(ModelBase, self).__repr__()]
        for slot, value in self.items():
            r = "\n\t".join(repr(value).split("\n"))
            s.append("\t{} = {}".format(slot, r))
        return "\n".join(s) + "}"

    def items(self):
        for slot in self._slots:
            yield (slot, getattr(self, slot))


class APIRoot(ModelBase):
    pass


class URLObject(ModelBase):
    _href_attr = 'href'

    def __unicode__(self):
        return "{}: {}".format(
            self.__class__.__name__, getattr(self, self._href_attr, 'n/a'))


class ObjectList(object):
    def __init__(self, klass, objects=[], next=None):
        self.klass = klass
        self.objects = objects
        self.next = next

    def __iter__(self):
        return (self.klass(**data) for data in self.objects)

    def __repr__(self):
        s = []
        for obj in self:
            s.append("\t" + "\n\t".join(repr(obj).split("\n")))
        if self.next is not None:
            s.append("\t...")
        return ("{ " + super(ObjectList, self).__repr__() +
                " [\n" + ",\n".join(s) + "]}")


class Archive(URLObject):
    pass


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
