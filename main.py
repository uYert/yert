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
import traceback
from collections.abc import Hashable
from datetime import datetime, timedelta, timezone
import json
import traceback
from typing import Any, Tuple, Union

import discord
from aiohttp import ClientSession
from discord.ext import commands
from discord.ext import commands, tasks

import config
from utils.containers import TimedCache
from utils.db import Table
from utils.formatters import BetterEmbed

COGS = (
    "jishaku",
    "cogs.anime",
    "cogs.events",
    "cogs.games",
    # "cogs.degeneracy",
    "cogs.images",
    "cogs.memes",
    "cogs.meta",
    "cogs.moderation",
    "cogs.practical",
    "cogs.other",
    "cogs.stats",
)


class NewCtx(commands.Context):
    """Custom context for extra functions"""

    # typehinted copypaste of the default init ## pylint: disable=super-init-not-called
    def __init__(self, **attrs):
        self.message: discord.Message = attrs.pop("message", None)
        self.bot: Bot = attrs.pop("bot", None)

        self.args: list = attrs.pop("args", [])
        self.kwargs: dict = attrs.pop("kwargs", {})
        self.prefix: str = attrs.pop("prefix")
        self.command: Union[commands.Command, None] = attrs.pop("command", None)

        self.view = attrs.pop("view", None)  # no idea about what that is

        self.invoked_with: str = attrs.pop("invoked_with", None)
        self.invoked_subcommand: commands.Command = attrs.pop(
            "invoked_subcommand", None
        )
        self.subcommand_passed: Union[str, None] = attrs.pop("subcommand_passed", None)
        self.command_failed: bool = attrs.pop("command_failed", False)

        self._state = self.message._state

        self._altered_cache_key = None

    async def webhook_send(
        self,
        short: str,
        full: str,
        exc_info: Tuple[str, str, str],
        *,
        webhook: discord.Webhook,
    ) -> None:
        """ This is a custom ctx addon for sending to the webhook and/or the ctx.channel. """

        embed = BetterEmbed(
            title="Error",
            description=f"```py\n{short}```",
            timestamp=datetime.now(tz=timezone.utc),
        )

        embed.add_field(
            name="Invoking command",
            value=f"{self.prefix}{self.invoked_with}",
            inline=True,
        )

        embed.add_field(name="Author", value=f"{str(self.author)}")

        embed.add_field(
            name=f"File: {exc_info[0]}",
            value=f"Line: {exc_info[1]} || Func: {exc_info[2]}",
            inline=True,
        )

        await self.send(embed=embed)
        await webhook.send(full)

    @property
    def qname(self) -> Union[str, None]:
        """Shortcut to get the command's qualified name"""
        return getattr(self.command, "qualified_name", None)

    @property
    def all_args(self) -> list:
        """Retrieves a list of all args and kwargs passed into the command"""  # ctx.args returns self too
        args = [
            arg
            for arg in self.args
            if not isinstance(arg, (commands.Cog, commands.Context))
        ]
        # there should be only one
        kwargs = [val for val in self.kwargs.values()]
        return args + kwargs

    @property
    def cache_key(self) -> list:
        """Returns the key used to access the cache"""
        return self._altered_cache_key or [self.qname] + self.all_args

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
        return self.cache.get(key=tuple(self.cache_key))

    def add_to_cache(
        self, value: Any, *, timeout: Union[int, timedelta] = None, key: Hashable = None
    ) -> Any:
        """Sets an item into the cache using the the provided keys"""
        return self.cache.set(
            key=tuple(key or self.cache_key), value=value, timeout=timeout
        )


class Bot(commands.Bot):
    """ Our main bot-ty bot. """

    def __init__(self, **options):
        super().__init__(intents=discord.Intents.all(), **options)
        with open('catpost.json') as file:
            self._cached_ids = json.load(file)
        if PSQL_DETAILS := getattr(config, 'PSQL_DETAILS', None):
            self._pool = asyncio.get_event_loop().create_task(
                Table.create_pool(PSQL_DETAILS, command_timeout=60)
            )

    async def connect(self, *, reconnect=True):
        self.prefixes = {}

        self._session = ClientSession(loop=self.loop)
        self._headers = {"Range": "bytes=0-10"}
        self._cache = TimedCache(loop=self.loop)
        self._before_invoke = self.before_invoke
        if PSQL_DETAILS := getattr(config, "PSQL_DETAILS", None):
            self._pool = await Table.create_pool(PSQL_DETAILS, command_timeout=60)

        # Extension load
        for extension in COGS:
            try:
                self.load_extension(extension)
            except Exception as e:
                wh_id, wh_token = config.WEBHOOK
                full_exc = traceback.format_exception(type(e), e, e.__traceback__)
                hook = discord.Webhook.partial(
                    id=wh_id,
                    token=wh_token,
                    adapter=discord.AsyncWebhookAdapter(self.session),
                )
                full_exc = [line.replace("/home/moogs", "", 1) for line in full_exc]
                full_exc = [
                    line.replace("C:\\Users\\aaron", "", 1) for line in full_exc
                ]
                output = "\n".join(full_exc)
                idx = 0
                while len(output) >= 1990:
                    idx -= 1
                    output = "\n".join(full_exc[:idx])
                output = f"```{output}```"
                await hook.send(output)

        with open('catpost.json') as file:
            data = json.load(file)
        self._cached_ids = data
        self.store_catposts.start()

        return await super().connect(reconnect=reconnect)

    async def before_invoke(self, ctx: NewCtx):
        """Nothing too important"""
        await ctx.trigger_typing()

    # ! Discord stuff
    async def get_context(self, message: discord.Message, *, cls=None):
        """Custom context stuff hahayes"""
        return await super().get_context(message, cls=cls or NewCtx)

    async def get_prefix(self, message):

        if message.guild:
            ret = self.prefixes.get(message.guild.id)
            if not ret:
                if ret := await self.pool.fetchval(
                    "SELECT prefixes FROM guild_config WHERE guild_id = $1",
                    message.guild.id,
                ):
                    self.prefixes[message.guild.id] = ret
                else:
                    await self.pool.execute(
                        """INSERT INTO guild_config (guild_id, prefixes)
                                                VALUES ($1, $2)
                                                ON CONFLICT (guild_id)
                                                DO UPDATE SET prefixes = $2;""",
                        message.guild.id,
                        [config.PREFIX],
                    )
                    self.prefixes[message.guild.id] = [config.PREFIX]
            return self.prefixes[message.guild.id]

        else:
            return config.PREFIX

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
        return getattr(self, '_pool', None)

    async def close(self):
        with open('catpost.json', 'w') as file:
            json.dump(self._cached_ids, file, indent=4)
        await super().close()

    @tasks.loop(hours=5)
    async def store_catposts(self):
        with open('catpost.json', 'w') as file:
            json.dump(self._cached_ids, file, indent=4)

    @store_catposts.before_loop
    async def pre_store(self):
        await self.wait_until_ready()



if __name__ == "__main__":
    allowed_mentions = discord.AllowedMentions(everyone=False, users=True, roles=False)
    bot = Bot(command_prefix=config.PREFIX, allowed_mentions=allowed_mentions)
    bot.run(config.BOT_TOKEN)
