#!/usr/bin/env python
# encoding: utf-8

"""
Usage:
  parse [--raw] (<filename> | -)
  parse (-h | --help)
"""

from __future__ import absolute_import
from __future__ import print_function
from json import dumps
from logging import getLogger, basicConfig, INFO
from time import struct_time

from docopt import docopt
import feedparser

from feed2any.rss import get_content, get_hash, output


logger = getLogger()


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


def main():
    arguments = docopt(__doc__)

    filename = arguments['<filename>']
    content = get_content(filename)
    if not content:
        logger.info('No content')
        return

    raw = arguments['--raw']

    data = parse_feed(content, raw)

    output(dumps(data, ensure_ascii=False))


if __name__ == '__main__':
    basicConfig(level=INFO)
    main()
