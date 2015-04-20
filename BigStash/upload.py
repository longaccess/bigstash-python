import boto3
import os
import sys
import logging
import posixpath
import threading
from getpass import getpass
from BigStash.conf import BigStashAPISettings, DEFAULT_SETTINGS
from BigStash import BigStashAPI, BigStashError, BigStashAuth
from BigStash.manifest import Manifest
from boto3.s3.transfer import S3Transfer, TransferConfig
from retrying import retry


log = logging.getLogger('bigstash.uploader')


class ProgressPercentage(object):
    def __init__(self, filename):
        self._filename = filename
        self._size = float(os.path.getsize(filename))
        self._seen_so_far = 0
        self._lock = threading.Lock()

    def __call__(self, bytes_amount):
        # To simplify we'll assume this is hooked up
        # to a single filename.
        with self._lock:
            # because: https://github.com/boto/boto3/issues/98
            if bytes_amount > 0 and self._seen_so_far == self._size:
                # assume we are now only starting the actual transfer
                self._seen_so_far = 0
            self._seen_so_far += bytes_amount
            percentage = (self._seen_so_far / self._size) * 100
            sys.stdout.write("\r%s %s / %s (%.2f%%)" % (
                self._filename, self._seen_so_far, self._size, percentage))
            sys.stdout.flush()


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
    level = getattr(logging, os.environ.get("BS_LOG_LEVEL", "error").upper())
    logging.basicConfig(level=level)
    if len(sys.argv) == 1:
        print("Usage: {} [file1, file2, ...]".format(sys.argv[0]))
        sys.exit(3)
    try:
        upload = None
        manifest, errors = Manifest.from_paths(sys.argv[1:])
        if errors:
            errtext = [": ".join(e) for e in errors]
            print("\n".join(["There were errors:"] + errtext))
            sys.exit(4)
        bigstash = get_api()
        upload = bigstash.CreateUpload(manifest=manifest)
        print("Uploading {}..".format(upload.archive.key))
        s3 = boto3.resource(
            's3', region_name=upload.s3.region,
            aws_access_key_id=upload.s3.token_access_key,
            aws_secret_access_key=upload.s3.token_secret_key,
            aws_session_token=upload.s3.token_session, use_ssl=False)
        config = TransferConfig(
            multipart_threshold=8 * 1024 * 1024,
            max_concurrency=10,
            num_download_attempts=10)
        transfer = S3Transfer(s3.meta.client, config)
        for f in manifest:
            transfer.upload_file(
                f.original_path, upload.s3.bucket,
                posixpath.join(upload.s3.prefix, f.path),
                callback=ProgressPercentage(f.original_path))
            print("..OK")
        bigstash.UpdateUploadStatus(upload, 'uploaded')
        print("Waiting for {}..".format(upload.url), end="", flush=True)
        retry_args = {
            'wait': 'exponential_sleep',
            'wait_exponential_multiplier': 1000,
            'wait_exponential_max': 10000,
            'retry_on_exception': lambda e: not isinstance(e, BigStashError),
            'retry_on_result': lambda r: r.status not in ('completed', 'error')
        }

        @retry(**retry_args)
        def refresh(u):
            print(".", end="", flush=True)
            return bigstash.RefreshUploadStatus(u)

        print("upload status: {}".format(refresh(upload).status))
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
