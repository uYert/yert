from itertools import cycle

import discord


class Player:
    def __init__(self, player: discord.Member, mark: str):
        self.player = player
        self.mark = mark


class Connect4:
    def __init__(self, ctx, players, columns=7, rows=6):
        self.columns = columns
        self.rows = rows
        self.ctx = ctx
        self.players = cycle(players)
        self.grid = [["⬛" for _ in range(rows)] for _ in range(columns)]
        self.current_player = players[0]
        self.react_emojis = {
            str(n) + "\N{variation selector-16}\N{combining enclosing keycap}": n - 1
            for n in range(1, columns + 1)
        }
        self.plays = 0

    def check_winner(self) -> bool:
        column_counter = diagonal_counter = row_counter = 0
        for array_index, array in enumerate(self.grid):
            for index, _ in enumerate(array):
                if (
                    array_index < self.rows
                    and self.grid[index][array_index] == self.current_player.mark
                ):
                    row_counter += 1
                else:
                    row_counter = 0
                if (
                    index < self.columns
                    and self.grid[array_index][index] == self.current_player.mark
                ):
                    column_counter += 1
                else:
                    column_counter = 0
        # If any of these 3 is equal to three then we have a winner
        if any([x >= 4 in (column_counter, diagonal_counter, row_counter)]):
            return True
        return False

    async def play(self):
        self.message = await self.ctx.send(
            f"{self.current_player.player.mention}, it's your turn !\n```{self.draw_grid()}```"
        )
        for emoji in self.react_emojis:
            await self.message.add_reaction(emoji)
        while True:
            await self.update_pos()
            self.plays += 1
            # check if someone has one only when the players played 8 times
            # the reason for that is: that we need at least 4 moves
            # from a player to win
            if self.plays >= 8 and self.check_winner():
                await self.ctx.send(
                    f"Congratulations ! {self.current_player.player.mention} has won the game."
                )
            else:
                self.current_player = next(self.players)
                await self.message.edit(
                    content=f"{self.current_player.player.mention}, it's your turn !\n```{self.draw_grid()}```"
                )

    def draw_grid(self):
        drawn_grid = ""
        for array_index, array in enumerate(self.grid):
            for index in range(len(array)):
                if array_index >= len(array):
                    break
                drawn_grid += f"{self.grid[array_index][index]}  "
                if index + 1 == len(array):
                    drawn_grid += f"{self.grid[array_index][index]}\n\n"
        return drawn_grid

    async def update_pos(self):
        emoji = await self.get_input()
        # Get the index for the array corresponding to that emoji
        index = self.react_emojis.get(emoji)
        for count, array in enumerate(self.grid):
            if count >= len(array):
                break
            # The first item which is not the default value
            # will be updated to be the current's player mark
            if array[index] == "⬛":
                self.grid[count][index] = self.current_player.mark
                break
            # if we are in the last iteration and we still haven't found
            # an empty slot then this column is completed
            if count + 1 == len(self.grid):
                if self.bot.permissions_in(self.ctx.channel).manage_messages:
                    # TODO: Remove the reaction
                    await self.message.remove_reaction(self.emoji)

    async def get_input(self) -> str:
        def check(reaction, user):
            return (
                user.id == self.current_player.player.id
                and str(reaction.emoji) in self.react_emojis
            )

        reaction, user = await self.ctx.bot.wait_for(
            "reaction_add", check=check, timeout=30.0
        )
        return str(reaction.emoji)
