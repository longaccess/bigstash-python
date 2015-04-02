# -*- coding: utf-8 -*-
# To the extent possible under law, the author of this work, Konstantinos
# Koukopoulos, has waived all copyright and related or neighboring rights to
# "Python codec for Wobbly Transformation Format - 8-bit (WTF-8)". It is
# dedicated to the public domain, as described in:
#     http://creativecommons.org/publicdomain/zero/1.0/
# This work is published from Greece and is available here:
# https://gist.github.com/kouk/d4e1faababf14b09b27f
from __future__ import unicode_literals, print_function
import six
import sys
import codecs


def encode(input, errors='strict'):
    """ convert from unicode text (with possible UTF-16 surrogates) to wtf-8
        encoded bytes.  If this is a python narrow build this will actually
        produce UTF-16 encoded unicode text (e.g. with surrogates).
    """

    # method to convert surrogate pairs to unicode code points permitting
    # lone surrogate pairs (aka potentially ill-formed UTF-16)

    def to_code_point(it):
        hi = None
        try:
            while True:
                c = ord(next(it))
                if c >= 0xD800 and c <= 0xDBFF:   # high surrogate
                    hi = c
                    c = ord(next(it))
                    if c >= 0xDC00 and c <= 0xDFFF:  # paired
                        c = 0x10000 + ((hi - 0xD800) << 10) + (c - 0xDC00)
                    else:
                        yield hi
                    hi = None
                yield c
        except StopIteration:
            if hi is not None:
                yield hi

    buf = six.binary_type()
    for code in to_code_point(iter(input)):

        if (0 == (code & 0xFFFFFF80)):
            buf += six.int2byte(code)
            continue
        elif (0 == (code & 0xFFFFF800)):
            buf += six.int2byte(((code >> 6) & 0x1F) | 0xC0)
        elif (0 == (code & 0xFFFF0000)):
            buf += six.int2byte(((code >> 12) & 0x0F) | 0xE0)
            buf += six.int2byte(((code >> 6) & 0x3F) | 0x80)
        elif (0 == (code & 0xFF300000)):
            buf += six.int2byte(((code >> 18) & 0x07) | 0xF0)
            buf += six.int2byte(((code >> 12) & 0x3F) | 0x80)
            buf += six.int2byte(((code >> 6) & 0x3F) | 0x80)
        buf += six.int2byte((code & 0x3F) | 0x80)

    return buf, len(buf)


def decode(input, errors='strict'):
    """ convert from wtf-8 encoded bytes to unicode text.
        If this is a python narrow build this will actually
        produce UTF-16 encoded unicode text (e.g. with surrogates).
    """

    buf = []
    try:
        it = six.iterbytes(input)
        c = None
        while True:
            c = next(it)
            if c < 0x80:
                pass
            elif c < 0xE0:
                c = (((c & 0x1F) << 6) +
                     (next(it) & 0x3F))
            elif c >= 0xE0 and c <= 0xEF:
                c = (((c & 0x0F) << 12) +
                     ((next(it) & 0x3F) << 6) +
                     (next(it) & 0x3F))
            elif c >= 0xF0 and c <= 0xF4:
                c = (((c & 0x07) << 18) +
                     ((next(it) & 0x3F) << 12) +
                     ((next(it) & 0x3F) << 6) +
                     (next(it) & 0x3F))
                if c >= sys.maxunicode:  # use a surrogate pair
                    buf.append(((c - 0x10000) >> 10) + 0xD800)
                    c = ((c - 0x10000) & 0x3FF) + 0xDC00
            else:
                raise ValueError("Invalid wtf sequence")
            buf.append(c)
            c = None
    except StopIteration:
        if c is not None:
            raise ValueError("Malformed WTF-8 sequence")
    return six.text_type().join(map(six.unichr, buf)), len(buf)


class StreamWriter(codecs.StreamWriter):
    encode = encode


class StreamReader(codecs.StreamReader):
    decode = decode


def find_codec(codec_name):
    if codec_name.lower() == 'wtf-8':
        return (encode, decode, StreamReader, StreamWriter)
    return None

codecs.register(find_codec)

if __name__ == "__main__":
    codecs.register(
        lambda name: codecs.lookup('utf-8') if name == 'cp65001' else None)

    msg = "I \u2665 Unicode. Even broken \ud800 Unicode."
    assert msg == msg.encode('wtf-8').decode('wtf-8')
    msg += "And high code points \U0001F62A. And γκρήκ τέξτ."
    assert msg == msg.encode('wtf-8').decode('wtf-8')
