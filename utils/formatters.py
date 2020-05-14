from collections import namedtuple
from math import ceil
from random import random, uniform
from typing import Iterator, Tuple

from discord import Color, Embed

def random_color() -> Color:
    """Returns a random pastel color"""
    return Color.from_hsv(random(), uniform(0.75, 0.95), 1)


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
        self.color = random_color()

    def fill_fields(self) -> 'ColoredEmbed':                
        """Fill the remaining fields so they are lined up properly"""
        inlines = len(self.fields[max(i for i, _ in enumerate(self.fields)):]) + 1
        for _ in range(ceil(inlines / 3) * 3 - inlines):
            self.add_field(name='\u200b', value='\u200b')
        return self
            
    def add_field(self, *, name, value, inline=True) -> 'ColoredEmbed':
        """Makes all field names bold, because I decided to"""
        return super().add_field(name=f"**{name}**", value=value, inline=inline)    

    def add_fields(self, fields: Iterator[Tuple[str, str, bool]]) -> 'ColoredEmbed':
        """Adds all fields at once"""
        for field in fields:
            self.add_field(name=field[0], value=field[1], inline=get_index(field, 2, True))
        return self