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
from collections import deque, namedtuple
from datetime import datetime, timedelta
from enum import Enum
import random
from typing import List

random.seed(datetime.utcnow())


class Payouts(Enum):
    STRAIGHT = 35
    RED = 1
    BLACK = 1
    EVEN = 1
    ODD = 1
    LOW = 1
    HIGH = 1
    FIRSTCOL = 2
    SECONDCOL = 2
    THIRDCOL = 2
    FIRST12 = 2
    SECOND12 = 2
    THIRD12 = 2


class Player:
    def __init__(self, name: str, player_id: int):
        self.name = name
        self.id = player_id
        self.payout = 0
        self.returned = 0
        self.bets = deque()

    def place_bet(self, **kwargs):
        bet = kwargs.get('bet')
        try:
            bet = int(bet)
        except ValueError:
            bet = bet
        amount = kwargs.get('amount', 15)
        self.bets.append((bet, amount))

    def __repr__(self) -> str:
        return f"<Player name={self.name} id={self.id} bets={len(self.bets)}>"

    def __str__(self) -> str: return self.name

    def __int__(self) -> int: return self.id


Bet = namedtuple('Bet', ['name', 'winners'])


class Tile:
    def __init__(self, name, **kwargs):
        self.name = name
        self.colour = kwargs.get('colour', None)
        self.column = kwargs.get('column', None)
        self.dozen = kwargs.get('dozen', None)
        self.half = kwargs.get('half', None)

    def __repr__(self) -> str:
        return f"<Tile name={self.name} colour={self.colour}>"

    def __str__(self) -> str:
        return ", ".join(self.__dict__)


class Table:
    def __init__(self):
        self.tiles = []
        self.tiles.append(Tile(0))
        for number in range(1, 37):
            column = 'first'
            dozen = 'first'
            colour = 'black'
            half = 'low'
            if (number % 2) == 0:
                colour = 'red'
            if 19 <= number <= 36:
                half = 'high'
            if 13 <= number <= 24:
                dozen = 'second'
            if 25 <= number <= 36:
                dozen = 'third'
            if (number % 3) == 0:
                column = 'third'
            if (number+1) % 3 == 0:
                column = 'second'
            self.tiles.append(Tile(number, colour=colour, column=column, half=half, dozen=dozen))
        self.firstcol = Bet('firstcol', [t.name for t in self.tiles if t.column == 'first'])
        self.secondcol = Bet('secondcol', [t.name for t in self.tiles if t.column == 'second'])
        self.thirdcol = Bet('thirdcol', [t.name for t in self.tiles if t.column == 'third'])
        self.first12 = Bet('first12', [t.name for t in self.tiles if t.dozen == 'first'])
        self.second12 = Bet('second12', [t.name for t in self.tiles if t.dozen == 'second'])
        self.third12 = Bet('third12', [t.name for t in self.tiles if t.dozen == 'third'])
        self.odd = Bet('odd', [t.name for t in self.tiles if t.name % 2 != 0])
        self.even = Bet('even', [t.name for t in self.tiles if t.name % 2 == 0])
        self.red = Bet('red', [t.name for t in self.tiles if t.colour == 'red'])
        self.black = Bet('black', [t.name for t in self.tiles if t.colour == 'black'])
        self.high = Bet('high', [t.name for t in self.tiles if t.half == 'high'])
        self.low = Bet('low', [t.name for t in self.tiles if t.half == 'low'])

        self.bets = [self.low, self.high, self.black, self.red, self.odd, self.even,
                     self.first12, self.second12, self.third12, self.firstcol, self.secondcol, self.thirdcol]


class Wheel:
    def __init__(self):
        self.spots = [*range(0, 37)]

    def spin(self) -> int:
        return random.choice(self.spots)


class Game:
    def __init__(self):
        self.table = Table()
        self.wheel = Wheel()
        self.landed = None
        self.players = dict()

    def add_player(self, player):
        if not self.players.get(player.id, False):
            self.players[player.id] = deque()

    def handle_bets(self):
        self.landed = self.spin_wheel()
        results = dict()
        for player, bets in self.players.items():
            print(bets)
            result = 0
            if player not in results:
                results[player] = []
            for bet, amount in bets:
                payout = self.calculate(bet)
                result += payout * amount
                results[player].append([bet, result])
        print(results)
        return results

    def spin_wheel(self) -> int:
        return self.wheel.spin()

    @property
    def winning_bets(self) -> List:
        return [bet.name for bet in self.table.bets if self.landed in bet.winners]

    def calculate(self, bet) -> int:
        payout = 0
        if isinstance(bet, int):
            if bet == self.landed:
                payout += 35
                return payout
        else:
            if getattr(self.table, bet).name in self.winning_bets:
                payout += getattr(Payouts, bet.upper()).value
                return payout
        return 0
