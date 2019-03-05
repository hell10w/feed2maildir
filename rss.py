# encoding: utf-8

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
from time import struct_time

try:
    import requests
    import feedparser
    from jinja2 import Template
    import dateutil.parser
    import html2text
    import inscriptis
except ImportError:
    print('pip install requests feedparser jinja2 '
          'dateutil html2text inscriptis')
    sys.exit(1)


logger = getLogger()


USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 ' \
             '(KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36'


def relative(path):
    return abspath(join(dirname(__file__), path))


def get_content(filename):
    if filename == '-':
        return sys.stdin.read()
    with open(filename, 'r') as input:
        return input.read()


def extend_dict(a, **kwargs):
    a.update(kwargs)
    return a


def add_prefix(items, prefix):
    return [
        extend_dict(item, prefix=prefix)
        for item in items
    ]


def get_hash(*data):
    m = hashlib.md5()
    m.update(dumps(data))
    return m.hexdigest()


def get_url(url):
    return requests.get(url, headers={
        'User-Agent': USER_AGENT,
    })


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


def get_feed(url, cache_path, invalidate=False, ttl=None):
    cache_path = cache_path or './.fetch-feed'
    if not exists(cache_path):
        makedirs(cache_path)

    filename = join(cache_path, get_hash(url))
    timestamp_filename = filename + '.last'

    now = time.time()

    timestamp = load_json(timestamp_filename)

    use_cache = not invalidate and \
                exists(filename) and \
                (timestamp is not None and now - timestamp <= ttl)

    if use_cache:
        logger.info('Cached %s', url)
        with open(filename, 'r') as input:
            return input.read()

    logger.info('Fetch %s', url)
    response = get_url(url)
    if response.status_code != 200:
        logger.error('Error with %s (status code %s)',
                     url, response.status_code)
        return

    content = response.content
    with open(filename, 'w') as output:
        output.write(content)

    dump_json(timestamp_filename, now)

    return content


def fetch_feed(url, cache, invalidate=False, ttl=60 * 5):
    content = get_feed(
        url,
        cache_path=join(cache, 'fetch-feed'),
        invalidate=invalidate,
        ttl=ttl,
    )
    return content or ''


def parse_entry(entry):
    id_ = entry.get('id', None)
    url = entry.get('link', None)
    title = entry.get('title', None)
    published = entry.get('published', None)
    updated = entry.get('updated', None)

    uid = get_hash(id_, url)

    content = entry.get('content', None)
    summary_detail = entry.get('summary_detail', None)

    tags = {
        item['term']
        for item in entry.get('tags', None) or []
    }

    items = \
        content or \
        ([summary_detail] if summary_detail else None) or \
        []

    content_by_type = {}

    for item in items:
        type_ = item['type']
        value = item['value']
        previous = content_by_type.get(type_, None)
        if previous is None or len(previous) < len(value):
            content_by_type[type_] = value

    return {
        'id': uid,
        'url': url,
        'published': published or updated,
        'title': title,
        'content': content_by_type,
        'tags': list(tags),
        'feed': entry['feed'],
    }


def split_items(content):
    parsed = feedparser.parse(content)
    generic = parsed['feed']
    feed = {
        'url': generic['link'],
        'title': generic['title'],
        'subtitle': generic.get('subtitle'),
    }
    for entry in parsed['entries']:
        entry['feed'] = feed
        yield entry


def omit_dates(data):
    if isinstance(data, dict):
        return {
            key: omit_dates(value)
            for key, value in data.items()
            if not isinstance(value, struct_time)
        }
    return data


def parse_feed(content, raw=False):
    return [
        parse_entry(item) if not raw else omit_dates(item)
        for item in split_items(content)
    ]


def check_maildir(base_path):
    for subdir in ('', 'cur', 'tmp', 'new'):
        path = join(base_path, subdir)
        if exists(path):
            continue
        makedirs(path)


def load_template(filename):
    with open(filename, 'r') as input:
        return Template(input.read())


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


def to_maildir(items, maildirs, cache=None, template_path=None):
    if not template_path:
        template_path = relative('message.jinja2')
    template = load_template(template_path)

    ids = {item['id'] for item in items}

    with skip_cache(cache, ids) as skip:
        for path in maildirs:
            check_maildir(path)

            for item in items:
                if item['id'] in skip:
                    continue

                published_parsed = dateutil.parser.parse(item['published'])
                timestamp = int(time.mktime(published_parsed.timetuple()))

                for content_type, content in item['content'].items():
                    message = template.render(
                        item=item,
                        published_parsed=published_parsed,
                        content_type=content_type,
                        content=content,
                    )

                    filename = join(path, 'new', '-'.join([
                        str(timestamp),
                        item['id'],
                    ]))
                    with open(filename, 'w') as output:
                        output.write(message.encode('utf-8'))

                    break


def process_item(item, transform):
    item['content'] = {
        key: transform(value)
        for key, value in item['content'].items()
    }
    return item


def process_items(items, transform):
    return [
        process_item(item, transform)
        for item in items
    ]


def markdown_transform(items):
    f = lambda text: html2text.html2text(text, bodywidth=10000)
    return process_items(items, f)


def text_transform(items):
    f = lambda text: inscriptis.get_text(text, display_links=True)
    return process_items(items, f)
