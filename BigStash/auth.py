import json
import requests

from requests.exceptions import RequestException
from BigStash import __version__
from .error import BigStashError

headers = {
    'User-agent': 'BigStash Python SDK v{}'.format(__version__),
    'Accept': 'application/vnd.deepfreeze+json',
    'Content-Type': 'application/vnd.deepfreeze+json'
}

class BigStashAuth(object):

    def __init__(self,
                 api_key=None,
                 secret=None,
                 base_url=None):
        self.api_key = api_key
        self.secret = secret
        self.base_url = base_url

    def GetAPIKey(self, username=None, password=None):
        url = self.base_url + '/tokens/'
        try:
            req = requests.post(url, auth=(username, password),
                                data=json.dumps({"name": "curl.py temp token"}),
                                headers=headers)
            r = json.loads(req.content)
        except RequestException:
            raise BigStashError
        except ValueError:
            raise BigStashError

        return (r.get("key", None), r.get("secret", None))
