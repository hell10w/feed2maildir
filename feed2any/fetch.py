#!/usr/bin/env python
# encoding: utf-8

"""
Usage:
  fetch [--invalidate] [--cache=<cache>] <url>
  fetch (-h | --help)
"""

from __future__ import absolute_import
from __future__ import print_function
from logging import getLogger, basicConfig, INFO
from os.path import join, exists
from os import makedirs
import time

from docopt import docopt
import requests

from feed2any.rss import get_hash, load_json, dump_json, output


logger = getLogger()


USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 ' \
             '(KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36'


def get_url(url):
    return requests.get(url, headers={
        'User-Agent': USER_AGENT,
    })


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


def main():
    arguments = docopt(__doc__)

    cache = arguments['--cache'] or './.cache'
    invalidate = arguments['--invalidate']
    url = arguments['<url>']

    content = fetch_feed(url, cache, invalidate)

    output(content)


if __name__ == '__main__':
    basicConfig(level=INFO)
    main()
