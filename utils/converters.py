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

from typing import Any
from re import findall
from contextlib import suppress
from collections import namedtuple


import discord
from discord.ext import commands


BetterUser = namedtuple('BetterUser', ['obj', 'http_dict'])
u_conv = commands.UserConverter()
m_conv = commands.MemberConverter()


class BetterUserConverter(commands.Converter):
    async def convert(self, ctx, argument):
        out = ctx.author if not argument else None
        for converter in (m_conv, u_conv):
            if out:
                break
            with suppress(Exception):
                out = await converter.convert(ctx, argument)
        if out is None:
            try:
                out = await ctx.bot.fetch_user(argument)
            except discord.HTTPException:
                raise commands.CommandError("Invalid user provided")
        http_dict = await ctx.bot.http.get_user(out.id)
        return BetterUser(obj=out, http_dict=http_dict)

def maybe_url(url: Any, /) -> str:
    """Returns an hyperlink version of an url if one is found, else the text"""
    url = str(url)
    if match := findall(r'//([^/]+)', url):  # we get full urls, no need to go too overkill
        return f"[{match[0]}]({url})"
    else:
        return url