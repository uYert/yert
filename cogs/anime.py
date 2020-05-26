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

import asyncio
from datetime import timedelta
from typing import Union

import discord
from discord.ext import commands, menus

from config import SAUCENAO_TOKEN
from main import NewCtx
from packages import aiojikan, aiosaucenao
from utils import converters


class Anime(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.aiosaucenao = aiosaucenao.Client(session=bot.session, api_key=SAUCENAO_TOKEN)
        self.aiojikan = aiojikan.Client(session=bot.session)
        self.create_mal_commands()
    
    @commands.command(name='saucenao')
    @commands.cooldown(7, 30, commands.BucketType.default)
    async def saucenao(self, ctx: NewCtx,
                       target: Union[discord.Member, discord.User, discord.Message] = None):
        """Provides informations about an image"""
        image = await self.aiosaucenao.select_image(ctx=ctx, target=target)
        
        ctx.cache_key += [image]
        
        if not (source := ctx.cached_data):
            
            response = await self.aiosaucenao.search(image) 
            source = ctx.add_to_cache(value=SauceNaoSource(response.results),
                                      timeout=timedelta(hours=24))
            
        menu = menus.MenuPages(source, clear_reactions_after=True) 
        
        # The menu isn't cached to allow for changes, as the cache is 
        # tied to the bot and not the cog
        
        await menu.start(ctx)
            
    @commands.group(name='mal', aliases=['myanimelist'])
    async def mal(self, ctx):
        """
        Mal related commands
        """
        pass
    
    async def _check_api_cooldowns(self, ctx: NewCtx):
        """Waits and complies with the api's rate limit"""
        msg = ctx.message
        
        bucket = aiojikan.API_COOLDOWNS.long.get_bucket(msg)

        if retry_after := bucket.update_rate_limit():
            raise commands.CommandOnCooldown(bucket, retry_after)
                
        bucket = aiojikan.API_COOLDOWNS.short.get_bucket(msg)
        await asyncio.sleep(bucket.update_rate_limit() or 0)
                
    def create_mal_commands(self):
        """Makes all mal commands in a row"""
        @commands.command() 
        @commands.cooldown(1, 30, commands.BucketType.user)          
        async def template(ctx: NewCtx, *, query: str):
            is_nsfw = ctx.channel.is_nsfw()
            ctx.cache_key += [is_nsfw]
            
            if not (response := ctx.cached_data):
                
                await self._check_api_cooldowns(ctx)
                
                response = await self.aiojikan.search(ctx.command.name, query)
                ctx.add_to_cache(response, timeout=timedelta(hours=24))
            
            source = aiojikan.Source(response.results, is_nsfw=is_nsfw)
            
            menu = menus.MenuPages(source, clear_reactions_after=True)
            
            await menu.start(ctx)

        for name in ('anime', 'manga', 'person', 'character'):
            mal_command = template.copy()
            mal_command.name = name
            
            article = 'a'
            
            if name == 'anime':
                article += 'n'
            
            mal_command.help = f"Searches {article} {name} on My Anime List"
            self.mal.add_command(mal_command)
    

            
    
            
            
def setup(bot):
    bot.add_cog(Anime(bot))
