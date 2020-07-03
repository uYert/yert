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

import contextlib
import inspect
import itertools

from datetime import datetime
from textwrap import dedent
from time import perf_counter

import discord
from discord.ext import commands, menus

import config
import main
from main import NewCtx
from utils.formatters import BetterEmbed
from utils.converters import BetterUserConverter, CommandConverter

checked_perms = ['is_owner', 'guild_only', 'dm_only', 'is_nsfw']
checked_perms.extend([p[0] for p in discord.Permissions()])


def retrieve_checks(command: commands.Command):
    req = []
    with contextlib.suppress(Exception):
        for line in inspect.getsource(command.callback).splitlines():
            for permi in checked_perms:
                if permi in line and line.lstrip().startswith('@'):
                    req.append(permi)
    return ', '.join(req)


class SrcPages(menus.ListPageSource):
    def __init__(self, data):
        super().__init__(data, per_page=1950)

    async def format_page(self, menu, entries):
        out = '```py\n'
        out += ''.join(entries).replace('```', '\u200b`\u200b`\u200b`')
        out += '\n```'
        return out


class UserInfo:
    def __init__(self, user):
        self.user = user

    @property
    def is_nitro(self):
        if isinstance(self.user, discord.Member) and self.user.premium_since:
            return True
        elif self.user.is_avatar_animated():
            return True
        return False


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
        description += "\n".join([f'{"⇶" if isinstance(command, commands.Group) else "⇾"} **{command.name}** -'
                                  f' {command.short_doc or "No description"}' for command in entries])
        embed.description = description
        footer_text = '⇶ indicates subcommands'
        if checks := retrieve_checks(group):
            footer_text += f' | Checks: {checks}'
        embed.set_footer(text=footer_text)
        await self.context.send(embed=embed)


class Meta(commands.Cog):
    """Bot-related commands"""

    def __init__(self, bot):
        self.bot = bot
        self.old_help = self.bot.help_command
        self.bot.help_command = EmbeddedHelpCommand()
        self.bot.help_command.cog = self
        self.git_cache = None

    def cog_unload(self):
        self.bot.help_command = self.old_help

    @commands.command(name='source', aliases=['src', 's'])
    async def _source(self, ctx: NewCtx, target: CommandConverter = None):
        """Shows the source code for a given command, or general information if a command name isn't provided"""
        if target:
            source_lines = inspect.getsource(target.callback)
            pages = menus.MenuPages(source=SrcPages(source_lines), clear_reactions_after=True)
            await pages.start(ctx)
        else:
            await self.bot.get_command('about')(ctx)

    async def get_profiles(self):
        # Because the endpoint gives data that is a few hours old, we will get it each 4 hours
        # so that it's somewhat correct
        if self.git_cache is None or (datetime.now() - self.git_cache[-1]).hours >= 4:
            async with self.bot.session.get("https://api.github.com/repos/uYert/yert/contributors",
                                            params={"anon": "true"}) as repo_info:
                self.git_cache = await repo_info.json()
                self.git_cache.append(datetime.now())
        return self.git_cache[:-1]

    @commands.command()
    async def about(self, ctx: NewCtx):
        """ This is the 'about the bot' command. """
        # Github id of the contributors and their corresponding discord id
        DISCORD_GIT_ACCOUNTS = {
            64285270: 361158149371199488, 
            16031716: 155863164544614402,
            4181102: 273035520840564736,
            54324533: 737985288605007953,
            60761231: 723268667579826267,
        }

        contributors = ""
        for contributor in await self.get_profiles():
            if contributor["type"] == "Anonymous":
                contributor["login"] = contributor["name"]
                discord_profile = "unknown"
            else:
                discord_profile = DISCORD_GIT_ACCOUNTS.get(contributor["id"], "unkown")
                if discord_profile != "unknown":
                    discord_profile = self.bot.get_user(discord_profile)
            contributors += f"{contributor['login']}({str(discord_profile)}): \
                            **{contributor['contributions']}** commits.\n"

        humans = sum([1 for user in self.bot.users if not user.bot])

        embed = BetterEmbed(title=f"About {ctx.guild.me.display_name}")
        embed.description = "A ~~shit~~ fun bot that was thrown together by a team of complete nincompoops."
        embed.set_author(name=ctx.me.display_name, icon_url=ctx.me.avatar_url)
        embed.add_field(name="Contributors", value=contributors, inline=False)
        embed.add_field(name="Current guilds",
                        value=f'{len(self.bot.guilds):,}', inline=False)
        embed.add_field(name="Total fleshy people being memed",
                        value=f'{humans:,}', inline=False)
        embed.add_field(name='Come check out our source at',
                        value='https://github.com/uYert/yert', inline=False)
        await ctx.send(embed=embed)

    @commands.command()
    async def ping(self, ctx: NewCtx):
        sabertooth_tiger = perf_counter()
        m = await ctx.send('_ _')
        endocrine_title = perf_counter()
        await m.edit(content='', embed=BetterEmbed(
            description=f'**API** {endocrine_title-sabertooth_tiger:.2f}s\n**WS** {(self.bot.latency*2):.2f}s'
        ))

    @commands.command()
    async def suggest(self, ctx: NewCtx, *, suggestion: str):
        if len(suggestion) >= 1000:
            raise commands.BadArgument(message="Cannot forward suggestions longer than 1000 characters")

        embed = BetterEmbed(title='Suggestion', description=suggestion)

        fields = (
            ('Guild', f"{ctx.guild.name} ({ctx.guild.id})"),
            ('Channel', f"{ctx.channel.name} ({ctx.channel.id})"),
            ('User', f"{ctx.author} ({ctx.author.id})")
        )

        channel = self.bot.get_channel(config.SUGGESTION)
        await channel.send(embed=embed.add_fields(fields))

        await ctx.send('Thank you for your suggestion')


def setup(bot):
    """ Cog entry point """
    bot.add_cog(Meta(bot))
