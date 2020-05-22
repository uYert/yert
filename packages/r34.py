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

from discord.ext.menus import ListPageSource
from humanize import naturaldate
from datetime import datetime
from utils.formatters import BetterEmbed
from rule34 import Rule34Post
from rule34 import Rule34 as BaseRule34
from asyncio import AbstractEventLoop
from aiohttp import ClientSession

class AioRule34(BaseRule34):
    def __init__(self, *, session: ClientSession, timeout: int = 10, 
                 loop: AbstractEventLoop = None):
        """
        :param loop: the event loop
        :param timeout: how long requests are allowed to run until timing out
        """
        self.session = session
        self.timeout = timeout  # it normally doesn't let us to use our own clientsession
        self.loop = loop


class R34Source(ListPageSource):
    def __init__(self, data, query: str):
        super().__init__(data, per_page=1)
        self.query = query
    
    def format_page(self, menu, page: Rule34Post):
        embed = BetterEmbed(title=f'Results for : {self.query}', url=page.file_url)
    
        created_at = datetime.strptime(page.created_at, "%a %b %d %H:%M:%S %z %Y")  # there must be a format for that
    
        fields = (
            ('Size', f'{page.width}x{page.height}'),
            ('Creator id', page.creator_ID),
            ('Created at', naturaldate(created_at)),
        )
        embed.set_image(url=page.file_url)
    
        return embed.add_fields(fields)