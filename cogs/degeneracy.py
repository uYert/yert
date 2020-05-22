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

from datetime import timedelta
from random import shuffle as rng_shuffle
from re import findall as re_findall

import discord
from discord.ext import commands, menus

from main import BetterEmbed, Bot, NewCtx
from packages.r34 import AioRule34, R34Source


class Hentai(commands.Cog):
    def __init__(self, bot):
        self.bot: Bot = bot
        self.aiorule34 = AioRule34(session=bot.session, loop=bot.loop)
        
        
    @commands.command(name='sixdigits')
    async def sixdigits(self, ctx: NewCtx):
        """Provides you a magical six digits number"""
        async with self.bot.session.head("https://nhentai.net/random", 
                                         allow_redirects=True) as resp:
            url = str(resp.url)
        
        digits = re_findall(r'\d+', url)[0]
        
        if ctx.channel.is_nsfw():
            return await ctx.send(embed=BetterEmbed(title=digits, url=url))
        
        await ctx.send(digits)
            
    @commands.command(name='r34')
    @commands.is_nsfw()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def r34(self, ctx: NewCtx, *, query: str, fuzzy: bool = False):
        """Searches a post on r34"""
        if not (source := ctx.cached_data):
            results = await self.aiorule34.getImages(query, fuzzy=fuzzy)
            ctx.add_to_cache(results, timeout=timedelta(minutes=60))
            
        rng_shuffle(results)  # the api returns a *lot* of results
        source = R34Source(results, query)
        menu = menus.MenuPages(source, clear_reactions_after=True)
        await menu.start(ctx)
    
    
def setup(bot):
    bot.add_cog(Hentai(bot))
