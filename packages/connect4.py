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
import collections
import itertools
import random
import typing
import contextlib
import copy
import discord

from discord.ext import commands, menus

import main
from utils import formatters


class Prompt(menus.Menu):
    accepted = None
    def __init__(self, msg: typing.Union[str, discord.Embed], **kwargs):
        super().__init__(**kwargs)
        self.msg = msg

    async def send_initial_message(self, ctx: main.NewCtx, channel: discord.abc.Messageable):
        if isinstance(self.msg, discord.Embed):
            return await channel.send(embed=self.msg)
        elif isinstance(self.msg, str):
            return await channel.send(content=self.msg)
        else:
            raise TypeError(f"Expected Embed or string, got {self.message.__class__.__name__}")

    @menus.button('✔️')
    async def on_green(self, payload: discord.RawReactionActionEvent):
        self.accepted = True
        self.stop()

    @menus.button('❌')
    async def on_red(self, payload: discord.RawReactionActionEvent):
        self.accepted = False
        self.stop()

Player = collections.namedtuple('Player', ['id', 'mention', 'token_id'])

class ConnectMenu(menus.Menu):

    emojis = ('⬛', '🟢', '🔴')  # ids : (0, 1, -1)
    operators = ('-', '+')
    spacing_row = '\n' * 2
    spacing_column = ' ' * 2

    def __init__(self,
                 *,
                 p1: discord.Member,
                 p2: discord.Member,
                 aligned_amount: int = 4,
                 column_amount: int = 7,
                 row_amount: int = 6,
                 **kwargs):
        super().__init__(**kwargs)
        self.aligned_amount = aligned_amount

        self.players = [Player(p1.id, p1.mention, 1), Player(p2.id, p2.mention, -1)]
        self.cycle_players = itertools.cycle((lambda x: [random.shuffle(x), x][1])(self.players))  # type: ignore
        self.current_player: Player = next(self.cycle_players)

        self.grid = grid = [[0 for _ in range(column_amount)] for _ in range(row_amount)]
        
        self.backup_grid = [[0 for _ in range(column_amount)] for _ in range(row_amount)]

        self.max_offset = max(len(grid), len(grid[0]))

        self.keycaps = [str(n) + '\N{variation selector-16}\N{combining enclosing keycap}' for n in range(column_amount)]

        self.f_keycaps = self.spacing_column.join(self.keycaps)

    async def make_buttons(self, react: bool = False) -> None:
        """Adds all keycaps emojis as buttons"""
        for key in self.keycaps:
            async def keycap_placeholder(self, payload: discord.RawReactionActionEvent):
                await self.on_keycap(payload)
                
            maybecoro = self.add_button(menus.Button(key, keycap_placeholder), react=react)
            if maybecoro is not None:
                await maybecoro

    async def prevent_burying(self):
        """
        Checks if the menu hasn't been burried too far into messages
        """
        counter = 0
        while self._running:
            try:
                await self.bot.wait_for('message', check=lambda m: m.channel == self.ctx.channel,
                                        timeout=5)
            except asyncio.TimeoutError:
                pass

            else:
                counter += 1

                if counter >= 10:
                    await self.message.delete()
                    self.clear_buttons()
                    self.message = await self.ctx.send(content=self.to_send(self.grid, self.current_player))
                    await self.make_buttons(react=True)
                    counter = 0

    async def start(self, ctx, *, channel=None, wait=False):
        await self.make_buttons()
        await super().start(ctx, channel=channel, wait=wait)
        self.bot.loop.create_task(self.prevent_burying())

    def format_grid(self, grid: typing.List[typing.List[int]]) -> str:  # don't question, it works
        """Formats the grid into an str"""
        return (f"```\n{self.spacing_row.join(((map(lambda row: self.spacing_column.join(map(lambda id_: self.emojis[id_], row)), grid))))}"
                f"{self.spacing_row}{self.f_keycaps}```")

    def to_send(self, grid: typing.List[typing.List[int]], current_player: Player):
        """Formats the full message to send"""
        return self.current_player.mention + self.format_grid(self.grid)

    async def send_initial_message(self, ctx: main.NewCtx, channel: discord.abc.Messageable):
        """Sends the initial grid"""
        return await ctx.send(self.to_send(self.grid, self.current_player))

    def reaction_check(self, payload: discord.RawReactionActionEvent):
        if payload.message_id != self.message.id:
            return False

        if payload.user_id != self.current_player.id:
            return False

        return payload.emoji in self.buttons

    async def update_grid(self, payload: typing.Union[discord.RawReactionActionEvent, None],
                          ) -> typing.Union[typing.Tuple[int, int], typing.Tuple[None, None]]:
        """Updates the displayed grid"""
        row_index = None
        column_index = None
        
        if payload:
            column_index = self.keycaps.index(str(payload.emoji))

            column = [row[column_index] for row in self.grid]

            for index, token_id in enumerate(reversed(column)):  # for some reason I failed to make it work the other way around
                if not token_id:
                    break
            else:
                return None, None # the column is filled

            row_index = len(column) - (index + 1)
            self.grid[row_index][column_index] = self.current_player.token_id
            self.current_player = next(self.cycle_players)

        await self.message.edit(content=self.to_send(self.grid, self.current_player))

        return row_index, column_index

    def get_lines(self, grid: typing.List[typing.List[int]], *,
                  row_index: int, column_index: int) -> typing.List[typing.List[int]]:
        """Gets all lines around the newly placed token"""
        operators = self.operators
        max_offset = self.max_offset
        
        for line in (grid[row_index], [row[column_index] for row in grid]):  # horizontal, vertical
            yield line

        with contextlib.suppress(IndexError):  # sideways up to down, both ways
            for left_operator, right_operator in (operators, reversed(operators)):
                nums = []
                for offset in range(max_offset * 2):

                    y_offset = row_index - max_offset + offset
                    x_offset = eval(f"column_index {left_operator} max_offset {right_operator} offset", locals())

                    if min(y_offset, x_offset) < 0:
                        continue

                    try:
                        nums.append(grid[y_offset][x_offset])
                    except IndexError:
                        pass

                yield nums

    def check_winner(self, lines: typing.List[typing.List[int]]):
        """Checks all provided lines looking for n aligned tokens in a row"""
        aligned_amount = self.aligned_amount

        for line in lines:
            for offset, _ in enumerate(line):
                sliced = line[offset : offset + aligned_amount]
                if abs(sum(sliced)) >= aligned_amount:
                    return [p for p in self.players if p.token_id == sliced[0]][0]
        else:
            return None

    async def check_filled_grid(self, grid: typing.List[typing.List[int]]):
        """Checks if the grid is completely filled"""
        if all(grid[0]):
            self.grid = self.backup_grid
            await self.update_grid(None)

    async def on_keycap(self, payload: discord.RawReactionActionEvent):
        """Dispatches the keycaps"""
        row_index, column_index = await self.update_grid(payload)
        if not (row_index and column_index):
            return
        
        lines = [*self.get_lines(self.grid, row_index=row_index, column_index=column_index)]

        if winner := self.check_winner(lines): 
            await self.ctx.send(winner.mention)
            return self.stop()

        await self.check_filled_grid(self.grid)
