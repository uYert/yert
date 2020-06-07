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

import inspect
import itertools
from contextlib import suppress
from textwrap import dedent
from time import perf_counter

import config
import discord
from discord.ext import commands
import humanize
import main

from utils.formatters import BetterEmbed
from utils.converters import BetterUserConverter

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


badge_mapping = {
    'staff': '<:staff:711628736977567776>',
    'partner': '<:partner:711628720963715096>',
    'hypesquad': '<:events:711628678748045483>',
    'hypesquad_balance': '<:balance:711628592081272943>',
    'hypesquad_bravery': '<:bravery:711628626742870026>',
    'hypesquad_brilliance': '<:brilliance:711628635152318475>',
    'bug_hunter': '<:bug1:711628644518461540>',
    'bug_hunter_level_2': '<:bug2:711628652340707408>',
    'verified_bot_developer': '<:dev:711628661077573644>',
    'early_supporter': '<:early:711628670032150568>'
}

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

    def cog_unload(self):
        self.bot.help_command = self.old_help

    @commands.command()
    async def about(self, ctx):
        """ This is the 'about the bot' command. """
        description = dedent(f"""\
                             A ~~shit~~ fun bot that was thrown together by a team of complete nincompoops.
                             In definitely no particular order:\n
                            {', '.join([self.bot.get_user(i).__str__() for i in self.bot.owner_ids])}
                             """)
        # uniq_mem_count = set(
        #     member for member in guild.members if not member.bot for guild in self.bot.guilds) #! TODO fix set comp
        uniq_mem_count = set()
        for guild in self.bot.guilds:
            for member in guild.members:
                if not member.bot:
                    uniq_mem_count.add(member)

        # {member for member in ctx.bot.get_all_members() if not member.bot}

        embed = BetterEmbed(title=f"About {ctx.guild.me.display_name}")
        embed.description = description
        embed.set_author(name=ctx.me.display_name, icon_url=ctx.me.avatar_url)
        embed.add_field(name="Current guilds",
                        value=f'{len(self.bot.guilds):,}')
        embed.add_field(name="Total fleshy people being memed",
                        value=f'{len(uniq_mem_count):,}')
        await ctx.send(embed=embed)

    @commands.command()
    async def ping(self, ctx):
        sabertooth_tiger = perf_counter()
        m = await ctx.send('_ _')
        endocrine_title = perf_counter()
        await m.edit(embed=BetterEmbed(
            description=f'**API** {endocrine_title-sabertooth_tiger:.2f}s\n**WS** {self.bot.latency:.2f}s'
        ))

    @commands.command()
    async def userinfo(self, ctx, *, user = None):
        user = (await BetterUserConverter().convert(ctx, user)).obj
        flags = [flag for flag, value in [*user.public_flags] if value]
        user_info = UserInfo(user)
        badges = [badge_mapping.get(f) for f in flags]
        if user_info.is_nitro:
            badges.append('<:nitro:711628687455420497>')
        embed = BetterEmbed(
            title=user.__str__(), description=' '.join(badges))\
            .set_thumbnail(url=user.avatar_url_as(static_format='png'))
        embed.add_field(name='Info', value=f'Account Created: {humanize.naturaltime(user.created_at)}')
        await ctx.send(embed=embed)
        
    @commands.command()
    async def suggest(self, ctx: main.NewCtx, *, suggestion: str):
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

        with suppress(discord.DiscordException):
            await ctx.message.delete()
        
        await ctx.send('Thank you for your suggestion')


def setup(bot):
    """ Cog Entrypoint """
    bot.add_cog(Meta(bot))
