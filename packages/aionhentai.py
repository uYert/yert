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

from asyncio import AbstractEventLoop
from typing import List, Union

import nhentaio
from discord.ext.menus import Last, ListPageSource, MenuPages, button
from utils.formatters import BetterEmbed


class Client(nhentaio.Client):
    def __init__(self, loop: AbstractEventLoop):
        self.loop = loop

    def _str_search(self, query: str):
        """Query using a string"""
        return [*self.search(query)]

    async def search(self, query: Union[int, str]) -> List[_nhentai.Doujinshi]:
        """Searches something on nhentai"""
        if isinstance(query, str):
            return await self.loop.run_in_executor(None, self._str_search, query)
        elif isinstance(query, int):
            res = await self.loop.run_in_executor(None, self._int_search, query)
            return [res, res]

    def filter_doujins(self, data: List[_nhentai.Doujinshi]):
        """Removes some dubious tags"""
        for doujin in data:
            for tag in doujin.tags:
                if any([True for t in ("loli", "shota") if t in tag.lower()]):
                    break
            else:
                yield doujin


class Source(ListPageSource):
    def __init__(self, data: Union[List[_nhentai.Doujinshi], List[str]]):
        super().__init__(data, per_page=1)
        self.last_viewed_page = 0

    def format_page(self, menu, page: Union[_nhentai.Doujinshi, str]):
        if isinstance(page, str):
            return page

        embed = BetterEmbed(title=f"{page.name} | {page.magic}")
        fields = (
            ("Tags", ", ".join(page.tags), False),
            ("Japanese name", page.jname),
            ("Page amount", page.pages),
            ("Galeries id", page.gid),
        )
        return embed.set_image(url=page.cover).add_fields(fields)

    def get_page(self, page_number: int):
        self.current_page = page_number
        return super().get_page(page_number)


class _ReadingSource(ListPageSource):
    def __init__(self, data: _nhentai.Doujinshi):
        super().__init__(data._images, per_page=1)
        self.data = data
        self.template = BetterEmbed(title=f"{data.name} | {data.magic}")

    def format_page(self, menu: MenuPages, page: str):
        embed = self.template.copy()
        embed.url = page
        embed.set_image(url=page)
        return embed.set_footer(
            text=f"Page {menu.current_page} out of {self.get_max_pages()}"
        )

    def get_page(self, page_number: int):
        self.current_page = page_number
        return super().get_page(page_number)


class Menu(MenuPages):
    def __init__(self, source: Source, **kwargs):
        super().__init__(source, **kwargs)
        self.backup_source = source

    async def change_source(self, source, *, at_index: int = 0):
        self._source = source
        self.current_page = at_index
        if self.message is not None:
            await source._prepare_once()
            await self.show_page(at_index)

    @button("📖", position=Last(5))
    async def open_doujin(self, payload):
        data = self.source.entries[self.current_page]
        await self.change_source(_ReadingSource(data))

    @button("↩️", position=Last(6))
    async def return_to_overview(self, payload):
        """Returns to overview mode"""
        source = self.backup_source
        await self.change_source(source, at_index=source.last_viewed_page)
