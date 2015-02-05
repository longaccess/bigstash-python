from requests.exceptions import RequestException
from .error import BigStashError
from wrapt import decorator


@decorator
def json_response(wrapped, instance, args, kwargs):
    try:
        r = wrapped(*args, **kwargs)
        r.raise_for_status()
        return r.json()
    except RequestException:
        raise BigStashError
    except ValueError:
        raise BigStashError
