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
from random import randint
import time
from typing import Optional, Tuple

from discord import File
from discord.ext import commands
from PIL import Image, ImageChops

from main import NewCtx
from utils.formatters import BetterEmbed
from utils.converters import LinkConverter


class Images(commands.Cog):
    """ Image cog. Time for manipulation. """

    def __init__(self, bot):
        self.bot = bot


    def _shifter(self, attachment_file: BytesIO, size: Tuple[int, int]) -> BytesIO:
        image_obj = Image.open(attachment_file)

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

        out_file = BytesIO()
        new_image.save(out_file, format='PNG')
        out_file.seek(0)
        return out_file

    def _jpeg(self, attachment_file: BytesIO, severity: int) -> BytesIO:
        image_obj = Image.open(attachment_file).convert('RGB')

        out_file = BytesIO()
        image_obj.save(out_file, format='jpeg', quality=severity)
        out_file.seek(0)
        return out_file

    def _loop_jpeg(self, attachment_file: BytesIO, severity: int, loops: int) -> BytesIO:
        for _ in range(loops):
            attachment_file = self._jpeg(attachment_file, severity)
        return attachment_file

    def _diff(self, image_obj_a: Image, image_obj_b: Image) -> BytesIO:

        new_image = ImageChops.difference(image_obj_a, image_obj_b)

        out_file = BytesIO()
        new_image.save(out_file, format='PNG')
        out_file.seek(0)

        return out_file

    async def _get_image(self, ctx: NewCtx, index: int = 0) -> Tuple[BytesIO, str, Tuple[int, int]]:
        attachment_file = BytesIO()

        if not ctx.message.attachments:
            await ctx.author.avatar_url_as(size=1024, format='png').save(attachment_file)
            filename = ctx.author.display_name + '.png'
            file_size = (1024, 1024)

        else:
            target = ctx.message.attachments[index]
            await target.save(attachment_file)
            filename = target.filename
            file_size = (target.width, target.height)

        return attachment_file, filename, file_size

    def _get_dimension(self, img_bytes: BytesIO) -> Tuple[BytesIO, int]:
        image_obj = Image.open(img_bytes)
        file_size = image_obj.size
        image_obj.close()
        return img_bytes, file_size

    def _resize_avg(self, image_a: BytesIO, size_a: Tuple[int, int],
                    image_b: BytesIO, size_b: Tuple[int, int]) -> Tuple[Image, Image]:

        new_width = (size_a[0] + size_b[0]) // 2
        new_height = (size_a[1] + size_b[1]) // 2

        new_a = Image.open(image_a)
        new_a = new_a.resize((new_width, new_height))


        new_b = Image.open(image_b)
        new_b = new_b.resize((new_width, new_height))

        return new_a, new_b

    @commands.command()
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.max_concurrency(1, commands.BucketType.guild, wait=False)
    async def shift(self, ctx: NewCtx):
        """Shifts the RGB bands in an attached image or the author's profile picture"""
        attachment_file, _, file_size = await self._get_image(ctx)

        start_time = time.time()
        new_file = await self.bot.loop.run_in_executor(
            None, self._shifter, attachment_file, file_size)
        end_time = time.time()

        fileout = File(new_file, "file.png")

        embed = BetterEmbed(title='shifting done.').set_footer(
            text=f"That took {end_time-start_time:.2f}s").set_image(url="attachment://file.png")

        await ctx.send(embed=embed, file=fileout)

    @commands.command(name='morejpeg', aliases=['jpeg', 'jpegify', 'more'])
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.max_concurrency(1, commands.BucketType.guild, wait=False)
    async def morejpeg(self, ctx: NewCtx, severity: int = 15, loopyloops: int = 1):
        """Adds jpeg compression proportional to severity to an uploaded image or the author's profile picture"""

        if not (0 <= severity <= 100):
            raise commands.BadArgument(
                "severity parameter must be between 0 and 100 inclusive")
        severity = 101 - severity

        if not(1 <= loopyloops <= 200):
            raise commands.BadArgument(
                "loopyloop parameter must be between 1 and 200 inclusive")

        attachment_file, _, _ = await self._get_image(ctx)

        start_time = time.time()
        new_file = await self.bot.loop.run_in_executor(
            None, self._loop_jpeg, attachment_file, severity, loopyloops)
        end_time = time.time()

        fileout = File(new_file, 'file.jpg')

        embed = BetterEmbed(title='jpegifying done.').set_footer(
            text=f"That took {end_time-start_time:.2f}s").set_image(url="attachment://file.jpg")

        await ctx.send(embed=embed, file=fileout)

    @commands.command(name='diff')
    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.max_concurrency(1, commands.BucketType.guild, wait=False)
    async def diff(self, ctx: NewCtx, *img_bytes: Optional[LinkConverter]):
        """Returns the difference between two images"""
        if len(ctx.message.attachments) == 2:
            file_a, _, file_a_size = await self._get_image(ctx, 0)
            file_b, _, file_b_size = await self._get_image(ctx, 1)

        elif len(img_bytes) == 2:
            file_a, file_a_size = self._get_dimension(img_bytes[0])
            file_b, file_b_size = self._get_dimension(img_bytes[1])

        else:
            raise commands.BadArgument("You must pass either two attachments or two image links")

        file_a, file_b = self._resize_avg(file_a, file_a_size, file_b, file_b_size)

        start_time = time.time()
        new_file = await self.bot.loop.run_in_executor(
            None, self._diff, file_a, file_b)
        end_time = time.time()

        fileout = File(new_file, 'diff.png')

        embed = BetterEmbed(title='diffing done.').set_footer(
            text=f"That took {end_time-start_time:.2f}s").set_image(url="attachment://diff.png")

        await ctx.send(embed=embed, file=fileout)


def setup(bot):
    """ Cog entry point. """
    bot.add_cog(Images(bot))
