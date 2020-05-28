import from functools import lru_cache, wraps
import traceback
import typing
import discord
from discord import Message
from discord.ext import commands
import config
from main import 
from utils.converters import GuildConverter

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
        self.webhook = self._webhook
        self.ignored = [commands.CommandNotFound, ]
        self.tracking = True
        self.tracked = []
        
    @property
    def _webhook(self) -> discord.Webhook:
    	wh_id, wh_token = config.WEBHOOK
        hook = discord.Webhook.partial(
            id=wh_id, token=wh_token, adapter=discord.AsyncWebhookAdapter(self.bot.session))
        return hook

    @lru_cache(maxsize=15)
    def tracy_beaker_fmt(self, error: Exception) -> typing.Tuple[str, str]:
        full_exc = traceback.format_exception(type(error), error, error.__traceback__)
        short_exc = full_exc[-1]
        full_exc = [line.replace("/home/moogs", "", 1) for line in full_exc]
        full_exc = [line.replace("C:\\Users\\aaron", "", 1) for line in full_exc]
        output = "\n".join(full_exc)
        idx = 0
        while len(output) >= 1990:
            idx -= 1
            output = "\n".join(full_exc[:idx])
        output = f"```{output}```"
        return short_exc, output

    @commands.command(name="toggle")
    @commands.has_permissions(administrator = True)
    async def _toggle_tracker(self, ctx ):
    	self.tracked.append(ctx.guild.id)
    	await self.bot.pool.execute("UPDATE guild_config SET stats_activated = true WHERE guild_id= $1")
    	await ctx.send("The stats were successfully activated for this server.")
    	
    @caching()
    @commands.command()
    @commands.cooldown(1, 15, commands.BucketType.guild)
    async def show_stats(self, ctx ):
    	query = """WITH one_day AS(
	    	SELECT guild_id, 
	    	joined_numb AS "day_joined",
	    	left_numb AS "day_left",
	    	joined_numb - (SELECT joined_numb FROM stats WHERE guild_id= $1 AND age(days) BETWEEN INTERVAL '1 DAY' AND '2 DAYS') AS "difference_join",
	    	left_numb - (SELECT left_numb FROM stats WHERE guild_id = $1 AND age(days) BETWEEN INTERVAL '1 DAY' AND '2 DAYS') FROM stats AS "difference_join"
	    	FROM stats
	    	WHERE
	    	age(days) <= INTERVAL '1 days'
	    	GROUP BY guild_id
    	),
    	seven_days AS(
	    	SELECT guild_id,
	    	SUM(joined_numb) AS "seven_joined",
	    	SUM(left_numb) AS "seven_left",
	    	AVG(joined_numb) AS "avg_joined_seven",
	    	AVG(left_numb) AS "avg_left_seven"
	    	FROM stats
	    	WHERE age(days) BETWEEN INTERVAL '-1 day' AND INTERVAL '-7day'
	    	GROUP BY guild_id
    	),
    	left_days AS(
	    	SELECT guild_id,
	    	SUM(joined_numb) AS "left_joined",
	    	SUM(left_numb) AS "left_left",
	    	AVG(joined_numb) AS "avg_joined_left",
	    	AVG(left_numb) AS "avg_left_left"
	    	FROM stats
	    	WHERE age(days) BETWEEN INTERVAL '-1 day' AND INTERVAL '-7day'
	    	GROUP BY guild_id
    	)
    	SELECT 
    	one_day.*,
    	seven_days.*,
    	left_days.*
    	FROM left_days
    	JOIN one_day ON one_day.guild_id = left_days.guild_id
    	JOIN seven_days ON seven_days.guild_id = left_days.guild_id
    	WHERE guild_id = $1
    	"""
    	async with self.bot.db.acquire() as conn:
    		result = await conn.fetch(query, ctx.guild.id)
    	embed = discord.Embed(colour = discord.Color.blue())
    	stats_joined = f"<:down:715574958176337920> {result['difference_join']}"if result['difference_join'] < 0 else f"<:up:715574974642913301> {result['difference_join']}" if  result['difference_join'] >= 0 else ""
    	stats_left = f"<:down:715574958176337920> {result['difference_left']}"if result['difference_left'] < 0 else f"<:up:715574974642913301> {result['difference_left']}" if  result['difference_left'] >= 0 else ""
    	embed.add_field(name= "\U0001f55aStats for the last 24 hours", value = "Member joined:{result['day_joined']} {stats_joined}\nMember left: {result['day_left']}{stats_left}")
    	embed.add_field(name = "\U0000231bStats for the last 7 days",value = "Member joined:{result['seven_joined']}\nMember left:{result['seven_left']}\nAverage joins:{result['avg_seven_joined']}\nAveragequits:{result['avg_seven_left']}")
    	embed.add_field(name = "\U0001f5d3 Stats for the last 30 days", value="Member joined:{result['left_joined']}\nMember left:{result['left_left']}\nAverage joins:{result['avg_left_joined']}\nAveragequits:{result['avg_left_left']}")
    	await ctx.send(embed= embed)
 
    @commands.group(invoke_without_command=True, name="ignored", hidden=True)
    @commands.is_owner()
    async def _ignored(self, ctx ) -> None:
        """
        Adds or removes an exception from the list of exceptions to ignore,
        if you want to add or remove commands.MissingRole,
        be sure to exclude the "commands."
        """
        await ctx.send(", ".join([exc.__name__ for exc in self.ignored]))

    @_ignored.command()
    @commands.is_owner()
    async def add(self, ctx , exc: str):
        """Adds an exception to the list of ignored exceptions"""
        if hasattr(commands, exc):
            if getattr(commands, exc) not in self.ignored:
                self.ignored.append(getattr(commands, exc))
            else:
                await ctx.webhook_send(f"commands.{exc} is already in the ignored exceptions.",
                                       webhook=self.webhook)
        else:
            raise AttributeError(
                "commands module has no attribute {0}, command aborted".format(exc))

    @_ignored.command()
    @commands.is_owner()
    async def remove(self, ctx , exc: str):
        """Removes an exception from the list of ingored exceptions"""
        if hasattr(commands, exc):
            try:
                self.ignored.pop(self.ignored.index(
                    getattr(commands, exc)))
            except ValueError:
                await ctx.webhook_send("{0} not in the ignored list of exceptions".format(exc),
                                       webhook=self.webhook)
        else:
            raise AttributeError(
                "commands module has no attribute {0}, command aborted".format(exc))

    @commands.Cog.listener()
    async def on_ready(self):
        """ On websocket ready. """
        
    @commands.Cog.listener()
    async def on_command_error(self, ctx , error: Exception):
        """ On command errors. """
        if hasattr(ctx.command, "on_error"):
            return

        if isinstance(error, tuple(self.ignored)):
            return

        error = getattr(error, "original", error)

        if isinstance(error, commands.CommandOnCooldown):
            if await self.bot.is_owner(ctx.author):
                return await ctx.reinvoke()

        short, full = self.tracy_beaker_fmt(error)

        await ctx.send(short)
        await self.webhook.send(full)

    @caching()
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
    	await self.bot.pool.execute(" CALL evaluate_data($1, true)",member.guild.id)

    @caching()
    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        await self.bot.pool.execute(" CALL evaluate_data($1, false)",member.guild.id)


def setup(bot):
    """ Cog entry point. """
    bot.add_cog(Stats(bot))
