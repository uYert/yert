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

import bottom
# import discord
from discord.ext import commands
from main import NewCtx


class Bottom(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(name="bottom")
    async def bottom(self, ctx: NewCtx):
        """Bottom translation commands."""
        ...

    @bottom.command(name="encode")
    async def bottom_encode(self, ctx: NewCtx, *, message: str):
        """Encodes a messsage."""
        await ctx.send(bottom.encode(message))

    @bottom.command(name="decode")
    async def bottom_decode(self, ctx: NewCtx, *, message: str):
        """Decodes a messsage."""
        try:
            await ctx.send(bottom.decode(message))
        except ValueError:
            await ctx.send('Failed to decode message.')
    

def setup(bot):
    bot.add_cog(Bottom(bot))
