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
import random
from dataclasses import dataclass
from datetime import datetime

from discord import Message
from main import BetterEmbed, NewCtx

random.seed(datetime.utcnow())


class Card:
    def __init__(self, name: str, suit: str):
        self.name = name
        self.suit = suit
        try:
            self._value = int(name)
        except ValueError:
            if name in ["J", "Q", "K"]:
                self._value = 10
            else:
                self._value = 1

    @property
    def value(self) -> int:
        return self._value

    def ace(self) -> None:
        self._value = 11

    def __repr__(self) -> str:
        return str(self)

    def __str__(self) -> str:
        return "{0.name} of {0.suit} ({0.value})".format(self)


class Deck:
    def __init__(self) -> None:
        names = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]
        suits = ["Clubs", "Spades", "Hearts", "Diamonds"]
        self.cards = []
        for suit in suits:
            for name in names:
                self.cards.append(Card(name, suit))
        random.shuffle(self.cards)

    def get(self) -> Card:
        card = self.cards.pop(0)
        random.shuffle(self.cards)
        return card

    def show_next(self) -> Card:
        return self.cards[0]


@dataclass
class Player:
    name: str
    hand: list
    score: int
    id: int
    is_turn: bool
    is_winner: bool

    def add_cards(self, card: Card) -> None:
        self.hand.append(card)

    async def update_hand(self, original: Message, embed: BetterEmbed):
        embed.set_field_at(
            1,
            name="Your hand :",
            value="\n".join([str(c) for c in self.hand]),
            inline=True,
        )
        await original.edit(embed=embed)
        return embed


