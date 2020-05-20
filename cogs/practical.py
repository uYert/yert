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

from collections.abc import Hashable
from datetime import timedelta
from typing import Optional

import discord
from discord.ext import commands

from config import WEATHER_TOKEN, GOOGLE_TOKENS
from main import NewCtx
from packages.aioweather import AioWeather
from packages.aiotranslator import to_language, check_length, AioTranslator
from packages.aiogooglesearch import AioSearchEngine


class Practical(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.aioweather = AioWeather(session=bot.session,
                                     api_key=WEATHER_TOKEN)
        self.aiotranslator = AioTranslator(session=bot.session)
        self.aiogoogle = AioSearchEngine(api_keys=GOOGLE_TOKENS, 
                                         session=bot.session)

    @commands.command(name='weather')
    @commands.cooldown(1, 30, type=commands.BucketType.channel)
    async def weather(self, ctx: NewCtx, *, city: str):
        """Displays the weather at a particular location"""
        if not (embed := ctx.cached_data):

            res = await self.aioweather.fetch_weather(city)
            embed = self.aioweather.format_weather(res)
            ctx.add_to_cache(value=embed, timeout=timedelta(minutes=10))

        await ctx.send(embed=embed)

    @commands.group(name='translate', invoke_without_command=True)
    async def translate(self, ctx: NewCtx, language: Optional[to_language] = 'auto', *, text: str):
        """Translates from another language"""
        if not (embed := ctx.cached_data):
            # the embed is implicitely cached there, since it's used by both subcommnands
            embed = await self.aiotranslator.do_translation(ctx=ctx, text=text,
                                                            translation_kwarg={'src': language})
        await ctx.send(embed=embed)

    @translate.command(name='to')
    async def translate_to(self, ctx: NewCtx, language: to_language, *, text: str):
        """Translate something to another language"""
        if not (embed := ctx.cached_data):
            embed = await self.aiotranslator.do_translation(ctx=ctx, text=text,
                                                            translation_kwarg={'dest': language})
        await ctx.send(embed=embed)

    @commands.group(name='google')
    async def google(self, ctx, *, query):
        is_nsfw = ctx.channel.is_nsfw()
        
        ctx.cache_key.append(is_nsfw)
        
        
        results = await self.aiogoogle.search(query, safesearch=not is_nsfw)
    
    @google.command(name='image', aliases=['-i'])
    async def google_image(self, ctx, *, query):
        pass
    


    # todo : use menus to implement google search + magmachain


def setup(bot):
    bot.add_cog(Practical(bot))
