from testtools import TestCase


class CurlTest(TestCase):
    def setUp(self):
        super(CurlTest, self).setUp()

    def tearDown(self):
        super(CurlTest, self).tearDown()

    def test_curl_get_signature_auth_temp(self):
        from BigStash.curl import get_auth
        self.assertEqual(get_auth(), None)
