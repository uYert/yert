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
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR
"""

import pathlib
import os
from textwrap import dedent

from aiohttp import ClientSession
import discord
from discord.ext import commands

import config

os.environ["JISHAKU_NO_UNDERSCORE"] = "True"
os.environ["JISHAKU_NO_DM_TRACEBACK"] = "True"
os.environ["JISHAKU_HIDE"] = "True"
os.environ["JISHAKU_RETAIN"] = "True"


class CustomContext(commands.Context):
    """Custom context for extra functions"""

    # def __init__(self, **attrs):
    #     super().__init__(**attrs)

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
            await webhook.send(dedent(
                f"""\
                {content} was sent to
                {self.guild.name}:{self.channel.name}
                attempting to invoke {self.invoked_with}"""))


class Bot(commands.Bot):
    def __init__(self, **options):
        super().__init__(**options)
        self.session = ClientSession(loop=self.loop)

        for file in pathlib.Path('cogs').glob('**/*.py'):
            *tree, _ = file.parts
            # fstrings would be ugly there
            self.load_extension('.'.join(tree) + '.' + file.stem)

        # Jishaku load
        self.load_extension("jishaku")

    async def get_context(self, message: discord.Message, *, cls=None):
        return await super().get_context(message, cls=cls or CustomContext)


if __name__ == '__main__':
    Bot(command_prefix='yoink ', owner_ids=config.OWNER_IDS).run(
        config.BOT_TOKEN)
