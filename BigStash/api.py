import json
import requests
import time

from httpsig.requests_auth import HTTPSignatureAuth
from requests.exceptions import RequestException
from six.moves.urllib.parse import urlparse
from .error import BigStashError
from .auth import headers


class BigStashAPI(object):

    def __init__(self, key=None, secret=None, base_url=None):
        self.key = key
        self.secret = secret
        self.base_url = base_url

    def _AuthRequest(self, url):
        if self.key and self.secret:
            signature_headers = ['(request-line)', 'date', 'host']
            host = urlparse(url).netloc
            headers.update({
                'Host': host,
                'X-Deepfreeze-Api-Key': self.key,
                'Date': time.strftime('%a, %d %b %Y %H:%M:%S GMT',
                                      time.gmtime(time.time()))
            })

            return HTTPSignatureAuth(key_id=self.key, secret=self.secret,
                                     algorithm='hmac-sha256',
                                     headers=signature_headers)

    def GetArchives(self):
        url = self.base_url + 'archives/'
        auth = self._AuthRequest(url)
        try:
            req = requests.get(url, auth=self._AuthRequest(url), headers=headers)
            return json.loads(req.content)
        except RequestException:
            raise BigStashError
        except ValueError:
            raise BigStashError

    def GetUser(self, User):
        url = self.base_url + 'user/'
        return requests.get(url, auth=self._AuthRequest(url), headers=headers)

    def GetArchive(self, archive_id):
        url = self.base_url + 'archives/' + archive_id + '/'
        return requests.get(url, auth=self._AuthRequest(url), headers=headers)

    def GetUpload(self, upload_id):
        url = self.base_url + 'uploads/' + upload_id + '/'
        return requests.get(url, auth=self._AuthRequest(url), headers=headers)

    def CreateArchive(self, title=None, size=None, user_id=None):
        url = self.base_url + 'archives/'
        return requests.get(url, auth=self._AuthRequest(url), headers=headers)

    def CreateUpload(self):
        url = self.base_url + 'uploads/'
        return requests.get(url, auth=self._AuthRequest(url), headers=headers)

    def UpdateUpload(self, upload_id):
        url = self.base_url + 'uploads/' + upload_id + '/'
        return requests.get(url, auth=self._AuthRequest(url), headers=headers)

    def DestroyUpload(self, upload_id):
        url = self.base_url + 'uploads/' + upload_id + '/'
        return requests.get(url, auth=self._AuthRequest(url), headers=headers)
