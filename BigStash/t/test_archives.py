from testtools import TestCase


class ArchivesTestCase(TestCase):
    def setUp(self):
        super(ArchivesTestCase, self).setUp()
        api_key = self.getUniqueString()
        api_secret = self.getUniqueString()
        url = self.getUniqueString()
        self.api = self._makeit(api_key, api_secret, url)

    def tearDown(self):
        del self.api
        super(ArchivesTestCase, self).setUp()

    def _makeit(self, *args, **kwargs):
        from BigStash import BigStashAPI
        return BigStashAPI(*args, **kwargs)

    def test_get_archive_list(self):
        archives = self.api.GetArchives()
        self.assertEqual(len(archives['results']), 2)
        self.assertEqual(archives[0].title, 'Photos')
        self.assertEqual(archives[1].title, 'Other')

    def test_get_archive_details(self):
        key = self.getUniqueString()
        archive = self.api.GetArchive(key)
        keys = [ "status", "key", "size", "checksum",
                 "created", "url", "upload", "title"]
        self.assertListEqual(keys, archive.keys())
        self.assertEqual(archive['key'], self.key)
