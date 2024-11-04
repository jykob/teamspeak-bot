from __future__ import annotations

import asyncio
import functools
from contextlib import suppress
from typing import TYPE_CHECKING

from tsbot import TSCtx, plugin, query
from tsbot.exceptions import TSCommandError, TSResponseError

from teamspeak_bot.plugins import BasePluginConfig
from teamspeak_bot.utils import formatters, parsers, try_

if TYPE_CHECKING:
    from tsbot import TSBot


DEFAULT_MAX_DELAY = 60 * 60


class NotifyConfig(BasePluginConfig, total=False):
    max_delay: int


DEFAULT_CONFIG = NotifyConfig(
    enabled=True,
)


class NotifyPlugin(plugin.TSPlugin):
    def __init__(self, config: NotifyConfig) -> None:
        self.max_delay = config.get("max_delay", DEFAULT_MAX_DELAY)

    @plugin.command(
        "notify",
        help_text="Pokes you after given amount of time in seconds or in XXh XXm XXs format",
    )
    async def notify_after(self, bot: TSBot, ctx: TSCtx, time: str, *message: str) -> None:
        delay = try_.or_none(parsers.parse_time, time)

        if delay is None:
            raise TSCommandError("Invalid time format")

        if self.max_delay and delay > self.max_delay:
            raise TSCommandError(f"Time must be under {formatters.seconds_to_time(self.max_delay)}")

        bot.register_task(
            functools.partial(
                self.notify_task,
                client_id=ctx["invokerid"],
                message=" ".join(message),
                delay=delay,
            )
        )

    async def notify_task(self, bot: TSBot, client_id: str, message: str, delay: int) -> None:
        await asyncio.sleep(delay)
        with suppress(TSResponseError):
            await bot.send(query("clientpoke").params(clid=client_id, msg=message))
