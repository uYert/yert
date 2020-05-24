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
from typing import Union

import discord
from discord.ext import commands, menus

from config import SAUCENAO_TOKEN
from main import NewCtx
from packages.aiojikan import (AioJikan, AnimeJikanSource, JikanResponse,
                               MangaJikanSource, PersonJikanSource)
from packages.aiosaucenao import AioSaucenao, SauceNaoSource


class Anime(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.aiosaucenao = AioSaucenao(session=bot.session, api_key=SAUCENAO_TOKEN)
        self.aiojikan = AioJikan(session=bot.session)
    
    
    @commands.command(name='saucenao')
    @commands.cooldown(7, 30, commands.BucketType.default)
    async def saucenao(self, ctx: NewCtx, # might be redundant
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
            
    @commands.group(name='mal')
    @commands.cooldown(1, 30, commands.BucketType.default)            
    async def mal(self, ctx):
        """
        Mal related commands
        """
        pass
    
    @mal.command(name='anime')  #todo: dynamically add the commands
    async def mal_anime(self, ctx: NewCtx, *, query: str):
        is_nsfw = ctx.channel.is_nsfw()
        ctx.cache_key += [is_nsfw]
        results = await self.aiojikan.search(search_type=ctx.command.name, query=query)
        
        if not (resp := ctx.cached_data):
            resp = ctx.add_to_cache(JikanResponse(**results), timeout=timedelta(hours=23))
                    
        source = AnimeJikanSource(resp, is_nsfw=is_nsfw)  # we filter the results everytime
                
        menu = menus.MenuPages(source, clear_reactions_after=True)
        
        await menu.start(ctx)
        
    
    @mal.command(name='manga')
    async def mal_manga(self, ctx: NewCtx, *, query: str):
        """Searches a manga on my anime list"""
        is_nsfw = ctx.channel.is_nsfw()
        ctx.cache_key += [is_nsfw]
        
        if not (resp := ctx.cached_data):
            results = await self.aiojikan.search(search_type=ctx.command.name, query=query)
            resp = ctx.add_to_cache(JikanResponse(**results), timeout=timedelta(hours=24))
                    
        source = MangaJikanSource(resp, is_nsfw=is_nsfw)
                
        menu = menus.MenuPages(source, clear_reactions_after=True)
        
        await menu.start(ctx)
    
    @mal.command(name='person')
    async def mal_person(self, ctx: NewCtx, *, query: str):
        """Searches a person on mal (Mangakas, Voice...)"""
        is_nsfw = ctx.channel.is_nsfw()
        ctx.cache_key += [is_nsfw]
        
        if not (resp := ctx.cached_data):
            results = await self.aiojikan.search(search_type=ctx.command.name, query=query)
            resp = ctx.add_to_cache(JikanResponse(**results), timeout=timedelta(hours=24))
                    
        source = PersonJikanSource(resp)
                
        menu = menus.MenuPages(source, clear_reactions_after=True)
        
        await menu.start(ctx)
    
    @mal.command(name='character')
    async def mal_character(self, ctx: NewCtx, *, query: str):
        """pass"""
        pass
        

            
def setup(bot):
    bot.add_cog(Anime(bot))
