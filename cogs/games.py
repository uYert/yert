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
from datetime import datetime

import discord
from discord.ext import commands

from utils import db
from utils.formatters import Flags


class HypeSquadHouse(db.Table, table_name="hypesquad_house"):
    """
    # ! This is probably just a documentation thing right now for db table.
    # ? I seen this format for RDanny tables and liked it so.....

    Documents the table layout, should be easy to read.
    """

    guild_id = db.Column(db.Integer(big=True))
    balance_count = db.Column(db.Integer)
    bravery_count = db.Column(db.Integer)
    brilliance_count = db.Column(db.Integer)


class HypeSquadHouseReacted(db.Table, table_name="hypesquad_house_reacted"):
    """
    Let's just store all people who have reacted, and which guild they came
    from since this game is guild agnostic.
    """
    guild_id = db.Column(db.Integer(big=True))
    user_id = db.Column(db.Integer(big=True))


class Games(commands.Cog):
    """ Games cog! """

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        """
        Adding the guild to the table in the event they want to play.
        """
        house_query = """INSERT INTO hypesquad_house
                         (guild_id, balance_count, bravery_count, brilliance_count)
                         VALUES ($1, 0, 0, 0);
                      """
        await self.bot.pool.execute(house_query, guild.id)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        """
        Let's wait for any and all Emoji reactions to the bot's messages.
        On a reaction we'll add the user's house to the count if they have
        not already reacted.
        """

        channel = self.bot.get_channel(payload.channel_id)
        if not channel.guild:
            return  # ! We don't want DM cheats
        try:
            message = await channel.fetch_message(payload.message_id)
        except discord.errors.NotFound:
            return
        if message.author != self.bot.user:
            return  # ! Only the bots messages work
        reacting_member = message.guild.get_member(payload.user_id)
        if reacting_member.bot:
            print("author bot")
            return  # ! No bots

        if not reacting_member:
            return  # ! Not in the guild?? Edge case
        # Time to check if they're already in here
        duped_query = """SELECT *
                         FROM hypesquad_house_reacted
                         WHERE guild_id = $1
                         AND user_id = $2;
                      """
        duped = await self.bot.pool.fetchrow(duped_query,
                                             reacting_member.guild.id,
                                             reacting_member.id)
        if duped:
            return  # ! They already reacted

        raw_member = await self.bot.http.get_user(reacting_member.id)
        member_flags = Flags(raw_member['public_flags'])
        if member_flags.value == 0:
            return
        if member_flags.hypesquad_balance:
            flag = "balance"
        elif member_flags.hypesquad_bravery:
            flag = "bravery"
        elif member_flags.hypesquad_brilliance:
            flag = "brilliance"
        else:
            return
        flag_query = f"""UPDATE hypesquad_house
                         SET {flag}_count = {flag}_count + 1
                         WHERE guild_id = $1
                      """
        query = """INSERT INTO hypesquad_house_reacted (guild_id, user_id, reacted_date) VALUES ($1, $2, $3);"""
        await self.bot.pool.execute(query, reacting_member.guild.id, reacting_member.id, datetime.utcnow())
        return await self.bot.pool.execute(flag_query, reacting_member.guild.id)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        """
        Little more confusing, we need to check if the removing user has reacted before,
        and if so, decrement the value for their house.
        """
        query = """DELETE FROM hypesquad_house_reacted
                   WHERE guild_id = $1
                   AND user_id = $2
                   RETURNING user_id;
                """
        possible_user = await self.bot.pool.fetchrow(query, payload.guild_id, payload.user_id)
        if not possible_user:
            return

        # ! Time to decrement their house value...
        user = await self.bot.http.get_user(payload.user_id)
        flags = Flags(user['public_flags'])
        if flags.hypesquad_balance:
            house = "balance"
        elif flags.hypesquad_bravery:
            house = "bravery"
        elif flags.hypesquad_brilliance:
            house = "brilliance"
        else:
            return

        house_query = f"""UPDATE hypesquad_house
                          SET {house}_count = {house}_count - 1
                          WHERE guild_id = $1;
                       """
        return await self.bot.pool.execute(house_query, payload.guild_id)


def setup(bot):
    """ Cog entrypoint. """
    bot.add_cog(Games(bot))
