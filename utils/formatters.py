"""
MIT License

Copyright (c) 2020 - Sudosnok, AbstractUmbra, Saphielle-Akiyama

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

from math import ceil
from random import random, uniform
from typing import Any, Iterator, Tuple

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


class BetterEmbed(Embed):
    """Haha yes"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.color = random_colour()

    def fill_fields(self) -> 'ColoredEmbed':
        """Fill the remaining fields so they are lined up properly"""
        inlines = len(
            self.fields[max(i for i, _ in enumerate(self.fields)):]) + 1
        for _ in range(ceil(inlines / 3) * 3 - inlines):
            self.add_field(name='\u200b', value='\u200b')
        return self

    # Useless super delegation. Commenting for now.
    # def add_field(self, *, name, value, inline=True) -> 'ColoredEmbed':
    #     """Makes all field names bold, because I decided to"""
    #     return super().add_field(name=f"**{name}**", value=value, inline=inline)

    def add_fields(self, fields: Iterator[Tuple[str, str, bool]]) -> 'ColoredEmbed':
        """Adds all fields at once"""
        for field in fields:
            self.add_field(name=field[0], value=field[1],
                           inline=get_index(field, 2, True))
        return self


class Flags():
    """ User profile flags. """

    def __init__(self, value: int):
        self.value = value

    @property
    def employee(self):
        """ Discord Employee. """
        return self.value >> 0

    @property
    def partner(self):
        """ Discord partner. """
        return self.value >> 1

    @property
    def hypesquad_events(self):
        """ Hypesqud events organizer. """
        return self.value >> 2

    @property
    def bug_hunter_one(self):
        """ Bug hunter tier 1. """
        return self.value >> 3

    @property
    def house_bravery(self):
        """ House of Bravery. """
        return self.value >> 6

    @property
    def house_brilliance(self):
        """ House of brilliance. """
        return self.value >> 7

    @property
    def house_balance(self):
        """ House of Balance. """
        return self.value >> 8

    @property
    def early_supporter(self):
        """ Early supporter. """
        return self.value >> 9

    @property
    def team_user(self):
        """ Uses discord Teams. """
        return self.value >> 10

    @property
    def system_user(self):
        """ System User, e.g. Clyde. """
        return self.value >> 12

    @property
    def bug_hunter_two(self):
        """ Bug hunter tier 2. """
        return self.value >> 14

    @property
    def verified_bot(self):
        """ Verified Bot. """
        return self.value >> 16

    @property
    def verified_user(self):
        """ Verified bot dev, I think. """
        return self.value >> 17
