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
from random import choice as rng_choice
from typing import Union

import async_cleverbot as ac
from aiohttp import ClientSession
from discord import Member, Message, User
from utils.checks import check_length

from main import NewCtx

class AioCleverbot(ac.Cleverbot):
    def __init__(self, *, api_key: str, session: ClientSession):
        self.api_key = api_key
        self.api_url = "https://public-api.travitia.xyz/talk" 
        
    def check_valid_message(self, ctx: NewCtx) -> str:
        """Chercks if the command should be invoking the cleverbot"""
        msg = ctx.message
        content = msg.content
        
        if msg.author.bot or ctx.command:
            return None    
        
        if ctx.guild is None:
            return content if 3 <= len(content) <= 60 else None
            
        for mention in (ctx.bot.user.mention + ' ', f'<@!{ctx.bot.user.id}> '):
            if content.startswith(mention):
                cropped = content[len(mention):]
                return cropped if check_length(cropped, min=3, max=60) else None
        else:
            return None   
        
    def update_emotion(self, ctx: NewCtx) -> ac.Emotion:
        """Checks an emotion for an author is cached"""
        if (emotion := ctx.cached_data):
            ct
        else:
            emotion = ctx.add_to_cache(value=rng_choice(self.emotions), 
                                       timeout=timedelta(minutes=60)) 
        return emotion