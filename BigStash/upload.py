import os
import hashlib
import re
import logging
from datetime import datetime
from BigStash import BigStashError


class Upload(object):

    MANIFEST_FILE = 'manifest.json'
    INVALID_CHAR_RE = re.compile(r"[\\\/<>\|\?\"\*:]+")
    MORE_INVALID_CHARS_RE = re.compile(
        r'[^\u0009\u000a\u000d\u0020-\uD7FF\uE000-\uFFFD]')
    TEMP_FILE_RE = re.compile(r'^~\$|\.~|~.*\.tmp')
    TRAILING_CHAR_RE = re.compile(r'\.+|\s+$')
    INVALID_FILES = ['desktop.ini', 'thumbs.db', '.ds_store', 'icon\\r',
                     '.dropbox', '.dropbox.attr']
    INVALID_CHAR_MSG = 'Invalid characters in path'
    INVALID_FILE_MSG = 'Non accepted file'
    LINK_FILE_MSG = 'File is link'
    TEMP_FILE_MSG = 'Temporary file'
    TRAILING_CHARS_MSG = 'Path contains trailing dots or spaces'

    def __init__(self, paths=[], prefix='', api=None):
        if not api:
            raise TypeError("You must provide a BigStash API instance")
        if not paths:
            raise TypeError("You must provide at least a file path")
        self.api = api
        self.paths = [os.path.abspath(p) for p in paths]
        self.basepath = os.path.commonprefix(self.paths)
        self.invalid_paths = []
        self.total_size = 0

    def archive(self, title=''):
        title = title if title else self._get_title()
        files_meta = self._get_files_meta()
        if self.invalid_paths:
            logging.info('There were invalid files in your selection')
            return
        try:
            archive = self.api.CreateArchive(title=title, size=self.total_size)
            manifest = {
                'title': archive.title,
                'size': archive.size,
                'file_count': len(files_meta)
            }
            self.api.CreateUpload(archive=archive, manifest=manifest)
        except BigStashError:
            logging.error("Couldn't create upload")

    def _get_file_meta(self, path):
        """ Create the file meta dictionary to be included in the manifest

        :param path: the absolute path of the file
        """
        file_meta = {
            'key_name': self._get_key_name(path),
            'file_name': os.path.basename(path),
            'full_path': path,
            'size': os.path.getsize(path),
            'last_modified': os.path.getmtime(path),
            'md5': hashlib.md5(open(path, 'rb').read()).hexdigest()
        }
        return file_meta

    def _get_files_meta(self):
        """
        Traverse the given paths and construct the total metadata stracture
        """
        files_meta = []
        for path in self.paths:
            if not os.path.exists(path):
                raise IOError('File "{}" does not exist'.format(path))
            if os.path.isdir(path):
                for r, _, files in os.walk(path):
                    for f in files:
                        fpath = os.path.join(r, f)
                        if self._is_valid(fpath):
                            files_meta.append(self._get_file_meta(fpath))
                            self.total_size += os.path.getsize(fpath)
            elif os.path.isfile(path):
                if self._is_valid(path):
                    files_meta.append(self._get_file_meta(path))
                    self.total_size += os.path.getsize(path)
        return files_meta

    def _is_valid(self, path):
        """ Check if file path is valid

        :param path: the absolute path of the file
        """
        filename = os.path.basename(path)
        if self.INVALID_CHAR_RE.match(filename):
            self.invalid_paths.append(
                {'path': path, 'msg': self.INVALID_CHAR_MSG})
        elif self.TRAILING_CHAR_RE.match(filename):
            self.invalid_paths.append(
                {'path': path, 'msg': self.TRAILING_CHARS_MSG})
        elif self.MORE_INVALID_CHARS_RE.match(filename):
            self.invalid_paths.append(
                {'path': path, 'msg': self.INVALID_CHAR_MSG})
        elif os.path.islink(path):
            self.invalid_paths.append(
                {'path': path, 'msg': self.LINK_FILE_MSG})
        elif self.TEMP_FILE_RE.match(filename):
            self.invalid_paths.append(
                {'path': path, 'msg': self.TEMP_FILE_MSG})
        elif filename in self.INVALID_FILES:
            self.invalid_paths.append(
                {'path': path, 'msg': self.INVALID_FILE_MSG})
        else:
            return True
        return False

    def _get_key_name(self, path):
        """ Return the appropriate s3 key name for a file

        :param path: the absolute path of the file
        """
        if self.basepath:
            if os.path.isdir(self.basepath):
                return path.replace(self.basepath, '')
            return os.path.basename(path)
        return path

    def _get_title(self):
        """ Create a title for the archive if none given """
        if self.basepath:
            title = os.path.basename(os.path.normpath(self.basepath))
        else:
            title = 'upload-{}'.format(datetime.now().date().isoformat())
        return title


if __name__ == "__main__":
    import sys
    from BigStash.conf import BigStashAPISettings, DEFAULT_SETTINGS
    from BigStash.api import BigStashAPI
    local_settings = BigStashAPISettings('local')
    local_settings['base_url'] = os.environ.get(
        'BS_API_URL', DEFAULT_SETTINGS['base_url'])
    logging.basicConfig(level=logging.DEBUG)

    def get_api(s=None):
        try:
            return BigStashAPI(
                key=os.environ['BS_API_KEY'],
                secret=os.environ['BS_API_SECRET'],
                settings=s or local_settings)
        except KeyError:
            print "Please define the following env vars:"
            print "BS_API_KEY"
            print "BS_API_SECRET"
    api = get_api()

    print Upload(paths=sys.argv[1:], api=get_api()).archive('foo')
