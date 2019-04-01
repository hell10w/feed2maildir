#!/usr/bin/env python
# encoding: utf-8

"""
Usage:
  cleanup (<filename> | -)
  cleanup (-h | --help)
"""

from __future__ import absolute_import
from __future__ import print_function
from json import dumps
from json import loads
from logging import getLogger, basicConfig, INFO
import re

from docopt import docopt
from lxml.html import fromstring

from feed2any.rss import get_content, output


logger = getLogger()

ignore_tags = 'script', 'noscript',
content_types = 'text/html', 'text/plain'

white = re.compile(r'\s{2,}')


class TextCollector(object):
    def __init__(self):
        self.text = ''

    def __iadd__(self, other):
        if other:
            if not self.text.endswith(' ') and not other.startswith(' '):
                self.text += ' '
            self.text += other
        return self


def plain(html, drop_links=True, drop_images=True, image_alt=False):
    images = []
    links = []

    content = TextCollector()

    tree = fromstring(html)
    # tree = fromstring(html.decode('utf-8'))

    for element in tree.xpath('./descendant-or-self::*'):
        if element.tag in ignore_tags:
            continue

        content += element.text

        if element.tag == 'a':
            link = element.attrib['href']
            if not drop_links:
                content += link
            else:
                content += '<link #{}>'.format(len(links))
            links.append(link)

        elif element.tag == 'br':
            content += ' '

        elif element.tag == 'img':
            image = element.attrib['src']
            if not drop_images:
                content += image
            else:
                content += '<image #{}>'.format(len(images))
            if image_alt:
                content += element.attrib['alt'] or element.attrib['title']
            images.append(image)

        content += element.tail

    text = white.sub(' ', content.text)

    return {
        'text': text,
        'links': links,
        'images': images,
    }


def process_item(item, **opts):
    content = None

    for content_type in content_types:
        content = item['content'].get(content_type, None)
        if content:
            break

    item.update(plain(content or '', **opts))

    return item


def plaintext_transform(items, **opts):
    return [
        process_item(item, **opts)
        for item in items
    ]


def main():
    arguments = docopt(__doc__)

    filename = arguments['<filename>']
    content = get_content(filename)
    if not content:
        logger.info('No content')
        return

    items = loads(content)
    data = plaintext_transform(items)

    output(dumps(data, ensure_ascii=False))


if __name__ == '__main__':
    basicConfig(level=INFO)
    main()
