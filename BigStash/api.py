from httpsig_cffi.requests_auth import HTTPSignatureAuth
from BigStash.base import BigStashAPIBase
from BigStash.decorators import json_response


class BigStashAPI(BigStashAPIBase):
    USER_DETAIL = "user"
    UPLOAD_LIST = "uploads"
    UPLOAD_DETAIL = "uploads/{id}"
    ARCHIVE_LIST = "archives"
    ARCHIVE_DETAIL = "archives/{id}"
    ARCHIVE_UPLOAD = "archives/{id}/upload"

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

    @json_response
    def GetArchives(self):
        """
        Get a list of archives
        """
        return self.get(self.ARCHIVE_LIST)

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
    def CreateArchive(self, *kwargs):
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
        return self.post(self.ARCHIVE_UPLOAD.format(archive_id))

    @json_response
    def UpdateUploadStatus(self, upload_id, status):
        """ Update an upload's status

        :param upload_id: the upload id
        :param status: the new upload status
        """
        return self.patch(self.UPLOAD_DETAIL.format(upload_id),
                          json={"status": status})

    @json_response
    def CancelUpload(self, upload_id):
        """ Cancel an upload

        :param upload_id: the upload id
        """
        return self.delete(self.UPLOAD_DETAIL.format(upload_id))


if __name__ == "__main__":
    from BigStash.conf import BigStashAPISettings
    s = BigStashAPISettings()
    s['base_url'] = 'http://192.168.1.16:8000/api/v1'
    api = BigStashAPI(
        key='3e4bf6fb92733765166ba2ce5e79734f661aa112',
        secret=('8e83b0aa82c694fd2a194024d1dd6957a411'
                'cc754a6166b8997e992a68e78a4e485c2679'
                'e36bf62b'),
        settings=s)
    print api.GetUser()
