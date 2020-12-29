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

import datetime
from typing import Optional

import config
import main
from discord.ext import commands, menus
from packages import aiogooglesearch, aiomagmachain, aiotranslator, aioweather


class Practical(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.aioweather = aioweather.AioWeather(
            session=bot.session, api_key=config.WEATHER_TOKEN
        )
        self.aiotranslator = aiotranslator.AioTranslator(session=bot.session)
        self.aiogoogle = aiogooglesearch.AioSearchEngine(
            api_keys=config.GOOGLE_TOKENS, session=bot.session
        )
        self.aioscreen = aiomagmachain.AioMagmaChain(
            session=bot.session, google_client=self.aiogoogle
        )

    @commands.command(name="weather")
    @commands.cooldown(1, 30, type=commands.BucketType.channel)
    async def weather(self, ctx: main.NewCtx, *, city: str):
        """Displays the weather at a particular location"""
        if not (embed := ctx.cached_data):

            res = await self.aioweather.fetch_weather(city)
            embed = self.aioweather.format_weather(res)
            ctx.add_to_cache(value=embed, timeout=datetime.timedelta(minutes=10))

        await ctx.send(embed=embed)

    @commands.group(name="translate", invoke_without_command=True)
    async def translate(
        self,
        ctx: main.NewCtx,
        language: Optional[aiotranslator.to_language] = "auto",
        *,
        text: str,
    ):
        """Translates from another language"""
        if not (embed := ctx.cached_data):
            # the embed is implicitely cached there, since it's used by both subcommnands
            embed = await self.aiotranslator.do_translation(
                ctx=ctx, text=text, translation_kwarg={"src": language}
            )
        await ctx.send(embed=embed)

    @translate.command(name="to")
    async def translate_to(
        self, ctx: main.NewCtx, language: aiotranslator.to_language, *, text: str
    ):
        """Translate something to another language"""
        if not (embed := ctx.cached_data):
            embed = await self.aiotranslator.do_translation(
                ctx=ctx, text=text, translation_kwarg={"dest": language}
            )
        await ctx.send(embed=embed)

    @commands.group(name="google", invoke_without_command=True)
    @commands.cooldown(1, 15, commands.BucketType.user)
    async def google(self, ctx: main.NewCtx, *, query: str):
        """Searches something on google"""
        is_nsfw = ctx.channel.is_nsfw()
        ctx.cache_key += [is_nsfw]

        if not (source := ctx.cached_data):

            source = await self.aiogoogle.do_search(ctx, query=query, is_nsfw=is_nsfw)

        menu = menus.MenuPages(source, delete_message_after=True)
        await menu.start(ctx)

    @google.command(name="image", aliases=["-i"])
    @commands.cooldown(1, 15, commands.BucketType.user)
    async def google_image(self, ctx: main.NewCtx, *, query: str):
        """Searches an image on google"""
        is_nsfw = ctx.channel.is_nsfw()
        ctx.cache_key += [is_nsfw]

        if not (source := ctx.cached_data):
            source = await self.aiogoogle.do_search(
                ctx, query=query, is_nsfw=is_nsfw, image_search=True
            )

        menu = menus.MenuPages(source, clear_reactions_after=True)

        await menu.start(ctx)

    @commands.command(name="screenshot")
    @commands.cooldown(1, 15, commands.BucketType.user)
    async def screenshot(self, ctx: main.NewCtx, url: str):
        """Screenshots a website"""
        is_nsfw = ctx.channel.is_nsfw()
        ctx.cache_key += [is_nsfw]

        if not (embed := ctx.cached_data):

            if not is_nsfw or len(url.split(".")) < 2:
                url = await self.aioscreen.check_url(url=url, is_nsfw=is_nsfw)

            response = await self.aioscreen.fetch_snapshot(url)
            embed = self.aioscreen.format_snapshot(response=response, is_nsfw=is_nsfw)

            ctx.add_to_cache(embed, timeout=datetime.timedelta(minutes=5))

        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Practical(bot))
