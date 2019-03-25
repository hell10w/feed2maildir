#!/usr/bin/env python
# encoding: utf-8

"""
Usage:
  to-maildir [--template=<template>] (<filename> | -) <maildir>...
  to-maildir (-h | --help)
"""

from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import print_function
from json import loads
from logging import getLogger, basicConfig, INFO
from os.path import join, exists
import time
from os import makedirs

import dateutil.parser
from docopt import docopt
from jinja2 import Template

from feed2any.rss import get_content, relative, skip_cache


logger = getLogger()


def load_template(filename):
    with open(filename, 'r') as input:
        return Template(input.read())


def check_maildir(base_path):
    for subdir in ('', 'cur', 'tmp', 'new'):
        path = join(base_path, subdir)
        if exists(path):
            continue
        makedirs(path)


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


def main():
    arguments = docopt(__doc__)

    filename = arguments['<filename>']
    content = get_content(filename)
    if not content:
        logger.info('No content')
        return

    items = loads(content)

    to_maildir(items, arguments['<maildir>'],
               template_path=arguments['--template'])


if __name__ == '__main__':
    basicConfig(level=INFO)
    main()
