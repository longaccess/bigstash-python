from __future__ import print_function
from BigStash.base import BigStashAPIBase
from BigStash.decorators import json_response, no_content_response
from BigStash.error import BigStashError, ResourceNotModified
from cached_property import cached_property
from BigStash import models
from BigStash.serialize import model_to_json
from BigStash.sign import HTTPSignatureAuth
from itertools import chain
import logging

log = logging.getLogger('bigstash.api')


class BigStashAPI(BigStashAPIBase):
    USER_DETAIL = "user"
    UPLOAD_LIST = "uploads"
    UPLOAD_DETAIL = "uploads/{id}"
    ARCHIVE_LIST = "archives"
    ARCHIVE_DETAIL = "archives/{id}"
    ARCHIVE_FILES = "archives/{id}/files/"
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
    def _root_resource(self):
        return self.get('')

    @property
    def _root(self):
        return self._root_resource[0]  # we only care about the body

    def _top_resource_url(self, resource):
        msg = "invalid resource '{}'".format(resource)
        try:
            return self._root[resource]
        except BigStashError:
            log.debug("error getting top resource url", exc_info=True)
            raise
        except Exception:
            log.error("error getting top resource url", exc_info=True)
            raise BigStashError(msg)

    @json_response
    def _get_page(self, url):
        return self.get(url)

    def _get_top_list(self, model):
        name = model.__name__.lower() + 's'
        res = {'next': self._top_resource_url(name)}
        while res['next'] is not None:
            body, headers = self._get_page(res['next'])
            for r in body['results']:
                yield model(**r)

    def _list_next(self, olist):
        while olist.next is not None:
            body, headers = self._get_page(olist.next)
            olist.next = body['next']
            for r in body['results']:
                obj = olist.klass(**r)
                olist.objects.append(obj)
                yield obj

    def get_all_objects(self, olist):
        return chain(olist, self._list_next(olist))

    def _refresh_resource(self, obj, **kwargs):
        lm = obj.get_meta('last-modified')
        if lm is not None:
            hdrs = kwargs.setdefault('headers', {})
            hdrs['If-Modified-Since'] = lm
        try:
            r, h = json_response(self.get)(obj.url, **kwargs)
            return obj.__class__(meta=h, **r)
        except ResourceNotModified:
            return obj

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
        body, headers = self._get_user()
        return models.User(meta=headers, **body)

    def GetArchive(self, archive_id):
        """ Get details for an archive

        :param archive_id: the archive id
        """
        body, headers = json_response(self.get)(
            self.ARCHIVE_DETAIL.format(id=archive_id))
        return models.Archive(meta=headers, **body)

    @json_response
    def GetArchiveFiles(self, archive_id):
        """ Get archive files

        :param archive_id: the archive id
        """
        return self.get(self.ARCHIVE_FILES.format(id=archive_id))

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
        body, headers = json_response(self.post)(
            self._top_resource_url('archives'),
            json={'title': title, 'size': size}, **kwargs)
        return models.Archive(meta=headers, **body)

    def RefreshUploadStatus(self, upload):
        log.debug("Refreshing upload {}".format(upload))
        upload = self._refresh_resource(upload)
        log.debug("Refreshed upload {}".format(upload))
        return upload

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
        body, headers = json_response(self.post)(url, **kwargs)
        return models.Upload(meta=headers, **body)

    @json_response
    def UpdateUploadFiles(self, upload, files=None):
        pass

    def UpdateUploadStatus(self, upload, status):
        """ Update an upload's status

        :param upload_id: the upload id
        :param status: the new upload status
        """
        patch = {"status": status}
        log.debug("Updating {} with status='{}'".format(upload, status))
        body, headers = json_response(self.patch)(
            upload.url, json=patch)
        upload.update(patch, headers)

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
