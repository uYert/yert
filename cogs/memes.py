"""
MIT License

Copyright (c) 2020 - µYert

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
import random
from typing import Any, List
from textwrap import shorten

from discord import Embed
from discord.ext import commands, menus

random.seed(datetime.utcnow())


class PagedEmbedMenu(menus.ListPageSource):
    """ Quick ListPageSource to allow for the creation of menus via lists of embeds """

    def __init__(self, embeds: List[Embed]):
        self.embeds = embeds
        super().__init__([*range(len(embeds))], per_page=1)

    async def format_page(self, menu, page):
        return self.embeds[page]


class Memes(commands.Cog):
    """ Memes cog. Probably gonna be loaded with dumb commands. """

    def __init__(self, bot):
        self.bot = bot
        self.webhook = bot.get_cog("Events").webhook

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
    async def reddit(self, ctx: commands.Context,
                     sub: str = 'memes',
                     sort: str = 'hot',
                     amount: int = 5):
        """Gets the <sub>reddits <amount> of posts sorted by <method>"""
        if sort.lower() not in ("top", "hot", "best", "controversial", "new", "rising"):
            return await ctx.send("Not a valid sort-by type.")

        PostObj = namedtuple('PostObj', ['nsfw', 'title', 'self_text', 'url', 'author',
                                         'image_link', 'video_link', 'upvotes',
                                         'comment_count', 'subreddit'])

        posts = set()

        base_url = f"https://www.reddit.com/r/{sub}/{sort}.json"

        async with self.bot.session.get(base_url) as res:
            page_json = await res.json()

        for counter in range(amount):
            try:
                post_data = page_json['data']['children'][counter]['data']

                nsfw = post_data['over_18']
                if nsfw and not ctx.channel.nsfw():
                    continue
                title = shorten(post_data['title'], width=250)
                self_text = post_data['selftext']
                url = "https://www.reddit.com{}".format(post_data['permalink'])
                author = post_data['author']
                image_link = None
                try:
                    if media := post_data['secure_media']:
                        if oembed := media['oembed']:
                            image_link = oembed['thumbnail_url']
                except KeyError:
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
            except Exception as err:
                await ctx.webhook_send(
                    f"{err} in {ctx.channel.mention} trying item {counter} of {amount}",
                    webhook=self.webhook, skip_ctx=True
                )
        embeds = self._gen_embeds(
            ctx.author, list(posts), ctx.channel.is_nsfw())
        pages = menus.MenuPages(PagedEmbedMenu(embeds))
        await pages.start(ctx)


def setup(bot):
    """ Cog Entrypoint. """
    bot.add_cog(Memes(bot))
