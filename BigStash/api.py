from httpsig_cffi.requests_auth import HTTPSignatureAuth
from BigStash.base import BigStashAPIBase
from BigStash.decorators import json_response, no_content_response
from BigStash.error import BigStashError
from cached_property import cached_property
from BigStash import models
import logging

log = logging.getLogger('bigstash.api')


class _api_object_list(models.ObjectList):
    def __init__(self, api=None, *args, **kwargs):
        super(_api_object_list, self).__init__(*args, **kwargs)
        if api is None:
            raise ValueError("api must not be None")
        self.api = api

    @json_response
    def _get_page(self, url):
        return self.api.get(url)

    def next_iter(self, url):
        res = {'next': url}
        while res['next'] is not None:
            res = self._get_page(res['next'])
            for r in res['results']:
                yield r


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
        auth = HTTPSignatureAuth(key_id=self.key, secret=self.secret,
                                 algorithm='hmac-sha256',
                                 headers=signature_headers)
        super(BigStashAPI, self).__init__(auth=auth, *args, **kwargs)

    @cached_property
    @json_response
    def _root(self):
        return self.get('')

    def _top_resource_url(self, resource):
        try:
            return self._root[resource]
        except Exception:
            msg = "invalid resource '{}'".format(resource)
            log.error(msg, exc_info=True)
            raise BigStashError(msg)

    def _get_top_list(self, model):
        name = model.__name__.lower() + 's'
        return _api_object_list(
            api=self, klass=model, next=self._top_resource_url(name))

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
    def GetUser(self):
        """Get the user resource"""

        return self.get(self.USER_DETAIL)

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

    @json_response
    def CreateArchive(self, **kwargs):
        """ Create a new archive

        :param title: the archive title
        :param size: the archive size in bytes
        """
        return self.post(self.ARCHIVE_LIST, json=kwargs)

    @json_response
    def CreateUpload(self, archive_id):
        """ Create a new upload for an archive

        :param archive_id: the archive id
        """
        return self.post(self.ARCHIVE_UPLOAD.format(id=archive_id))

    @json_response
    def UpdateUploadStatus(self, upload_id, status):
        """ Update an upload's status

        :param upload_id: the upload id
        :param status: the new upload status
        """
        return self.patch(self.UPLOAD_DETAIL.format(id=upload_id),
                          json={"status": status})

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
    import os
    import sys
    from BigStash.conf import BigStashAPISettings, DEFAULT_SETTINGS
    from BigStash.models import ObjectList
    local_settings = BigStashAPISettings('local')
    local_settings['base_url'] = os.environ.get(
        'BS_API_URL', DEFAULT_SETTINGS['base_url'])
    logging.basicConfig()

    def get_api(s=None):
        try:
            return BigStashAPI(
                key=os.environ['BS_API_KEY'],
                secret=os.environ['BS_API_SECRET'],
                settings=s or local_settings)
        except KeyError:
            print "Please define the following env vars:"
            print "BS_API_KEY"
            print "BS_API_SECRET"
    if len(sys.argv) > 1:
        api = get_api()
        method = sys.argv[1]
        args = sys.argv[2:]
        if not hasattr(api, method):
            print "No such method {}".format(method)
        try:
            r = getattr(api, method)(*args)
        except BigStashError as e:
            print "There was an error: {}".format(e)
            sys.exit(1)

        if not isinstance(r, ObjectList):
            r = [r]
        for obj in r:
            print obj
    else:
        import IPython
        IPython.embed(user_ns={
            'get_api': get_api
        })
