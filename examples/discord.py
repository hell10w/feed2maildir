#!/usr/bin/env python
# encoding: utf-8

from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals
from logging import basicConfig, INFO

from feed2any.plaintext import plaintext_transform
from feed2any.parse import parse_feed
from feed2any.fetch import fetch_feed
from feed2any.to_discord import to_discord


class Rss(object):
    def __init__(self, url, ttl=None):
        self.url = url
        self.ttl = ttl or 60 * 5


class Reddit(Rss):
    def __init__(self, subreddits, ttl=None):
        url = 'https://www.reddit.com/r/{}/.rss'.format('+'.join(subreddits))
        super(Reddit, self).__init__(url=url, ttl=ttl)


class Channel(object):
    def __init__(self, webhook, *sources):
        self.webhook = webhook
        self.sources = sources


TEST_HOOK = 'https://discordapp.com/api/webhooks/****************************'


CHANNELS = [
    # crypto
    Channel(
        TEST_HOOK,
        Reddit([
            'Bitcoin',
            'CryptoCurrency',
            'BTCNews',
            'ethereum',
        ]),
        Rss('https://www.schneier.com/blog/atom.xml'),
    ),

    # editors
    Channel(
        TEST_HOOK,
        Reddit([
            'vim',
            'emacs',
            'SpaceVim',
        ]),
    ),

    # linux
    Channel(
        TEST_HOOK,
        Reddit([
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
        Rss('https://www.kernel.org/feeds/kdist.xml'),
    ),

    # life game
    Channel(
        TEST_HOOK,
        Reddit([
            'cellular_automata',
        ]),
    ),

]


def main():
    cache_path = './.cache/'

    for channel in CHANNELS:
        for source in channel.sources:
            print('processing {}'.format(source.url))

            content = fetch_feed(source.url, cache_path)
            if not content:
                continue

            items = parse_feed(content)
            if not items:
                continue

            items = plaintext_transform(items)

            to_discord(items, channel.webhook)


if __name__ == '__main__':
    basicConfig(level=INFO)
    main()
