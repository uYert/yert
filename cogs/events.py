"""
MIT License

Copyright (c) 2020 - Sudosnok, AbstractUmbra, Saphielle-Akiyama, nickofolas

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
from datetime import datetime
import traceback
import typing

import discord
from discord import Message
from discord.ext import commands

import config


class Events(commands.Cog):
    """ Event handler cog. Mostly errors and stuff rn. """

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.webhook = self._webhook()

        self.ignored = [commands.CommandNotFound, ]

    def _webhook(self) -> discord.Webhook:
        wh_id, wh_token = config.WEBHOOK
        hook = discord.Webhook.partial(
            id=wh_id, token=wh_token, adapter=discord.AsyncWebhookAdapter(self.bot.session))
        return hook

    def fmt(self, daytee: datetime):
        """ Quick datetime formatter. """
        return daytee.strftime("%Y %b %d: %H:%M:%S:%f")

    async def any_role_converter(self, ctx: commands.Context,
                                 args: typing.Sequence[typing.Union[int, str]]
                                 ) -> typing.Sequence[str]:
        """ Converts to a role object. """
        for idx, item in enumerate(args):
            if isinstance(item, int):
                args[idx] = await commands.RoleConverter().convert(ctx, str(item))
        return args

    @commands.group(invoke_without_command=True, name="ignored")
    @commands.is_owner()
    async def _ignored(self, ctx: commands.Context) -> None:
        """
        Adds or removes an exception from the list of exceptions to ignore,
        if you want to add or remove commands.MissingRole,
        be sure to exclude the 'commands.'
        """
        await ctx.send(", ".join([exc.__name__ for exc in self.ignored]))

    @_ignored.command()
    @commands.is_owner()
    async def add(self, ctx: commands.Context, exc: str):
        """Adds an exception to the list of ingored exceptions"""
        if hasattr(commands, exc):
            if getattr(commands, exc) not in self.ignored:
                self.ignored.append(getattr(commands, exc))
            else:
                await ctx.webhook_send(f"commands.{exc} is already in the ignored exceptions.")
        else:
            raise AttributeError(
                "commands module has no attribute {0}, command aborted".format(exc))

    @_ignored.command()
    @commands.is_owner()
    async def remove(self, ctx: commands.Context, exc: str):
        """Removes an exception from the list of ingored exceptions"""
        if hasattr(commands, exc):
            try:
                self.ignored.pop(self.ignored.index(
                    getattr(commands, exc)))
            except ValueError:
                await ctx.webhook_send("{0} not in the ignored list of exceptions".format(exc))
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
    async def on_command(self, ctx: commands.Context):
        """ On command invokation. """

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error: Exception):
        """ On command errors. """
        if hasattr(ctx.command, 'on_error'):
            return

        if isinstance(error, tuple(self.ignored)):
            return

        error = getattr(error, 'original', error)

        if isinstance(error, commands.MissingPermissions):
            message = (f"{ctx.author.mention}, you're missing the "
                       f"following persissions to use that command; {error.missing_perms}")
            return await ctx.webhook_send(message, webhook=self.webhook)

        if isinstance(error, commands.BotMissingPermissions):
            message = (f"{ctx.author.mention}, I'm missing permissions "
                       f"for that command; {error.missing_perms}")
            return await ctx.webhook_send(message, webhook=self.webhook)

        if isinstance(error, commands.CommandOnCooldown):
            message = (f"{ctx.author.mention}, that command is on cooldown"
                       f" for another {error.retry_after}s.")
            return await ctx.webhook_send(message, webhook=self.webhook, skip_ctx=True)

        if isinstance(error, commands.MissingRequiredArgument):
            message = (f"{ctx.author.mention}, you were missing at least one"
                       f" argument from that command; {error.param}")
            return await ctx.webhook_send(message, webhook=self.webhook)

        if isinstance(error, commands.BadArgument):
            bad_argument = list(ctx.command.clean_params)[len(
                ctx.args[2:] if ctx.command.cog else ctx.args[1:])]
            bad_typehint = signature(
                ctx.command.callback).parameters[bad_argument].annotation
            message = "{0.mention}, argument {1} was expecting {2}".format(
                ctx.author, bad_argument, bad_typehint)
            return await ctx.webhook_send(message, webhook=self.webhook)

        if isinstance(error, commands.BadUnionArgument):
            bad_argument = error.param
            bad_typehints = error.converters
            message = "{0.mention}, argument {1} was expecting {2}".format(
                ctx.author, bad_argument, *bad_typehints)
            return await ctx.webhook_send(message, webhook=self.webhook)

        if isinstance(error, commands.MaxConcurrencyReached):
            max_conc = error.number
            message = (f"{ctx.author.mention}, {ctx.command.name} has reached"
                       f" maximum concurrent uses at {max_conc}")
            return await ctx.webhook_send(message, webhook=self.webhook)

        if isinstance(error, commands.MissingRole):
            if isinstance(error.role, int):
                role_name = commands.RoleConverter().convert(ctx, str(error.missing_role))
            else:
                role_name = error.missing_role
            message = "{0.mention}, you're missing the role {1}".format(
                ctx.author, role_name)
            return await ctx.webhook_send(message, webhook=self.webhook)

        if isinstance(error, commands.BotMissingRole):
            if isinstance(error.role, int):  # ! what
                role_name = commands.RoleConverter().convert(ctx, str(error.missing_role))
            else:
                role_name = error.missing_role
            message = "{0.mention}, I'm missing the role {1}".format(
                ctx.author, role_name)
            return await ctx.webhook_send(message, webhook=self.webhook)

        if isinstance(error, commands.MissingAnyRole):
            role_names = await self.any_role_converter(ctx, error.missing_roles)
            message = "{0.mention}, you're missing these roles for that command {1}".format(
                ctx.author, ', '.join(role_names))
            return await ctx.webhook_send(message, webhook=self.webhook)

        if isinstance(error, commands.BotMissingAnyRole):
            role_names = await self.any_role_converter(ctx, error.missing_roles)
            message = "{0.mention}, I'm missing these roles for {1}".format(
                ctx.author, ', '.join(role_names))
            return await ctx.webhook_send(message, webhook=self.webhook)

        if isinstance(error, commands.ConversionError):
            converter_name = error.converter.__name__
            cause = error.__cause__
            message = "{0.mention}, a conversion error occured with the {1} due to {2}".format(
                ctx.author, converter_name, cause)
            return await ctx.webhook_send(message, webhook=self.webhook)

        if isinstance(error, AssertionError):
            message = "AssertionError : {0}".format(error.args[0])
            return await ctx.webhook_send(message, webhook=self.webhook, skip_ctx=True)

        else:
            tracy_beaker = traceback.format_exception(
                type(error), error, error.__traceback__)
            message = "\n".join(tracy_beaker)
            idx = 0
            while len(message) >= 1990:
                idx -= 1
                message = "\n".join(tracy_beaker[:idx])
            message = "```{0}```".format(message)
            return await ctx.webhook_send(message, webhook=self.webhook)

    @commands.Cog.listener()
    async def on_command_completion(self, ctx: commands.Context):
        """ On command completion. """


def setup(bot):
    """ Cog entrypoint. """
    bot.add_cog(Events(bot))
