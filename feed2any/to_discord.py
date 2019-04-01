#!/usr/bin/env python
# encoding: utf-8

"""
Usage:
  to_discord (<filename> | -) <web-hook>
  to_discord (-h | --help)
"""

from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import print_function

from json import loads
from logging import getLogger, basicConfig, INFO

from docopt import docopt
import dateutil.parser
from discord_webhook import DiscordWebhook, DiscordEmbed

from feed2any.rss import skip_cache, get_content, get_description

logger = getLogger()


def to_discord(items, webhook_url, cache=None):
    ids = {item['id'] for item in items}

    with skip_cache(cache, ids) as skip:
        for item in items:
            if item['id'] in skip:
                continue

            webhook = DiscordWebhook(url=webhook_url)

            embed = DiscordEmbed(
                title=item['title'],
                description=(get_description(item) + '\n\n' + item['url']).strip(),
                # color=242424,
            )

            published_parsed = dateutil.parser.parse(item['published'])
            embed.set_footer(text='Published at {}'.format(published_parsed))

            # embed.add_embed_field(name='published', value=)

            feed = item['feed']
            # feed_name = item['feed'].get('title', None)
            embed.set_author(
                name=feed.get('title', None) or '',
                url=feed.get('url', None) or '',
                icon_url='https://avatars0.githubusercontent.com/u/14542790',
            )

            tags = item.get('tags', None)
            if tags:
                embed.add_embed_field(name='tags', value=', '.join(tags))

            for url in item.get('images', None) or []:
                embed.set_image(url=url)
                break

            for link in item.get('links', None) or []:
                embed.add_embed_field(name='link', value=link)

            webhook.add_embed(embed)

            webhook.execute()


def main():
    arguments = docopt(__doc__)
    from pprint import pprint
    pprint(arguments)

    filename = arguments['<filename>']
    content = get_content(filename)
    if not content:
        logger.info('No content')
        return

    items = loads(content)

    to_discord(items, arguments['<web-hook>'])


if __name__ == '__main__':
    basicConfig(level=INFO)
    main()
