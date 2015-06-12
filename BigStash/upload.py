"""bgst is a command line client to BigStash.co

Usage:
  bgst put [--ignore-file IGNORE] [-t TITLE] [--silent] [--dont-wait] FILES...
  bgst settings [--user=USERNAME] [--password=PASSWORD]
  bgst settings --reset
  bgst list [--limit=NUMBER]
  bgst info (ARCHIVE_ID)
  bgst files (ARCHIVE_ID)
  bgst notifications [--limit=NUMBER]
  bgst (-h | --help)
  bgst --version

Options:
  -h --help                     Show this screen.
  --version                     Show version.
  -t TITLE --title=TITLE        Set archive title [default: ]
  --dont-wait                   Do not wait for archive status after uploading.
  --silent                      Do not show ANY progress or other messages.
  --username=USERNAME           Use bigstash username.
  --password=PASSWORD           Use bigstash password.
  --reset                       Remove saved configuration, revoke
                                authentication token.
  --limit=NUMBER                Show up to NUMBER results. [default: 10]
  --ignore-file=IGNORE           Path to a .gitignore like file.
"""

from __future__ import print_function
import boto3
import six
import sys
import os
import errno
import logging
import posixpath
import threading
import inflect
from wrapt import decorator
from BigStash import __version__
from BigStash.filename import setup_user_ignore
from BigStash.auth import get_api_credentials
from BigStash.conf import BigStashAPISettings
from BigStash import BigStashAPI, BigStashError
from BigStash.manifest import Manifest
from boto3.s3.transfer import S3Transfer, TransferConfig
from retrying import retry
from docopt import docopt

log = logging.getLogger('bigstash.upload')

peng = inflect.engine()


def smart_str(s):
    if isinstance(s, six.text_type):
        return s
    return s.decode('utf-8')


@decorator
def handles_encoding_errors(wrapped, instance, args, kwargs):
    try:
        return wrapped(*args, **kwargs)
    except UnicodeEncodeError:
        outenc = sys.stdout.encoding
        log.debug("Error while outputting to terminal", exc_info=True)
        if not outenc or outenc.lower() not in ('utf-8', 'cp65001'):
            sys.stderr.write(
                "There was an error while trying to encode data for display "
                "to your terminal. If your terminal is capable of displaying "
                "unicode characters you may get around the problem by setting "
                "PYTHONIOENCODING=UTF-8 in the environment\n")
            sys.exit(1)
        raise


