from __future__ import annotations

import asyncio
from contextlib import suppress
from typing import TYPE_CHECKING

from tsbot import plugin, query
from tsbot.exceptions import TSResponseError

from teamspeak_bot.common import CLIENT_LIST_QUERY
from teamspeak_bot.plugins import BasePluginConfig
from teamspeak_bot.utils import cache

if TYPE_CHECKING:
    from collections.abc import Callable

    from tsbot import TSBot, TSCtx, TSTask


REASON_KICK_SERVER = 5
DEFAULT_MESSAGE = "Nickname banned"
DEFAULT_CHECK_PERIOD = 30


class BannedNamesConfig(BasePluginConfig, total=False):
    banned_names: tuple[str, ...]
    is_banned_name: Callable[[str], bool]
    message: str
    check_period: float


DEFAULT_CONFIG = BannedNamesConfig(
    enabled=True,
    banned_names=("TeamSpeakUser",),
)


class BannedNamesPlugin(plugin.TSPlugin):
    KICK_QUERY = query("clientkick").params(reasonid=REASON_KICK_SERVER)

    def __init__(self, bot: TSBot, config: BannedNamesConfig) -> None:
        self.message = config.get("message", DEFAULT_MESSAGE)
        self.banned_names = config.get("banned_names")
        self.is_banned_name = config.get("is_banned_name")
        self.check_period = config.get("check_period", DEFAULT_CHECK_PERIOD)

        self.check_task: TSTask | None = None

        if self.banned_names is None and self.is_banned_name is None:
            raise RuntimeError("Either 'banned_names' or 'is_banned_name' has to be declared")

        bot.register_event_handler("cliententerview", self.check_for_banned_names_on_enter)
        bot.register_event_handler("connect", self.start_check_task)
        bot.register_event_handler("disconnect", self.cancel_check_task)

    async def start_check_task(self, bot: TSBot, ctx: None) -> None:
        self.check_task = bot.register_every_task(
            self.check_period, self.check_for_banned_names_periodically
        )

    async def cancel_check_task(self, bot: TSBot, ctx: None) -> None:
        if self.check_task:
            self.check_task = bot.remove_task(self.check_task)

    def check_client_nickname(self, nickname: str) -> bool:
        return bool(
            self.banned_names is not None
            and nickname in self.banned_names
            or self.is_banned_name is not None
            and self.is_banned_name(nickname)
        )

    async def check_for_banned_names_on_enter(self, bot: TSBot, ctx: TSCtx) -> None:
        if self.check_client_nickname(ctx["client_nickname"]):
            await self.kick_client(bot, ctx["clid"])

    async def check_for_banned_names_periodically(self, bot: TSBot) -> None:
        client_list = await cache.with_cache(bot.send, CLIENT_LIST_QUERY, max_ttl=0)

        kick_coros = tuple(
            self.kick_client(bot, client["clid"])
            for client in client_list
            if self.check_client_nickname(client["client_nickname"])
        )

        if not kick_coros:
            return

        await asyncio.gather(*kick_coros)

    async def kick_client(self, bot: TSBot, clid: str) -> None:
        with suppress(TSResponseError):
            await bot.send(self.KICK_QUERY.params(clid=clid, reasonmsg=self.message))
