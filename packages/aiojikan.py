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
from functools import partial as funct_partial
from typing import List, Tuple, Union

from discord.ext.commands import CooldownMapping
from discord.ext.menus import ListPageSource
from jikanpy import AioJikan

from utils.converters import to_human_datetime, try_unpack_class
from utils.formatters import BetterEmbed


NSFW_MANGA = {'doujinshi', 'ecchi', 'hentai'}
TIME_TEMPLATE = "%Y-%m-%dT%H:%M:%S%z"  # iso 8601

#* Base classes

@dataclass
class Response:
    request_hash: str
    request_cached: bool
    request_cache_expiry: int
    results: list
    last_page: int
    jikan_url: str
    headers: dict

# Result

@dataclass
class Result:
    mal_id: int
    url: str
    
    def make_field(self, name: str, *, inline: bool = True) -> Tuple[str, str, bool]:
        """Returns a tuple that can be added as a field"""
        return (name.replace('_', ' ').capitalize(), getattr(self, name), inline)

class ResultEmbed(BetterEmbed):
    def __init__(self, data: Result, **options):
        super().__init__(**options)
        self.url = data.url
        self.set_footer(text=f"Mal id : {data.mal_id}")
    
# Image url

@dataclass
class ImageUrl(Result):
    image_url: str

class ImageUrlEmbed(ResultEmbed):
    def __init__(self, data: ImageUrl, **options):
        super().__init__(data, **options)
        self.set_thumbnail(url=data.image_url)

# Media

@dataclass
class Media(ImageUrl):
    title: str
    synopsis: str
    type: str
    score: float
    start_date: str
    end_date: str
    members: int

to_natur_dt = funct_partial(to_human_datetime, template=TIME_TEMPLATE)

class MediaEmbed(ImageUrlEmbed):
    def __init__(self, data: Media, **options):
        super().__init__(data, **options)
        
        self.title = f"[{data.type}] {data.title}"
        
        end_date = data.end_date
        end_date = 'Currently airing' if end_date is None else to_natur_dt(end_date)

        fields = (
            data.make_field('synopsis', inline=False),
            
            ('Start date', to_natur_dt(data.start_date)),
            ('End date', end_date),
            ('Score', f"{data.score} / 10"),
        )

        self.add_fields(fields)

#* Finished classes

# Anime

@dataclass
class Rating:
    desc: str
    nsfw: bool

ANIME_RATINGS = {
    'G': Rating(desc='G - All ages', nsfw=False),
    'PG': Rating(desc='Children', nsfw=False),
    'PG-13': Rating(desc='Teens 13 or older', nsfw=False),
    
    'R': Rating(desc='17+ recommended (violence & profanity)', nsfw=True),
    'R+': Rating(desc='Mild nudity (may also contain violence & profanity)', nsfw=True),
    'Rx': Rating(desc='Hentai (extreme sexual content/nudity)', nsfw=True)
}

@dataclass
class Anime(Media):
    airing: bool
    episodes: int
    rated: str

def get_rating(data: Anime, attr_name: str) -> Union[str, None]: # reused in the main cog to filter 
    """Gets the rating obj of an anime"""
    return getattr(ANIME_RATINGS.get(data.rated), attr_name, None)

class AnimeEmbed(MediaEmbed):
    def __init__(self, data: Anime, **options):
        super().__init__(data, **options)

        fields = (
            data.make_field('episodes'),
            ('Rated', get_rating(data, 'desc')),  # might randomly return none
        )
        self.add_fields(fields).fill_fields()

# Manga

@dataclass
class Manga(Media):
    publishing: bool
    chapters: int
    volumes: int

class MangaEmbed(MediaEmbed):
    def __init__(self, data: Manga, **options):
        super().__init__(data, **options)

        fields = (
            data.make_field('chapters'),
            data.make_field('volumes'),
        )

        self.add_fields(fields).fill_fields()

# Person

@dataclass
class Person(ImageUrl):
    name: str
    alternative_names: list

class PersonEmbed(ImageUrlEmbed):
    def __init__(self, data: Person, **options):
        super().__init__(data, **options)
        alt_names = ', '.join(data.alternative_names) or 'No aliases'
        self.title = f'{data.name} | Aliases : {alt_names}'

# Character

@dataclass
class CharacterMedia(Result):
    type: str  
    name: str

@dataclass
class Character(Person):
    anime: list  
    manga: list

    def __post_init__(self):
        for attr in ('anime', 'manga'):
            setattr(self, attr, [CharacterMedia(**r) for r in getattr(self, attr)])

class CharacterEmbed(PersonEmbed):
    def __init__(self, data: Character, **options):
        super().__init__(data, **options)
        
        for attr in ('anime', 'manga'):
            field_value = '-' + '\n-'.join([f"[{c.type}] {c.name}" for c in getattr(data, attr)])
            self.add_field(name=attr.capitalize(), value=field_value, inline=False)

class Source(ListPageSource):
    def __init__(self, data: List[Result], *, is_nsfw: bool = None):  # any subclass of it
        
        sample = data[0]
        # filtering only in the source I guess
        if isinstance(sample, Anime):
            data = [r for r in data if not get_rating(r, 'nsfw') or is_nsfw]
            
        if isinstance(sample, Manga):
            data = [r for r in data if not str(r.type).lower() in NSFW_MANGA or is_nsfw]
            
        super().__init__(data, per_page=1)
        
        # self.template = globals().get(type(data[0]).__name__ + 'Embed') 
        
        self.template = {
            'Person': PersonEmbed,
            'Anime': AnimeEmbed,
            'Manga': MangaEmbed,
            'Character': CharacterEmbed,
        }[type(data[0]).__name__]
    
    def format_page(self, menu, page: Result):
        return self.template(page)
    
class Client(AioJikan):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.result_templates = {
            'anime': Anime, 
            'manga': Manga, 
            'person': Person, 
            'character': Character,
        }
    
    async def search(self, search_type: str, query: str, 
                     page: int = None, parameters: dict = None) -> Response:
        """Searches something on jikanpy, refer to the superclass' docstring"""
        resp = await super().search(search_type, query, page=page, parameters=parameters)
        response = Response(**resp)

        response.results = [*try_unpack_class(class_=self.result_templates[search_type], 
                                              iterable=response.results)]
        
        return response
