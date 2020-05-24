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
from typing import List
from jikanpy import AioJikan  # meant to be imported from the cog
from dataclasses import dataclass
from discord.ext.menus import ListPageSource
from utils.formatters import BetterEmbed
from utils.converters import to_human_datetime

NSFW_ANIME = {'r17', 'r', 'rx'}
NSFW_MANGA = {'doujinshi', 'ecchi', 'hentai'}
TIME_TEMPLATE = "%Y-%m-%dT%H:%M:%S%z"  # iso 8601

@dataclass(frozen=True)
class JikanResponse:  # that one is just there as a placeholder, dunno if it'll be needed later on 
    request_hash: str = None
    request_cached: bool = None
    request_cache_expiry: int = None
    results: list = None
    last_page: int = None
    jikan_url: str = None
    headers: dict = None

@dataclass(frozen=True)
class AnimeJikanResponse:
    mal_id: int = None
    url: str = None
    image_url: str = None
    title: str = None
    airing: bool = None 
    synopsis: str = None
    type: str = None
    episodes: int = None
    score: float = None
    start_date: str = None
    end_date: str = None 
    members: int = None
    rated: str = None

class AnimeJikanSource(ListPageSource):
    def __init__(self, data: JikanResponse, *, is_nsfw: bool):
        results = data.results
        
        results = (AnimeJikanResponse(**r) for r in results if r.get('title'))  # flag value
        
        nsfw_filtered = [r for r in results if r.rated.lower() not in NSFW_ANIME or is_nsfw]        
     
        super().__init__(nsfw_filtered or 'No results', per_page=1)

    def format_page(self, menu, page: AnimeJikanResponse):
        """Formats the page into an embed"""  # felt empty without a docstring
        embed = BetterEmbed(title=f'{page.title} | Rated : {page.rated}', url=page.url)
        embed.set_image(url=page.image_url)

        fields = (
            ('Synopsis', page.synopsis, False),

            ('Airing', page.airing),
            ('Start date', to_human_datetime(page.start_date, TIME_TEMPLATE)),
            ('End date', to_human_datetime(page.end_date, TIME_TEMPLATE)),

            ('Episodes', page.episodes),
            ('Type', page.type),
            ('Score', f'{page.score} / 10')
        )
        return embed.add_fields(fields)

@dataclass(frozen=True)
class MangaJikanResponse:
    mal_id: int = None
    url: str = None
    image_url: str = None
    title: str = None
    publishing: bool = None
    synopsis: str = None
    type: str = None
    chapters: int = None
    volumes: int = None
    score: float = None
    start_date: str = None
    end_date: str = None
    members: int = None
class MangaJikanSource(ListPageSource):
    def __init__(self, data: JikanResponse, *, is_nsfw: bool):
        results = data.results
        
        results = [MangaJikanResponse(**r) for r in results if r.get('chapters')]
        
        nsfw_filtered = [r for r in results if r.type.lower() not in NSFW_MANGA or is_nsfw]  
        
        super().__init__(nsfw_filtered, per_page=1)
        
    def format_page(self, menu, page: MangaJikanResponse):
        """Formats the page into an embed"""
        embed = BetterEmbed(title=f'{page.title} | Genre : {page.type}')
        embed.set_image(url=page.image_url)
    
        fields = (
            ('Synopsis', page.synopsis, False),
            
            ('Publishing', page.publishing),
            ('Start date', to_human_datetime(page.start_date, TIME_TEMPLATE)),
            ('End date', to_human_datetime(page.end_date, TIME_TEMPLATE)),
            
            ('Volumes', page.volumes),
            ('Chapters', page.chapters),
            ('Score', f"{page.score} / 10"),
        )
        return embed.add_fields(fields)

@dataclass(frozen=True)
class PersonJikanResponse:
    mal_id: int = None
    url: str = None
    image_url: str = None
    name: str = None
    alternative_names: list = None

class PersonJikanSource(ListPageSource):
    def __init__(self, data: JikanResponse):
        results = [PersonJikanResponse(**r) for r in data.results]
        super().__init__(results, per_page=1)
    
    def format_page(self, menu, page: PersonJikanResponse):
        """Formats the page into an embed"""
        embed = BetterEmbed(title=f"{page.name} | Aliases : {', '.join(page.alternative_names) or None}",
                            url=page.url)
        
        return embed.set_image(url=page.image_url)