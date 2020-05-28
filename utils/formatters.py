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

from datetime import datetime
from math import ceil
from random import random, uniform
from typing import Any, Iterator, Tuple, Optional, Union

from discord import Colour, Embed


def random_colour() -> Colour:
    """Returns a random pastel colour"""
    return Colour.from_hsv(random(), uniform(0.75, 0.95), 1)


def chunker(to_chunk: list, chunk_size: int = 5) -> Iterator:
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(to_chunk), chunk_size):
        yield to_chunk[i:i + chunk_size]


def get_index(indexable, index: int, default=None) -> Any:
    """Tries to get an item using it's index, returns the default is not found"""
    try:
        return indexable[index]
    except IndexError:
        return default


def fmt(daytee: Union[datetime, int], stringform: Optional[str]):
    """ Quick datetime formatter from timestamp or datetime object. """
    if isinstance(daytee, int):
        daytee = datetime.fromtimestamp(daytee)
    stringform = stringform or "%Y %b %d: %H:%M"
    return daytee.strftime(stringform)

class BetterEmbed(Embed):
    """Haha yes"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.color = random_colour()
        self._empty_field = "**⚠️ MISSING FIELD ⚠️**"

    def fill_fields(self) -> 'ColoredEmbed':
        """Fill the remaining fields so they are lined up properly"""
        inlines = len(self.fields[max(i for i, _ in enumerate(self.fields)):]) + 1
        for _ in range(ceil(inlines / 3) * 3 - inlines):
            self.add_field(name='\u200b', value='\u200b')
        return self

    # Useless super delegation. Commenting for now.
    # def add_field(self, *, name, value, inline=True) -> 'ColoredEmbed':
    #     """Makes all field names bold, because I decided to"""
    #     return super().add_field(name=f"**{name}**", value=value, inline=inline)

    def add_field(self, *, name, value, inline=True):
        return super().add_field(name=str(name) or self._empty_field,  # sends the embed anyways, but with a warn
                                 value=str(value) or self._empty_field,  # a bit clearer than the missing field error
                                 inline=inline)

    def add_fields(self, fields: Iterator[Tuple[str, str, bool]]) -> 'ColoredEmbed':
        """Adds all fields at once"""
        for field in fields:
            self.add_field(name=field[0], value=field[1],
                           inline=get_index(field, 2, True))
        return self

class Flags:
    def __init__(self, value):
        self.value = value

    def __repr__(self):
        return f"<{self.__class__.__name__} value={self.value}>"

    def __contains__(self, item):
        return getattr(self, item) if isinstance(item, str) else getattr(self, item.fget.__name__)

    def has_flag(self, v):
        return (self.value & v) == v

    @property
    def staff(self):
        return self.has_flag(1)

    @property
    def partner(self):
        return self.has_flag(2)

    @property
    def hypesquad_events(self):
        return self.has_flag(4)

    @property
    def bug_hunter_level_1(self):
        return self.has_flag(8)

    @property
    def mfa_sms(self):
        return self.has_flag(16)

    @property
    def premium_promo_dismissed(self):
        return self.has_flag(32)

    @property
    def hypesquad_bravery(self):
        return self.has_flag(64)

    @property
    def hypesquad_brilliance(self):
        return self.has_flag(128)

    @property
    def hypesquad_balance(self):
        return self.has_flag(256)

    @property
    def early_supporter(self):
        return self.has_flag(512)

    @property
    def team_user(self):
        return self.has_flag(1024)

    @property
    def system(self):
        return self.has_flag(4096)

    @property
    def unread_sys_msg(self):
        return self.has_flag(8192)

    @property
    def bug_hunter_level_2(self):
        return self.has_flag(16384)

    @property
    def underage_deleted(self):
        return self.has_flag(32768)

    @property
    def verified_bot(self):
        return self.has_flag(65536)

    @property
    def verified_bot_developer(self):
        return self.has_flag(131072)
