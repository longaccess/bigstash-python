import json
import requests
import time

from httpsig_cffi.requests_auth import HTTPSignatureAuth
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
            signature_headers = ['(request-target)', 'date', 'host']
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
        try:
            req = requests.get(url, auth=self._AuthRequest(url), headers=headers)
            return json.loads(req.content)
        except RequestException:
            raise BigStashError
        except ValueError:
            raise BigStashError

    def GetUser(self, User):
        url = self.base_url + 'user/'
        try:
            req = requests.get(url, auth=self._AuthRequest(url), headers=headers)
            return json.loads(req.content)
        except RequestException:
            raise BigStashError
        except ValueError:
            raise BigStashError

    def GetArchive(self, archive_id):
        url = self.base_url + 'archives/%d/' % archive_id
        try:
            req = requests.get(url, auth=self._AuthRequest(url), headers=headers)
            return json.loads(req.content)
        except RequestException:
            raise BigStashError
        except ValueError:
            raise BigStashError

    def GetArchiveFiles(self, archive_id):
        url = self.base_url + 'archives/%d/files/' % archive_id
        try:
            req = requests.get(url, auth=self._AuthRequest(url), headers=headers)
            return json.loads(req.content)
        except RequestException:
            raise BigStashError
        except ValueError:
            raise BigStashError

    def GetUpload(self, upload_id):
        url = self.base_url + 'uploads/%d/' % upload_id
        try:
            req = requests.get(url, auth=self._AuthRequest(url), headers=headers)
            return json.loads(req.content)
        except RequestException:
            raise BigStashError
        except ValueError:
            raise BigStashError

    def CreateArchive(self, title=None, size=None, user_id=None):
        url = self.base_url + 'archives/'
        data = {
            'title': title,
            'size': size,
            'user_id': user_id
        }
        try:
            req = requests.post(url, auth=self._AuthRequest(url),
                                data=json.dumps(data), headers=headers)
            return json.loads(req.content)
        except RequestException:
            raise BigStashError
        except ValueError:
            raise BigStashError

    def CreateUpload(self, archive_id):
        url = self.base_url + 'archives/%d/upload/' % archive_id
        try:
            req = requests.post(url, auth=self._AuthRequest(url),
                                headers=headers)
            return json.loads(req.content)
        except RequestException:
            raise BigStashError
        except ValueError:
            raise BigStashError

    def UpdateUpload(self, upload_id, status=None):
        url = self.base_url + 'uploads/%d/' % upload_id
        data = {'status': status }
        try:
            req = requests.patch(url, auth=self._AuthRequest(url),
                                 data=json.dumps(data), headers=headers)
            return json.loads(req.content)
        except RequestException:
            raise BigStashError
        except ValueError:
            raise BigStashError

    def DestroyUpload(self, upload_id):
        url = self.base_url + 'uploads/%d/' % upload_id
        try:
            req = requests.delete(url, auth=self._AuthRequest(url),
                                  headers=headers)
        except RequestException:
            raise BigStashError

    def GetUser(self):
        url = self.base_url + 'user/'
        try:
            req = requests.get(url, auth=self._AuthRequest(url), headers=headers)
            return json.loads(req.content)
        except RequestException:
            raise BigStashError
        except ValueError:
            raise BigStashError
