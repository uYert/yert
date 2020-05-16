"""
MIT License

Copyright (c) 2020 - Sudosnok, AbstractUmbra, Nickofolas, Saphielle-Akiyama

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
import inspect
import itertools
from contextlib import suppress

import discord
from discord.ext import commands

from utils.formatters import BetterEmbed

checked_perms = ['is_owner', 'guild_only', 'dm_only', 'is_nsfw']
checked_perms.extend([p[0] for p in discord.Permissions()])


def retrieve_checks(command):
    req = []
    with suppress(Exception):
        for line in inspect.getsource(command.callback).splitlines():
            for permi in checked_perms:
                if permi in line and line.lstrip().startswith('@'):
                    req.append(permi)
    return ', '.join(req)


class EmbeddedHelpCommand(commands.HelpCommand):
    def __init__(self):
        super().__init__(command_attrs={
            'help': 'Shows help for the bot, a category, or a command.',
            'cooldown': commands.Cooldown(1, 2.5, commands.BucketType.user)
        })

    def get_command_signature(self, command):
        parent = command.full_parent_name
        if len(command.aliases) > 0:
            aliases = '|'.join(command.aliases)
            fmt = f'{command.name}|{aliases}'
            if parent:
                fmt = f'{parent} {fmt}'
            alias = fmt
        else:
            alias = command.name if not parent else f'{parent} {command.name}'
        return f'{self.clean_prefix}{alias} {command.signature}'

    async def send_bot_help(self, mapping):
        def key(c):
            return c.cog_name or '\u200bUncategorized'
        bot = self.context.bot
        embed = BetterEmbed(title=f'{bot.user.name} Help')
        description = f'Use `{self.clean_prefix}help <command/category>` for more help\n\n'
        entries = await self.filter_commands(bot.commands, sort=True, key=key)
        for cog, cmds in itertools.groupby(entries, key=key):
            cmds = sorted(cmds, key=lambda c: c.name)
            description += f'**➣ {cog}**\n{" • ".join([c.name for c in cmds])}\n'
        embed.description = description
        await self.context.send(embed=embed)

    async def send_cog_help(self, cog):
        embed = BetterEmbed(title=f'{cog.qualified_name} Category')\
            .set_footer(text='⇶ indicates subcommands')
        description = f'{cog.description or ""}\n\n'
        entries = await self.filter_commands(cog.get_commands(), sort=True)
        description += "\n".join([f'{"⇶" if isinstance(c, commands.Group) else "⇾"} **{c.name}** -'
                                  f' {c.short_doc or "No description"}' for c in entries])
        embed.description = description
        await self.context.send(embed=embed)

    async def send_command_help(self, command):
        embed = BetterEmbed(title=self.get_command_signature(command))
        description = f'{command.help or "No description provided"}\n\n'
        embed.description = description
        if c := retrieve_checks(command):
            embed.set_footer(text=f'Checks: {c}')
        await self.context.send(embed=embed)

    async def send_group_help(self, group):
        embed = BetterEmbed(title=self.get_command_signature(group))
        description = f'{group.help or "No description provided"}\n\n'
        entries = await self.filter_commands(group.commands, sort=True)
        description += "\n".join([f'{"⇶" if isinstance(c, commands.Group) else "⇾"} **{c.name}** -'
                                  f' {c.short_doc or "No description"}' for c in entries])
        embed.description = description
        footer_text = '⇶ indicates subcommands'
        if c := retrieve_checks(group):
            footer_text += f' | Checks: {c}'
        embed.set_footer(text=footer_text)
        await self.context.send(embed=embed)


class Meta(commands.Cog):
    """Bot-related commands"""

    def __init__(self, bot):
        self.bot = bot
        self.old_help = self.bot.help_command
        self.bot.help_command = EmbeddedHelpCommand()
        self.bot.help_command.cog = self

    def cog_unload(self):
        self.bot.help_command = self.old_help


def setup(bot):
    """ Cog Entrypoint """
    bot.add_cog(Meta(bot))
