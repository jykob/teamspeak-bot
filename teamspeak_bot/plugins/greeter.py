from __future__ import annotations

from contextlib import suppress
from typing import TYPE_CHECKING

from tsbot import plugin, query
from tsbot.exceptions import TSException, TSResponseError

from teamspeak_bot.common import SERVER_GROUPS_QUERY
from teamspeak_bot.plugins import BasePluginConfig
from teamspeak_bot.utils import cache

if TYPE_CHECKING:
    from tsbot import TSBot, TSCtx


DEFAULT_MESSAGE = "Welcome to server, {client_nickname}"


class GreeterConfig(BasePluginConfig, total=False):
    message: str


DEFAULT_CONFIG = GreeterConfig(
    enabled=True,
)


class GreeterPlugin(plugin.TSPlugin):
    POKE_QUERY = query("clientpoke")

    def __init__(self, config: GreeterConfig) -> None:
        self.message = config.get("message", DEFAULT_MESSAGE)

        self.guest_id: str = ""

    @plugin.once("connect")
    async def get_guest_id(self, bot: TSBot, ctx: None) -> None:
        server_groups = await cache.with_cache(bot.send, SERVER_GROUPS_QUERY, max_ttl=60)

        guest_id = None
        for group in server_groups:
            if group["name"] == "Guest" and group["type"] == "1":
                guest_id = group["sgid"]

        if not guest_id:
            raise TSException("Failed to find 'Guest' server id")

        self.guest_id = guest_id

    @plugin.on("cliententerview")
    async def handle_client_enter(self, bot: TSBot, ctx: TSCtx) -> None:
        # Only greet users who have no server groups
        if ctx["client_servergroups"] != self.guest_id:
            return

        poke_query = self.POKE_QUERY.params(clid=ctx["clid"], msg=self.message.format(**ctx))
        with suppress(TSResponseError):
            await bot.send(poke_query)
