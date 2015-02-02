from mock import Mock
from testtools.matchers import Contains
from testtools import TestCase


class AuthTest(TestCase):
    def setUp(self):
        super(AuthTest, self).setUp()

    def tearDown(self):
        super(AuthTest, self).tearDown()

    def _makeit(self, *args, **kwargs):
        from BigStash import BigStashAuth
        return BigStashAuth(*args, **kwargs)

    def test_auth_class(self):
        assert self._makeit(self.getUniqueString(),
                            self.getUniqueString(),
                            self.getUniqueString())

    def test_do_login(self):
        requests = Mock()
        requests.post.return_value = self.getUniqueString()
        api_key = self.getUniqueString()
        api_secret = self.getUniqueString()
        url = self.getUniqueString()

        auth = self._makeit(api_key, api_secret, url)

        self.assertThat(auth.GetAPIKey(),
                        Contains('authentication succesfull'))
