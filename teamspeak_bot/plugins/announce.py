from __future__ import annotations

from typing import TYPE_CHECKING

from result import Err, Ok, Result, as_async_result
from tsbot import plugin, query
from tsbot.exceptions import TSCommandError, TSResponseError

from teamspeak_bot.common import CLIENT_LIST_QUERY
from teamspeak_bot.plugins import BasePluginConfig
from teamspeak_bot.utils import cache, checks, find

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping

    from tsbot import TSBot, TSCtx


DEFAULT_ALLOWED_UIDS: tuple[str, ...] = ()
DEFAULT_ALLOWED_SERVER_GROUPS: tuple[str, ...] = ("Admin",)


class AnnouncementConfig(BasePluginConfig, total=False):
    allowed_uids: tuple[str, ...]
    allowed_server_groups: tuple[str, ...]
    strict_server_group_checking: bool


DEFAULT_CONFIG = AnnouncementConfig(
    enabled=True,
)


class AnnouncementPlugin(plugin.TSPlugin):
    def __init__(self, bot: TSBot, config: AnnouncementConfig) -> None:
        announce_check = (
            checks.check_uids_and_server_groups(
                uids=config.get("allowed_uids", DEFAULT_ALLOWED_UIDS),
                server_groups=config.get("allowed_server_groups", DEFAULT_ALLOWED_SERVER_GROUPS),
                strict=config.get("strict_server_group_checking", False),
            ),
        )

        bot.register_command("announce", self.announce, checks=announce_check)

    async def _get_server_group_clients(
        self, bot: TSBot, group: str, clients: Iterable[Mapping[str, str]]
    ) -> Result[Iterable[Mapping[str, str]], str]:
        server_groups = await bot.send(query("servergrouplist"))

        group_id = find.from_iterable(
            server_groups,
            search=group,
            key="name",
            result="sgid",
            predicate=lambda g: g["type"] == "1",
        )

        if group_id is None:
            return Err("No such group")

        server_group_clientlist = await as_async_result(TSResponseError)(bot.send)(
            query("servergroupclientlist").params(sgid=group_id)
        )

        if isinstance(server_group_clientlist, Err):
            return server_group_clientlist.map_err(lambda e: str(e))

        server_group_clients = {client["cldbid"] for client in server_group_clientlist.unwrap()}
        return Ok(filter(lambda c: c["client_database_id"] in server_group_clients, clients))

    async def announce(self, bot: TSBot, ctx: TSCtx, message: str, group: str = "all") -> None:
        client_list = await cache.with_cache(bot.send, CLIENT_LIST_QUERY)
        poke_query = query("clientpoke").params(msg=message)

        if group != "all":
            client_list = (
                await self._get_server_group_clients(bot, group, client_list)
            ).unwrap_or_raise(TSCommandError)

        await bot.send_batched(poke_query.params(clid=c["clid"]) for c in client_list)
