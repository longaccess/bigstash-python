import time
import logging
import logging.handlers
import os
import os.path

from BigStash import __version__
from .conf import BigStashAPISettings
from requests import Session
from requests.sessions import merge_setting
from six.moves.urllib.parse import urlparse
from BigStash.structures import CaseInsensitiveDict

DEFAULT_MEDIA_PARAMS = {
    'version': '1.0'
}

DEFAULT_MEDIA_TYPE = 'application/vnd.deepfreeze'

DEFAULT_MEDIA_SUBTYPE = 'json'


def _media_type(subtype=DEFAULT_MEDIA_SUBTYPE, params=DEFAULT_MEDIA_PARAMS):
    return "; ".join(["{}+{}".format(DEFAULT_MEDIA_TYPE, subtype)] +
                     ["=".join(p) for p in params.items()])


DEFAULT_HEADERS = CaseInsensitiveDict({
    'User-agent': 'BigStash Python SDK v{}'.format(__version__),
    'Accept': _media_type(),
    'Content-Type': _media_type()
})


class BigStashAPIBase(object):
    def __init__(self, auth=None, settings=None, headers=None,
                 *args, **kwargs):
        """
        Initialize the Base API client functions
        :param auth: optional authentication tuple or object for request
        :param settings: optional :class:`BigStashAPISettings` instance to use.
        :param headers: optional dict  of HTTP Headers
        """
        self.settings = settings or BigStashAPISettings()
        if 'base_url' not in self.settings:
            raise TypeError("Must provide base_url setting")
        self._base_url = self.settings['base_url'].rstrip('/')

        self._headers = DEFAULT_HEADERS
        if headers is not None:
            self._headers = merge_setting(
                headers, self._headers,
                dict_class=CaseInsensitiveDict)

        self._auth = None
        if 'auth' is not None:
            self._auth = auth

        # setup requests session
        self._session = self._setup_session()

        super(BigStashAPIBase, self).__init__(*args, **kwargs)

    @classmethod
    def setup_logging(cls, settings):
        level = getattr(logging, settings['log_level'])
        logging.basicConfig(level=level)
        for h in logging.getLogger().handlers:
            h.level = level
        requests_log = logging.getLogger("requests.packages.urllib3")
        requests_log.setLevel(level)
        requests_log.propagate = True
        logdir = settings.get_config_file('logs')
        if not os.path.exists(logdir):
            os.makedirs(logdir)
        if not os.path.isdir(logdir):
            raise Exception("Fatal error: {} is not a directory".format(
                logdir))
        bgstlog = logging.getLogger('bigstash')
        bgstlog.setLevel(logging.INFO)
        bgstlog.propagate = True
        fname = os.path.join(logdir, 'bigstash')
        handler = logging.handlers.RotatingFileHandler(
            fname, maxBytes=10000, backupCount=5)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        bgstlog.addHandler(handler)
        if level == logging.DEBUG:
            from requests.packages.urllib3.connection import HTTPConnection
            HTTPConnection.debuglevel = 1

    def _setup_session(self):
        s = Session()
        if 'verify' in self.settings:  # default is True
            s.verify = self.settings['verify']
        if 'trust_env' in self.settings:
            s.trust_env = self.settings['trust_env']
        if self._auth is not None:
            s.auth = self._auth

        s.headers = merge_setting(  # add our headers to requests' default set
            self._headers, s.headers, dict_class=CaseInsensitiveDict)

        return s

    def api_url(self, url=''):
        """
        Return a full URL to the API resource at 'url'
        """
        p = urlparse(url)
        path = p.path.rstrip('/')
        if path:
            p = p._replace(path=path+"/")
        if not p.netloc:
            base = urlparse(self._base_url)
            p = p._replace(netloc=base.netloc)
            p = p._replace(scheme=base.scheme)
            p = p._replace(path="/".join([base.path, p.path]))
        return p.geturl()

    def add_date(self, headers):
        if 'date' not in [h.lower() for h in headers]:
            headers['Date'] = time.strftime('%a, %d %b %Y %H:%M:%S GMT',
                                            time.gmtime(time.time()))

    def get(self, path, *args, **kwargs):
        """Sends a GET request, returns result. Assumes a JSON response.

        :param path: URL to GET
        :param \*\*kwargs: Optional arguments that ``requests.get`` takes.
        """
        self.add_date(kwargs.setdefault('headers', {}))
        return self._session.get(self.api_url(path), *args, **kwargs)

    def post(self, path, *args, **kwargs):
        """Sends a POST request, returns result.

        :param path: URL to POST
        :param \*\*kwargs: Optional arguments that ``requests.post`` takes.
        """
        self.add_date(kwargs.setdefault('headers', {}))
        return self._session.post(self.api_url(path), *args, **kwargs)

    def patch(self, path, *args, **kwargs):
        """ Sends a PATCH request, returns results.

        :param path: URL to PATCH
        :param \*\*kwargs: Optional arguments that ``requests.patch`` takes.
        """
        self.add_date(kwargs.setdefault('headers', {}))
        return self._session.patch(self.api_url(path), *args, **kwargs)

    def delete(self, path, *args, **kwargs):
        """ Sends a DELETE request, returns results.

        :param path: URL to DELETE
        :param \*\*kwargs: Optional arguments that ``requests.delete`` takes.
        """
        self.add_date(kwargs.setdefault('headers', {}))
        return self._session.delete(self.api_url(path), *args, **kwargs)
