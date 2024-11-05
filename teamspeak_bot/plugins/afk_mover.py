from __future__ import annotations

from contextlib import suppress
from typing import TYPE_CHECKING

from tsbot import plugin, query
from tsbot.exceptions import TSResponseError

from teamspeak_bot.common import CHANNEL_LIST_QUERY, CLIENT_LIST_QUERY
from teamspeak_bot.plugins import BasePluginConfig
from teamspeak_bot.utils import cache, find

if TYPE_CHECKING:
    from collections.abc import Callable

    from tsbot import TSBot, TSTask


DEFAULT_AFK_CHANNEL = "AFK"
DEFAULT_IDLE_TIME = 30 * 60  # 30 mins


class AFKMoverConfig(BasePluginConfig, total=False):
    afk_channel: str
    idle_time: float
    channel_whitelist: tuple[str, ...]
    channel_blacklist: tuple[str, ...]


DEFAULT_CONFIG = AFKMoverConfig(
    enabled=True,
)


def create_should_be_moved(
    max_idle_time: float,
    afk_channel_id: str,
    whitelist: tuple[str, ...] | None,
    blacklist: tuple[str, ...] | None,
) -> Callable[[dict[str, str]], bool]:
    def is_not_active(client: dict[str, str]) -> bool:
        return int(client.get("client_idle_time", 0)) > max_idle_time

    def not_in_afk_channel(client: dict[str, str]) -> bool:
        return client.get("cid", "") != afk_channel_id

    def is_not_query(client: dict[str, str]) -> bool:
        return client["client_type"] != "1"

    def not_in_blacklisted_channel(client: dict[str, str]) -> bool:
        return client["cid"] not in blacklist if blacklist else True

    def in_whitelisted_channel(client: dict[str, str]) -> bool:
        return client["cid"] in whitelist if whitelist else True

    checks = (
        is_not_active,
        not_in_afk_channel,
        is_not_query,
        not_in_blacklisted_channel,
        in_whitelisted_channel,
    )

    def should_be_moved(client: dict[str, str]) -> bool:
        return all(check(client) for check in checks)

    return should_be_moved


class AFKMover(plugin.TSPlugin):
    CHECK_INTERVAL = 60  # Check every minute

    def __init__(self, config: AFKMoverConfig) -> None:
        self.afk_channel = config.get("afk_channel", DEFAULT_AFK_CHANNEL)
        self.idle_time = config.get("idle_time", DEFAULT_IDLE_TIME) * 1000

        self.afk_channel_id: str = ""
        self.task: TSTask | None = None

        self.whitelisted_channels = config.get("channel_whitelist")
        self.blacklisted_channels = config.get("channel_blacklist")

        self.should_be_moved: Callable[[dict[str, str]], bool] = lambda c: False

    async def afk_mover_task(self, bot: TSBot) -> None:
        client_list = await cache.with_cache(
            bot.send, CLIENT_LIST_QUERY, max_ttl=self.CHECK_INTERVAL
        )

        to_be_moved = set(map(lambda c: c["clid"], filter(self.should_be_moved, client_list)))
        if not to_be_moved:
            return

        move_query = (
            query("clientmove")
            .params(cid=self.afk_channel_id)
            .param_block({"clid": clid} for clid in to_be_moved)
        )

        with suppress(TSResponseError):
            await bot.send(move_query)

    @plugin.once("connect")
    async def init_afk(self, bot: TSBot, ctx: None) -> None:
        self.afk_channel_id = await self.get_afk_channel(bot)
        self.should_be_moved = create_should_be_moved(
            self.idle_time,
            self.afk_channel_id,
            await self.get_whitelist_ids(bot),
            await self.get_blacklisted_ids(bot),
        )

    async def get_afk_channel(self, bot: TSBot) -> str:
        channel_list = await cache.with_cache(bot.send, CHANNEL_LIST_QUERY, max_ttl=60)

        channel_id = find.from_iterable(channel_list, self.afk_channel, "channel_name", "cid")
        if not channel_id:
            channel_id = await self.create_afk_channel(bot)

        return channel_id

    async def create_afk_channel(self, bot: TSBot) -> str:
        resp = await bot.send(
            query("channelcreate").params(
                channel_name=self.afk_channel, channel_flag_permanent=True
            )
        )

        return resp.first["cid"]

    async def get_whitelist_ids(self, bot: TSBot) -> tuple[str, ...] | None:
        if self.whitelisted_channels is None:
            return None

        channel_list = await cache.with_cache(bot.send, CHANNEL_LIST_QUERY, max_ttl=60)

        return tuple(
            c["cid"]
            for c in channel_list
            if any(wlc in c["channel_name"] for wlc in self.whitelisted_channels)
        )

    async def get_blacklisted_ids(self, bot: TSBot) -> tuple[str, ...] | None:
        if self.blacklisted_channels is None:
            return None

        channel_list = await cache.with_cache(bot.send, CHANNEL_LIST_QUERY, max_ttl=60)

        return tuple(
            c["cid"]
            for c in channel_list
            if any(blc in c["channel_name"] for blc in self.blacklisted_channels)
        )

    @plugin.on("connect")
    async def start_afk_mover(self, bot: TSBot, ctx: None) -> None:
        self.task = bot.register_every_task(
            self.CHECK_INTERVAL, self.afk_mover_task, name="AFKMover-Task"
        )

    @plugin.on("disconnect")
    async def stop_afk_mover(self, bot: TSBot, ctx: None) -> None:
        if self.task is not None:
            self.task = bot.remove_task(self.task)
