# -*- coding: utf-8 -*-
import base64
from datetime import datetime
import math
import os

from Crypto.Random import random
from jinja2 import Markup, escape


def datetimeformat(dt, fmt=None, relative=False):
    """Template filter for readable formatting of datetime.datetime"""
    fmt = fmt or '%b %d, %Y %I:%M %p'
    if relative:
        time_difference = _relative_timestamp(dt)
        if time_difference:
            return '{} ago'.format(time_difference)
    return dt.strftime(fmt)


def _relative_timestamp(dt):
    """"
    Format a human readable relative time for timestamps up to 30 days old
    """
    delta = datetime.utcnow() - dt
    diff = (delta.microseconds + (delta.seconds + delta.days * 24 * 3600) * 1e6) / 1e6
    if diff < 45:
        return '{} second{}'.format(int(diff), '' if int(diff) == 1 else 's')
    elif diff < 90:
        return 'a minute'
    elif diff < 2700:
        return '{} minutes'.format(int(max(diff / 60, 2)))
    elif diff < 5400:
        return 'an hour'
    elif diff < 79200:
        return '{} hours'.format(int(max(diff / 3600, 2)))
    elif diff < 129600:
        return 'a day'
    elif diff < 2592000:
        return '{} days'.format(int(max(diff / 86400, 2)))
    else:
        return None


def nl2br(context, value):
    formatted = u'<br>\n'.join(escape(value).split('\n'))
    if context.autoescape:
        formatted = Markup(formatted)
    return formatted


def random_padding(nchunks=1, size=1048576):
    """
    Returns a random amount, between 0 and `size` bytes, of random data intended
    to be used for compression-resistant padding. The random data is urlsafe
    base64-encoded to avoid possible collisions with special characters in HTML
    (inspired by the common technique for inlining images in HTML).

    The padding is further split into randomly-sized chunks, which is useful so
    some of the random data may be used to help pad POST requests (via hidden
    form fields) in addition to the response.
    """
    # Make sure there's enough padding to partition into the requested number of
    # chunks.
    assert size >= nchunks
    pad_amt = 0
    while pad_amt < nchunks:
        pad_amt = random.randint(0, size)

    # base64 adds a 4:3 overhead, so we need less than pad_amt random bytes to
    # get pad_amt random base64 characters
    pad_bytes = os.urandom(int(math.ceil(pad_amt / 4.0 * 3.0)))
    # base64 output is padded to the nearest multiple of 4 bytes, so we need to
    # shave off any extra bytes here.
    padding = base64.urlsafe_b64encode(pad_bytes)[:pad_amt]

    chunk_indexes = set()
    chunk_indexes.update((0, pad_amt))
    for chunk in range(nchunks-1):
        # `pad_amt-1` because Crypto.random's randint is a closed interval: [a,
        # b] and we want to avoid picking an invalid index.
        while True:
            index = random.randint(1, pad_amt-1)
            # Avoid picking the same index more than once, because that would
            # result in a chunk of length 0.
            if index not in chunk_indexes:
                chunk_indexes.add(index)
                break

    chunks = []
    chunk_indexes = sorted(list(chunk_indexes))
    for i in range(len(chunk_indexes)-1):
        chunks.append(padding[chunk_indexes[i]:chunk_indexes[i+1]])

    return chunks

