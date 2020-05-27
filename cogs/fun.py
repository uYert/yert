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

import discord
import uwuify
from discord.ext import commands

from config import TRAVITIA_TOKEN
from main import NewCtx
from packages.aiocleverbot import AioCleverbot


class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.aiocleverbot = AioCleverbot(api_key=TRAVITIA_TOKEN, 
                                         session=bot.session)
        
    @commands.Cog.listener('on_message')
    async def cb_listener(self, msg: discord.Message):
        """the infamous cleverbot"""
        ctx: NewCtx = await self.bot.get_context(msg)
        if not (txt := self.aiocleverbot.check_valid_message(ctx)):
            return
        
        ctx.cache_key = ('cleverbot', ctx.author.id)  
        emotion = self.aiocleverbot.update_emotion(ctx)
        
        await ctx.trigger_typing()
        response = await self.aiocleverbot.ask(query=txt,
                                               id_=msg.author.id,
                                               emotion=emotion)
            
        await ctx.send(self.aiocleverbot.format_response(msg=msg,
                                                         response=response, 
                                                         clean_txt=txt))
        
    @commands.command(name='uwuify')
    async def uwuify(self, ctx, *, text: str):
        """Uwuify a text"""
        if len(text) > 200:
            raise commands.BadArgument(message='The text needs to be shorter then 200 characters')
        
        flags = uwuify.SMILEY | uwuify.YU  # lazyness 200
        await ctx.send(uwuify.uwu(text, flags=flags))
    
        
        
def setup(bot):
    bot.add_cog(Fun(bot))
