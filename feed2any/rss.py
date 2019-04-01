from __future__ import absolute_import
from __future__ import print_function
import time
import sys
from contextlib import contextmanager
from json import dumps, dump, load
from logging import getLogger
import hashlib
from os import makedirs
from os.path import join, exists, dirname, abspath


logger = getLogger()


def relative(path):
    return abspath(join(dirname(__file__), path))


def get_content(filename):
    if filename == '-':
        return sys.stdin.read()
    with open(filename, 'r') as input:
        return input.read()


def get_hash(*data):
    m = hashlib.md5()
    m.update(dumps(data).encode('utf-8'))
    return m.hexdigest()


def dump_json(filename, data):
    with open(filename, 'w') as output:
        dump(data, output)


def load_json(filename):
    if not exists(filename):
        return
    with open(filename, 'r') as input:
        try:
            return load(input)
        except:
            pass


def output(content):
    print(content.encode('utf-8'), end='', file=sys.stdout)


@contextmanager
def skip_cache(cache, additional):
    if not cache:
        yield set()
        return

    if not exists(cache):
        makedirs(cache)

    filename = join(cache, 'to-maildir.json')
    cached = load_json(filename) or {}

    yield set(cached.keys())

    now = int(time.time())
    cached = {
        key: timestamp
        for key, timestamp in cached.items()
        if now - timestamp <= 60 * 60 * 24
    }
    cached.update({
        item: now
        for item in additional
    })
    dump_json(filename, cached)


def get_description(item):
    if 'text' in item:
        return item['text']
    for content_type, content in item['content'].items():
        return content
    return ''
