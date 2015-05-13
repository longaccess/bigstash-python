from __future__ import print_function
from BigStash.base import BigStashAPIBase
from BigStash.decorators import json_response, no_content_response
from BigStash.error import BigStashError
from cached_property import cached_property
from BigStash import models
from collections import Mapping
from BigStash.serialize import model_to_json
import logging

log = logging.getLogger('bigstash.api')

from requests.auth import AuthBase
import urlparse
import hmac
import base64
import hashlib

class Light_HTTPSignatureAuth(AuthBase):
    def __init__(self, key_id='', secret='', algorithm='rsa-sha256', headers=None, allow_agent=False):
        self.algorithm = algorithm
        self.key_id = key_id
        self.secret = secret
        self.headers = headers
        self.signature_string_head = self.build_header_content()
    
    def build_header_content(self):
        param_map = {'keyId': 'hmac-key-1' , 
                     'algorithm': self.algorithm,
                     'signature': '%s'}
        if self.headers:
            param_map['headers'] = ' '.join(self.headers)
        kv = map('{0[0]}="{0[1]}"'.format, param_map.items())
        kv_string = ','.join(kv)
        sig_string = 'Signature {0}'.format(kv_string)
        return sig_string
    
    def sign(self, data):
        dig = hmac.new(self.secret, data.encode('utf-8'), hashlib.sha256).digest()
        return base64.b64encode(dig)
    def __call__(self, r):
        url_parts = urlparse.urlparse(r.url)
        if 'Date' not in r.headers:
            now = datetime.now()
            stamp = mktime(now.timetuple())
            r.headers['Date'] = format_date_time(stamp)
        if self.headers:
            signable_list = []
            for x in self.headers:
                if x in r.headers:
                    signable_list.append("%s: %s" % (x, r.headers[x]) )
                elif x=='(request-target)':
                    signable_list.append("%s: %s %s" % (x, r.method.lower(), url_parts.path))
                elif x=='host':
                    signable_list.append("%s: %s" % (x,url_parts.netloc) )
            signable = '\n'.join(signable_list)
        else:
            signable = r.headers['Date']
        signature = self.sign(signable)
        r.headers['Authorization'] = self.signature_string_head % signature      
        return r


