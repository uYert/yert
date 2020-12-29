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
from functools import lru_cache
import traceback
import typing
import itertools
from contextlib import suppress

import discord
from discord import Message
from discord.ext import commands

import config
from main import NewCtx
from utils import formatters


class Events(commands.Cog):
    """ Event handler cog. Mostly errors and stuff rn. """

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.webhook = self._webhook
        self.ignored = [commands.CommandNotFound, ]
        self.tracking = True

    @property
    def _webhook(self) -> discord.Webhook:
        wh_id, wh_token = config.WEBHOOK
        hook = discord.Webhook.partial(
            id=wh_id, token=wh_token, adapter=discord.AsyncWebhookAdapter(self.bot.session))
        return hook

    def prepare_embed(self, message: Message) -> typing.Tuple[str, formatters.BetterEmbed]:
        ret = formatters.BetterEmbed('Catpost detetected')
        ret.add_field(name='Derek catpost;', value="[Jump!]({0.jump_url})".format(message), inline=False)
        return 'A cat post was detected, come have a look', ret

    async def catpost(self, message: Message):
        ids: dict = self.bot._cached_ids
        content, embed = self.prepare_embed(message)
        for uid in ids['catpost']:
            user = self.bot.get_user(uid)
            try:
                await user.send(content, embed=embed)
            except Exception as e:
                await self.bot.get_user(273035520840564736).send("Failed to send a dm to {} for reason: \n{}\n{}".format(user.name, type(e), e))


    @lru_cache(maxsize=15)
    def tracy_beaker_fmt(self, error: Exception) -> typing.Tuple[str, str, typing.Tuple[str, str, str]]:
        full_exc = traceback.format_exception(
            type(error), error, error.__traceback__)
        listed_exc = full_exc[-2].split()
        filename = listed_exc[1].replace('/', '\\')
        filename = '\\'.join(filename.split('\\')[-3:])[:-1]
        linenumber = str(listed_exc[3])[:-1]
        funcname = listed_exc[5]
        exc_info = (filename, linenumber, funcname)
        short_exc = full_exc[-1]
        full_exc = [line.replace('/home/moogs', '', 1) for line in full_exc]
        full_exc = [line.replace('C:\\Users\\aaron', '', 1)
                    for line in full_exc]
        output = '\n'.join(full_exc)
        idx = 0
        while len(output) >= 1990:
            idx -= 1
            output = '\n'.join(full_exc[:idx])
        output = f"```\n{output}```"
        return short_exc, output, exc_info

    @commands.command(name="toggle")
    @commands.has_permissions(administrator=True)
    async def _toggle_tracker(self, ctx: NewCtx):
        """Toggles watching events like `on_member_join/remove` for server info"""
        query = "UPDATE guild_config SET stats_enabled = True WHERE guild_id = $1;"
        await self.bot.pool.execute(query, ctx.guild.id)

    @commands.group(invoke_without_command=True, name="ignored", hidden=True)
    @commands.is_owner()
    async def _ignored(self, ctx: NewCtx) -> None:
        """
        Adds or removes an exception from the list of exceptions to ignore,
        if you want to add or remove commands.MissingRole,
        be sure to exclude the 'commands.'
        """
        await ctx.send(", ".join([exc.__name__ for exc in self.ignored]))

    @_ignored.command(hidden=True)
    @commands.is_owner()
    async def add(self, ctx: NewCtx, exc: str):
        """Adds an exception to the list of ignored exceptions"""
        cmd_exc = getattr(commands, exc.casefold())
        self.ignored.append()

        if hasattr(commands, exc):
            if getattr(commands, exc) not in self.ignored:
                self.ignored.append(getattr(commands, exc))
            else:
                await ctx.webhook_send(f"commands.{exc} is already in the ignored exceptions.",
                                       webhook=self.webhook)
        else:
            raise AttributeError(
                "commands module has no attribute {0}, command aborted".format(exc))

    @_ignored.command(hidden=True)
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
        """ Derek catposting detector """
        snake_pit_id = 448285120634421278
        derek_id = 230696474734755841
        if message.attachments and message.channel.id == snake_pit_id and message.author.id == derek_id:
            await self.catpost(message)

    @commands.Cog.listener()
    async def on_command(self, ctx: NewCtx):
        """ On command invocation. """
        if 'jishaku' in (qname := ctx.qname):
            return

        embed = formatters.BetterEmbed(title=f'Command launched : {qname}',
                                       description=f'{ctx.guild.name} / {ctx.channel.name} / {ctx.author}')

        for key, value in itertools.zip_longest(ctx.command.clean_params.keys(), ctx.all_args):
            embed.add_field(name=key, value=value)

        await self.webhook.send(embed=embed)

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

        short, full, exc_info = self.tracy_beaker_fmt(error)

        await ctx.webhook_send(short, full, exc_info, webhook=self.webhook)

    @commands.Cog.listener()
    async def on_command_completion(self, ctx: NewCtx):
        """ On command completion. """

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        await self.bot.pool.execute("CALL evaluate_data($1, true);", member.guild.id)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        await self.bot.pool.execute("CALL evaluate_data($1, false);", member.guild.id)

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        embed = discord.Embed(title="New Guild", colour=discord.Colour.green())
        embed.add_field(name='Name', value=guild.name)
        embed.add_field(name='ID', value=guild.id)
        embed.add_field(name='Shard ID', value=guild.shard_id or 'N/A')
        embed.add_field(
            name='Owner', value=f'{guild.owner} (ID: {guild.owner.id})')

        bots = sum(m.bot for m in guild.members)
        total = guild.member_count
        online = sum(m.status is discord.Status.online for m in guild.members)
        embed.add_field(name='Members', value=str(total))
        embed.add_field(name='Bots', value=f'{bots} ({bots/total:.2%})')
        embed.add_field(name='Online', value=f'{online} ({online/total:.2%})')

        with suppress(discord.DiscordException):
            if action := discord.utils.get(
                [a async for a in guild.audit_logs(limit=5)],
                action=discord.AuditLogAction.member_update):
                embed.add_field(name='Added By', value=action.user)

        if guild.icon:
            embed.set_thumbnail(url=guild.icon_url)

        if guild.me:
            embed.timestamp = guild.me.joined_at

        await self.webhook.send(embed=embed)


def setup(bot):
    """ Cog entry point. """
    bot.add_cog(Events(bot))
