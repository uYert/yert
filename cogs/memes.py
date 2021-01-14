"""
MIT License

Copyright (c) 2021 - µYert

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

import aiohttp
import contextlib
import random
import string
from datetime import datetime
from typing import Any, List

import discord
from discord import Embed  # needs fix :tm:
from discord.ext import commands, menus
from main import NewCtx

from reddit import Reddit

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
        _reddit_session = aiohttp.ClientSession(headers={"User-Agent": "Yoink discord bot"})
        self._reddit = Reddit.from_sub('memes', cs=_reddit_session)

    def _gen_embeds(self, requester: str, posts: List[Any]) -> List[Embed]:
        embeds = []

        for post in posts:
            embed = Embed(
                title = post.title,
                description = post.selftext,
                colour = random.randint(0, 0xffffff),
                url = post.url
            )
            embed.set_author(name=post.author)

            if post.media or post.is_video:
                embed.set_image(url=post.media.url)
                embed.add_field(
                    name="Vidya!",
                    value=f"[Click here!]({post.media.url}",
                    inline=False
                )

            embed.add_field(name="Updoots", value=post.ups, inline=True)
            embed.add_field(name="Total comments", value=post.num_comments, inline=True)
            page = f"Result {posts.index(post) + 1} of {len(posts)}"
            embed.set_footer(text=f"{page} | {post.subreddit} | Requested by {requester}")

            embeds.append(embed)
        return embeds

    @commands.command()
    @commands.max_concurrency(1, commands.BucketType.channel, wait=False)
    async def reddit(self, ctx: NewCtx, sub: str = 'memes', sort: str = 'hot', timeframe: str = 'all', comments: bool = False):
        """Gets the <sub>reddit's posts sorted by <sort> method within the <timeframe> with <comments> determining wether to fetch comments too"""
        if not sort.lower() in ('hot', 'new', 'top', 'rising', 'controversial'):
            return await ctx.send('Not a valid sort method')

        if sub != self._reddit.sub:
            self._reddit = await Reddit.from_sub(
                sub,
                method=sort,
                timeframe=timeframe,
                cs=self._reddit._cs
            ).load(comments=comments)
        else:
            await self._reddit.load(comments=comments)
        embeds = self._gen_embeds(ctx.author, self._reddit.posts)
        pages = menus.MenuPages(PagedEmbedMenu(embeds))
        await pages.start(ctx)

    @reddit.error
    async def reddit_error(self, ctx: NewCtx, error):
        """ Local Error handler for reddit command. """
        error = getattr(error, "original", error)
        if isinstance(error, commands.NSFWChannelRequired):
            return await ctx.send("This ain't an NSFW channel.")
        elif isinstance(error, commands.BadArgument):
            msg = (
                "There seems to be no Reddit posts to show, common cases are:\n"
                "- Not a real subreddit.\n"
            )
            return await ctx.send(msg)
        else:
            raise error

    @commands.command(name="mock")
    async def _mock(self, ctx: NewCtx, *, message: str):
        with contextlib.suppress(discord.Forbidden):
            await ctx.message.delete()
        output = ""
        for counter, char in enumerate(message):
            if char != string.whitespace:
                if counter % 2 == 0:
                    output += char.upper()
                else:
                    output += char
            else:
                output += string.whitespace

        mentions = discord.AllowedMentions(everyone=False, users=False, roles=False)
        await ctx.send(output, allowed_mentions=mentions)


def setup(bot):
    """ Cog Entrypoint. """
    bot.add_cog(Memes(bot))
