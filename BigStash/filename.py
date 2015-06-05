from __future__ import unicode_literals
import six
import re
import sys
import os.path
import posixpath
import fnmatch
from functools import partial
from operator import contains

# from: https://github.com/longaccess/deepfreeze.io/blob/dev/docs/api.md

# Dissalowed XML character ranges. See http://www.w3.org/TR/REC-xml/#NT-Char

_xml_invalid_ranges = [
    '\u0000-\u0008', '\u000B-\u000C', '\u000E-\u001F', '\u007F-\u0084',
    '\u0086-\u009F', '\uFDD0-\uFDDF', '\uFFFE-\uFFFF']

if sys.maxunicode >= 0x10000:
    # if UCS-4 is supported
    _xml_invalid_ranges += [
        '\U0001FFFE-\U0001FFFF', '\U0002FFFE-\U0002FFFF',
        '\U0003FFFE-\U0003FFFF', '\U0004FFFE-\U0004FFFF',
        '\U0005FFFE-\U0005FFFF', '\U0006FFFE-\U0006FFFF',
        '\U0007FFFE-\U0007FFFF', '\U0008FFFE-\U0008FFFF',
        '\U0009FFFE-\U0009FFFF', '\U000AFFFE-\U000AFFFF',
        '\U000BFFFE-\U000BFFFF', '\U000CFFFE-\U000CFFFF',
        '\U000DFFFE-\U000DFFFF', '\U000EFFFE-\U000EFFFF',
        '\U000FFFFE-\U000FFFFF', '\U0010FFFE-\U0010FFFF']

_xml_invalid_high_surrogate = [
    '\uD83F', '\uD87F', '\uD8BF', '\uD8FF',
    '\uD93F', '\uD97F', '\uD9BF', '\uD9FF',
    '\uDA3F', '\uDA7F', '\uDABF', '\uDAFF',
    '\uDB3F', '\uDB7F', '\uDBBF', '\uDBFF']

SEARCH_PATTERNS = {
    "restricted characters": r"[\\\/<>\|\?\"\*:]+",
    "invalid character for xml": "[{}]".format(
        "".join(_xml_invalid_ranges)),
    "invalid character for xml (surrogate pair)": "[{}][\uDFFE-\uDFFF]".format(
        "".join(_xml_invalid_high_surrogate)),
}

MATCH_PATTERNS = {
    "name looks like temporary file": r'^~\$|\.~|~.*\.tmp',
    "trailing dot characters": r'\.+$',
    "trailing whitespace": r'\s+$',
}

IGNORED_FILE_NAMES = [
    'desktop.ini', 'thumbs.db', '.ds_store',
    'icon\r', '.dropbox', '.dropbox.attr'
]

IGNORE_TESTS = {
    'small system file': partial(contains, IGNORED_FILE_NAMES),
    'is link': os.path.islink
}


class FnMatches(object):
    def __init__(self, patterns=[]):
        self.patterns = patterns

    def __call__(self, path):
        return any(map(partial(fnmatch.fnmatch, path), self.patterns))


def setup_user_ignore(ignorefile):
    with open(os.path.expanduser(ignorefile)) as ignorefile:
        p = list(l.strip() for l in ignorefile if not l.startswith('#'))
        IGNORE_TESTS['is user ignored'] = FnMatches(p)


def splitpath(path):
    _, path = os.path.splitdrive(path)
    folders = []
    path, file = os.path.split(path)
    if file:
        folders.append(file)
    while True:
        path, folder = os.path.split(path)
        if folder != "":
            folders.append(folder)
        else:
            if path != "":
                folders.append(path)
            break
    folders.reverse()
    return folders


def toposix(path):
    components = splitpath(path)
    if components[0] == os.sep:
        components[0] = posixpath.sep
    return posixpath.join(*components)


def get_validator(tests={}, search={}, match={}):
    validators = [(m, re.compile(p).search) for m, p in six.iteritems(search)]
    validators += [(m, re.compile(p).match) for m, p in six.iteritems(match)]
    validators += [(m, f) for m, f in six.iteritems(tests)]

    return lambda path: ((m, f, p) for p in splitpath(path)
                         for m, f in validators if p != os.sep and f(p))

should_ignore = lambda: get_validator(tests=IGNORE_TESTS)
is_invalid = lambda: get_validator(
    search=SEARCH_PATTERNS, match=MATCH_PATTERNS)
