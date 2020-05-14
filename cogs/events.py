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

from inspect import signature
from datetime import datetime
import traceback
import typing

import discord
from discord import Message
from discord.ext import commands

import config


class Events(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

        self.WEBHOOK = self.webhook()
        self.IGNORED = [commands.CommandNotFound, ]

    async def bot_check_once(self, ctx):
        return await self.bot.is_owner(ctx.author)

    def webhook(self) -> discord.Webhook:
        wh_id, wh_token = config.WEBHOOK
        hook = discord.Webhook.partial(
            id=wh_id, token=wh_token, adapter=discord.AsyncWebhookAdapter(self.bot.session))
        return hook

    def fmt(self, dt: datetime):
        return dt.strftime("%Y %b %d: %H:%M:%S:%f")

    async def any_role_converter(self, ctx: commands.Context, args: typing.Sequence[typing.Union[int, str]]) -> typing.Sequence[str]:
        for idx, item in enumerate(args):
            if isinstance(item, int):
                args[idx] = await commands.RoleConverter().convert(ctx, str(item))
        return args

    @commands.command()
    @commands.is_owner()
    async def edit_ignored(self, ctx: commands.Context, mode: str, *args: typing.Sequence[str]) -> None:
        """Adds or removes an exception from the list of exceptions to ignore, if you want to add or remove commands.MissingRole, be sure to exclude the 'commands.'"""
        assert mode in ['add', 'remove'], "You entered an invalid mode."
        for arg in args:
            if hasattr(commands, arg):

                if mode == 'add':
                    if getattr(commands, arg) not in self.IGNORED:
                        self.IGNORED.append(getattr(commands, arg))
                    else:
                        await ctx.webhook_send("commands.{0} is already in the list of ignored exceptions".format(arg))

                elif mode == 'remove':
                    try:
                        self.IGNORED.pop(self.IGNORED.index(
                            getattr(commands, arg)))
                    except ValueError:
                        await ctx.webhook_send("{0} not in the ignored list of exceptions".format(arg))
            else:
                raise AttributeError(
                    "commands module has no attribute {0}, command aborted".format(arg))

    @commands.Cog.listener()
    async def on_ready(self):
        pass

    @commands.Cog.listener()
    async def on_message(self, message: Message):
        pass

    @commands.Cog.listener()
    async def on_command(self, ctx: commands.Context):
        pass

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error: Exception):
        if hasattr(ctx.command, 'on_error'):
            return

        if isinstance(error, tuple(self.IGNORED)):
            return

        error = getattr(error, 'original', error)
        if isinstance(error, commands.MissingPermissions):
            message = "{0.mention}, you're missing the following persissions to use that command; {1.missing_perms}".format(
                ctx.author, error)
            return await ctx.webhook_send(message, webhook=self.WEBHOOK)

        if isinstance(error, commands.BotMissingPermissions):
            message = "{0.mention}, I'm missing permissions for that command; {1.missing_perms}".format(
                ctx.author, error)
            return await ctx.webhook_send(message, webhook=self.WEBHOOK)

        if isinstance(error, commands.CommandOnCooldown):
            message = "{0.mention}, that command is on cooldown for another {1.retry_after}s".format(
                ctx.author, error)
            return await ctx.webhook_send(message, webhook=self.WEBHOOK, skip_ctx=True)

        if isinstance(error, commands.MissingRequiredArgument):
            message = "{0.mention}, you were missing at least one argument from that command; {1.param}".format(
                ctx.author, error)
            return await ctx.webhook_send(message, webhook=self.WEBHOOK)

        if isinstance(error, commands.BadArgument):
            bad_argument = list(ctx.command.clean_params)[len(
                ctx.args[2:] if ctx.command.cog else ctx.args[1:])]
            bad_typehint = signature(
                ctx.command.__call__).parameters[bad_argument].annotation
            message = "{0.mention}, argument {1} was expecting {2}".format(
                ctx.author, bad_argument, bad_typehint)
            return await ctx.webhook_send(message, webhook=self.WEBHOOK)

        if isinstance(error, commands.BadUnionArgument):
            bad_argument = error.param
            bad_typehints = error.converters
            message = "{0.mention}, argument {1} was expecting {2}".format(
                ctx.author, bad_argument, *bad_typehints)
            return await ctx.webhook_send(message, webhook=self.WEBHOOK)

        if isinstance(error, commands.MaxConcurrencyReached):
            max_conc = error.number
            message = "{0.author.mention}, {0.command.name} has reached maximum concurrent uses at {1}".format(
                ctx, max_conc)
            return await ctx.webhook_send(message, webhook=self.WEBHOOK)

        if isinstance(error, commands.MissingRole):
            if isinstance(error.role, int):
                role_name = commands.RoleConverter().convert(ctx, str(error.missing_role))
            else:
                role_name = error.missing_role
            message = "{0.mention}, you're missing the role {1}".format(
                ctx.author, role_name)
            return await ctx.webhook_send(message, webhook=self.WEBHOOK)

        if isinstance(error, commands.BotMissingRole):
            if isinstance(error.role):
                role_name = commands.RoleConverter().convert(ctx, str(error.missing_role))
            else:
                role_name = error.missing_role
            message = "{0.mention}, I'm missing the role {1}".format(
                ctx.author, role_name)
            return await ctx.webhook_send(message, webhook=self.WEBHOOK)

        if isinstance(error, commands.MissingAnyRole):
            role_names = await self.any_role_converter(ctx, error.missing_roles)
            message = "{0.mention}, you're missing these roles for that command {1}".format(
                ctx.author, ', '.join(role_names))
            return await ctx.webhook_send(message, webhook=self.WEBHOOK)

        if isinstance(error, commands.BotMissingAnyRole):
            role_names = await self.any_role_converter(ctx, error.missing_roles)
            message = "{0.mention}, I'm missing these roles for {1}".format(
                ctx.author, ', '.join(role_names))
            return await ctx.webhook_send(message, webhook=self.WEBHOOK)

        if isinstance(error, commands.ConversionError):
            converter_name = error.converter.__name__
            cause = error.__cause__
            message = "{0.mention}, a conversion error occured with the {1} due to {2}".format(
                ctx.author, converter_name, cause)
            return await ctx.webhook_send(message, webhook=self.WEBHOOK)

        if isinstance(error, AssertionError):
            message = "AssertionError : {0}".format(error.args[0])
            return await ctx.webhook_send(message, webhook=self.WEBHOOK, skip_ctx=True)

        else:
            tb = traceback.format_exception(
                type(error), error, error.__traceback__)
            message = "\n".join(tb)
            idx = 0
            while len(message) >= 1990:
                idx -= 1
                message = "\n".join(tb[:idx])
            message = "```{0}```".format(message)
            return await ctx.webhook_send(message, webhook=self.WEBHOOK)

    @commands.Cog.listener()
    async def on_command_completion(self, ctx: commands.Context):
        pass


def setup(bot):
    bot.add_cog(Events(bot))
