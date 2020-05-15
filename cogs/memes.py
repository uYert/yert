"""
MIT License

Copyright (c) 2020 - Sudosnok, AbstractUmbra, Saphielle-Akiyama

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
from collections import namedtuple
from datetime import datetime
import json
import random
from typing import Any, List

from discord import AsyncWebhookAdapter, Embed, Webhook
from discord.ext import commands, menus

import config

random.seed(datetime.utcnow())


class RedditSource(menus.ListPageSource):
    def __init__(self, data, embeds):
        self.data = data
        self.embeds = embeds
        super().__init__(data, per_page=1)

    async def format_page(self, menu, entries):
        return self.embeds[entries]


class Memes(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.WEBHOOK = self._webhook()

    def _webhook(self) -> Webhook:
        wh_id, wh_token = config.WEBHOOK
        hook = Webhook.partial(
            id=wh_id, token=wh_token, adapter=AsyncWebhookAdapter(self.bot.session))
        return hook

    def _gen_embeds(self, requester: str, iterable: List[Any], nsfw_channel: bool) -> List[Embed]:
        embeds = []

        for item in iterable:
            if item.nsfw and not nsfw_channel:
                continue

            embed = Embed(
                title=item.title,
                description=item.self_text,
                colour=random.randint(0, 0xffffff),
                url=item.url
            )
            embed.set_author(name=item.author)

            if item.image_link:
                embed.set_image(url=item.image_link)

            if item.video_link:
                embed.add_field(
                    name="Vidya!",
                    value="[Click here!]({0.video_link})".format(item),
                    inline=False
                )
            embed.add_field(
                name="Updoots", value=item.upvotes, inline=True
            )
            embed.add_field(
                name="Total comments", value=item.comment_count, inline=True
            )
            page_counter = "Result {0} of {1}".format(
                iterable.index(item), len(iterable) - 1)
            embed.set_footer(
                text="{0} | {1.subreddit} | Requested by {2}".format(
                    page_counter, item, requester)
            )

            embeds.append(embed)

        return embeds

    @commands.command()
    @commands.max_concurrency(1, commands.BucketType.channel, wait=False)
    async def reddit(self, ctx: commands.Context, sub: str = 'memes', method: str = 'hot', amount: int = 5):
        """Gets the <sub>reddits <amount> of posts sorted by <method>"""

        PostObj = namedtuple('PostObj', ['nsfw', 'title', 'self_text', 'url', 'author',
                                         'image_link', 'video_link', 'upvotes', 'comment_count', 'subreddit'])

        posts = set()

        base_url = "https://www.reddit.com/r/{}/{}.json".format(sub, method)

        async with self.bot.session.get(base_url) as res:
            page_json = await res.json()

        for counter in range(amount):
            try:
                post_data = page_json['data']['children'][counter]['data']

                nsfw = post_data['over_18']
                title = post_data['title'] if len(
                    post_data) <= 250 else post_data['title'][:200] + '...'
                self_text = post_data['selftext']
                url = "https://www.reddit.com{}".format(post_data['permalink'])
                author = post_data['author']
                try:
                    image_link = post_data['secure_media']['oembed']['thumbnail_url']
                except TypeError:
                    image_link = post_data['thumbnail']
                video_link = post_data['url']
                upvotes = post_data['score']
                comment_count = post_data['num_comments']
                subreddit = post_data['subreddit']

                _post = PostObj(nsfw=nsfw, title=title, self_text=self_text,
                                url=url, author=author, image_link=image_link,
                                video_link=video_link, upvotes=upvotes,
                                comment_count=comment_count, subreddit=subreddit
                                )

                posts.add(_post)
            except json.decoder.JSONDecodeError:
                await ctx.webhook_send(
                    "json decode error in {0.mention} trying item {1} of {2}".format(
                        ctx.channel, counter, amount),
                    webhook=self.WEBHOOK, skip_ctx=True
                )
        embeds = self._gen_embeds(ctx.author, posts, ctx.channel.is_nsfw())
        pages = menus.MenuPages(source=RedditSource(None, embeds))
        await pages.start(ctx)


def setup(bot):
    """ Cog Entrypoint. """
    bot.add_cog(Memes(bot))
