from __future__ import annotations

import random
from typing import TYPE_CHECKING

from tsbot import plugin
from tsbot.exceptions import TSCommandError

from teamspeak_bot.plugins import BasePluginConfig
from teamspeak_bot.utils import try_

if TYPE_CHECKING:
    from tsbot import TSBot, TSCtx


class FunConfig(BasePluginConfig): ...


DEFAULT_CONFIG = FunConfig(
    enabled=True,
)


class FunPlugin(plugin.TSPlugin):
    @plugin.command("coinflip", help_text="Heads or tails")
    async def coin_flip(self, bot: TSBot, ctx: TSCtx) -> None:
        await bot.respond(ctx, random.choice(("Heads!", "Tails!")))

    @plugin.command("roll", help_text="Roll a die")
    async def roll_a_die(self, bot: TSBot, ctx: TSCtx, sides: str = "6") -> None:
        dice = try_.or_none(int, sides)

        if dice is None or dice <= 0:
            raise TSCommandError("Invalid dice")

        await bot.respond(ctx, f"{random.randint(1, dice)}!")
