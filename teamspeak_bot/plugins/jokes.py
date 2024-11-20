from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, NamedTuple

import httpx
from result import Err, Ok, Result
from tsbot import plugin
from tsbot.exceptions import TSCommandError

from teamspeak_bot.plugins import BasePluginConfig

if TYPE_CHECKING:
    from tsbot import TSBot, TSCtx


class JokesPluginConfig(BasePluginConfig): ...


DEFAULT_CONFIG = JokesPluginConfig(
    enabled=True,
)


class Joke(NamedTuple):
    setup: str
    delivery: str


class JokesPlugin(plugin.TSPlugin):
    API_URL = "https://v2.jokeapi.dev/joke/Programming?type=twopart"

    async def get_a_joke(self) -> Result[Joke, str]:
        async with httpx.AsyncClient() as client:
            data = (await client.get(self.API_URL)).json()

            if data["error"]:
                return Err(data["message"])

            return Ok(Joke(data["setup"], data["delivery"]))

    @plugin.command("joke", help_text="Tells a programming joke")
    async def tell_a_joke(self, bot: TSBot, ctx: TSCtx) -> None:
        joke = (await self.get_a_joke()).unwrap_or_raise(TSCommandError)
        bot.register_task(self.tell_a_joke_task, ctx, joke)

    async def tell_a_joke_task(self, bot: TSBot, ctx: TSCtx, joke: Joke) -> None:
        await bot.respond(ctx, joke.setup)
        await asyncio.sleep(3)
        await bot.respond(ctx, joke.delivery)
