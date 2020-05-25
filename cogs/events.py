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

from inspect import signature
import traceback
import typing

import discord
from discord import Message
from discord.ext import commands

import config
from main import NewCtx


class Events(commands.Cog):
    """ Event handler cog. Mostly errors and stuff rn. """

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.webhook = self._webhook

        self.ignored = [commands.CommandNotFound, ]

    @property
    def _webhook(self) -> discord.Webhook:
        wh_id, wh_token = config.WEBHOOK
        hook = discord.Webhook.partial(
            id=wh_id, token=wh_token, adapter=discord.AsyncWebhookAdapter(self.bot.session))
        return hook

    def tracy_beaker_fmt(self, error: Exception) -> typing.Tuple[str, str]:
        full_exc = traceback.format_exception(type(error), error, error.__traceback__)
        short_exc = full_exc[-1]
        full_exc = [line.replace('/home/moogs', '', 1) for line in full_exc]
        full_exc = [line.replace('C:\\Users\\aaron', '', 1) for line in full_exc]
        output = '\n'.join(full_exc)
        idx = 0
        while len(output) >= 1990:
            idx -= 1
            output = '\n'.join(full_exc[:idx])
        output = f"```{output}```"
        return short_exc, output

    @commands.group(invoke_without_command=True, name="ignored")
    @commands.is_owner()
    async def _ignored(self, ctx: NewCtx) -> None:
        """
        Adds or removes an exception from the list of exceptions to ignore,
        if you want to add or remove commands.MissingRole,
        be sure to exclude the 'commands.'
        """
        await ctx.send(", ".join([exc.__name__ for exc in self.ignored]))

    @_ignored.command()
    @commands.is_owner()
    async def add(self, ctx: NewCtx, exc: str):
        """Adds an exception to the list of ingored exceptions"""
        if hasattr(commands, exc):
            if getattr(commands, exc) not in self.ignored:
                self.ignored.append(getattr(commands, exc))
            else:
                await ctx.webhook_send(f"commands.{exc} is already in the ignored exceptions.",
                                       webhook=self.webhook)
        else:
            raise AttributeError(
                "commands module has no attribute {0}, command aborted".format(exc))

    @_ignored.command()
    @commands.is_owner()
    async def remove(self, ctx: NewCtx, exc: str):
        """Removes an exception from the list of ingored exceptions"""
        if hasattr(commands, exc):
            try:
                self.ignored.pop(self.ignored.index(
                    getattr(commands, exc)))
            except ValueError:
                await ctx.webhook_send("{0} not in the ignored list of exceptions".format(exc),
                                       webhook=self.webhook)
        else:
            raise AttributeError(
                "commands module has no attribute {0}, command aborted".format(exc))

    @commands.Cog.listener()
    async def on_ready(self):
        """ On websocket ready. """

    @commands.Cog.listener()
    async def on_message(self, message: Message):
        """ On any message. """

    @commands.Cog.listener()
    async def on_command(self, ctx: NewCtx):
        """ On command invokation. """

    @commands.Cog.listener()
    async def on_command_error(self, ctx: NewCtx, error: Exception):
        """ On command errors. """
        if hasattr(ctx.command, 'on_error'):
            return

        if isinstance(error, tuple(self.ignored)):
            return

        error = getattr(error, 'original', error)

        if isinstance(error, commands.CommandOnCooldown):
            if await self.bot.is_owner(ctx.author):
                return await ctx.reinvoke()

        short, full = self.tracy_beaker_fmt(error)

        await ctx.send(short)
        await self.webhook.send(full)



    @commands.Cog.listener()
    async def on_command_completion(self, ctx: NewCtx):
        """ On command completion. """


def setup(bot):
    """ Cog entry point. """
    bot.add_cog(Events(bot))
