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
import asyncio
from datetime import datetime
import random
from typing import Optional, Union

import discord
from discord import Message
from discord.ext import commands


from main import NewCtx
from utils import db
from utils.formatters import Flags, BetterEmbed

random.seed(datetime.utcnow())


class Player:
    def __init__(self, name, player_id):
        self.hand = []
        self.score = 0
        self.name = name
        self.id = player_id


class Dealer:
    def __init__(self):
        self.hand = []
        self.score = 0
        self.name = 'Dealer'


class Card:
    def __init__(self, name: str, suit: str) -> None:
        self.name = name
        self.suit = suit
        try:
            self._value = int(self.name)
        except ValueError:
            if self.name in ['J', 'Q', 'K']:
                self._value = 10
            else:
                self._value = 1

    @property
    def value(self) -> int: return self._value

    def ace_card(self) -> None:
        self._value = 11

    def __repr__(self) -> str:
        return "<Card value={0._value} name={0.name} suit={0.suit}".format(self)

    def __str__(self) -> str: return f"{self.name} of {self.suit} ({self.value})"


class Deck:
    def __init__(self) -> None:
        values = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
        suits = ['Clubs', 'Spades', 'Hearts', 'Diamonds']
        self.cards = []
        for suit in suits:
            for value in values:
                self.cards.append(Card(value, suit))
        random.shuffle(self.cards)

    def get(self) -> Card:
        card = random.choice(self.cards)
        self.cards.pop(self.cards.index(card))
        return card

    def shuffle(self) -> None:
        random.shuffle(self.cards)


