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
import string
from typing import Any, List
from textwrap import shorten

import contextlib
from discord import Embed  # needs fix :tm:
import discord
from discord.ext import commands, menus

from main import NewCtx

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

    def _gen_embeds(self, requester: str, iterable: List[Any]) -> List[Embed]:
        embeds = []

        for item in iterable:
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
                    value=f"[Click here!]({item.video_link})",
                    inline=False
                )
            embed.add_field(
                name="Updoots", value=item.upvotes, inline=True
            )
            embed.add_field(
                name="Total comments", value=item.comment_count, inline=True
            )
            page_counter = f"Result {iterable.index(item)+1} of {len(iterable)}"
            embed.set_footer(
                text=f"{page_counter} | {item.subreddit} | Requested by {requester}")

            embeds.append(embed)

        return embeds[:15]

    @commands.command()
    @commands.max_concurrency(1, commands.BucketType.channel, wait=False)
    async def reddit(self, ctx: NewCtx,
                     sub: str = 'memes',
                     sort: str = 'hot'):
        """Gets the <sub>reddits <amount> of posts sorted by <method>"""
        if sort.lower() not in ("top", "hot", "best", "controversial", "new", "rising"):
            return await ctx.send("Not a valid sort-by type.")

        PostObj = namedtuple('PostObj', ['title', 'self_text', 'url', 'author',
                                         'image_link', 'video_link', 'upvotes',
                                         'comment_count', 'subreddit'])

        posts = set()

        subr_url = f"https://www.reddit.com/r/{sub}/about.json"
        base_url = f"https://www.reddit.com/r/{sub}/{sort}.json"

        async with self.bot.session.get(subr_url, headers={"User-Agent": "Yoink discord bot"}) as subr_resp:
            subr_deets = await subr_resp.json()

        if 'data' not in subr_deets:
            raise commands.BadArgument("Subreddit does not exist.")
        if subr_deets['data'].get('over18', None) and not ctx.channel.is_nsfw():
            raise commands.NSFWChannelRequired(ctx.channel)

        async with self.bot.session.get(base_url) as res:
            page_json = await res.json()

        idx = 0
        for post_data in page_json['data']['children']:
            image_url = None
            video_url = None

            if idx == 20:
                break

            post = post_data['data']
            if post['stickied'] or (post['over_18'] and not ctx.channel.is_nsfw()):
                idx += 1
                continue

            title = shorten(post['title'], width=250)
            self_text = shorten(post['selftext'], width=1500)
            url = f"https://www.reddit.com{post['permalink']}"
            author = post['author']
            image_url = post['url'] if post['url'].endswith((
                ".jpg", ".png", ".jpeg", ".gif", ".webp")) else None
            if "v.redd.it" in post['url']:
                image_url = post['thumbnail']
                if post.get("media", None):
                    video_url = post['url']
                else:
                    continue
            upvotes = post['score']
            comment_count = post['num_comments']
            subreddit = post['subreddit']

            _post = PostObj(title=title, self_text=self_text,
                            url=url, author=author, image_link=image_url,
                            video_link=video_url, upvotes=upvotes,
                            comment_count=comment_count, subreddit=subreddit
                            )

            posts.add(_post)
        embeds = self._gen_embeds(ctx.author, list(posts))
        pages = menus.MenuPages(PagedEmbedMenu(embeds))
        await pages.start(ctx)

    @reddit.error
    async def reddit_error(self, ctx: NewCtx, error):
        """ Local Error handler for reddit command. """
        error = getattr(error, "original", error)
        if isinstance(error, commands.NSFWChannelRequired):
            return await ctx.send("This ain't an NSFW channel.")
        elif isinstance(error, commands.BadArgument):
            msg = ("There seems to be no Reddit posts to show, common cases are:\n"
                   "- Not a real subreddit.\n")
            return await ctx.send(msg)

    @commands.command(name='mock')
    async def _mock(self, ctx: NewCtx, *, message: str):
        with contextlib.suppress(discord.Forbidden):
            await ctx.message.delete()
        output = ''
        for counter, char in enumerate(message):
            if char != string.whitespace:
                if counter % 2 == 0:
                    output += char.upper()
                else:
                    output += char
            else:
                output += string.whitespace
        await ctx.send(output)


def setup(bot):
    """ Cog Entrypoint. """
    bot.add_cog(Memes(bot))
