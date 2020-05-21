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

from typing import List
from datetime import timedelta

from async_cse import Search as BaseGoogleSearch
from async_cse import Result as GoogleResponse

from discord.ext.menus import ListPageSource
from utils.formatters import BetterEmbed

from main import NewCtx

class AioSearchEngine(BaseGoogleSearch):
    async def do_search(self, ctx: NewCtx, *, query: str, 
                        is_nsfw: bool, image_search: bool = False) -> ListPageSource:
        """Searches stuff and returns the formatted version of it"""
        results = await self.search(query, 
                                    safesearch=not is_nsfw, 
                                    image_search=image_search)
                
        return ctx.add_to_cache(GoogleSource(results, is_nsfw), 
                                timeout=timedelta(minutes=5))

class GoogleSource(ListPageSource):
    def __init__(self, data: List[GoogleResponse], search_is_nsfw: bool):
        super().__init__(data, per_page=1)
        self.search_is_nsfw = search_is_nsfw

    def format_page(self, menu, response: GoogleResponse):
        safesearch_state = 'OFF' if self.search_is_nsfw else 'ON'
        
        embed = BetterEmbed(title=f'{response.title} | Safesearch : {safesearch_state}',
                            description=response.description,
                            url=response.url)
        
        return embed.set_image(url=response.image_url)