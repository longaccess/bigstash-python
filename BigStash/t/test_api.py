from testtools.testcase import TestCase
from BigStash import BigStashAPISettings, BigStashError


class APITestCase(TestCase):
    def setUp(self):
        super(APITestCase, self).setUp()
        api_key = self.getUniqueString()
        api_secret = self.getUniqueString()
        s = BigStashAPISettings()
        s['base_url'] = 'http://localhost:3000/api/v1/'
        self.api = self._makeit(key=api_key, secret=api_secret, settings=s)

    def tearDown(self):
        del self.api
        super(APITestCase, self).tearDown()

    def _makeit(self, *args, **kwargs):
        from BigStash import BigStashAPI
        return BigStashAPI(*args, **kwargs)

    def test_api_bad_auth(self):
        from BigStash import BigStashAPI
        key = self.getUniqueString()
        secret = self.getUniqueString()
        self.assertRaises(TypeError, BigStashAPI)
        self.assertRaises(TypeError, BigStashAPI, key=key)
        self.assertRaises(TypeError, BigStashAPI, secret=secret)

    def test_api_no_base_url(self):
        from BigStash import BigStashAPI
        settings = BigStashAPISettings(profile='some_profile')
        key = self.getUniqueString()
        secret = self.getUniqueString()
        self.assertRaises(TypeError, BigStashAPI, key=key,
                          secret=secret, settings=settings)

    def test_get_archive_list(self):
        archives = self.api.GetArchives()
        self.assertEqual(len(archives['results']), 2)
        self.assertEqual(archives['results'][0]['title'], 'Photos')
        self.assertEqual(archives['results'][1]['title'], 'Other')

    def test_get_archive_details(self):
        archive_id = 1
        archive = self.api.GetArchive(archive_id)
        keys = ["status", "key", "size", "checksum",
                "created", "url", "upload", "title"]
        self.assertListEqual(sorted(keys), sorted(archive.keys()))

    def test_create_archive(self):
        title = self.getUniqueString()
        size = 300000
        uid = 1
        archive = self.api.CreateArchive(title=title, size=size, user_id=uid)
        keys = ["status", "key", "size", "checksum",
                "created", "url", "upload", "title"]
        self.assertListEqual(sorted(keys), sorted(archive.keys()))
        self.assertEqual(archive['title'], title)

    def test_get_upload_details(self):
        upload_id = 1
        upload, headers = self.api.GetUpload(upload_id)
        keys = [u'status', u'comment', u'created', u'url', u's3', u'archive']
        self.assertListEqual(sorted(keys), sorted(upload.keys()))

    def test_update_upload_status(self):
        upload_id = 1
        status = 'completed'
        upload = self.api.UpdateUploadStatus(upload_id, status)
        keys = [u'status', u'comment', u'created', u'url', u's3', u'archive']
        self.assertListEqual(sorted(keys), sorted(upload.keys()))
        self.assertEqual(upload['status'], status)

    def test_get_user(self):
        user = self.api.GetUser()
        keys = [u'displayname',
                u'avatar',
                u'quota',
                u'email',
                u'archives',
                u'id',
                u'date_joined']
        self.assertListEqual(sorted(keys), sorted(user.keys()))

    def test_create_upload(self):
        archive_id = 1
        upload = self.api.CreateUpload(archive_id)
        keys = [u'status', u'comment', u'created', u'url', u's3', u'archive']
        self.assertListEqual(sorted(keys), sorted(upload.keys()))

    def test_404_response(self):
        archive_id = 3
        self.assertRaises(BigStashError, self.api.GetArchive, archive_id)
