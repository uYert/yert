"""
MIT License

Copyright (c) 2021 - µYert

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


import json
import re
import typing
from datetime import datetime

import config
import discord
from aiohttp import BasicAuth
from dateutil.relativedelta import relativedelta
from discord.ext import commands, tasks
from main import NewCtx
from utils import formatters


class Catpost(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.snake_pit_id = 448285120634421278
        self.derek_id = 230696474734755841
        self.cat_re = re.compile(r"cat|kitt(en|y)?")
        self.url_re = re.compile(
            r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*(),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+"
        )
        self.warned = False
        self.api_count_reset.start()
        self.store_catposts.start()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """ Derek catposting detector """
        snake_pit_id = 448285120634421278
        derek_id = 230696474734755841
        if message.author.id in self.bot._cached_ids["catpost"]:

            if message.channel.id == snake_pit_id:
                if message.author.id == derek_id and message.attachments:
                    return await self.derekpost(message)

                elif (
                    not message.embeds
                    and self.url_re.match(message.content.lower())
                    and message.attachments
                ):
                    return await self.query_image(message)

    @commands.command()
    async def notify(self, ctx: NewCtx):
        """ Has the bot DM you when derek posts a cat picture, since they're determined to not do it"""
        if ctx.author.id not in self.bot._cached_ids["catpost"]:
            self.bot._cached_ids["catpost"].append(ctx.author.id)
            return await ctx.message.add_reaction("<:wowkitty:739613802672422982>")
        return await ctx.send("Your id has already been added to the list.")

    @commands.command(name="stop")
    async def _stop_catposts(self, ctx: NewCtx):
        """ Stops the bot DM'ing you when a cat post detected"""
        if ctx.author.id in self.bot._cached_ids["catpost"]:
            self.bot._cached_ids["catpost"].remove(ctx.author.id)
            return await ctx.message.add_reaction("<a:rooFight:747679958440345621>")
        return await ctx.send("Your id wasn't in the list.")

    def prepare_embed(
        self, message: discord.Message
    ) -> typing.Tuple[str, formatters.BetterEmbed]:
        ret = formatters.BetterEmbed(title="Catpost detected.")
        ret.add_field(
            name="Derek catpost;",
            value=f"[Jump!]({message.jump_url})",
            inline=False,
        )
        return "A cat post was detected, come have a look", ret

    async def query_image(self, message: discord.Message):
        self.bot._cached_ids["api"] += 1
        data = self.bot._cached_ids
        response = await self.bot.session.get(
            config.IMG_BASE + message.attachments[0].url,
            auth=BasicAuth(*config.IMG_AUTH),
        )
        response = await response.json()
        if response["status"]["type"] == "error":
            await self.bot.get_user(273035520840564736).send(
                f"Error from the image api: {response['status']['text']}"
            )
        top_eighty = [
            res for res in response["result"]["tags"][:10] if res["confidence"] >= 80.0
        ]

        if any(self.cat_re.match(res["tag"]["en"]) for res in top_eighty):

            for uid in data["catpost"]:
                user = self.bot.get_user(uid)
                _, embed = self.prepare_embed(message)

                try:
                    await user.send(
                        "I'm pretty sure sure i just saw a catpost", embed=embed
                    )
                except discord.Forbidden:
                    pass
                except Exception as e:
                    await self.bot.get_user(273035520840564736).send(
                        "Failed to send a dm to {} for reason: \n{}\n{}".format(
                            user.name, type(e), e
                        )
                    )

    async def derekpost(self, message: discord.Message):
        content, embed = self.prepare_embed(message)
        data = self.bot._cached_ids["catpost"]
        for uid in data:
            user = self.bot.get_user(uid)
            try:
                await user.send(content, embed=embed)
            except discord.Forbidden:
                pass
            except Exception as e:
                await self.bot.get_user(273035520840564736).send(
                    "Failed to send a dm to {} for reason: \n{}\n{}".format(
                        user.name, type(e), e
                    )
                )

    @tasks.loop(hours=5)
    async def store_catposts(self):
        if not self.warned and self.bot._cached_ids["api"] >= 1500:
            await self.bot.get_user(273035520840564736).send("75%")
            self.warned = True
        with open("catpost.json", "w") as file:
            json.dump(self.bot._cached_ids, file, indent=4)

    @store_catposts.before_loop
    async def pre_store(self):
        await self.bot.wait_until_ready()

    @tasks.loop(hours=30 * 24)
    async def api_count_reset(self):
        with open("catpost.json") as file:
            data = json.load(file)
        data["api"] = 0
        with open("catpost.json", "w") as file:
            json.dump(data, file)

    @api_count_reset.before_loop
    async def pre_loop(self):
        next_time = datetime.utcnow().replace(day=6) + relativedelta(months=1)
        await discord.utils.sleep_until(next_time)


def setup(bot):
    bot.add_cog(Catpost(bot))
