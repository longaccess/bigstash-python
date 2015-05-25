from wsgiref.handlers import format_date_time
from six.moves.urllib.parse import urlparse
from requests.auth import AuthBase
from datetime import datetime
import six
import time
import hmac
import base64
import hashlib
import logging

log = logging.getLogger('bigstash.sign')


class Light_HTTPSignatureAuth(AuthBase):
    def __init__(self, key_id='', secret='', algorithm='rsa-sha256',
                 headers=None, allow_agent=False):
        self.algorithm = algorithm
        self.key_id = key_id
        self.secret = six.b(secret)
        self.headers = headers
        self.signature_string_head = self.build_header_content()

    def build_header_content(self):
        param_map = {'keyId': 'hmac-key-1',
                     'algorithm': self.algorithm,
                     'signature': '%s'}
        if self.headers:
            param_map['headers'] = ' '.join(self.headers)
        kv = map('{0[0]}="{0[1]}"'.format, param_map.items())
        kv_string = ','.join(kv)
        sig_string = 'Signature {0}'.format(kv_string)
        return sig_string

    def hmac_sha256(self, data):
        return hmac.new(self.secret, data, digestmod=hashlib.sha256).digest()

    def sign(self, data):
        try:
            signer = getattr(self, self.algorithm.replace('-', '_'))
        except AttributeError:
            raise NotImplemented(
                "algorithm {} not implemented".format(self.algorithm))
        return base64.b64encode(signer(data.encode('utf-8'))).decode('ascii')

    def __call__(self, r):
        url_parts = urlparse(r.url)
        if 'Date' not in r.headers:
            now = datetime.now()
            stamp = time.mktime(now.timetuple())
            r.headers['Date'] = format_date_time(stamp)
        if self.headers:
            signable_list = []
            for x in self.headers:
                if x in r.headers:
                    signable_list.append("%s: %s" % (x, r.headers[x]))
                elif x == '(request-target)':
                    signable_list.append(
                        "%s: %s %s" % (
                            x, 
                            r.method.lower(), 
                            url_parts.path if not url_parts.query else '%s?%s' % (url_parts.path, url_parts.query)))
                elif x == 'host':
                    signable_list.append("%s: %s" % (x, url_parts.netloc))
            signable = '\n'.join(signable_list)
        else:
            signable = r.headers['Date']
        log.debug("data to sign: \n{}".format(signable))
        signature = self.sign(signable)
        r.headers['Authorization'] = self.signature_string_head % signature
        return r


HTTPSignatureAuth = Light_HTTPSignatureAuth
