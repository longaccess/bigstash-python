from testtools import TestCase


class ArchivesTestCase(TestCase):
    def setUp(self):
        super(ArchivesTestCase, self).setUp()
        api_key = self.getUniqueString()
        api_secret = self.getUniqueString()
        url = 'http://localhost:3000/api/v1/'
        self.api = self._makeit(api_key, api_secret, url)

    def tearDown(self):
        del self.api
        super(ArchivesTestCase, self).tearDown()

    def _makeit(self, *args, **kwargs):
        from BigStash import BigStashAPI
        return BigStashAPI(*args, **kwargs)

    def test_get_archive_list(self):
        archives = self.api.GetArchives()
        self.assertEqual(len(archives['results']), 2)
        self.assertEqual(archives['results'][0]['title'], 'Photos')
        self.assertEqual(archives['results'][1]['title'], 'Other')

    def test_get_archive_details(self):
        archive_id = 1
        archive = self.api.GetArchive(archive_id)
        keys = [ "status", "key", "size", "checksum",
                 "created", "url", "upload", "title"]
        self.assertListEqual(sorted(keys), sorted(archive.keys()))

    def test_create_archive(self):
        title = self.getUniqueString()
        size = 300000
        user_id = 1
        archive = self.api.CreateArchive(title=title, size=size, user_id=user_id)
        keys = [ "status", "key", "size", "checksum",
                 "created", "url", "upload", "title"]
        self.assertListEqual(sorted(keys), sorted(archive.keys()))
        self.assertEqual(archive['title'], title)
