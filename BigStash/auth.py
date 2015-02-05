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
    s = BigStashAPISettings()
    from getpass import getpass
    p = getpass()
    s['base_url'] = 'http://192.168.1.16:8000/api/v1'
    auth = BigStashAuth(settings=s)
    print auth.GetAPIKey('koukopoulos@gmail.com', p)
