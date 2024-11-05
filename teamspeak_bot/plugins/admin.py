from __future__ import annotations

from typing import TYPE_CHECKING

from tsbot import plugin, query
from tsbot.response import TSResponse

from teamspeak_bot.plugins import BasePluginConfig
from teamspeak_bot.utils import checks, try_

if TYPE_CHECKING:
    from tsbot import TSBot, TSCtx


class AdminConfig(BasePluginConfig, total=False):
    allowed_uids: tuple[str, ...]
    allowed_server_groups: tuple[str, ...]
    strict_server_group_checking: bool


DEFAULT_CONFIG = AdminConfig(
    enabled=False,
)


class AdminPlugin(plugin.TSPlugin):
    def __init__(self, bot: TSBot, config: AdminConfig) -> None:
        admin_check = [
            checks.check_uids_and_server_groups(
                uids=config.get("allowed_uids"),
                server_groups=config.get("allowed_server_groups"),
                strict=config.get("strict_server_group_checking", False),
            )
        ]

        bot.register_command("eval", self.eval_, hidden=True, raw=True, checks=admin_check)
        bot.register_command("exec", self.exec_, hidden=True, raw=True, checks=admin_check)
        bot.register_command("quit", self.quit_, hidden=True, checks=admin_check)
        bot.register_command("send", self.send, hidden=True, raw=True, checks=admin_check)
        bot.register_command("spam", self.spam, hidden=True, checks=admin_check)
        bot.register_command("nickname", self.change_nickname, hidden=True, checks=admin_check)

    async def eval_(self, bot: TSBot, ctx: TSCtx, eval_str: str) -> None:
        response = try_.or_call(
            eval,
            eval_str,
            globals(),
            locals(),
            on_error=lambda e: type(e).__name__,
        )
        await bot.respond(ctx, response)

    async def exec_(self, bot: TSBot, ctx: TSCtx, exec_str: str) -> None:
        exec(exec_str, globals(), locals())

    async def quit_(self, bot: TSBot, ctx: TSCtx) -> None:
        bot.close()

    async def send(self, bot: TSBot, ctx: TSCtx, raw_command: str) -> None:
        response = await try_.async_or_call(
            bot.send_raw(raw_command), lambda e: f"{type(e).__name__}: {e}"
        )

        await bot.respond(ctx, repr(response) if isinstance(response, TSResponse) else response)

    async def spam(self, bot: TSBot, ctx: TSCtx, amount: str, line: str) -> None:
        for _ in range(int(amount)):
            await bot.respond(ctx, line)

    async def change_nickname(self, bot: TSBot, ctx: TSCtx, nickname: str | None = None) -> None:
        if not nickname:
            resp = await bot.send_raw("whoami")
            nickname = resp.first["client_login_name"]

        await bot.send(query("clientupdate").params(client_nickname=nickname))
        await bot.respond(ctx, f"Nickname changed to {nickname!r}")
