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

from typing import Optional, Union

import discord
from discord.ext import commands


class Moderation(commands.Cog):
    """ Moderation cog. All things admin! """

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

        self.def_days = 7
        self.def_reason = "No reason given"

    @commands.command()
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    async def ban(self, ctx: commands.Context,
                  target: Union[discord.Member, discord.Object], days: Optional[int],
                  *, reason: Optional[str]) -> None:
        """Bans the given <target> for [reason], deleting [days] of messages"""  # that good?
        days = days or self.def_days
        reason = reason or self.def_reason
        await ctx.guild.ban(target, delete_message_days=days, reason=reason)

    @commands.command()
    @commands.has_permissions(kick_members=True)
    @commands.bot_has_permissions(kick_members=True)
    async def kick(self, ctx: commands.Context, target: discord.Member, *, reason: Optional[str]) -> None:
        """Kicks the given target for a reason"""
        reason = reason or self.def_reason
        await target.kick(reason=reason)

    @commands.command()
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    async def unban(self, ctx: commands.Context, target: int, *, reason: Optional[str]) -> None:
        """Unbans the given target"""
        reason = reason or self.def_reason
        await ctx.guild.unban(discord.Object(id=target), reason=reason)

    @commands.command()
    @commands.has_guild_permissions(mute_members=True)
    @commands.bot_has_guild_permissions(mute_members=True)
    async def mute(self, ctx: commands.Context, target: discord.Member, *, reason: Optional[str]) -> None:
        """Mutes the given target with a reason"""
        reason = reason or self.def_reason
        await target.edit(mute=True, reason=reason)

    @commands.command()
    @commands.has_guild_permissions(mute_members=True)
    @commands.bot_has_guild_permissions(mute_members=True)
    async def unmute(self, ctx: commands.Context, target: discord.Member, *, reason: Optional[str]) -> None:
        """ Unmutes the given target with optional reason. """
        reason = reason or self.def_reason
        await target.edit(mute=False, reason=reason)

    @commands.group(invoke_without_command=True)
    @commands.has_permissions(manage_roles=True)
    async def config(self, ctx):

        await ctx.send_help(ctx.command)

    @config.group(name='prefix', invoke_without_command=True)
    async def config_prefix(self, ctx):

        fmt = ', '.join(await self.bot.get_prefix(ctx.message))

        await ctx.send(f'The prefixes for `{ctx.guild}` are `{fmt}`')

    @config_prefix.command(name='set')
    @commands.has_permissions(manage_roles=True)
    async def prefix_set(self, ctx, prefix):

        self.bot.prefixes[ctx.guild.id] = [prefix]
        await ctx.send(f'Set the prefix to `{prefix}`')

    @config_prefix.command(name='add')
    @commands.has_permissions(manage_roles=True)
    async def prefix_add(self, ctx, prefix):

        if len(self.bot.prefixes[ctx.guild.id]) >= 7:

            raise commands.BadArgument('You cannot have more than 7 prefixes')

        if len(prefix) > 12:

            raise commands.BadArgument('The prefix cannot be longer than 12 characters')

        if prefix in self.bot.prefixes[ctx.guild.id]:

            raise commands.BadArgument('You cannot have the same prefix twice')

        self.bot.prefixes[ctx.guild.id].append(prefix)
        await ctx.send(f'Added `{prefix}` to the list of prefixes')

    @config_prefix.command(name='remove')
    @commands.has_permissions(manage_roles=True)
    async def prefix_remove(self, ctx, prefix):

        if len(self.bot.prefixes[ctx.guild.id]) <= 1:

            raise commands.BadArgument('You cannot remove all of your prefixes')

        prefix = [a for a in enumerate(self.bot.prefixes[ctx.guild.id]) if a[1] == prefix]
        if not prefix:
            raise commands.BadArgument('That was not a prefix')

        self.bot.prefixes[ctx.guild.id].pop(prefix[0][0])
        await ctx.send(f'Removed `{prefix[0][1]}` from the list of prefixes')


def setup(bot):
    """ Cog entrypoint. """
    bot.add_cog(Moderation(bot))