class Blackjack:
    def __init__(
        self, ctx: NewCtx, original: Message, embed: BetterEmbed, timeout: int = 30
    ) -> None:
        self.move_options = ["h", "hit", "s", "stay", "q", "quit"]

        self.move_counter = 0
        self.timeout = timeout
        self.winner = None

        self.ctx = ctx
        self.bot = ctx.bot
        self.original = original
        self.embed = self.create_placeholders(embed)
        print(len(self.embed.fields))

        self.player_field = 1
        self.dealer_field = 2
        self.ace_field = 3

        self.deck = Deck()

        self.player = Player(ctx.author.display_name, [], 0, ctx.author.id, True, False)
        self.player.add_cards(self.deck.get())
        self.player.add_cards(self.deck.get())
        self.embed.set_field_at(
            self.player_field,
            name="Your hand :",
            value="\n".join([str(c) for c in self.player.hand]),
            inline=True,
        )

        self.dealer = Player("Dealer", [], 0, 0, False, False)
        self.dealer.add_cards(self.deck.get())
        self.dealer.add_cards(self.deck.get())
        self.embed.set_field_at(
            self.dealer_field,
            name="Dealer's face up card :",
            value=str(self.dealer.hand[0]),
            inline=True,
        )

    def create_placeholders(self, embed: BetterEmbed):
        embed.insert_field_at(1, name="\u200b", value="\u200b", inline=True)
        embed.insert_field_at(2, name="\u200b", value="\u200b", inline=True)
        return embed

    async def calculate_score(self, target: Player) -> int:
        cards = target.hand
        hand_val = 0

        def ace_check(m):
            return (
                m.author.id == self.player.id
                and m.channel == self.ctx.channel
                and m.content in ["1", "11"]
            )

        for card in cards:
            if card.name != "A":
                hand_val += card.value
            else:
                if target.id == 0:
                    hand_val += 11
                else:
                    self.embed.insert_field_at(
                        self.ace_field,
                        name="\u200b",
                        value="You got an ace, do you want it to be 1 or 11?",
                    )
                    await self.original.edit(embed=self.embed)
                    try:
                        reply = await self.bot.wait_for(
                            "message", check=ace_check, timeout=self.timeout
                        )
                        reply = int(reply.content)
                        hand_val += reply

                        if reply == 11:
                            card.ace()

                        self.embed.remove_field(self.ace_field)
                        self.embed = await self.player.update_hand(
                            self.original, self.embed
                        )
                        await self.original.edit(embed=self.embed)

                    except asyncio.TimeoutError:
                        await self.ctx.send("You took too long, dealer wins")
                        self.dealer.is_winner = True
                        self.player.is_turn = False
                        break

        if hand_val <= 21 and len(target.hand) == 5:
            target.is_winner = True

        if hand_val == 21:
            if len(target.hand) == 2:
                self.embed.add_field(name="Blackjack!", value="\u200b")
                await self.original.edit(embed=self.embed)
            target.is_winner = True

        return hand_val

    async def player_turn(self):
        def move_check(m):
            return (
                m.author.id == self.player.id
                and m.channel == self.original.channel
                and m.content.lower() in self.move_options
            )

        self.dealer.score = await self.calculate_score(self.dealer)

        while self.player.is_turn:
            self.move_counter += 1
            self.player.score = await self.calculate_score(self.player)

            if self.player.score < 21:
                try:
                    reply = await self.bot.wait_for(
                        "message", check=move_check, timeout=self.timeout
                    )
                    choice = reply.content.lower()
                    if choice in ["h", "hit"]:
                        card = self.deck.get()
                        await asyncio.sleep(1)
                        self.embed.add_field(
                            name="\u200b",
                            value=f"**You got : {str(card)}**",
                            inline=False,
                        )
                        self.player.add_cards(card)
                        self.embed = await self.player.update_hand(
                            self.original, self.embed
                        )
                        self.player.score = await self.calculate_score(self.player)
                        if self.player.is_winner:
                            self.player.is_turn = False
                            break

                    elif choice in ["s", "stay"]:
                        self.embed.add_field(
                            name="\u200b",
                            value="Bold strategy cotton, lets see how that plays out",
                            inline=False,
                        )
                        self.embed.add_field(
                            name="Your next card would've been :\n",
                            value=str(self.deck.show_next()),
                            inline=False,
                        )
                        await self.original.edit(embed=self.embed)
                        self.player.is_turn = False
                        self.dealer.is_turn = True
                        await asyncio.sleep(1)
                        break

                    else:
                        if self.move_counter == 1:
                            self.embed.add_field(
                                name="You cash out on your first move",
                                value="\u200b",
                                inline=False,
                            )
                            await self.original.edit(embed=self.embed)
                            self.winner = "Draw"
                            self.player.is_turn = False
                            self.dealer.is_turn = True
                            break
                        else:
                            self.embed.add_field(
                                name="You can only do this on your first move",
                                value="\u200b",
                                inline=False,
                            )
                            await self.original.edit(embed=self.embed)
                            continue

                except asyncio.TimeoutError:
                    await self.ctx.send("You took too long, dealer wins")
                    self.dealer.is_winner = True
                    self.player.is_turn = False
                    self.dealer.is_turn = False
                    break

            elif self.player.score == 21:
                self.player.is_winner = True
                self.player.is_turn = False
                break

            elif self.player.score > 21:
                self.embed.add_field(
                    name="\u200b",
                    value=f"**Your last card, {str(self.player.hand[-1])}, put you over 21.**",
                    inline=False,
                )
                self.embed = await self.player.update_hand(self.original, self.embed)
                self.dealer.is_winner = True
                self.player.is_turn = False
                break

    async def dealer_turn(self):
        while self.dealer.is_turn:
            while self.dealer.score < 21:

                while self.dealer.score < 17:
                    card = self.deck.get()
                    self.dealer.add_cards(card)
                    self.dealer.score = await self.calculate_score(self.dealer)
                    await asyncio.sleep(1)

                else:
                    self.dealer.is_turn = False
                    break

            if self.dealer.score == 21:
                if self.player.score == 21:
                    self.winner = "Draw"
                    self.player.is_winner = False
                    self.dealer.is_winner = False
                    break
                else:
                    self.dealer.is_winner = True
                    self.dealer.is_turn = False
                    break

            elif self.dealer.score > 21:
                self.player.is_winner = True
                self.dealer.is_turn = False
                break

    async def game_end(self):
        playerwin = self.player.is_winner
        dealerwin = self.dealer.is_winner
        draw = bool(self.winner)

        if playerwin and not dealerwin and not draw:
            winner = self.player
        elif dealerwin and not playerwin and not draw:
            winner = self.dealer
        else:
            winner = "Draw"

        self.embed.add_field(
            name=f"Winner : {getattr(winner, 'name', 'No one')}",
            value=f"Player score : {self.player.score} || Dealer score : {self.dealer.score}",
            inline=False,
        )
        self.embed.set_field_at(
            self.dealer_field,
            name="Dealer's hand :",
            value="\n".join([str(c) for c in self.dealer.hand]),
            inline=True,
        )
        await self.original.edit(embed=self.embed)

        return winner
