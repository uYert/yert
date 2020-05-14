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

import discord
import pathlib
import config
from typing import Optional
from discord.ext import commands

class CustomContext(commands.Context):
    """Custom context for extra functions"""

    def __init__(self, **attrs):
        super().__init__(**attrs)

    async def webhook_send(self, content: str, *, webhook: discord.Webhook, skip_wh: bool = False, skip_ctx: bool = False) -> None:
        if not skip_ctx:
            await super().send(content=content)
        if not skip_wh:
            await webhook.send("{0} was sent to {1.guild.name}:{1.channel.name} attempting to invoke {1.invoked_with}".format(content, self))
        

class Bot(commands.Bot):
    def __init__(self, **options):
        super().__init__(**options)
        
        for file in pathlib.Path('extensions').glob('**/*.py'):
            *tree, _ = file.parts 
            self.load_extension('.'.join(tree) + '.' + file.stem)  # fstrings would be ugly there 
        
    async def get_context(self, message: discord.Message, *, cls=None):
        return await super().get_context(message, cls=cls or CustomContext)

    
            
if __name__ == '__main__':
    Bot(command_prefix='yoink ').run(config.BOT_TOKEN, owner_ids=[273035520840564736, 361158149371199488, 155863164544614402])