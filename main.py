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
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR
"""

import asyncio
from collections.abc import Hashable
from datetime import datetime, timedelta, timezone
import os
import sys
import traceback
from typing import Any, Union

from aiohttp import ClientSession
import discord
from discord.ext import commands

import config
from utils.containers import TimedCache
from utils.db import Table
from utils.formatters import BetterEmbed

for env in ('NO_UNDERSCORE', 'NO_DM_TRACEBACK', 'HIDE', 'RETAIN'):
    os.environ['JISHAKU_' + env] = 'True'

COGS = (
    "jishaku",
    "cogs.events",
    "cogs.fun",
    "cogs.games",
    "cogs.images",
    "cogs.memes",
    "cogs.meta",
    "cogs.moderation",
    "cogs.practical",
    "cogs.other"
)


class NewCtx(commands.Context):
    """Custom context for extra functions"""

    # typehinted copypaste of the default init ## pylint: disable=super-init-not-called
    def __init__(self, **attrs):
        self.message: Union[discord.Message, None] = attrs.pop('message', None)
        self.bot: Union[Bot, None] = attrs.pop('bot', None)

        self.args: list = attrs.pop('args', [])
        self.kwargs: dict = attrs.pop('kwargs', {})
        self.prefix: str = attrs.pop('prefix')
        self.command: Union[commands.Command,
                            None] = attrs.pop('command', None)

        self.view = attrs.pop('view', None)  # no idea about what that is

        self.invoked_with: str = attrs.pop('invoked_with', None)
        self.invoked_subcommand: commands.Command = attrs.pop(
            'invoked_subcommand', None)
        self.subcommand_passed: Union[str, None] = attrs.pop(
            'subcommand_passed', None)
        self.command_failed: bool = attrs.pop('command_failed', False)

        self._state = self.message._state

        self._altered_cache_key = None

    async def webhook_send(self,
                           content: str,
                           *,
                           webhook: discord.Webhook,
                           skip_wh: bool = False,
                           skip_ctx: bool = False) -> None:
        """ This is a custom ctx addon for sending to the webhook and/or the ctx.channel. """
        content = content.strip("```")
        embed = BetterEmbed(title="Error", description=f"```py\n{content}```",
                            timestamp=datetime.now(tz=timezone.utc))
        embed.add_field(name="Invoking command",
                        value=f"{self.prefix}{self.invoked_with}", inline=True)
        embed.add_field(name="Author", value=f"{str(self.author)}")
        if not skip_ctx:
            await super().send(embed=embed)

        if not skip_wh:
            await webhook.send(embed=embed)

    @property
    def qname(self) -> Union[str, None]:
        """Shortcut to get the command's qualified name"""
        return self.command.qualified_name if self.command else None

    @property
    def all_args(self) -> list:
        """Retrieves a list of all args and kwargs passed into the command"""  # ctx.args returns self too
        args = [arg for arg in self.args if not isinstance(
            arg, (commands.Cog, commands.Context))]
        # there should be only one
        kwargs = [val for val in self.kwargs.values()]
        return args + kwargs

    @property
    def cache_key(self) -> tuple:
        """Returns the key used to access the cache"""
        return self._altered_cache_key or tuple([self.qname] + self.all_args)

    @cache_key.setter
    def cache_key(self, key: Hashable) -> None:
        """Sets another key to use for this Context"""
        self._altered_cache_key = key

    @property
    def cache(self) -> TimedCache:
        """Returns the cache tied to the bot"""
        return self.bot.cache

    @property
    def cached_data(self) -> Union[Any, None]:
        """Tries to retrieve cached data"""
        return self.cache.get(key=self.cache_key)

    def add_to_cache(self, *, value: Any, timeout: Union[int, timedelta] = None,
                     key: Hashable = None) -> Any:
        """Sets an item into the cache using the the provided keys"""
        return self.cache.set(key=key or self.cache_key, value=value, timeout=timeout)


class Bot(commands.Bot):
    """ Our main bot-ty bot. """

    def __init__(self, **options):
        super().__init__(**options)
        self._session = ClientSession(loop=self.loop)
        self._cache = TimedCache(loop=self.loop)
        if PSQL_DETAILS := getattr(config, 'PSQL_DETAILS', None):
            self._pool = asyncio.get_event_loop().run_until_complete(
                Table.create_pool(
                    PSQL_DETAILS, command_timeout=60
                ))

        # Extension load
        for extension in COGS:
            try:
                self.load_extension(extension)
            except Exception:
                pass  # ! TODO: webhook the print_exc

    #! Discord stuff
    async def get_context(self, message: discord.Message, *, cls=None):
        """Custom context stuff hahayes"""
        return await super().get_context(message, cls=cls or NewCtx)

    async def on_ready(self):
        """ We're online. """
        print("yert is ready for memes.")

    @property
    def session(self):
        """Don't want to accidentally edit those"""
        return self._session

    @property
    def cache(self):
        """ Quick return of the cache. """
        return self._cache

    @property
    def pool(self):
        """ Let's not rewrite internals... """
        if self._pool:
            return self._pool
        return None


if __name__ == '__main__':
    bot = Bot(command_prefix=config.PREFIX)
    bot.run(config.BOT_TOKEN)
