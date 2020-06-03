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

from functools import wraps
import discord
from discord.ext import commands

def caching():
    def wrapper(func):
        @wraps(func)
        async def wrapped(*args, **kwargs):
            guild = args[1].guild
            if guild.id in args[0].tracked and args[0].tracking:
                return await func(*args, **kwargs)
            async with args[0].bot.pool.acquire() as con:
                query = """SELECT stats_enabled AS activated FROM guild_config WHERE guild_id= $1 """
                activated = await con.fetchrow(query, guild.id)
            if activated["activated"]:
                args[0].tracked.append(guild.id)
                return await func(*args, **kwargs)
        return wrapped
    return wrapper


class Stats(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.tracking = True
        self.tracked = []
        
    @commands.command()
    @commands.has_permissions(administrator = True)
    async def enable_stats(self, ctx):
    	self.tracked.append(ctx.guild.id)
	query = """
	INSERT INTO guild_config(guild_id)
	VALUES($1)
	ON CONFLICT (guild_id)
	DO UPDATE SET stats_enabled = true
	"""
    	await self.bot.pool.execute(query, ctx.guild.id)
    	await ctx.send("The stats were successfully activated for this server.")
	

    @commands.command()
    @commands.has_permissions(administrator = True)
    async def disable_stats(self, ctx):
    	self.tracked.remove(ctx.guild.id)
	query = """
	INSERT INTO guild_config(guild_id)
	VALUES($1)
	ON CONFLICT (guild_id)
	DO UPDATE SET stats_enabled = false
	"""
    	await self.bot.pool.execute(query, ctx.guild.id)
    	await ctx.send("The stats were successfully disabled for this server.")
	
    @commands.command()
    @commands.cooldown(1, 15, commands.BucketType.guild)
    @caching()
    async def show_stats(self, ctx):
    	query = """
    	WITH one_day AS(
	    	SELECT guild_id, 
	    	joined_numb AS "day_joined",
	    	left_numb AS "day_left",
	    	joined_numb - (SELECT joined_numb FROM stats WHERE  age(now(), days) BETWEEN INTERVAL '1 DAY' AND '2 DAYS') AS "difference_join",
	    	left_numb - (SELECT left_numb FROM stats WHERE age(now(),days) BETWEEN INTERVAL '1 DAY' AND '2 DAYS') AS "difference_left"
	    	FROM stats
	    	WHERE age(days) <= INTERVAL '1 days'
    	),
    	seven_days AS(
	    	SELECT guild_id,
	    	SUM(joined_numb) AS "seven_joined",
	    	SUM(left_numb) AS "seven_left",
	    	AVG(joined_numb) AS "avg_joined_seven",
	    	AVG(left_numb) AS "avg_left_seven"
	    	FROM stats
	    	WHERE age(now(), days) <= INTERVAL '7day'
	    	GROUP BY guild_id
    	),
    	left_days AS(
	    	SELECT guild_id,
	    	SUM(joined_numb) AS "left_joined",
	    	SUM(left_numb) AS "left_left",
	    	AVG(joined_numb) AS "avg_joined_left",
	    	AVG(left_numb) AS "avg_left_left"
	    	FROM stats
	    	WHERE age(now(), days) <= INTERVAL '30 days'
	    	GROUP BY guild_id
    	)
    	SELECT 
    	one_day.*,
    	left_days.*,
    	seven_days.*
    	FROM left_days
    	INNER JOIN one_day ON one_day.guild_id = left_days.guild_id
    	INNER JOIN seven_days ON seven_days.guild_id = left_days.guild_id
    	WHERE left_days.guild_id = $1
    	"""
    	async with self.bot.db.acquire() as conn:
    		result = await conn.fetchrow(query, ctx.guild.id)
    	embed = discord.Embed(colour=discord.Color.blurple(), timestamp=datetime.now())
    	embed.set_thumbnail(url=ctx.guild.icon_url)
    	stats_joined = f"<:down:715574958176337920> {result['difference_join']}"if result['difference_join'] < 0 else f"<:up:715574974642913301> {result['difference_join']}" if  result['difference_join'] >= 0 else ""
    	stats_left = f"<:down:715574958176337920> {result['difference_left']}"if result['difference_left'] < 0 else f"<:up:715574974642913301> {result['difference_left']}" if  result['difference_left'] >= 0 else ""
    	embed.add_field(name="\U0001f55aStats for the last 24 hours", value=f"Members who have joined:{result['day_joined']} {stats_joined}\nMembers who have left: {result['day_left']}{stats_left}")
    	embed.add_field(name="\U0000231bStats for the last 7 days", value=f"Members who have joined:{result['seven_joined']}\nMembers who have left:{result['seven_left']}\nAverage joins:{result['avg_joined_seven']}\nAveragequits:{result['avg_joined_seven']}")
    	embed.add_field(name="\U0001f5d3 Stats for the last 30 days", value=f"Members who have joined:{result['left_joined']}\nMembers who have left:{result['left_left']}\nAverage joins:{result['avg_joined_left']}\nAverage quits:{result['avg_left_left']}")
    	await ctx.send(embed=embed)
  
    @caching()
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
    	await self.bot.pool.execute("CALL evaluate_data($1, true)",member.guild.id)

    @caching()
    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        await self.bot.pool.execute("CALL evaluate_data($1, false)",member.guild.id)


def setup(bot):
    """ Cog entry point. """
    bot.add_cog(Stats(bot))
