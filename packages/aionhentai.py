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

import nhentai as _nhentai
from asyncio import AbstractEventLoop
from typing import Union, List
from discord.ext.menus import ListPageSource
from utils.formatters import BetterEmbed

class Client:
    def __init__(self, loop: AbstractEventLoop):
        self.loop = loop
        
    def _str_search(self, query: str):
        """Query using a string"""
        return [*_nhentai.search(query)]
        
    def _int_search(self, query: int):
        """Query using an int"""
        return _nhentai.Doujinshi(query)
    
    async def search(self, query: Union[int, str]) -> List[_nhentai.Doujinshi]:
        """Searches something on nhentai"""
        if isinstance(query, str):
            return await self.loop.run_in_executor(self._str_search(query))
        elif isinstance(query, int):
            return [await self.loop.run_in_executor(self._int_search(query))]

"""
.name = primary/english name
.jname = secondary/non english name
.tags = a list of numerical tags
.magic = magic number/id
.cover = cover(thumbnail)
.gid = /galleries/ id for page lookup
.pages = number of pages
"""


class Source(ListPageSource):
    def __init__(self, data: List[_nhentai.Doujinshi]):
        super().__init__(data, per_page=1)
        self.is_reading = False
    
    def format_page(self, menu, page: _nhentai.Doujinshi):
        pass
    
    
    
    def format_overview(self, page: _nhentai.Doujinshi):
        """Formats the overview page that provides general informations"""
        embed = BetterEmbed(title=f"{page.name} | {page.magic}")
        embed.set_image(url=page.cover)
        fields = (
            ('Tags', ', '.join(page.tags), False),
            ('Japanese name', page.jname),
            ('Page amount', page.pages),
            ('Galeries id', page.gid)
        )
        return embed.add_fields(fields)