class Game:
    def __init__(self, ctx: NewCtx, original: Message, embed: BetterEmbed):
        self.move_opts = ['h', 'hit', 's', 'stay', 'q', 'quit']

        self.playerturn = True
        self.dealerturn = False
        self.move_counter = 0

        self.ctx = ctx
        self.bot = ctx.bot
        self.original = original
        self.embed = embed

        self.five_card_winner = False
        self.winner = None

        self.deck = Deck()

        self.player = Player(ctx.author.display_name, ctx.author.id)
        self.player.hand.append(self.deck.get())
        self.player.hand.append(self.deck.get())

        self.dealer = Dealer()
        self.dealer.hand.append(self.deck.get())
        self.dealer.hand.append(self.deck.get())

    async def calculate_score(self, target: Union[Player, Dealer]) -> int:
        cards = target.hand
        hand_value = 0

        def ace_check(m):
            return m.author.id == self.player.id and \
                m.channel == self.ctx.channel and \
                m.content in ['1', '11']

        for card in cards:

            if card.name != 'A':
                hand_value += card.value

            else:
                if isinstance(target, Dealer):
                    hand_value += 11
                else:
                    self.embed.add_field(name=f'Your hand : {", ".join([str(c) for c in target.hand])}',
                                        value="You got an Ace, do you want it to be 1 or 11?")
                    await self.original.edit(embed=self.embed)
                    try:
                        reply = await self.bot.wait_for('message', check=ace_check, timeout=30)

                        reply = int(reply.content)
                        hand_value += reply

                        if reply == 11:
                            card.ace_card()

                        for idx in range(len(self.embed.fields)):
                            if self.embed.fields[idx].value.startswith('You got'):
                                self.embed.remove_field(idx)
                    except asyncio.TimeoutError:
                        await self.ctx.send("You took too long, dealer wins.")
                        self.winner = 'Dealer'
                        self.playerturn = False
                        self.dealerturn = False
                        break


        if hand_value <= 21 and len(target.hand) == 5:
            self.five_card_winner = True
            self.winner = target.__class__.__name__

        if hand_value == 21:
            self.embed.add_field(name="Blackjack!!", value='\u200b')
            await self.original.edit(embed=self.embed)
            self.winner = target.name
            self.playerturn = False
            self.dealerturn = False

        return hand_value

    async def player_turn(self):
        def move_check(m):
            return m.author.id == self.player.id and \
                m.channel == self.ctx.channel and \
                m.content in self.move_opts

        self.dealer.score = await self.calculate_score(self.dealer)

        while self.playerturn:
            self.move_counter += 1
            self.player.score = await self.calculate_score(self.player)

            if self.player.score < 21:
                if self.move_counter == 1:
                    self.embed.add_field(
                        name = "Your hand :", value='\n'.join([str(c) for c in self.player.hand]), inline=True
                    )
                    self.embed.add_field(
                        name="Dealer's face up card :", value=str(self.dealer.hand[0]), inline=True
                    )
                    await self.original.edit(embed=self.embed)

                else:
                    for idx in range(len(self.embed.fields)):
                        if self.embed.fields[idx].name.startswith('Your hand :'):
                            self.embed.remove_field(idx)
                            self.embed.insert_field_at(
                                idx, name='Your hand :',
                                value='\n'.join([str(c) for c in self.player.hand]),
                                inline=True
                            )
                            await self.original.edit(embed=self.embed)

                try:
                    reply = await self.bot.wait_for('message', check=move_check, timeout=30)
                    choice = reply.content.lower()

                    if choice in ['h', 'hit']:
                        card = self.deck.get()
                        await asyncio.sleep(0.5)
                        self.embed.add_field(
                            name='\u200b', value=f"You got : {str(card)}", inline=False
                        )
                        await self.original.edit(embed=self.embed)

                        self.player.hand.append(card)
                        print([repr(c) for c in self.player.hand])
                        self.player.score = await self.calculate_score(self.player)
                        if self.five_card_winner:
                            self.playerturn = False
                            self.dealerturn = False
                            break

                    elif choice in ['s', 'stay']:
                        self.embed.add_field(
                            name="Bold strategy cotton, lets see how that plays out",
                            value='\u200b', inline=False
                        )
                        await self.original.edit(embed=self.embed)
                        await asyncio.sleep(0.5)
                        self.playerturn = False
                        self.dealerturn = True
                        break

                    else:
                        if self.move_counter == 1:
                            self.embed.add_field(
                                name="You cash out on the first move",
                                value="\u200b", inline=False
                            )
                            self.winner = 'Draw'
                            break
                        else:
                            self.embed.add_field(
                                name="You can only do this on the first move",
                                value='\u200b', inline=False
                            )
                            continue
                except asyncio.TimeoutError:
                    await self.ctx.send("You took too long, dealer wins")
                    self.winner = 'Dealer'
                    self.playerturn = False
                    self.dealerturn = False
                    break

            elif self.player.score == 21:
                self.winner = self.player.name
                self.playerturn = False
                self.dealerturn = False
                break

            elif self.player.score > 21:
                self.embed.add_field(
                    value=f"Your last card, {str(self.player.hand[-1])},  put you over 21",
                    name='\u200b', inline=False
                )
                for idx in range(len(self.embed.fields)):
                    if self.embed.fields[idx].name.startswith('Your hand'):
                        self.embed.remove_field(idx)
                        self.embed.insert_field_at(
                            idx, name="Your hand :",
                            value='\n'.join([str(c) for c in self.player.hand]),
                            inline=True
                        )
                await self.original.edit(embed=self.embed)
                self.winner = self.dealer.name
                self.playerturn = False
                self.dealerturn = False

    async def dealer_turn(self):
        while self.dealerturn:
            while self.dealer.score < 21:

                while self.dealer.score < 17:
                    card = self.deck.get()
                    self.dealer.hand.append(card)
                    self.dealer.score = await self.calculate_score(self.dealer)
                    await asyncio.sleep(0.5)

                else:   #house stays at 17 and up
                    self.dealerturn = False
                    break

            if self.dealer.score == 21:
                self.winner = self.dealer.name
                self.dealerturn = False

            elif self.dealer.score > 21:
                self.winner = self.player.name
                self.dealerturn = False

    async def game_end(self):

        if not self.winner and self.player.score <= 21 and self.dealer.score <= 21:
            if self.player.score == self.dealer.score:
                self.winner = 'Draw'
            elif self.player.score > self.dealer.score:
                self.winner = self.player.name
            else:
                self.winner = self.dealer.name

        self.embed.add_field(
            name=f"Winner is {self.winner}",
            value=f"Player score : {self.player.score}, Dealer score : {self.dealer.score}",
            inline=False
        )

        for idx in range(len(self.embed.fields)):
            if self.embed.fields[idx].name.startswith('Dealer'):
                self.embed.remove_field(idx)
                self.embed.insert_field_at(
                    idx, name="Dealer's hand",
                    value='\n'.join([str(c) for c in self.dealer.hand]),
                    inline=True
                )
        await self.original.edit(embed=self.embed)




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

    @commands.command(name='blackjack', aliases=['21'])
    @commands.max_concurrency(1, commands.BucketType.channel, wait=False)
    async def _blackjack(self, ctx: NewCtx, bet: int = 30):
        """Plays blackjack against the house, default bet is 30 <:peepee:712691831703601223>"""
        if not(1 <= bet <= 100):
            return await ctx.send("You must bet between 1 and 100 <:peepee:712691831703601223>.")
        else:
            query = "SELECT * FROM game_data WHERE user_id=$1;"
            result = await self.bot.pool.fetchrow(query, ctx.author.id)
            if result:
                available_currency = result['amount']
                if bet > available_currency:
                    return await ctx.send("You don't have enough <:peepee:712691831703601223> for that bet.")
                else:
                    await ctx.send(f"Very well, your {bet}<:peepee:712691831703601223> will be gladly accepted.")
                    wins = result['wins']
                    losses = result['losses']

            else:
                query = "INSERT INTO game_data VALUES($1, $2, $3, $4);"
                await self.bot.pool.execute(query, ctx.author.id, 0, 0, 150)
                wins = 0
                losses = 0
                available_currency = 150
                await ctx.send("Yoink has not seen you before, have 150 <:peepee:712691831703601223> on the house.")

            query = "SELECT * FROM game_data WHERE user_id=$1;"
            house = await self.bot.pool.fetchrow(query, self.bot.user.id)

            embed = BetterEmbed()
            embed.add_field(
                name=f"{ctx.author.display_name} vs the house",
                value="[h | hit] [s | stay] [q | quit (only on the first turn)] ",
                inline=False
            )

            original = await ctx.send(embed=embed)

            game = Game(ctx, original, embed)

            await game.player_turn()
            await game.dealer_turn()
            await game.game_end()

            if game.winner == 'Draw' or game.winner is False:
                await ctx.send("The game was drawn, your <:peepee:712691831703601223> have been returned.")

            elif game.winner == ctx.author.display_name:
                await ctx.send(f"Congratulations, you beat the house, take your {bet}<:peepee:712691831703601223> ")
                end_amount = available_currency + bet
                query = "UPDATE game_data SET wins=$1, amount=$2 WHERE user_id=$3;"
                await self.bot.pool.execute(query, wins+1, end_amount, ctx.author.id)
                other_query = "UPDATE game_data SET losses=$1, amount=$2 WHERE user_id=$3;"
                await self.bot.pool.execute(other_query, house['losses']+1, house['amount']-bet, self.bot.user.id)

            else:
                await ctx.send(f"The house always wins, your {bet}<:peepee:712691831703601223> have been yoinked.")
                end_amount = available_currency - bet
                query = "UPDATE game_data SET losses=$1, amount=$2 WHERE user_id=$3;"
                await self.bot.pool.execute(query, losses+1, end_amount, ctx.author.id)
                other_query = "UPDATE game_data SET wins=$1, amount=$2 WHERE user_id=$3;"
                await self.bot.pool.execute(other_query, house['wins']+1, house['amount']+bet, self.bot.user.id)

    @commands.command(name='check', aliases=['account'])
    async def _check_bal(self, ctx: NewCtx, target: Optional[discord.Member]):
        """"""
        user_id = getattr(target, 'id', None) or ctx.author.id
        target = target or ctx.author

        query = "SELECT * FROM game_data WHERE user_id=$1;"
        result = await self.bot.pool.fetchrow(query, user_id)
        if result:
            e = BetterEmbed(title=target.display_name)
            e.add_field(name=f"Your currently have {result['amount']} <:peepee:712691831703601223>.",
                        value='\u200b')
            e.description = f"Wins : {result['wins']}\nLosses : {result['losses']}"
            e.set_author(name=target.display_name, icon_url=str(target.avatar_url))
            return await ctx.send(embed=e)
        else:
            await ctx.send("Yoink hasn't seen you before, wait one.")
            query = "INSERT INTO game_data (user_id, wins, losses, amount)" \
                    "VALUES ($1, $2, $3, $4);"
            await self.bot.pool.execute(query, user_id, 0, 0, 150)
            e = BetterEmbed(title=target.display_name)
            e.add_field(name = f"Your currently have 150 <:peepee:712691831703601223>.",
                        value = '\u200b')
            e.description = f"Wins : 0\nLosses : 0"
            e.set_author(name = target.display_name, icon_url = str(target.avatar_url))
            return await ctx.send(embed = e)

    @commands.command(name="del")
    @commands.is_owner()
    async def _delete(self, ctx: NewCtx, target: Optional[discord.Member]):

        user_id = getattr(target, 'id', None) or ctx.author.id
        name = getattr(target, 'display_name', None) or ctx.author.display_name
        query = "DELETE FROM game_data WHERE user_id=$1;"
        await self.bot.pool.execute(query, user_id)
        await ctx.send(f"Entry of {name} cleared.")



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
