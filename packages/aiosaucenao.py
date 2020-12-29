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

from dataclasses import dataclass
from typing import List, Union

from aiohttp import ClientSession, FormData
from discord import Message, User
from discord.ext.commands import BadArgument
from discord.ext.menus import ListPageSource
from utils.converters import maybe_url
from utils.formatters import BetterEmbed


@dataclass
class MainHeader:  # todo: check the rate limit
    account_type: str = None
    index: dict = None
    long_limit: str = None
    long_remaining: int = None
    minimum_similarity: float = None
    query_image: str = None
    query_image_display: str = None
    results_requested: str = None
    results_returned: int = None
    search_depth: str = None
    short_limit: str = None
    short_remaining: int = None
    status: int = None
    user_id: str = None

    def __post_init__(self):
        del self.index  # useless data


@dataclass
class ResultHeader:
    similarity: str  # percentage
    thumbnail: str  # url
    index_id: int  # idk
    index_name: str  # title


@dataclass
class Result:
    header: dict
    data: dict  # too dynamic to be worth converting

    def __post_init__(self):
        self.header = ResultHeader(**self.header)


class Response:
    def __init__(self, data: dict, /):
        self.header = MainHeader(**data.pop("header"))
        self.results = [Result(**result) for result in data.pop("results")]
        self.extra_data = data  # keeping extra stuff there, in case the api updates


class Client:
    """Provides informations about images using saucenao's api"""

    def __init__(self, *, session: ClientSession, api_key: str):
        self.session = session
        self.api_key = api_key
        self.url = (
            f"http://saucenao.com/search.php?output_type=2&api_key={self.api_key}"
        )

    async def select_image(self, *, ctx, target: Union[User, Message, None]) -> bytes:
        """Converts into bytes suitable to send with saucenao"""
        if isinstance(target, Message):  # kinda funky, needs fix
            msg = target
        else:
            msg = ctx.message

        if (imgs := msg.attachments):
            if (img := imgs[0]).size > 8000000:
                raise BadArgument(message="Images must be smaller than 8 mb")
            elif getattr(img, "height", None) and img.filename.endswith(
                ("webp", "jpg", "png", "jpeg")
            ):
                return await imgs[0].read()
            else:
                raise BadArgument(message="Invalid image type")
        elif target is None:
            return await ctx.author.avatar_url_as(format="png", size=4096).read()
        else:
            return await target.avatar_url_as(format="png", size=4096).read()

    async def search(self, image: bytes, /) -> Response:
        """Sends the image to the api"""
        data = FormData()
        data.add_field("file", image, filename="image.png")
        async with self.session.post(url=self.url, data=data) as r:
            return Response(await r.json())


class Source(ListPageSource):
    def __init__(self, results: List[Result], /):
        super().__init__(results, per_page=1)

    def format_page(self, menu, response: Result) -> BetterEmbed:
        """Formats the repsponse into an embed"""
        header = response.header
        data = response.data

        embed = BetterEmbed(title=f"{header.index_name} | {header.similarity}%")
        embed.set_thumbnail(url=header.thumbnail)
        embed.add_field(
            name="External urls",
            value="\n".join(
                [maybe_url(url) for url in data.get("ext_urls", ["Empty"])]
            ),
        )

        for key, value in data.items():
            if not isinstance(value, list):
                if url := maybe_url(value):
                    embed.add_field(
                        name=key, value=url
                    )  # no idea about what it will return

        return embed.fill_fields()
