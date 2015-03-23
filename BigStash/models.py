import six


class ModelBase(object):
    def __init__(self, *args, **kwargs):
        for (key, value) in six.iteritems(kwargs):
            setattr(self, key, value)


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
