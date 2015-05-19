from requests.exceptions import RequestException
from .error import BigStashError, BigStashForbiddenError, ResourceNotModified
from wrapt import decorator
from collections import Mapping
import logging


log = logging.getLogger('bigstash.api')


@decorator
def json_response(wrapped, instance, args, kwargs):
    exc = None
    try:
        r = wrapped(*args, **kwargs)
        ctype = r.headers.get('content-type', 'application/json')
        r.raise_for_status()
        if r.status_code == 304:
            raise ResourceNotModified()
        return r.json(), r.headers
    except RequestException as e:
        text = e.response.reason
        body = e.response.json() if 'json' in ctype else e.response.text
        log.debug("error on {}".format(r.request.url), exc_info=True)
        if isinstance(body, Mapping) and 'detail' in body:
            text = body['detail']
        if e.response.status_code in (401, 403):
            exc = BigStashForbiddenError(
                text, request=e.request, response=e.response)
        elif e.response.status_code in (400, 500):
            exc = BigStashError(text)
        else:
            exc = BigStashError(e)
    except ValueError as e:
        exc = BigStashError(e)
    raise exc


@decorator
def no_content_response(wrapped, instance, args, kwargs):
    try:
        r = wrapped(*args, **kwargs)
        r.raise_for_status()
    except RequestException as e:
        raise BigStashError(e)
