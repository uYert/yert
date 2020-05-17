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
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR
"""

import os
from textwrap import dedent
from typing import Union

from aiohttp import ClientSession
import discord
from discord.ext import commands

import config


for env in ('NO_UNDERSCORE', 'NO_DM_TRACEBACK', 'HIDE', 'RETAIN'):
    os.environ['JISHAKU_' + env] = 'True'

COGS = (
    "jishaku",
    "cogs.events",
    "cogs.games",
    "cogs.images",
    "cogs.memes",
    "cogs.meta",
    "cogs.moderation"
)


class CustomContext(commands.Context):
    """Custom context for extra functions"""
    def __init__(self, **attrs):  # typehinted copypaste of the default init
        self.message: Union[discord.Message, None] = attrs.pop('message', None)
        self.bot: Union[Bot, None] = attrs.pop('bot', None)

        self.args: list = attrs.pop('args', [])
        self.kwargs: dict = attrs.pop('kwargs', {})
        self.prefix: str = attrs.pop('prefix')
        self.command: Union[commands.Command, None] = attrs.pop('command', None)

        self.view = attrs.pop('view', None)  # no idea about what that is

        self.invoked_with: str = attrs.pop('invoked_with', None)
        self.invoked_subcommand: commands.Command = attrs.pop('invoked_subcommand', None)
        self.subcommand_passed: Union[str, None] = attrs.pop('subcommand_passed', None)
        self.command_failed: bool = attrs.pop('command_failed', False)

        self._state = self.message._state

        self._altered_cache_key = None
        
        super().__init__()



    async def webhook_send(self,
                           content: str,
                           *,
                           webhook: discord.Webhook,
                           skip_wh: bool = False,
                           skip_ctx: bool = False) -> None:
        """ This is a custom ctx addon for sending to the webhook and/or the ctx.channel. """
        if not skip_ctx:
            await super().send(content=content)

        if not skip_wh:
            await webhook.send(dedent(  # straight up using \n stuff might be a bit easier
                f"""\
                {content} was sent to
                {self.guild.name}:{self.channel.name}
                attempting to invoke {self.invoked_with}
                """))


class Bot(commands.Bot):
    """ Our main bot-ty bot. """

    def __init__(self, **options):
        super().__init__(**options)
        self.session = ClientSession(loop=self.loop)

        # Extension load
        for extension in COGS:
            self.load_extension(extension)

    async def get_context(self, message: discord.Message, *, cls=None):
        """Custom context stuff hahayes"""
        return await super().get_context(message, cls=cls or CustomContext)


if __name__ == '__main__':
    Bot(command_prefix='yoink ', owner_ids=config.OWNER_IDS).run(
        config.BOT_TOKEN)
