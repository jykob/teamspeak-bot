from __future__ import annotations

from typing import TYPE_CHECKING

from tsbot import query

if TYPE_CHECKING:
    from tsbot import TSBot, TSCtx


async def client_server_groups(bot: TSBot, ctx: TSCtx) -> tuple[dict[str, str], ...]:
    ids = await bot.send(query("clientgetdbidfromuid").params(cluid=ctx["invokeruid"]))
    groups = await bot.send(query("servergroupsbyclientid").params(cldbid=ids.first["cldbid"]))

    return groups.data
