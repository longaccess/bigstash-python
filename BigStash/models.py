import six
from itertools import chain


class ModelBase(object):
    def __init__(self, *args, **kwargs):
        self._slots = []
        for (key, value) in six.iteritems(kwargs):
            self._slots.append(key)
            setattr(self, key, value)

    def __repr__(self):
        s = ["{ " + super(ModelBase, self).__repr__()]
        for slot in self._slots:
            r = "\n\t".join(repr(getattr(self, slot)).split("\n"))
            s.append("\t{} = {}".format(slot, r))
        return "\n".join(s) + "}"


class APIRoot(ModelBase):
    pass


class URLObject(ModelBase):
    def __unicode__(self):
        return "{}: {}".format(self.__class__.__name__, self.url)


class ObjectList(object):
    def __init__(self, klass, objects=[], next=None):
        self.klass = klass
        self.objects = objects
        self.next = next

    def next_iter(self, url):
        raise NotImplementedError(
            "Must implement next_iter for partial lists")

    def _lister(self):
        if self.next is None:
            return iter(self.objects)
        return chain(self.objects, self.next_iter(self.next))

    def __iter__(self):
        return (self.klass(**data) for data in self._lister())


class Archive(URLObject):
    pass


class Upload(URLObject):
    def __init__(self, *args, **kwargs):
        super(Upload, self).__init__(*args, **kwargs)
        if hasattr(self, 's3') and self.s3 is not None:
            self.s3 = BucketToken(**self.s3)
        if hasattr(self, 'archive') and self.archive is not None:
            self.archive = Archive(**self.archive)


class BucketToken(URLObject):
    pass


class User(URLObject):

    def __init__(self, *args, **kwargs):
        super(User, self).__init__(*args, **kwargs)
        if hasattr(self, 'archives') and self.archives is not None:
            self.archives = ObjectList(
                Archive, self.archive['results'], self.archive['next'])
