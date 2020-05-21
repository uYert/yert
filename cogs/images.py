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
from functools import lru_cache
from io import BytesIO
from random import randint
import time
from typing import Optional, Tuple

from discord import File
from discord.ext import commands
from PIL import Image, ImageChops, ImageFilter, ImageOps

from main import NewCtx
from utils.formatters import BetterEmbed
from utils.converters import LinkConverter

FILTERS = {'blur': ImageFilter.BLUR, 'contour': ImageFilter.CONTOUR,
           'detail': ImageFilter.DETAIL, 'edge': ImageFilter.EDGE_ENHANCE,
           'moreedge': ImageFilter.EDGE_ENHANCE_MORE, 'emboss': ImageFilter.EMBOSS,
           'find': ImageFilter.FIND_EDGES, 'sharpen': ImageFilter.SHARPEN,
           'smooth': ImageFilter.SMOOTH, 'moresmooth': ImageFilter.SMOOTH_MORE}


class Images(commands.Cog):
    """ Image cog. Time for manipulation. """

    def __init__(self, bot):
        self.bot = bot

    async def embed_file(self, ctx: NewCtx, message: str, fileout: BytesIO, timediff: float, filename: str):
        fileout = File(fileout, filename)

        embed = BetterEmbed(title = message)
        embed.set_footer(text = f"That took {timediff:.2f}s")
        embed.set_image(url = "attachment://" + filename)

        await ctx.send(embed = embed, file = fileout)

    @lru_cache(maxsize=10)
    def _shifter(self, attachment_file: BytesIO, size: Tuple[int, int]) -> BytesIO:

        image_obj = Image.open(attachment_file)

        bands = image_obj.split()

        red_data = list(bands[0].getdata())
        green_data = list(bands[1].getdata())
        blue_data = list(bands[2].getdata())

        for i in [red_data, green_data, blue_data]:
            random_num = randint(0, len(i))
            low = randint(1, 15)
            high = randint(low, 30)
            i[random_num // high:random_num // low] = i[random_num // low:random_num // high]

        new_red = Image.new('L', size)
        new_red.putdata(red_data)

        new_green = Image.new('L', size)
        new_green.putdata(green_data)

        new_blue = Image.new('L', size)
        new_blue.putdata(blue_data)

        new_image = Image.merge('RGB', (new_red, new_green, new_blue))
        new_image = new_image.resize((1024, 1024))

        out_file = BytesIO()
        new_image.save(out_file, format = 'jpeg')
        out_file.seek(0)
        return out_file

    @lru_cache(maxsize = 10)
    def _jpeg(self, attachment_file: BytesIO, severity: int) -> BytesIO:
        image_obj = Image.open(attachment_file).convert('RGB')

        out_file = BytesIO()
        image_obj.save(out_file, format = 'jpeg', quality = severity)
        out_file.seek(0)
        return out_file

    def _loop_jpeg(self, attachment_file: BytesIO, severity: int, loops: int) -> BytesIO:
        for _ in range(loops):
            attachment_file = self._jpeg(attachment_file, severity)
        return attachment_file

    @lru_cache(maxsize = 10)
    def _diff(self, file_a: BytesIO, file_a_size: Tuple[int, int],
              file_b: BytesIO, file_b_size: Tuple[int, int]) -> BytesIO:

        new_width = (file_a_size[0] + file_b_size[0]) // 2
        new_height = (file_a_size[1] + file_b_size[1]) // 2

        image_obj_a = Image.open(file_a)
        image_obj_a = image_obj_a.convert('RGB')
        image_obj_a = image_obj_a.resize((new_width, new_height))

        image_obj_b = Image.open(file_b)
        image_obj_b = image_obj_b.convert('RGB')
        image_obj_b = image_obj_b.resize((new_width, new_height))

        new_image = ImageChops.difference(image_obj_a, image_obj_b)

        out_file = BytesIO()
        new_image.save(out_file, format = 'PNG')
        out_file.seek(0)

        return out_file

    @lru_cache(maxsize=10)
    async def _get_image(self, ctx: NewCtx, index: int = 0) -> Tuple[BytesIO, str, Tuple[int, int]]:
        attachment_file = BytesIO()

        if not ctx.message.attachments:
            await ctx.author.avatar_url_as(size = 128, format = 'jpeg').save(attachment_file)
            filename = ctx.author.display_name + '.png'
            file_size = (128, 128)

        else:
            target = ctx.message.attachments[index]
            await target.save(attachment_file)
            filename = target.filename
            file_size = (target.width, target.height)

        return attachment_file, filename, file_size

    @lru_cache(maxsize = 10)
    def _get_dimension(self, img_bytes: BytesIO) -> Tuple[BytesIO, int]:
        image_obj = Image.open(img_bytes)
        file_size = image_obj.size
        return img_bytes, file_size

    @lru_cache(maxsize = 15)
    async def _image_ops_func(self, ctx: NewCtx, img_bytes: Tuple[BytesIO, Optional[BytesIO]]):
        if len(ctx.message.attachments) == 1:
            file_a, _, file_size = await self._get_image(ctx, 0)

        elif img_bytes:
            file_a, file_size = self._get_dimension(img_bytes[0])

        else:
            file_a = BytesIO(await ctx.author.avatar_url_as(format = 'png', size = 128).read())
            file_size = (128, 128)

        return file_a, file_size

    @commands.command()
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.max_concurrency(1, commands.BucketType.guild, wait = False)
    async def shift(self, ctx: NewCtx, *img_bytes: Optional[LinkConverter]):
        """Shifts the RGB bands in an attached image or the author's profile picture"""

        attachment_file, file_size = await self._image_ops_func(ctx, img_bytes)

        start = time.time()
        new_file = self._shifter(attachment_file, file_size)
        end = time.time()

        await self.embed_file(ctx, "Shifting done", new_file, end - start, "shifted.png")

    @commands.command(name = 'morejpeg', aliases = ['jpeg', 'jpegify', 'more'])
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.max_concurrency(1, commands.BucketType.guild, wait = False)
    async def _morejpeg(self, ctx: NewCtx, severity: int = 15):
        """Adds jpeg compression proportional to severity to an uploaded image or the author's profile picture"""

        if not (0 <= severity <= 100):
            raise commands.BadArgument(
                "severity parameter must be between 0 and 100 inclusive")
        severity = 101 - severity

        attachment_file, _, _ = await self._get_image(ctx)

        start = time.time()
        new_file = await self.bot.loop.run_in_executor(
            None, self._loop_jpeg, attachment_file, severity, 1)
        end = time.time()

        await self.embed_file(ctx, "Jpegifying done", new_file, end - start, "diff.png")

    @commands.command(name = 'diff')
    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.max_concurrency(1, commands.BucketType.guild, wait = False)
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

        start = time.time()
        new_file = self._diff(file_a, file_a_size, file_b, file_b_size)
        end = time.time()

        await self.embed_file(ctx, "Difference finished", new_file, end - start, "diff.png")

    @commands.command(name = 'invert', aliases = ['negative'])
    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.max_concurrency(1, commands.BucketType.guild, wait = False)
    async def _invert(self, ctx: NewCtx, *img_bytes: Optional[LinkConverter]):
        """Inverts a given image to negative"""

        file_a, file_size = await self._image_ops_func(ctx, img_bytes)

        start = time.time()

        image_obj = Image.open(file_a)
        try:
            image_obj = ImageOps.invert(image_obj)
        except:
            image_obj = image_obj.convert(mode = 'RGB')
            image_obj = ImageOps.invert(image_obj)
        new_file = BytesIO()
        image_obj.save(new_file, format = 'PNG')
        new_file.seek(0)

        end = time.time()

        await self.embed_file(ctx, "Inverting finished", new_file, end - start, "inverted.png")

    @commands.command(name = 'poster')
    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.max_concurrency(1, commands.BucketType.guild, wait = False)
    async def _poster(self, ctx: NewCtx, bits: int = 8, *img_bytes: Optional[LinkConverter]):
        """Changes the number of bits (1 - 8 inc) dedicated to each channel"""

        if not (1 <= bits <= 8):
            raise commands.BadArgument("Bits argument should be between 1 and 8 inclusive")

        file_a, file_size = await self._image_ops_func(ctx, img_bytes)

        start = time.time()

        image_obj = Image.open(file_a)
        try:
            image_obj = ImageOps.posterize(image_obj, bits)
        except:
            image_obj = image_obj.convert(mode = 'RGB')
            image_obj = ImageOps.posterize(image_obj, bits)
        new_file = BytesIO()
        image_obj.save(new_file, format = 'PNG')
        new_file.seek(0)

        end = time.time()

        await self.embed_file(ctx, "Postering done", new_file, end - start, "poster.png")

    @commands.command(name = 'filter')
    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.max_concurrency(1, commands.BucketType.guild, wait = False)
    async def _filter(self, ctx: NewCtx, filter_type: str, *img_bytes: Optional[LinkConverter]):
        """Applies a filter to a given image"""

        filter_type = filter_type.lower()

        if not (filter_type in FILTERS):
            raise commands.BadArgument("Filter must be one of those in ImageFilter docs")

        file_a, file_size = await self._image_ops_func(ctx, img_bytes)

        start = time.time()

        image_obj = Image.open(file_a)
        try:
            image_obj = image_obj.filter(FILTERS[filter_type])
        except:
            image_obj = image_obj.convert(mode = 'RGB')
            image_obj = image_obj.filter(FILTERS[filter_type])
        new_file = BytesIO()
        image_obj.save(new_file, format = 'png')
        new_file.seek(0)

        end = time.time()

        await self.embed_file(ctx, "Applying the filter done", new_file, end - start, "filtered.png")

    @commands.command(name = 'rotate')
    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.max_concurrency(1, commands.BucketType.guild, wait = False)
    async def _rotate(self, ctx: NewCtx, degrees: int, *img_bytes: Optional[LinkConverter]):
        """Rotates an image some degrees, 360 returns it to original position"""
        degrees = degrees % 360 if degrees > 360 else degrees

        file_a, file_size = await self._image_ops_func(ctx, img_bytes)

        start = time.time()

        image_obj = Image.open(file_a)
        image_obj = image_obj.rotate(angle = degrees)
        fileout = BytesIO()
        image_obj.save(fileout, format = 'PNG')
        fileout.seek(0)
        end = time.time()

        await self.embed_file(ctx, "Rotationings finished", fileout, end - start, "rotated.png")


def setup(bot):
    """ Cog entry point. """
    bot.add_cog(Images(bot))
