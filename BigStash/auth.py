from __future__ import print_function
from BigStash import __version__
from BigStash.base import BigStashAPIBase
from BigStash.decorators import json_response
from getpass import getpass
from six.moves import input
import os
import logging

log = logging.getLogger('bigstash.auth')


class BigStashAuth(BigStashAPIBase):
    NAME = "BigStash Python SDK v{}".format(__version__)

    @json_response
    def GetAPIKey(self, username=None, password=None, auth=None, name=NAME):
        if auth is None and username is not None and password is not None:
            auth = (username, password)
        return self.post('tokens', auth=auth, json={"name": name})


def get_api_credentials(settings, username=None):
    k = s = None
    if all(e in os.environ for e in ('BS_API_KEY', 'BS_API_SECRET')):
        k, s = (os.environ['BS_API_KEY'], os.environ['BS_API_SECRET'])
    else:
        authfile = 'auth.{}'.format(settings.profile)
        try:
            r = settings.read_config_file(authfile)
        except Exception:
            log.debug("error reading config file", exc_info=True)
            print("No saved credentials found")
            auth = BigStashAuth(settings=settings)
            r = auth.GetAPIKey(
                username or raw_input("Username: "), getpass("Password: "))
            if raw_input("Save api key to settings? (y/N) ").lower() == "y":
                settings.write_config_file(authfile, r)
        k, s = (r['key'], r['secret'])
    return (k, s)


if __name__ == "__main__":
    import sys
    from BigStash.conf import BigStashAPISettings
    settings = BigStashAPISettings.load_settings()
    u = None
    if len(sys.argv) > 1 and sys.argv[1] == '-d':
        logging.basicConfig(level=logging.DEBUG)
        sys.argv = sys.argv[1:]
    if len(sys.argv) > 1:
        u = sys.argv[1]

    k, s = get_api_credentials(settings, username=u)
    print("Key: {}".format(k))
    print("Secret: {}".format(s))
