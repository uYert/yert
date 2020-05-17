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
from io import BytesIO
import os
from random import randint
import time

from discord import Embed, File
from discord.ext import commands
from PIL import Image


class Images(commands.Cog):
    """ Image cog. Time for manipulation. """

    def __init__(self, bot):
        self.bot = bot

    def _shifter(self, attachment_bytes: bytes, size: tuple, filename: str):
        image_obj = Image.open(BytesIO(attachment_bytes))

        bands = image_obj.split()

        red_data = list(bands[0].getdata())
        green_data = list(bands[1].getdata())
        blue_data = list(bands[2].getdata())

        for i in [red_data, green_data, blue_data]:
            random_num = randint(0, len(i))
            i[random_num // 3:random_num // 2], i[random_num // 2:random_num //
                                                  3] = i[random_num // 4:random_num // 5], i[random_num // 5:random_num // 4]

        new_red = Image.new('L', size)
        new_red.putdata(red_data)

        new_green = Image.new('L', size)
        new_green.putdata(green_data)

        new_blue = Image.new('L', size)
        new_blue.putdata(blue_data)

        new_image = Image.merge('RGB', (new_red, new_green, new_blue))

        new_image.save(fp=filename)
        return

    @commands.command()
    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.max_concurrency(1, commands.BucketType.guild, wait=False)
    async def shift(self, ctx: commands.Context):
        """Shifts the RGB bands in an attached image or the author's profile picture"""
        if len(ctx.message.attachments) == 0:
            attachment_bytes = await ctx.author.avatar_url_as(size=1024, format='png').read()
            filename = ctx.author.display_name + '.png'
            file_size = (1024, 1024)

        else:
            target = ctx.message.attachments[0]
            attachment_bytes = await target.read()
            filename = target.filename
            file_size = (target.width, target.height)

        start_time = time.time()
        await self.bot.loop.run_in_executor(
            None, self._shifter, attachment_bytes, file_size, filename)
        end_time = time.time()

        new_image = File(fp=filename)
        os.remove(filename)

        embed = Embed(title="", colour=randint(0, 0xffffff))
        embed.set_footer(
            text=f"Shifting that image took : {end_time-start_time}")
        embed.set_image(url=f"attachment://{filename}")

        await ctx.send(embed=embed, file=new_image)


def setup(bot):
    """ Cog entry point. """
    bot.add_cog(Images(bot))
