#!/usr/bin/env python
# encoding: utf-8

"""
Usage:
  prefix (<filename> | -) <prefix>
  prefix (-h | --help)
"""

from __future__ import absolute_import
from __future__ import print_function
from json import dumps
from json import loads
from logging import getLogger, basicConfig, INFO

from docopt import docopt

from feed2any.rss import get_content, output


logger = getLogger()


def extend_dict(a, **kwargs):
    a.update(kwargs)
    return a


def add_prefix(items, prefix):
    return [
        extend_dict(item, prefix=prefix)
        for item in items
    ]


def main():
    arguments = docopt(__doc__)

    filename = arguments['<filename>']
    content = get_content(filename)
    if not content:
        logger.info('No content')
        return

    prefix = arguments['<prefix>']

    data = add_prefix(loads(content), prefix)

    output(dumps(data, ensure_ascii=False))


if __name__ == '__main__':
    basicConfig(level=INFO)
    main()
