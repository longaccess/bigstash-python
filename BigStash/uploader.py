import os
import sys
import logging
from getpass import getpass
from BigStash.conf import BigStashAPISettings, DEFAULT_SETTINGS
from BigStash import BigStashAPI, BigStashError, BigStashAuth
from BigStash.upload import Upload as Uploader


log = logging.getLogger('bigstash.uploader')


def get_api(settings=None):
    if settings is None:
        settings = BigStashAPISettings('local')
        settings['base_url'] = os.environ.get(
            'BS_API_URL', DEFAULT_SETTINGS['base_url'])
    k = s = None
    if all(e in os.environ for e in ('BS_API_KEY', 'BS_API_SECRET')):
        k, s = (os.environ['BS_API_KEY'], os.environ['BS_API_SECRET'])
    else:
        auth = BigStashAuth(settings=settings)
        k, s = auth.GetAPIKey(input("Username: "), getpass("Password: "))
    return BigStashAPI(key=k, secret=s, settings=settings)


def main():
    logging.basicConfig()
    if len(sys.argv) == 1:
        print("Usage: {} [file1, file2, ...]".format(sys.argv[0]))
        sys.exit(3)
    try:
        Uploader(get_api()).archive(sys.argv[1:])
    except OSError as e:
        err = "error"
        if e.filename is not None:
            err = e.filename
        print("{}: {}".format(err, e.strerror))
        sys.exit(3)
    except BigStashError as e:
        print(e)
        sys.exit(2)
    except Exception as e:
        log.error("error", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
