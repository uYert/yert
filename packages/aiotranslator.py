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

from __future__ import annotations

import asyncio
from datetime import timedelta
from functools import partial
from typing import TYPE_CHECKING, Dict, Union

import aiohttp
from discord.ext.commands import BadArgument
from googletrans import LANGCODES, LANGUAGES
from googletrans import Translator as BaseTranslator
from googletrans.client import Translated
from utils.formatters import BetterEmbed

if TYPE_CHECKING:
    from asyncio import AbstractEventLoop

    from aiohttp import ClientSession


# outside of the class to use it as a converter
def to_language(arg: str) -> Union[str, None]:
    """Converts a string into a valid google trans language"""
    if (low := arg.lower()) in LANGUAGES:
        return low
    elif res := LANGCODES.get(low):
        return res
    raise BadArgument(message=f"Couldn't find the language {arg}")


def check_length(arg: str) -> str:
    """Checks the initial text and returns it"""
    if len(arg) > 200:
        raise BadArgument(message="Cannot translate texts longer than 200 characters")
    return arg


class AioTranslator(BaseTranslator):
    """Translates stuff using google translate's api"""

    def __init__(self, *args, **kwargs):
        self.session: ClientSession = kwargs.pop("session", aiohttp.ClientSession())
        self.loop: AbstractEventLoop = kwargs.pop("loop", asyncio.get_event_loop())
        super().__init__(*args, **kwargs)

    def format_resp(self, *, resp: Translated, text: str) -> BetterEmbed:
        """Formats the response into an embed"""
        src = LANGUAGES.get(resp.src) or resp.src
        dest = LANGUAGES.get(resp.dest) or resp.dest

        conf = round(resp.confidence * 100, 1)
        f_confidence = str(conf) + "%"

        if conf < 50.0:
            f_confidence += " (might be innacurate)"

        embed = BetterEmbed(title="Translated something !")

        fields = (
            ("original", text, False),
            ("Translation", resp.text, False),
            ("Confidence", f_confidence, True),
            ("Languages", f"{src} -> {dest}", True),
        )

        return embed.add_fields(fields)

    async def do_translation(
        self, *, ctx, text: str, translation_kwarg: Dict[str, str]
    ) -> BetterEmbed:
        """Does the translation and formats it"""
        func = partial(self.translate, text, **translation_kwarg)
        resp = await self.loop.run_in_executor(None, func)
        embed = self.format_resp(resp=resp, text=text)
        return ctx.add_to_cache(value=embed, timeout=timedelta(minutes=60))
