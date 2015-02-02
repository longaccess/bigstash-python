class BigStashError(Exception):
    """ Base class for BigStash errors """
    pass


class BigStashServerError(BigStashError):
    pass


class BigStashClientError(BigStashError):
    pass
