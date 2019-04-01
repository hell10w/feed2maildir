#!/usr/bin/env python
# encoding: utf-8

"""
Usage:
  transform (--text | --markdown) (<filename> | -)
  transform (-h | --help)
"""

from __future__ import absolute_import
from __future__ import print_function
from json import dumps
from json import loads
from logging import getLogger, basicConfig, INFO
import re

from docopt import docopt
import html2text
import inscriptis

from feed2any.rss import get_content, output


logger = getLogger()


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


def whitespace_transform(items):
    strip_white = re.compile(r'\s{2,}')
    f = lambda text: strip_white.sub(' ', text)
    return process_items(items, f)


def text_transform(items):
    f = lambda text: inscriptis.get_text(text,
                                         display_links=True,
                                         display_images=True)
    return whitespace_transform(process_items(items, f))


def main():
    arguments = docopt(__doc__)

    filename = arguments['<filename>']
    content = get_content(filename)
    if not content:
        logger.info('No content')
        return

    items = loads(content)
    if arguments['--markdown']:
        data = markdown_transform(items)
    elif arguments['--text']:
        data = text_transform(items)
    else:
        raise NotImplementedError

    output(dumps(data, ensure_ascii=False))


if __name__ == '__main__':
    basicConfig(level=INFO)
    main()
