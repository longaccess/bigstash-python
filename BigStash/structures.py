from requests.structures import CaseInsensitiveDict  # noqa


class ObjectList(object):
    def __init__(self, klass, objects=[], next=None, meta=None):
        self.klass = klass
        self.objects = objects
        self.next = next
        self.meta = meta

    def __iter__(self):
        return (self.klass(meta=self.meta, **data) for data in self.objects)

    def __repr__(self):
        s = []
        for obj in self:
            s.append("\t" + "\n\t".join(repr(obj).split("\n")))
        if self.next is not None:
            s.append("\t...")
        return ("{ " + super(ObjectList, self).__repr__() +
                " [\n" + ",\n".join(s) + "]}")
