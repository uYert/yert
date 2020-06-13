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
import contextlib
import copy
import itertools
import random
import typing

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
    operators = ('-', '+')  # those should be all caps
    spacing_row = '\n' * 2
    spacing_column = ' ' * 2
    white_flag = '🏳️'

    def __init__(self,
                 *,
                 p1: discord.Member,
                 p2: discord.Member,
                 aligned_amount: int = 4,
                 column_amount: int = 7,
                 row_amount: int = 6):

        super().__init__(timeout=30, clear_reactions_after=True, check_embeds=True)

        self.emojis = ('⬛', '🟢', '🔴')  # ids : (0, 1, -1)

        self.aligned_amount = aligned_amount
        self.is_timeout_win = True

        self.players = [Player(p1.id, p1.mention, 1), Player(p2.id, p2.mention, -1)]
        self.cycle_players = itertools.cycle((lambda x: [random.shuffle(x), x][1])(self.players))  # type: ignore
        self.current_player: Player = next(self.cycle_players)

        self.grid = grid = [[0 for _ in range(column_amount)] for _ in range(row_amount)]

        self.backup_grid = [[0 for _ in range(column_amount)] for _ in range(row_amount)]  # less painful than deepcopy

        title = f'Connect {self.aligned_amount} using {row_amount} rows and {column_amount} columns'
        self.embed_template = formatters.BetterEmbed(title=title)

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

        async def on_french(self, payload: discord.RawReactionActionEvent):  # not very dry, but we clear the buttons everytime
            self.stop()

        maybecoro = self.add_button(menus.Button(self.white_flag, on_french), react=react)
        if maybecoro is not None:
            await maybecoro

    async def prevent_burying(self) -> None:
        """
        Checks if the menu hasn't been burried too far into messages
        """
        def check(m: discord.Message):
            return m.channel == self.ctx.channel

        counter = 0
        while self._running:
            try:
                msg = await self.bot.wait_for('message', check=check, timeout=5)
            except asyncio.TimeoutError:
                continue

            else:
                counter += len(msg.content.split('\n'))
                if msg.embeds or msg.attachments:
                    counter += 9

                if counter >= 12:
                    await self.message.delete()
                    self.clear_buttons()
                    self.message = await self.ctx.send(**self.to_send(self.grid, self.current_player))
                    await self.make_buttons(react=True)
                    counter = 0

    async def start(self, ctx, *, channel=None, wait=False) -> None:
        await self.make_buttons()
        await super().start(ctx, channel=channel, wait=wait)
        self.bury_task = self.bot.loop.create_task(self.prevent_burying())

    def get_emoji(self, id_: int) -> str:
        """Gets the emoji corresponding to the id"""
        return self.emojis[id_]

    def format_row(self, row: typing.List[int]) -> str:
        """Formats a row xd"""
        return self.spacing_column.join(map(self.get_emoji, row))

    def format_grid(self, grid: typing.List[typing.List[int]]) -> str:
        """Formats the grid into an str"""
        return (f"```\n{self.spacing_row.join(map(self.format_row, grid))}"
                f"{self.spacing_row}{self.f_keycaps}```")

    def to_send(self, grid: typing.List[typing.List[int]], current_player: Player
                ) -> typing.Dict[str, typing.Union[str, formatters.BetterEmbed]]:
        """Formats the full message to send"""
        curr_player = self.current_player
        return {'content': curr_player.mention + ' - ' + self.emojis[curr_player.token_id],
                'embed': self.embed_template(description=self.format_grid(grid))}

    async def send_initial_message(self, ctx: main.NewCtx, channel: discord.abc.Messageable) -> discord.Message:
        """Sends the initial grid"""
        return await channel.send(**self.to_send(self.grid, self.current_player))

    def reaction_check(self, payload: discord.RawReactionActionEvent) -> bool:
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

        await self.message.edit(**self.to_send(self.grid, self.current_player))

        return row_index, column_index

    def get_lines(self, grid: typing.List[typing.List[int]], *,
                  row_index: int, column_index: int) -> typing.List[typing.List[int]]:
        """Gets all lines around the newly placed token"""
        operators = self.operators
        max_offset = self.max_offset

        for line in (grid[row_index], [row[column_index] for row in grid]):  # horizontal, vertical
            yield line

        # sideways up to down, both ways
        for left_operator, right_operator in (operators, reversed(operators)):
            nums = []
            for offset in range(max_offset * 2):

                y_offset = row_index - max_offset + offset
                x_offset = eval(f"column_index {left_operator} max_offset {right_operator} offset", locals())

                if min(y_offset, x_offset) < 0:
                    continue

                with contextlib.suppress(IndexError):
                    nums.append(grid[y_offset][x_offset])

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

    async def check_filled_grid(self, grid: typing.List[typing.List[int]]) -> None:
        """Checks if the grid is completely filled"""
        if not 0 in grid[0]:
            self.grid = self.backup_grid
            await self.update_grid(None)

    async def on_keycap(self, payload: discord.RawReactionActionEvent) -> None:
        """Dispatches the keycaps"""
        row_index, column_index = await self.update_grid(payload)
        if None in {row_index, column_index}:
            return

        lines = [*self.get_lines(self.grid, row_index=row_index, column_index=column_index)]

        if winner := self.check_winner(lines):
            self.is_timeout_win = False
            return self.stop()

        await self.check_filled_grid(self.grid)

    async def finalize(self) -> None:
        if self.is_timeout_win:
            self.current_player = next(self.cycle_players)

        await self.message.edit(embed=self.embed_template(description=self.format_grid(self.grid)),
                                content=self.current_player.mention + ' won ! ')

