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

import colorsys
from datetime import datetime
from io import BytesIO
import random
from typing import Union

from discord.ext import commands
from discord import Colour, Embed, File
from PIL import Image

from main import NewCtx
from utils.formatters import BetterEmbed

random.seed(datetime.utcnow())


class Other(commands.Cog):
	def __init__(self, bot):
		self.bot = bot


	@commands.command(name='random number', aliases=['rnum', 'num'])
	async def _rand_num(self, ctx: NewCtx, start: Union[int, float], stop: Union[int, float]):
		"""Generates a random number from start to stop inclusive, if either is a float, number will be float"""

		if isinstance(start, float) or isinstance(stop, float):
			number = random.uniform(start, stop)
		else:
			number = random.randint(start, stop)

		embed = BetterEmbed()
		embed.description = f"Number between {start} and {stop}, {number=}"

		await ctx.send(embed=embed)


	@commands.command(aliases=['d'])
	async def _dice(self, ctx: NewCtx, dice: str):
		"""Generates dice with the supplied format `NdN`"""
		dice_list = dice.split('d')
		try:
			d_count, d_value = int(dice_list[0]), int(dice_list[1])
		except ValueError:
			raise commands.BadArgument("The entered format was incorrect, `NdN` only currently")

		counter = []
		crit_s = 0; crit_f = 0
		for dice_num in range(d_count):
			randomnum = random.randint(1, d_value)
			if randomnum == d_value:
				crit_s += 1
			if randomnum == 1:
				crit_f += 1
			counter.append(randomnum)

		embed = BetterEmbed()
		embed.description = f"{dice} gave {', '.join(counter)} with {crit_s} crit successes and {crit_f} fails"

		await ctx.send(embed=embed)

	@commands.command(name = 'rc')
	async def random_colour(self, ctx: NewCtx):
		"""Generates a random colour, displaying its representation in Hex, RGB and HSV values"""
		col = Colour.from_rgb(*[random.randint(0, 255) for _ in range(3)])
		hex_v = col.value

		r, g, b = col.r, col.g, col.b
		h, s, v = colorsys.rgb_to_hsv(r, g, b)

		h = round((h * 360))
		s = round((s * 100))
		v = round((h * 100))

		image_obj = Image.new('RGB', (500, 500), (r, g, b))
		new_obj = BytesIO()
		image_obj.save(new_obj, format='png')
		fileout = File(new_obj, filename='file.png')


		embed = Embed(colour = col, title = '`Random colour : `')
		embed.description = f'Hex : {hex_v} / {hex(hex_v).replace("0x")}\nRGB : {r}, {g}, {b}\nHSV : {h}, {s}, {v//1000}'
		embed.set_image(url="attachment://file.png")
		embed.set_author(name = ctx.author.display_name, icon_url = ctx.author.avatar_url)

		await ctx.send(embed=embed, file=fileout)

def setup(bot):
	"""Cog entry point"""
	bot.add_cog(Other(bot))
