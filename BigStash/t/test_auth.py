from testtools.testcase import TestCase
from BigStash import BigStashAPISettings


class AuthTest(TestCase):
    def setUp(self):
        settings = BigStashAPISettings()
        settings['base_url'] = 'http://localhost:3000/api/v1/'
        self.auth = self._makeit(settings=settings)
        super(AuthTest, self).setUp()

    def tearDown(self):
        super(AuthTest, self).tearDown()

    def _makeit(self, *args, **kwargs):
        from BigStash import BigStashAuth
        return BigStashAuth(*args, **kwargs)

    def test_auth_class(self):
        settings = BigStashAPISettings()
        settings['base_url'] = 'http://localhost:3000/api/v1/'
        assert self._makeit(settings=settings)

    def test_do_login(self):
        r = self.auth.GetAPIKey(username='test', password='test')
        keys = [u'url', u'secret', u'name', u'key', u'created']
        self.assertListEqual(sorted(r.keys()), sorted(keys))
        self.assertNotEqual(r['key'], '')
        self.assertNotEqual(r['secret'], '')