class BigStashAPI(BigStashAPIBase):
    USER_DETAIL = "user"
    UPLOAD_LIST = "uploads"
    UPLOAD_DETAIL = "uploads/{id}"
    ARCHIVE_LIST = "archives"
    ARCHIVE_DETAIL = "archives/{id}"
    ARCHIVE_UPLOAD = "archives/{id}/upload"
    TOKEN_DETAIL = "tokens/{id}"
    NOTIFICATION_LIST = "notifications"

    def __init__(self, key=None, secret=None, *args, **kwargs):
        """Initialize a :class:`BigStashAPI <BigStashAPI>` object.

        :param key: API key
        :param secret: API secret
        :param settings: optional :class:`BigStashAPISettings` instance to use.

        Usage::

          >>> from BigStash import BigStashAPI
          >>> api = BigStashAPI('AHBFEXAMPLE', '12039898FADEXAMPLE')
          >>> archives = api.GetArchives()
          [{ }]

        """
        headers = kwargs.setdefault('headers', {})
        self.key = key
        self.secret = secret
        if key is None or secret is None:
            raise TypeError("Must provide API key and secret.")
        # setup auth
        headers['X-Deepfreeze-Api-Key'] = self.key
        signature_headers = ['(request-target)', 'date', 'host']
        auth = Light_HTTPSignatureAuth(key_id=self.key, secret=self.secret,
                                 algorithm='hmac-sha256',
                                 headers=signature_headers)
        print '\n\nAUTH: %s\n\n' % auth
        super(BigStashAPI, self).__init__(auth=auth, *args, **kwargs)

    @cached_property
    @json_response
    def _root(self):
        return self.get('')

    def _top_resource_url(self, resource):
        msg = "invalid resource '{}'".format(resource)
        try:
            return self._root[resource]
        except BigStashError:
            raise
        except Exception:
            raise BigStashError(msg)

    @json_response
    def _get_page(self, url):
        return self.get(url)

    def _get_top_list(self, model):
        name = model.__name__.lower() + 's'
        res = {'next': self._top_resource_url(name)}
        while res['next'] is not None:
            res = self._get_page(res['next'])
            for r in res['results']:
                yield model(**r)

    def _add_pagination_param(self, params={}, page=None):
        """
        Add the proper query parameters for pagination
        """
        if page:
            params.update({'page': page})
        return params

    def GetNotifications(self):
        """
            Get all notifications
        """
        return self._get_top_list(models.Notification)

    def GetUploads(self):
        """
            Get all uploads. Returns an ObjectList.
        """
        return self._get_top_list(models.Upload)

    def GetArchives(self):
        """
            Get a list of archives. Returns an ObjectList
        """
        return self._get_top_list(models.Archive)

    @json_response
    def _get_user(self):
        return self.get(self.USER_DETAIL)

    def GetUser(self):
        """Get the user resource"""
        return models.User(**self._get_user())

    @json_response
    def GetArchive(self, archive_id):
        """ Get details for an archive

        :param archive_id: the archive id
        """
        return self.get(self.ARCHIVE_DETAIL.format(id=archive_id))

    @json_response
    def GetUpload(self, upload_id):
        """ Get details for an upload

        :param upload_id: the upload id
        """
        return self.get(self.UPLOAD_DETAIL.format(id=upload_id))

    def CreateArchive(self, title=None, size=None, **kwargs):
        """ Create a new archive. Returns an Archive instance.

        :param title: the archive title
        :param size: the archive size in bytes
        """
        ret = json_response(self.post)(
            self._top_resource_url('archives'),
            json={'title': title, 'size': size}, **kwargs)
        return models.Archive(**ret)

    def RefreshUploadStatus(self, upload):
        status = upload.status
        ret = json_response(self.get)(upload.url)
        if ret['status'] == status:
            return upload
        new_archive = ret.get('archive', None)
        if new_archive and not isinstance(new_archive, Mapping):
            new_archive = json_response(self.get)(new_archive)
        ret['archive'] = models.Archive(**new_archive)
        return upload.__class__(**ret)

    def CreateUpload(self, archive=None, manifest=None, **kwargs):
        """ Create a new upload for an archive

        :param archive: the archive model instance
        :param manifest: the upload manifest
        """
        if archive is not None:
            url = archive.upload
        else:
            url = self._top_resource_url('uploads')
        kwargs['data'] = model_to_json(manifest)
        ret = json_response(self.post)(url, **kwargs)
        if archive is None:
            new_archive = ret.get('archive', None)
            if new_archive and not isinstance(new_archive, Mapping):
                new_archive = json_response(self.get)(new_archive)
            archive = models.Archive(**new_archive)
        ret['archive'] = archive
        return models.Upload(**ret)

    @json_response
    def UpdateUploadFiles(self, upload, files=None):
        pass

    @json_response
    def UpdateUploadStatus(self, upload, status):
        """ Update an upload's status

        :param upload_id: the upload id
        :param status: the new upload status
        """
        return self.patch(upload.url, json={"status": status})

    @no_content_response
    def CancelUpload(self, upload_id):
        """ Cancel an upload

        :param upload_id: the upload id
        """
        return self.delete(self.UPLOAD_DETAIL.format(id=upload_id))

    @no_content_response
    def DestroyAPIKey(self, token_id):
        """ Delete an API key

        :param token_id: the token id
        """
        return self.delete(self.TOKEN_DETAIL.format(id=token_id))


if __name__ == "__main__":
    import sys
    from BigStash.models import ObjectList
    from BigStash.conf import BigStashAPISettings
    from BigStash.auth import get_api_credentials
    settings = BigStashAPISettings.load_settings()
    k, s = get_api_credentials(settings)
    api = BigStashAPI(key=k, secret=s, settings=settings)
    logging.basicConfig()

    if len(sys.argv) > 1:
        method = sys.argv[1]
        args = sys.argv[2:]
        if not hasattr(api, method):
            print("No such method {}".format(method))
        try:
            r = getattr(api, method)(*args)
        except BigStashError as e:
            print("There was an error: {}".format(e))
            sys.exit(1)

        if not isinstance(r, ObjectList):
            r = [r]
        for obj in r:
            print(obj)
    else:
        import IPython
        IPython.embed(user_ns={
            'api': api
        })
