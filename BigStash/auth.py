import json
import requests
from BigStash import version


class Auth(object):

    def __init__(self,
                 api_key=None,
                 secret=None,
                 base_url=None):
        self.api_key = api_key
        self.secret = secret
        self.base_url = base_url

    def GetAPIKey(self, username=None, password=None):
        headers = {
            'User-agent': 'BigStash Python SDK v{}'.format(version),
            'Accept': 'application/vnd.deepfreeze+json',
            'Content-Type': 'application/vnd.deepfreeze+json'
        }
        url = self.base_url + '/tokens/'
        req = requests.post(url, auth=(username, password),
                            data=json.dumps({"name": "curl.py temp token"}),
                            headers=headers)
        r = json.loads(req.content)
        return (r.get("key", None), r.get("secret", None))
