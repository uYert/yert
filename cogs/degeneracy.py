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

import datetime
import random
import re
from typing import Tuple, Union

import main
from discord.ext import commands, menus
from packages import aionhentai, r34
from utils import formatters


class Degeneracy(commands.Cog):
    def __init__(self, bot: main.Bot):
        self.bot = bot
        self.aiorule34 = r34.AioRule34(session=bot.session, loop=bot.loop)
        self.aionhentai = aionhentai.Client(loop=bot.loop)

    async def _get_random_nhentai(self) -> Tuple[str, int]:
        """Returns a random nhentai doujin index"""
        async with self.bot.session.head(
            "https://nhentai.net/random", allow_redirects=True
        ) as resp:
            url = str(resp.url)

        return url, int(re.findall(r"\d+", url)[0])

    @commands.command(name="sixdigits")
    async def sixdigits(self, ctx: main.NewCtx):
        """Provides you a magical six digits number"""
        url, digits = await self._get_random_nhentai()

        if ctx.channel.is_nsfw():
            return await ctx.send(embed=formatters.BetterEmbed(title=digits, url=url))

        await ctx.send(digits)

    @commands.command(name="nhentai", aliases=["doujin", "doujins"])
    @commands.is_nsfw()
    async def nhentai(self, ctx, doujin: Union[int, str] = None):
        """
        Displays a doujin from nhentai
        If no doujin is provided, a random one will be selected
        """
        if doujin is None:
            while not doujin:
                _, doujin_id = await self._get_random_nhentai()
                response = await self.aionhentai.search(doujin_id)
                doujin = [*self.aionhentai.filter_doujins(response)]
        else:
            response = await self.aionhentai.search(doujin)
            doujin = [*self.aionhentai.filter_doujins(response)] or ["No results"]

        source = aionhentai.Source(doujin)

        menu = aionhentai.Menu(source, delete_message_after=True)
        await menu.start(ctx)

    @commands.command(name="r34", aliases=["rule34"])
    @commands.is_nsfw()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def r34(self, ctx: main.NewCtx, *, query: str, fuzzy: bool = False):
        """Searches a post on r34"""
        if not (source := ctx.cached_data):
            results = await self.aiorule34.getImages(query, fuzzy=fuzzy)
            ctx.add_to_cache(results, timeout=datetime.timedelta(minutes=60))

        random.shuffle(results)  # the api returns a *lot* of results
        source = r34.R34Source(results, query)
        menu = menus.MenuPages(source, delete_message_after=True)
        await menu.start(ctx)


def setup(bot):
    bot.add_cog(Degeneracy(bot))
