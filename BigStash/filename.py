from __future__ import unicode_literals
import six
import re
import sys
import os.path
from functools import partial
from operator import contains

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

INVALID_TESTS = {
    "file doesn't exist": lambda p: not os.path.exists(p)
}


def get_validator(tests={}, search={}, match={}):
    validators = [(m, re.compile(p).search) for m, p in six.iteritems(search)]
    validators += [(m, re.compile(p).match) for m, p in six.iteritems(match)]
    validators += [(m, f) for m, f in six.iteritems(tests)]

    return lambda p: ((m, f) for m, f in validators if f(p))

should_ignore = get_validator(tests=IGNORE_TESTS)
is_invalid = get_validator(
    tests=INVALID_TESTS, search=SEARCH_PATTERNS, match=MATCH_PATTERNS)
