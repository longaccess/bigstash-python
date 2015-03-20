from httpsig_cffi.requests_auth import HTTPSignatureAuth
from BigStash.base import BigStashAPIBase
from BigStash.decorators import json_response, no_content_response
from .error import BigStashError
from cached_property import cached_property


class BigStashAPI(BigStashAPIBase):
    USER_DETAIL = "user"
    UPLOAD_LIST = "uploads"
    UPLOAD_DETAIL = "uploads/{id}"
    ARCHIVE_LIST = "archives"
    ARCHIVE_DETAIL = "archives/{id}"
    ARCHIVE_UPLOAD = "archives/{id}/upload"
    TOKEN_DETAIL = "tokens/{id}"

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
        except Exception as e:
            raise BigStashError(e)

    def _add_pagination_param(self, params={}, page=None):
        """
        Add the proper query parameters for pagination
        """
        if page:
            params.update({'page': page})
        return params

    @json_response
    def GetNotifications(self, page=None):
        """
        Get a list of notifications

        :param page: the page param for paginated results
        """
        return self.get(self._top_resource_url('notifications'),
                        params=self._add_pagination_param(page))

    @json_response
    def GetArchives(self, page=None):
        """
        Get a list of archives

        :param page: the page param for paginated results
        """
        params = {}
        if page:
            params.update({'page': page})
        return self.get(self.ARCHIVE_LIST, params=params)

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
    from BigStash.conf import BigStashAPISettings
    s = BigStashAPISettings()
    try:
        api = BigStashAPI(
            key=os.environ['BS_API_KEY'],
            secret=os.environ['BS_API_SECRET'],
            settings=s)
    except KeyError:
        print "Please define BS_API_KEY and BS_API_SECRET"
        exit()
    import IPython
    IPython.embed(user_ns={'api': api})