class ProgressPercentage(object):
    def __init__(self, filename):
        self._filename = smart_str(filename)
        self._size = os.path.getsize(filename)
        self._seen_so_far = 0
        self._lock = threading.Lock()

    def _write_progress(self, wrote, total):
        percentage = 100
        if total > 0:
            percentage = (wrote / float(total)) * 100
        sys.stdout.write(u"\r{} {} / {} ({:.2f}%)".format(
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
    outenc = sys.stdout.encoding
    if not outenc or outenc.lower() not in ('utf-8', 'cp65001'):
        sys.stderr.write(
            "WARNING: terminal doesn't seem to support unicode.\n"
            "If this is incorrect, fix your locale settings or "
            "set PYTHONIOENCODING='UTF-8' in the environment\n"
            "(python reported output encoding: '{}')\n".format(outenc))
    argv = sys.argv
    if not six.PY3 and os.name == 'nt':
        from BigStash.winargvfix import fix_argv_on_windows, fix_env_on_windows
        argv = fix_argv_on_windows()
        fix_env_on_windows()
    args = docopt(__doc__, argv=argv[1:], version=__version__)

    settings = BigStashAPISettings.load_settings()
    BigStashAPI.setup_logging(settings)
    if os.name == 'nt':
        try:
            import win_unicode_console
            win_unicode_console.enable()
        except ImportError:
            log.debug("win_unicode_console not found", exc_info=True)
            pass

    if args['put']:
        bgst_put(args, settings)
    elif args['settings']:
        bgst_settings(args, settings)
    elif args['list']:
        bgst_list_archives(args, settings)
    elif args['files']:
        bgst_archive_files(args, settings)
    elif args['info']:
        bgst_archive_info(args, settings)
    elif args['notifications']:
        bgst_list_notifications(args, settings)


@handles_encoding_errors
def bgst_archive_files(args, settings):
    k, s = get_api_credentials(settings)
    api = BigStashAPI(key=k, secret=s, settings=settings)
    archive_id = args['ARCHIVE_ID'].split('-')[0]
    for f in api.get_all_objects(api.GetArchive(archive_id).files):
        print(u"{}\t{}".format(f.path, f.size))


@handles_encoding_errors
def bgst_list_archives(args, settings):
    k, s = get_api_credentials(settings)
    api = BigStashAPI(key=k, secret=s, settings=settings)
    count = 0
    for archive in api.GetArchives():
        count = count+1
        print(u"{}\t{}\t{}\t{}\t{}".format(
            archive.key,
            archive.status.upper().ljust(8),
            archive.created,
            archive.title,
            archive.size))
        if count >= int(args['--limit']):
            break


def bgst_settings(args, settings):
    if args['--reset']:
        authfile = 'auth.{}'.format(settings.profile)
        try:
            r = settings.read_config_file(authfile)
        except IOError as e:
            if e.errno == errno.ENOENT:
                return
            else:
                raise
        try:
            api = BigStashAPI(key=r['key'], secret=r['secret'])
            os.remove(settings.get_config_file(authfile))
            # This is a hack. The API should allow a client to destroy its own
            # key without knowing the token_id.
            token_id = r['url'].split('/')[-2]
            api.DestroyAPIKey(token_id)
        except OSError as e:
            # errno.ENOENT = no such file or directory
            if e.errno != errno.ENOENT:
                raise
    else:
        k, s = get_api_credentials(
            settings, args['--user'], args['--password'])


@handles_encoding_errors
def bgst_put(args, settings):
    try:
        title = args['--title'] if args['--title'] else None
        opt_silent = False if not args['--silent'] else True
        opt_dont_wait = False if not args['--dont-wait'] else True
        upload = None
        filepaths = map(smart_str, args['FILES'])
        ignorefile = args['--ignore-file']
        if ignorefile:
            setup_user_ignore(ignorefile)
        manifest, errors, ignored = Manifest.from_paths(
            paths=filepaths, title=title)
        ignored_msg = ''
        if ignored:
            ignored_msg = "({} {} ignored)".format(
                len(ignored), peng.plural("file", len(ignored)))
        if len(manifest) == 0:
            print(" ".join(["No files found", ignored_msg]))
            sys.exit(5)
        if errors:
            errtext = [": ".join(e) for e in errors]
            print("\n".join(["There were errors:"] + errtext))
            sys.exit(4)
        k, s = get_api_credentials(settings)
        bigstash = BigStashAPI(key=k, secret=s, settings=settings)
        upload = bigstash.CreateUpload(manifest=manifest)
        filecount = len(manifest)
        if not opt_silent:
            msg = "Uploading {} {} as archive {}..".format(
                filecount, peng.plural("file", filecount), upload.archive.key)
            print(" ".join([msg, ignored_msg]))
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
        msg = "{}: {}".format(err, e.strerror)
        log.warn(msg, exc_info=True)
        print(msg)
        sys.exit(3)
    except BigStashError as e:
        log.warn("oops", exc_info=True)
        print(e)
        sys.exit(2)
    except Exception as e:
        log.error("error", exc_info=True)
        sys.exit(1)


@handles_encoding_errors
def bgst_list_notifications(args, settings):
    k, s = get_api_credentials(settings)
    api = BigStashAPI(key=k, secret=s, settings=settings)
    count = 0
    for notification in api.GetNotifications():
        count = count+1
        print(u"{}\t{}\t{}\t{}".format(
            notification.created,
            notification.status.upper().ljust(8),
            notification.id,
            notification.verb))
        if count >= int(args['--limit']):
            break


@handles_encoding_errors
def bgst_archive_info(args, settings):
    k, s = get_api_credentials(settings)
    api = BigStashAPI(key=k, secret=s, settings=settings)
    archive_id = args['ARCHIVE_ID'].split('-')[0]
    archive = api.GetArchive(archive_id)
    print(u'Archive ID:\t{}'.format(archive.key))
    print(u'Status:    \t{}'.format(archive.status))
    print(u'Created:   \t{}'.format(archive.created))
    print(u'Title:     \t{}'.format(archive.title))
    print(u'Size:      \t{}'.format(archive.size))


if __name__ == "__main__":
    main()
