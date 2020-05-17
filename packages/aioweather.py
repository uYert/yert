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
from aiohttp import ClientSession
from utils.formatters import BetterEmbed
from humanize import naturaltime
from datetime import datetime as dt
from datetime import timezone as tz


@dataclass(frozen=True)
class Coordinates:
    lon: int = None  # longitude
    lat: int = None  # latitude


@dataclass(frozen=True)
class Weather:
    id: int = None  # city id
    main: str = None  # One word description
    description: str = None  # Full description
    icon: str = None  # id of the corresponding icon


@dataclass(frozen=True)
class Main:
    temp: float = None  # kelvin
    feels_like: float = None  # kelvin
    temp_min: float = None  # kelvin
    temp_max: float = None  # kelvin
    pressure: int = None  # hectopascals
    humidity: int = None  # percentage
    sea_level: int = None  # hectopascals
    grnd_level: int = None  # hectopascals


@dataclass(frozen=True)
class Wind:
    speed: float = None  # meters / s
    deg: int = None  # degrees


@dataclass(frozen=True)
class Clouds:
    all: int = None  # percentage


@dataclass(frozen=True)
class Precipitation:  # used by both rain and snow
    _1h: int = None  # millimeters
    _3h: int = None  # millimeters


@dataclass(frozen=True)
class Sys:
    type: int = None  # internal
    id: int = None  # internal
    country: str = None  # Country
    sunrise: int = None  # sunrise time, unix utc
    sunset: int = None  # sunset time, unix utc


class WeatherResponse:
    def __init__(self, data: dict):
        self.coord = Coordinates(**data.pop('coord', None))
        self.weather = [Weather(**w)
                        for w in data.pop('weather', {'id': None})]
        self.main = Main(**data.pop('main', None))
        self.wind = Wind(**data.pop('wind', None))
        self.clouds = Clouds(**data.pop('clouds', None))

        for attr in ('rain', 'snow'):
            setattr(self, attr, Precipitation(
                **{'_' + k: v for k, v in data.pop(attr, {}).items()}))

        self.sys = Sys(**data.pop('sys', None))

        self.dt = data.pop('dt', None)  # time of data calculation, unix, utc
        self.timezone = data.pop('timezone', None)  # shift in seconds from utc
        self.id = data.pop('id', None)  # city id
        self.name = data.pop('name', None)  # city name
        self.visibility = data.pop('visibility', None)  # visibility in meters

        self.base = data.pop('base', None)  # internal
        self.cod = data.pop('cod', None)  # internal

        self.extra_data = data  # if the api is updated, stuff will be kept here


class AioWeather:
    """Fetches data from the openweather api"""

    def __init__(self, *, session: ClientSession, api_key: str):
        self.session = session
        self.api_key = api_key

    async def fetch_weather(self, city: str, /) -> WeatherResponse:
        """Fetches weather using openweather's api"""

        link = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={self.api_key}"

        async with self.session.get(link) as r:
            return WeatherResponse(await r.json())

    def format_weather(self, res: WeatherResponse, /) -> BetterEmbed:
        """Returns a formatted embed from the data received by the api"""

        embed = BetterEmbed(title=f"Weather in {res.name} ({res.sys.country})",
                            description=f"Overall description : {res.weather[0].description}")

        embed.set_thumbnail(
            url=f"http://openweathermap.org/img/wn/{res.weather[0].icon}@2x.png")

        main = res.main
        sys = res.sys
        wind = res.wind

        def nf(obj, attr): return getattr(obj, attr, '[NF]')  # -> Any

        def from_timestamp(ts): return naturaltime(
            dt.now(tz.utc) - dt.fromtimestamp(ts, tz=tz.utc))  # -> str

        def from_kelvin(
            kt): return f"{kt - 273.15:.1f}°C | {(kt * 9/5 - 459.67):.1f}°F"  # -> str

        fields = (
            ('Min temperature', from_kelvin(main.temp_min)),
            ('Max temperature', from_kelvin(main.temp_max)),
            ('Feels like', from_kelvin(main.feels_like)),

            ('Pressure', f"{main.pressure} hPA"),
            ('Humidity', f"{main.humidity}%"),
            ('Visibility', f"{((res.visibility or 0) / 1000):.1f} kilometers"),

            ('Wind speed', f"{wind.speed} km/h"),
            ('Wind direction', f"{wind.deg} degrees"),
            ('Cloudiness', f"{res.clouds.all}%"),

            ('Data refreshed', from_timestamp(res.dt)),
            ('Sunrise', from_timestamp(sys.sunrise)),
            ('Sunset', from_timestamp(sys.sunset))
        )

        return embed.add_fields(fields)
