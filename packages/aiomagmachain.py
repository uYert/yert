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

from dataclasses import dataclass

from aiohttp import ClientSession
from async_cse.search import NoResults
from discord.ext.commands import BadArgument
from utils.converters import maybe_url
from utils.formatters import BetterEmbed

from .aiogooglesearch import AioSearchEngine


@dataclass(frozen=True)
class MagmaChainResponse:
    snapshot: str  # url to the image
    status: int  # status of the request
    website: str  # url to the screenshotted website


class AioMagmaChain:
    """Screenshots some websites"""

    def __init__(self, *, session: ClientSession, google_client: AioSearchEngine):
        self.session = session
        self.google_client = google_client
        self.screener = "http://magmafuck.herokuapp.com/api/v1"

    async def check_url(self, *, url: str, is_nsfw: bool) -> str:
        """checks if the result is a proper sfw one"""
        try:
            results = await self.google_client.search(url, safesearch=not is_nsfw)
        except NoResults:
            raise BadArgument(message="Couldn't find the url you're looking for")
        else:
            return results[0].url

    async def fetch_snapshot(self, url: str) -> MagmaChainResponse:
        """Takes a screenshot using the magmachain api"""
        async with self.session.post(self.screener, headers={"website": url}) as r:
            return MagmaChainResponse(**await r.json())

    def format_snapshot(
        self, *, response: MagmaChainResponse, is_nsfw: bool
    ) -> BetterEmbed:
        """Formats the snaphot into an embed"""
        embed = BetterEmbed(
            title=f"Screenshot | Safe : {'OFF' if is_nsfw else 'ON'}",
            url=response.website,
        )

        embed.add_field(name="Link", value=maybe_url(response.website))

        return embed.set_image(url=response.snapshot)
