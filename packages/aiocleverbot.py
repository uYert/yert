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
from random import choice as rng_choice
from typing import Union
# no need to import the whole thing
from functools import partial as funct_partial

import async_cleverbot as ac
from aiohttp import ClientSession
from discord import Member, Message, User

from main import NewCtx
from utils.checks import check_length


class AioCleverbot(ac.Cleverbot):
    def __init__(self, api_key: str, session: ClientSession = None):
        self.session = session or None
        self.api_key = api_key  # API key for the Cleverbot API
        self.api_url = "https://public-api.travitia.xyz/talk"  # URL for requests
        self.emotions = tuple(ac.Emotion)
        self.set_context(ac.DictContext())

    def check_valid_message(self, ctx: NewCtx) -> str:
        """Chercks if the command should be invoking the cleverbot"""
        msg = ctx.message
        content = msg.content

        if msg.author.bot or ctx.command:
            return None

        checker = funct_partial(check_length, min=3, max=60)

        if ctx.guild is None:
            return content if checker(content) else None

        for mention in (ctx.bot.user.mention + ' ', f'<@!{ctx.bot.user.id}> '):
            if content.startswith(mention):
                cropped = content[len(mention):]  # removing the witespace
                return cropped if checker(cropped) else None
        else:
            return None

    def update_emotion(self, ctx: NewCtx) -> ac.Emotion:
        """Checks an emotion for an author is cached"""
        if not (emotion := ctx.cached_data):
            emotion = rng_choice(self.emotions)

        return ctx.add_to_cache(value=emotion,  # the timer is refreshed
                                timeout=timedelta(minutes=30))

    def format_response(self, *, msg: Message, response: ac.Response, clean_txt: str) -> str:
        """Formats the reponse depending on the context"""
        if msg.guild is None:
            return response.text
        return f"> {clean_txt}\n{msg.author.mention} {response.text}"
