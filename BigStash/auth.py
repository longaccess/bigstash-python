from BigStash import __version__

from BigStash.base import BigStashAPIBase
from BigStash.decorators import json_response


class BigStashAuth(BigStashAPIBase):
    NAME = "BigStash Python SDK v{}".format(__version__)

    @json_response
    def GetAPIKey(self, username=None, password=None, auth=None, name=NAME):
        if auth is None and username is not None and password is not None:
            auth = (username, password)
        return self.post('tokens', auth=auth, json={"name": name})


if __name__ == "__main__":
    from BigStash.conf import BigStashAPISettings
    import sys
    import logging
    if len(sys.argv) < 2:
        print "username required"
        exit()
    if len(sys.argv) > 2 and sys.argv[1] == '-d':
        logging.basicConfig(level=logging.DEBUG)
        u = sys.argv[2]
    else:
        u = sys.argv[1]

    s = BigStashAPISettings()
    from getpass import getpass
    p = getpass()
    auth = BigStashAuth(settings=s)
    print auth.GetAPIKey(u, p)
