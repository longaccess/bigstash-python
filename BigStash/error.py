class BigStashError(Exception):
    """ Base class for BigStash errors """
    pass


class BigStashServerError(BigStashError):
    pass


class BigStashClientError(BigStashError):
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        self.response = kwargs.pop('response', None)
        super(BigStashClientError, self).__init__(*args, **kwargs)


class BigStashForbiddenError(BigStashClientError):
    pass


class ResourceNotModified(Exception):
    pass
