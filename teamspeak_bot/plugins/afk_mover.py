from __future__ import annotations

from contextlib import suppress
from typing import TYPE_CHECKING

from tsbot import plugin, query
from tsbot.exceptions import TSException, TSResponseError

from teamspeak_bot.common import CLIENT_LIST_QUERY
from teamspeak_bot.plugins import BasePluginConfig
from teamspeak_bot.utils import cache, find

if TYPE_CHECKING:
    from tsbot import TSBot, TSTask


DEFAULT_AFK_CHANNEL = "AFK"
DEFAULT_IDLE_TIME = 30 * 60


class AFKMoverConfig(BasePluginConfig, total=False):
    afk_channel: str
    idle_time: float


DEFAULT_CONFIG = AFKMoverConfig(
    enabled=True,
)


def is_active(client: dict[str, str], max_idle_time: float) -> bool:
    return int(client.get("client_idle_time", 0)) < max_idle_time


def in_afk_channel(client: dict[str, str], afk_channel_id: str) -> bool:
    return client.get("cid", "") == afk_channel_id


def is_query(client: dict[str, str]) -> bool:
    return client["client_type"] == "1"


class AFKMover(plugin.TSPlugin):
    CHECK_INTERVAL = 60  # Check every minute

    def __init__(self, config: AFKMoverConfig) -> None:
        self.afk_channel = config.get("afk_channel", DEFAULT_AFK_CHANNEL)
        self.idle_time = config.get("idle_time", DEFAULT_IDLE_TIME) * 1000

        self.afk_channel_id: str = ""
        self.task: TSTask | None = None

    def should_be_moved(self, client: dict[str, str]) -> bool:
        if is_query(client):
            return False

        if is_active(client, self.idle_time):
            return False

        if in_afk_channel(client, self.afk_channel_id):  # noqa: SIM103
            return False

        return True

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
    async def get_afk_channel(self, bot: TSBot, ctx: None) -> None:
        channel_list = await bot.send(query("channellist"))

        channel_id = find.from_iterable(channel_list, self.afk_channel, "channel_name", "cid")
        if not channel_id:
            raise TSException("No AFK Channel Found")

        self.afk_channel_id = channel_id

    @plugin.on("connect")
    async def start_afk_mover(self, bot: TSBot, ctx: None) -> None:
        self.task = bot.register_every_task(
            self.CHECK_INTERVAL, self.afk_mover_task, name="AFKMover-Task"
        )

    @plugin.on("disconnect")
    async def stop_afk_mover(self, bot: TSBot, ctx: None) -> None:
        if self.task is not None:
            self.task = bot.remove_task(self.task)
