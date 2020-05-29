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
from discord.ext.menus import ListPageSource, MenuPages, button, Last
from utils.formatters import BetterEmbed
from copy import copy

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
            return await self.loop.run_in_executor(None, self._str_search, query)
        elif isinstance(query, int):
            res = await self.loop.run_in_executor(None, self._int_search, query)
            return [res, res]

class Source(ListPageSource):
    
    def _filter_doujins(self, data: List[_nhentai.Doujinshi]):
        """Removes some dubious tags"""
        for doujin in data:
            for tag in doujin.tags:
                if any([True for t in ('loli', 'shota') if t in tag.lower()]):
                    break
            else:
                yield doujin
    
    def __init__(self, data: List[_nhentai.Doujinshi]):
        filtered = [*self._filter_doujins(data)] or ["No results"]
        super().__init__(filtered, per_page=1)

    def format_page(self, menu, page: Union[_nhentai.Doujinshi, str]):
        if isinstance(page, str):
            return page
        
        embed = BetterEmbed(title=f"{page.name} | {page.magic}")
        fields = (
            ('Tags', ', '.join(page.tags), False),
            ('Japanese name', page.jname),
            ('Page amount', page.pages),
            ('Galeries id', page.gid)
        )
        return embed.set_image(url=page.cover).add_fields(fields)

class _ReadingSource(ListPageSource):
    def __init__(self, data: _nhentai.Doujinshi):
        super().__init__(data._images, per_page=1)
        self.data = data
        self.current_page = 0  # hacky way to do it
        self.template = BetterEmbed(title=f"{data.name} | {data.magic}")

    def format_page(self, menu, page: str):
        embed = self.template.copy()
        embed.url = page
        embed.set_image(url=page)
        return embed.set_footer(text=f'Page {self.current_page} out of {self._max_pages}')

    def get_page(self, page_number: int):
        self.current_page = page_number
        return super().get_page(page_number)

class Menu(MenuPages):
    def __init__(self, source: Source, **kwargs):
        super().__init__(source, **kwargs)
        self.backup_source = source
        self.last_overview_page: int = 0

    async def change_source(self, source, *, new_page: int = 0):
        self._source = source
        self.current_page = new_page
        if self.message is not None:
            await source._prepare_once()
            await self.show_page(new_page)

    @button('📖', position=Last(5))
    async def open_doujin(self, payload):
        self.last_overview_page = self.current_page
        data = self.source.entries[self.current_page]
        await self.change_source(_ReadingSource(data))

    @button('↩️', position=Last(6))
    async def return_to_overview(self, payload):
        """Returns to overview mode"""
        await self.change_source(self.backup_source,
                                 new_page=self.last_overview_page)
