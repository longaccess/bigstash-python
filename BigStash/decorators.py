from requests.exceptions import RequestException
from .error import BigStashError
from wrapt import decorator
import logging


log = logging.getLogger('bigstash.api')


@decorator
def json_response(wrapped, instance, args, kwargs):
    try:
        r = wrapped(*args, **kwargs)
        r.raise_for_status()
        json = r.json()
        ctype = r.headers.get('content-type', None)
        if ctype is None:
            log.warning("No content-type header found. Assuming JSON.")
        elif 'json' not in r.headers.get('content-type'):
            raise BigStashError("Unexpected content type: {}".format(ctype))
        else:
            json['_type'] = ctype
        return json
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
