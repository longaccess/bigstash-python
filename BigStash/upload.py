import os
import json
import hashlib
import re
import logging


class Upload(object):

    MANIFEST_FILE = 'manifest.json'
    INVALID_CHAR_RE = re.compile(r"[\\\/<>\|\?\"\*:]+")
    MORE_INVALID_CHARS_RE = re.compile(
        r'[^\u0009\u000a\u000d\u0020-\uD7FF\uE000-\uFFFD]')
    TEMP_FILE_RE = re.compile(r'^~\$|\.~|~.*\.tmp')
    TRAILING_CHAR_RE = re.compile(r'\.*|\s*$')
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
        self.paths = paths
        self.invalid_paths = []
        self.total_size = 0

    def _get_file_meta(self, path):
        meta = {
            'full_path': path,
            'size': os.path.getsize(path),
            'md5': hashlib.md5(open(path, 'rb').read()).hexdigest()
        }
        return meta

    def _create_manifest(self, paths):
        all_files = []
        total_size = 0
        for path in paths:
            if os.path.isdir(path):
                for r, _, files in os.walk(path):
                    for f in files:
                        fpath = os.path.join(r, f)
                        if self._is_valid(fpath):
                            all_files.append(self._get_file_meta(fpath))
                            self.total_size += os.path.getsize(fpath)
            elif os.path.isfile(path):
                if self._is_valid(path):
                    all_files.append(self._get_file_meta(path))
                    self.total_size += os.getsize(path)
        try:
            man = open(self.MANIFEST_FILE, 'w+')
            man.write(json.dumps(all_files))
            return True
        except IOError:
            logging.error("Error writing manifest")
        finally:
            man.close()
        return False

    def archive(self, title=''):
        success = self.create_manifest(self.paths)
        if not success or self.invalid_paths:
            logging.info('Something went wrong')
            return
        if not title:
            title = self._get_title()
        try:
            a = self.api.CreateArchive(title=title, size=self.total_size)
            u = self.CreateUpload(a.id)
            self._sendManifest(u.id)
        except:
            logging.error("Couldn't create upload")

    def _send_manifest(self, upload_id):
        self.api.UploadManifest(upload_id, self.MANIFEST_FILE)

    def _is_valid(self, path):
        filename = os.path.basename(path)
        if self.INVALID_CHAR_RE.search(path):
            self.invalid_paths.append(
                {'path': path, 'msg': self.INVALID_CHAR_MSG})
        elif self.TRAILING_CHAR_RE.match(path):
            self.invalid_paths.append(
                {'path': path, 'msg': self.TRAILING_CHARS_MSG})
        elif self.MORE_INVALID_CHAR_RE.match(path):
            self.invalid_paths.append(
                {'path': path, 'msg': self.INVALID_CHAR_MSG})
        elif os.path.islink(path):
            self.invalid_paths.append(
                {'path': path, 'msg': self.LINK_FILE_MSG})
        elif self.TEMP_FILE_RE.match(filename):
            self.invalid_paths.append(
                {'path': path, 'msg': self.TEMP_FILE_MSG})
        elif filename in self.INVALID_PATH:
            self.invalid_paths.append(
                {'path': path, 'msg': self.INVALID_FILE_MSG})
        else:
            return True
        return False

    def _get_title(self):
        title = os.path.commonprefix(self.paths)
        return title if title else self.paths[0]
