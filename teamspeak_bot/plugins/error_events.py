from __future__ import annotations

from typing import TYPE_CHECKING

import tsformatter as tsf
from tsbot import plugin

from teamspeak_bot.plugins import BasePluginConfig

if TYPE_CHECKING:
    import logging

    from tsbot import TSBot, TSCtx


def create_error_prefix(error_name: str) -> str:
    return tsf.bold(str.join("", ("[", tsf.color("#f9655d", error_name), "]")))


DEFAULT_MESSAGES = {
    "invalid_invocation_message": f"{create_error_prefix('Argument error')}: {'{exception}'}\nUse '!help {'{command}'}' to see usage.",
    "permission_error_message": f"{create_error_prefix('Permission error')}: {'{exception}'}",
    "permission_error_log_message": "{invokername!r} ({invokeruid}) tried to use command {command!r} with args {raw_args!r}",
    "command_error_message": f"{create_error_prefix('Command error')}: {'{exception}'}",
}


class ErrorEventsConfig(BasePluginConfig, total=False):
    invalid_invocation_message: str
    permission_error_message: str
    permission_error_log_message: str
    command_error_message: str


DEFAULT_CONFIG = ErrorEventsConfig(
    enabled=True,
)


class ErrorEventsPlugin(plugin.TSPlugin):
    def __init__(
        self,
        logger: logging.Logger,
        config: ErrorEventsConfig,
    ) -> None:
        self.logger = logger

        self.invalid_invocation_message = config.get(
            "invalid_invocation_message", DEFAULT_MESSAGES["invalid_invocation_message"]
        )
        self.permission_error_message = config.get(
            "permission_error_message", DEFAULT_MESSAGES["permission_error_message"]
        )
        self.permission_error_log_message = config.get(
            "permission_error_log_message", DEFAULT_MESSAGES["permission_error_log_message"]
        )
        self.command_error_message = config.get(
            "command_error_message", DEFAULT_MESSAGES["command_error_message"]
        )

    @plugin.on("parameter_error")
    async def handle_parameter_error(self, bot: TSBot, ctx: TSCtx) -> None:
        await bot.respond(ctx, self.invalid_invocation_message.format(**ctx))

    @plugin.on("command_error")
    async def handle_command_error(self, bot: TSBot, ctx: TSCtx) -> None:
        await bot.respond(ctx, self.command_error_message.format(**ctx))

    @plugin.on("permission_error")
    async def handle_permission_error(self, bot: TSBot, ctx: TSCtx) -> None:
        self.logger.warning(self.permission_error_log_message.format(**ctx))
        await bot.respond(ctx, self.permission_error_message.format(**ctx))
