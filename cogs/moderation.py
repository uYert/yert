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
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
""" 
#==moderation.py==#
#imports

#from imports
from discord import Member, Object
from discord.ext import commands
from typing import Union, Optional


class Moderation(commands.Cog):
	def __init__(self, bot) -> None:
		self.bot = bot

		self.DEF_DAYS = 7
		self.DEF_REASON = "No reason given"


	@commands.command()
	@commands.has_permissions(ban_members=True)  
	@commands.bot_has_permissions(ban_members=True)
	async def ban(self, ctx: commands.Context, target: Union[Member, Object], days: Optional[int], *, reason: Optional[str]) -> None:
		"""Bans the given <target> for [reason], deleting [days] of messages"""  #that good?
		days = days or self.DEF_DAYS
		reason = reason or self.DEF_REASON
		await ctx.guild.ban(target, delete_message_days=days, reason=reason)

	@commands.command()
	@commands.has_permissions(kick_members=True)
	@commands.bot_has_permissions(kick_members=True)
	async def kick(self, ctx: commands.Context, target: Member, *, reason:Optional[str]) -> None:
		"""Kicks the given target for a reason"""
		reason = reason or self.DEF_REASON
		await target.kick(reason=reason)  # might just let you write all of them, you're way better at explaining lol
	#how are we going to explain shit like in the ban command? how can we say 'you can supply a days arg if you want, but it wont break if you dont'? like <required arg> [optional arg] ? it should be yeah, the help command should be showing them like that, ill let you try and explain default args then lmao oof this is gonna be hard lol, will it be better if we assume the user isnt completely incompetent and just shout gitgud if something goes wrong? lmfao, why not the user is a stupid cunt anyways lol, imma go loo, one sec
	
	@commands.command() # how about saying that it's an optionnal arg and define all of those when the user uses the help command
	@commands.has_permissions(ban_members=True)
	@commands.bot_has_permissions(ban_members=True)
	async def unban(self, ctx: commands.Context, target: int, *, reason: Optional[str]) -> None:
		"""Unbans the given target"""
		reason = reason or self.DEF_REASON
		await ctx.guild.unban(Object(id=target), reason=reason)

	@commands.command()
	@commands.has_guild_permissions(mute_members=True)
	@commands.bot_has_guild_permissions(mute_members=True)
	async def mute(self, ctx: commands.Context, target: Member, *, reason: Optional[str]) -> None:
		"""Mutes the given target with a reason"""
		reason = reason or self.DEF_REASON
		await target.edit(mute=True, reason=reason)

	@commands.command()
	@commands.has_guild_permissions(mute_members=True)
	@commands.bot_has_guild_permissions(mute_members=True)
	async def unmute(self, ctx: commands.Context, target: Member, *, reason: Optional[str]) -> None:
		reason = reason or self.DEF_REASON
		await target.edit(mute=False, reason=reason)

def setup(bot):
	bot.add_cog(Moderation(bot))
 
"""
Hey
You should be able to write too
Snek best 
ayyyyyyyyy
this is noice
do you have any ideas about what kind of game we should be amking 
don't ignore me :c
no u
smh
umbra is a person lmao
haha yes 
bet he is human 
imagine being human lmao
ikr
fuck humans
they suck
like wtf 
you have elfs and stuff lol 
imagine only living to about 80 years old
ikr
barely enough, can't even ejoy yourself 
holy typos lmao
lmfao
shit happen
also, I'm just gonnaedit a little thing in your cog
because pep 8 is gonna geet mad at me again otherwisr
sure, good catch
:thonk:
"""