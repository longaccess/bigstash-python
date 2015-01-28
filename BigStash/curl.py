import json
import logging
import os
import sys
import time
import requests
from httpsig.requests_auth import HTTPSignatureAuth
from BigStash import version
from urlparse import urlparse

API_KEY_ID = os.environ.get('BIGSTASH_API_TOKEN', None)
SECRET = os.environ.get('BIGSTASH_API_SECRET', None)
URL = os.environ.get('BIGSTASH_API_URL', 'http://localhost:8000/api/v1')
TOKEN = os.environ.get('BIGSTASH_TOKEN_FILE', 'token.json')
headers = {
    'User-agent': 'BigStash Python SDK v{}'.format(version),
    'Accept': 'application/vnd.deepfreeze+json',
    'Content-Type': 'application/vnd.deepfreeze+json'
}
host = urlparse(URL).netloc
temp_token = key = secret = None
logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))


def get_basic_auth():
    from netrc import netrc
    username, _, password = netrc().authenticators(host.split(':')[0])
    return (username, password)


def get_signature_auth_temp():
    global temp_token
    username, password = get_basic_auth()
    logging.getLogger().warn(
        "creating temporary token as {}".format(username))
    assert username is not None
    req = requests.post(URL + '/tokens/', auth=(username, password),
                        data=json.dumps({"name": "curl.py temp token"}),
                        headers=headers)
    req.raise_for_status()
    r = json.loads(req.content)
    temp_token = r.get("url", None)
    return (r.get("key", None), r.get("secret", None))


def get_signature_auth(key, secret, **kwargs):
    global headers
    signature_headers = ['(request-line)', 'date', 'host']
    headers.update({
        'Host': host,
        'X-Deepfreeze-Api-Key': key,
        'Date': time.strftime('%a, %d %b %Y %H:%M:%S GMT',
                              time.gmtime(time.time()))
    })

    return HTTPSignatureAuth(key_id=key, secret=secret,
                             algorithm='hmac-sha256',
                             headers=signature_headers)


def get_args():
    etag = data = None
    method = requests.get
    arg = sys.argv[1:]
    if arg[0] == '--etag':
        etag = arg[1]
        arg = arg[2:]
    url = URL + arg[0]
    if len(arg) > 2:
        data = arg[2]
        method = requests.patch
    elif len(arg) > 1:
        data = arg[1]
        method = requests.post
    return (method, url, data, etag)


def get_auth():
    if API_KEY_ID is None:
        try:
            with open(TOKEN) as t:
                return get_signature_auth(**json.load(t))
        except Exception:
            logging.getLogger().warn(
                "couldn't load auth from {}".format(TOKEN))
            key, secret = get_signature_auth_temp()
            return get_signature_auth(key, secret)
    else:
        assert SECRET is not None
        return get_signature_auth(API_KEY_ID, SECRET)


def main(auth, argv):
    global temp_token

    method, url, data, etag = get_args()

    if etag is not None:
        headers['If-None-Match'] = etag

    req = method(url, auth=auth, headers=headers, data=data)
    if temp_token is not None:
        yn = raw_input('Save temporary token?: [y/N] ')
        if yn and yn[0].lower() == 'y':
            with open(TOKEN, 'w') as t:
                json.dump({'key': key, 'secret': secret}, t)
            temp_token = None
    return req


if __name__ == "__main__":
    auth = None
    try:
        basic = sys.argv[1].startswith('/tokens')
        auth = get_basic_auth() if basic else get_auth()
        req = main(auth, sys.argv)
    finally:
        if temp_token is not None and auth is not None:
            requests.delete(temp_token, auth=auth, headers=headers)

    print req.status_code, req.reason
    for k, v in req.links.items():
        print k, v
    for k, v in req.headers.items():
        print k + ':', v
    print
    try:
        json.dump(req.json(), sys.stdout, indent=4)
    except ValueError:
        logging.getLogger().warn("no JSON data returned")
    print
