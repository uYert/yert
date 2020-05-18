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

from typing import Union

import discord
from discord.ext import commands, menus
from packages.aiosaucenao import AioSaucenao, SauceNaoSource
from config import SAUCENAO_TOKEN
from main import NewCtx
from datetime import timedelta

class Anime(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.aiosaucenao = AioSaucenao(session=bot.session, 
                                       api_key=SAUCENAO_TOKEN)
    
    @commands.command(name='saucenao')
    async def saucenao(self, ctx: NewCtx, target: Union[discord.User, discord.Message] = None):
        if not (source := ctx.cached_data):
            image = await self.aiosaucenao.select_image(ctx=ctx, target=target)
            response = await self.aiosaucenao.search(image)  #todo: check rate limit with the main header
            source = ctx.add_to_cache(value=SauceNaoSource(response.results),
                                      timeout=timedelta(minutes=5))
            
        menu = menus.MenuPages(source, )
        await menu.start(ctx)
            
def setup(bot):
    bot.add_cog(Anime(bot))