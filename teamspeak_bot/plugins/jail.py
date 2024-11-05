from __future__ import annotations

import asyncio
import functools
from typing import TYPE_CHECKING

from tsbot import TSBot, TSCtx, TSTask, plugin, query
from tsbot.exceptions import TSCommandError

from teamspeak_bot.common import CHANNEL_LIST_QUERY, SERVER_GROUPS_QUERY
from teamspeak_bot.plugins import BasePluginConfig
from teamspeak_bot.utils import cache, checks, find, parsers, try_

if TYPE_CHECKING:
    from collections.abc import Mapping

DEFAULT_JAIL_CHANNEL = "Jail"
DEFAULT_INMATE_NAME = "Inmate"


class JailConfig(BasePluginConfig, total=False):
    jail_channel: str
    inmate_server_group_name: str
    can_jail_uids: tuple[str, ...]
    can_jail_server_groups: tuple[str, ...]
    strict_server_group_checking: bool


DEFAULT_CONFIG = JailConfig(
    enabled=False,
)

INMATE_SERVER_GROUP_PERMS = (
    {"permsid": "i_channel_join_power", "permvalue": -1, "permnegated": True},
    {"permsid": "i_group_needed_modify_power", "permvalue": 75},
    {"permsid": "i_group_needed_member_add_power", "permvalue": 75},
    {"permsid": "i_group_needed_member_remove_power", "permvalue": 75},
    {"permsid": "b_group_is_permanent", "permvalue": True},
    {"permsid": "b_client_is_sticky", "permvalue": True},
)


class JailPlugin(plugin.TSPlugin):
    FREE_QUERY = query("servergroupdelclient")
    JAIL_QUERY = query("servergroupaddclient")
    MOVE_QUERY = query("clientmove")

    def __init__(self, bot: TSBot, config: JailConfig) -> None:
        self.jail_channel = config.get("jail_channel", DEFAULT_JAIL_CHANNEL)
        self.inmate_name = config.get("inmate_server_group_name", DEFAULT_INMATE_NAME)

        self.jail_channel_id: str = ""
        self.inmate_server_group_id: str = ""

        self.jail_tasks: dict[str, TSTask] = {}

        can_jail_check = [
            checks.check_uids_and_server_groups(
                uids=config.get("can_jail_uids"),
                server_groups=config.get("can_jail_server_groups"),
                strict=config.get("strict_server_group_checking", False),
            )
        ]

        bot.register_command(
            "jail", self.jail, help_text="Jail a client for misbehaving", checks=can_jail_check
        )
        bot.register_command(
            "free", self.free, help_text="Free a client from jail", checks=can_jail_check
        )

    @plugin.once("connect")
    async def init_jail(self, bot: TSBot, ctx: None) -> None:
        self.jail_channel_id = await self.get_jail_channel_id(bot)
        self.inmate_server_group_id = await self.get_inmate_server_group_id(bot)
        await self.free_inmates_on_startup(bot)

    async def get_jail_channel_id(self, bot: TSBot) -> str:
        channel_list = await cache.with_cache(bot.send, CHANNEL_LIST_QUERY, max_ttl=60)

        channel_id = find.from_iterable(channel_list, self.jail_channel, "channel_name", "cid")
        if not channel_id:
            channel_id = await self.create_jail_channel(bot)

        return channel_id

    async def create_jail_channel(self, bot: TSBot) -> str:
        resp = await bot.send(
            query("channelcreate").params(
                channel_name=self.jail_channel, channel_flag_permanent=True
            )
        )

        return resp.first["cid"]

    async def get_inmate_server_group_id(self, bot: TSBot) -> str:
        server_groups_list = await cache.with_cache(bot.send, SERVER_GROUPS_QUERY, max_ttl=60)

        inmate_id = find.from_iterable(server_groups_list, self.inmate_name, "name", "sgid")
        if inmate_id is None:
            inmate_id = await self.create_inmate_server_group(bot)

        return inmate_id

    async def create_inmate_server_group(self, bot: TSBot) -> str:
        resp = await bot.send(query("servergroupadd").params(name=self.inmate_name))
        inmate_id = resp.first["cid"]

        await bot.send(
            query("servergroupaddperm")
            .params(sgid=inmate_id)
            .param_block(INMATE_SERVER_GROUP_PERMS)
        )

        return inmate_id

    async def free_inmates_on_startup(self, bot: TSBot) -> None:
        inmates = await bot.send(
            query("servergroupclientlist").params(sgid=self.inmate_server_group_id)
        )

        if not inmates.data:
            return

        await bot.send(
            self.FREE_QUERY.params(sgid=self.inmate_server_group_id).param_block(
                {"cldbid": c["cldbid"]} for c in inmates
            )
        )

    @plugin.on("cliententerview")
    async def handle_connect(self, bot: TSBot, ctx: TSCtx) -> None:
        if self.inmate_server_group_id in ctx["client_servergroups"].split(","):
            await bot.send(self.MOVE_QUERY.params(cid=self.jail_channel_id, clid=ctx["clid"]))

    async def jail(self, bot: TSBot, ctx: TSCtx, nickname: str, time: str) -> None:
        jail_time = try_.or_none(parsers.parse_time, time)
        if jail_time is None:
            raise TSCommandError("Invalid time format")

        client_list = await bot.send(query("clientlist").option("groups"))

        client = find.from_iterable(client_list, nickname, "client_nickname")
        if client is None:
            raise TSCommandError("No client found")

        if self.inmate_server_group_id in client["client_servergroups"].split(","):
            raise TSCommandError("Client already jailed")

        self.jail_tasks[client["client_database_id"]] = bot.register_task(
            functools.partial(
                self.jail_client_task,
                client=client,
                jail_time=jail_time,
            )
        )

    async def free(self, bot: TSBot, ctx: TSCtx, nickname: str) -> None:
        client_list = await bot.send(query("clientlist").option("groups"))

        client = find.from_iterable(client_list, nickname, "client_nickname")
        if client is None:
            raise TSCommandError("No client found")

        if self.inmate_server_group_id not in client["client_servergroups"].split(","):
            raise TSCommandError("Client not jailed")

        cldbid = client["client_database_id"]
        await bot.send(self.FREE_QUERY.params(sgid=self.inmate_server_group_id, cldbid=cldbid))

        if task := self.jail_tasks.get(cldbid):
            bot.remove_task(task)

    async def jail_client_task(self, bot: TSBot, client: Mapping[str, str], jail_time: int) -> None:
        clid = client["clid"]
        cldbid = client["client_database_id"]

        try:
            await bot.send(self.JAIL_QUERY.params(sgid=self.inmate_server_group_id, cldbid=cldbid))
            await bot.send(self.MOVE_QUERY.params(cid=self.jail_channel_id, clid=clid))

            await asyncio.sleep(jail_time)

            await bot.send(self.FREE_QUERY.params(sgid=self.inmate_server_group_id, cldbid=cldbid))

        finally:
            self.jail_tasks.pop(cldbid, None)
