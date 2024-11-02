from __future__ import annotations

import operator
from collections.abc import Sequence
from typing import TYPE_CHECKING

from teamspeak_bot.utils import get

if TYPE_CHECKING:
    from tsbot import TSBot, TSCtx


def has_group(
    groups: Sequence[str], client_groups: Sequence[dict[str, str]], *, strict: bool = False
) -> bool:
    op = operator.eq if strict else operator.contains
    return any(op(g, cg["name"]) for g in groups for cg in client_groups)


async def check_groups(
    bot: TSBot, ctx: TSCtx, groups: Sequence[str], *, strict: bool = False
) -> bool:
    return has_group(groups, await get.client_server_groups(bot, ctx), strict=strict)


def check_uids(uids: Sequence[str], ctx: TSCtx) -> bool:
    return ctx.get("invokeruid") in uids
