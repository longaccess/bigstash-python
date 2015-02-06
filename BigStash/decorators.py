from requests.exceptions import RequestException
from .error import BigStashError
from wrapt import decorator


@decorator
def json_response(wrapped, instance, args, kwargs):
    try:
        r = wrapped(*args, **kwargs)
        r.raise_for_status()
        return r.json()
    except RequestException as e:
        raise BigStashError(e)
    except ValueError as e:
        raise BigStashError(e)


@decorator
def no_content_response(wrapped, instance, args, kwargs):
    try:
        r = wrapped(*args, **kwargs)
        r.raise_for_status()
    except RequestException as e:
        raise BigStashError(e)
