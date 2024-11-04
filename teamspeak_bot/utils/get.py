from __future__ import annotations

from typing import TYPE_CHECKING

from tsbot import query

if TYPE_CHECKING:
    from tsbot import TSBot, TSCtx


GET_DATABASE_ID_QUERY = query("clientgetdbidfromuid")
SERVER_GROUPS_BY_ID_QUERY = query("servergroupsbyclientid")


async def client_server_groups(bot: TSBot, ctx: TSCtx) -> tuple[dict[str, str], ...]:
    ids = await bot.send(GET_DATABASE_ID_QUERY.params(cluid=ctx["invokeruid"]))
    groups = await bot.send(SERVER_GROUPS_BY_ID_QUERY.params(cldbid=ids.first["cldbid"]))

    return groups.data
