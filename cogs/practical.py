"""
MIT License

Copyright (c) 2020 - Sudosnok, AbstractUmbra, Saphielle-Akiyama, nickofolas

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

import discord
from discord.ext import commands

from config import WEATHER_TOKEN
from packages.aioweather import AioWeather
from collections.abc import Hashable

class Practical(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.aioweather = AioWeather(session=bot.session, 
                                     api_key=WEATHER_TOKEN)
    
    @commands.command(name='weather')
    async def weather(self, ctx, *, city: str):
        """Tells you the weather at a particular location"""
        if not (embed := ctx.cached_data):

            res = await self.aioweather.fetch_weather(city)
            embed = self.aioweather.format_weather(res)
            ctx.add_to_cache(value=embed, timeout=timedelta(minutes=10))

        await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(Practical(bot))