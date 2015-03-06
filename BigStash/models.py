import six


class APIRoot(object):
    def __init__(self, *args, **kwargs):
        for (key, value) in six.iteritems(kwargs):
            setattr(self, key, value)


class Archive(object):

    def __init__(self, *args, **kwargs):
        for (key, value) in six.iteritems(kwargs):
            setattr(self, key, value)

    def __unicode__(self):
        return "Archive: %s" % self.url


class Upload(object):

    def __init__(self, *args, **kwargs):
        for (key, value) in six.iteritems(kwargs):
            if key == 's3':
                self.s3 = BucketToken(**value) if value else None
            else:
                setattr(self, key, value)

    def __unicode__(self):
        return "Upload: %s" % self.url


class BucketToken(object):

    def __init__(self, *args, **kwargs):
        for (key, value) in six.iteritems(kwargs):
            setattr(self, key, value)

    def __unicode__(self):
        return "BucketToken: %s" % self.url


class User(object):

    def __init__(self, *args, **kwargs):
        for (key, value) in six.iteritems(kwargs):
            if key == 'archives':
                if value:
                    self.archives = {
                        'count': value['count'],
                        'next': value['next'],
                        'previous': value['previous'],
                        'results': [Archive(**a) for a in value['results']]
                    }
            else:
                setattr(self, key, value)

    def __unicode__(self):
        return "User: %s" % self.email
