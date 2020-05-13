import discord
import pathlib
from discord.ext import commands

class Bot(commands.Bot):
    def __init__(self, **options):
        super().__init__(**options)
        
        for file in pathlib.Path('extensions').glob('**/*.py'):
            *tree, _ = file.parts 
            self.load_extension('.'.join(tree) + '.' + file.stem)  # fstrings would be ugly there 