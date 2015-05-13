"""bsput
Usage:
  bsput [-t TITLE] [--silent] [--dont-wait] FILES...
  bsput (-h | --help)
  bsput --version

Options:
  -h --help                     Show this screen.
  --version                     Show version
  -t TITLE --title=TITLE        Set archive title [default: ]
  --dont-wait                   Do not wait for archive status after uploading
  --silent                      Do not show ANY progress or other messages.
"""

from __future__ import print_function
import boto3
import os
import sys
import logging
import posixpath
import threading
from BigStash import __version__
from BigStash.auth import get_api_credentials
from BigStash.conf import BigStashAPISettings
from BigStash import BigStashAPI, BigStashError
from BigStash.manifest import Manifest
from boto3.s3.transfer import S3Transfer, TransferConfig
from retrying import retry
from docopt import docopt

log = logging.getLogger('bigstash.upload')


class ProgressPercentage(object):
    def __init__(self, filename):
        self._filename = filename
        self._size = os.path.getsize(filename)
        self._seen_so_far = 0
        self._lock = threading.Lock()

    def _write_progress(self, wrote, total):
        percentage = 100
        if total > 0:
            percentage = (wrote / float(total)) * 100
        sys.stdout.write("\r{} {} / {} ({:.2f}%)".format(
            self._filename, wrote, total, percentage))
        sys.stdout.flush()

    def __call__(self, bytes_amount):
        # To simplify we'll assume this is hooked up
        # to a single filename.
        with self._lock:
            # because: https://github.com/boto/boto3/issues/98
            if bytes_amount > 0 and self._seen_so_far == self._size:
                # assume we are now only starting the actual transfer
                self._seen_so_far = 0
            self._seen_so_far += bytes_amount
            self._write_progress(self._seen_so_far, self._size)


def main():
    args = docopt(__doc__, version=__version__)
    title = args['--title'] if args['--title'] else None
    paths = args['FILES']
    opt_silent = False if not args['--silent'] else True
    opt_dont_wait = False if not args['--dont-wait'] else True

    level = getattr(logging, os.environ.get("BS_LOG_LEVEL", "error").upper())
    logging.basicConfig(level=level)
    try:
        upload = None
        manifest, errors = Manifest.from_paths(paths=paths, title=title)
        if errors:
            errtext = [": ".join(e) for e in errors]
            print("\n".join(["There were errors:"] + errtext))
            sys.exit(4)
        settings = BigStashAPISettings.load_settings()
        k, s = get_api_credentials(settings)
        bigstash = BigStashAPI(key=k, secret=s, settings=settings)
        upload = bigstash.CreateUpload(manifest=manifest)
        if not opt_silent:
            print("Uploading {}..".format(upload.archive.key))
        s3 = boto3.resource(
            's3', region_name=upload.s3.region,
            aws_access_key_id=upload.s3.token_access_key,
            aws_secret_access_key=upload.s3.token_secret_key,
            aws_session_token=upload.s3.token_session)
        config = TransferConfig(
            multipart_threshold=8 * 1024 * 1024,
            max_concurrency=10,
            num_download_attempts=10)
        transfer = S3Transfer(s3.meta.client, config)

        cb = None
        for f in manifest:
            if not opt_silent:
                cb = ProgressPercentage(f.original_path)
            transfer.upload_file(
                f.original_path, upload.s3.bucket,
                posixpath.join(upload.s3.prefix, f.path),
                callback=cb)
            if not opt_silent:
                print("..OK")
        bigstash.UpdateUploadStatus(upload, 'uploaded')
        if opt_dont_wait:
            sys.stdout.flush()
            sys.exit(0)
        if not opt_silent:
            print("Waiting for {}..".format(upload.url), end="")
        sys.stdout.flush()
        retry_args = {
            'wait': 'exponential_sleep',
            'wait_exponential_multiplier': 1000,
            'wait_exponential_max': 10000,
            'retry_on_exception': lambda e: not isinstance(e, BigStashError),
            'retry_on_result': lambda r: r.status not in ('completed', 'error')
        }

        @retry(**retry_args)
        def refresh(u):
            if not opt_silent:
                print(".", end="")
                sys.stdout.flush()
            return bigstash.RefreshUploadStatus(u)
        if not opt_silent:
            print("upload status: ", end="")
        final_status = refresh(upload).status
        if not opt_silent:
            print(final_status)
        if final_status != 'completed':
            sys.exit(2)
        else:
            sys.exit(0)

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
