#!/usr/bin/env python
# encoding: utf-8

from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals
from logging import basicConfig, INFO

from feed2any.to_maildir import to_maildir
from feed2any.prefix import add_prefix
from feed2any.parse import parse_feed
from feed2any.fetch import fetch_feed


class Rss(object):
    def __init__(self, prefix, url, ttl=None):
        self.prefix = prefix
        self.url = url
        self.ttl = ttl or 60 * 5


class Reddit(Rss):
    def __init__(self, prefix, subreddits, ttl=None):
        url = 'https://www.reddit.com/r/{}/.rss'.format('+'.join(subreddits))
        super(Reddit, self).__init__(prefix, url=url, ttl=ttl)


RSS = [
    Reddit('crypto', [
        'Bitcoin',
        'CryptoCurrency',
        'BTCNews',
        'ethereum',
    ]),
    Rss('crypto', 'https://www.schneier.com/blog/atom.xml'),

    Reddit('editors', [
        'vim',
        'emacs',
        'SpaceVim',
    ]),

    Reddit('unix', [
        'debian',
        'django',
        'docker',
        'awesomewm',
        'NixOS',
        'ranger',
        'i3wm',
        'linux',
        'linuxmasterrace',
        'Python',
        'unix',
        'TempleOS_Official',
    ]),
    Rss('unixshit', 'https://www.kernel.org/feeds/kdist.xml'),

    Reddit('life', [
        'cellular_automata',
    ]),

]


def main():
    cache_path = './.cache/'
    for rss in RSS:
        content = fetch_feed(rss.url, cache_path)
        if not content:
            continue

        items = parse_feed(content)
        items = add_prefix(items, rss.prefix)
        if not items:
            continue

        to_maildir(items, ('./.feeds', ), cache=cache_path)


if __name__ == '__main__':
    basicConfig(level=INFO)
    main()
