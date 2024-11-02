from __future__ import annotations

import argparse
import asyncio
import logging
import signal
from contextlib import suppress

from tsbot import TSBot, TSCtx

from teamspeak_bot.config import get_config
from teamspeak_bot.logging import setup_logger
from teamspeak_bot.plugins import (
    admin,
    afk_mover,
    banned_names,
    error_events,
    fun,
    greeter,
    jokes,
    notify,
)

logger = logging.getLogger(__package__)


async def open_console(bot: TSBot, ctx: TSCtx):
    """
    Responds to the client with a dm.

    The bot accepts commands in private chats so you can invoke commands anywhere.
    Plus you don't have to use the invoker on commands inside private chats.
    """
    await bot.respond_to_client(ctx, "Console opened")


async def async_main(bot: TSBot):
    with suppress(NotImplementedError):
        asyncio.get_running_loop().add_signal_handler(signal.SIGINT, bot.close)

    await bot.run()


def main():
    parser = argparse.ArgumentParser(prog="TeamSpeak Bot", description="TeamSpeak Server Query Bot")

    parser.add_argument("-c", "--config", default="config.py", help="Path to a config file")
    parser.add_argument("-v", "--verbose", action="count", default=0, help="Verbosity level")
    parser.add_argument("-l", "--logfile", default="log.txt", help="Path to log file")

    args = parser.parse_args()
    config = get_config(args.config).unwrap_or_raise(RuntimeError)

    logging_config = config["logging"]  # type: ignore
    formats = logging_config["console_format"], logging_config["file_format"]  # type: ignore

    setup_logger(args.verbose, args.logfile, *formats)

    extra_kwargs = {
        k: v
        for k in (
            "port",
            "protocol",
            "server_id",
            "nickname",
            "invoker",
            "connection_retries",
            "connection_retry_timeout",
            "ratelimited",
            "ratelimit_calls",
            "ratelimit_period",
            "query_timeout",
        )
        if (v := config.get(k)) is not None
    }

    bot = TSBot(
        username=config["username"],
        password=config["password"],
        address=config["address"],
        **extra_kwargs,
    )

    bot.register_command(
        "console",
        open_console,
        help_text="Sends the client a private message. Clients can use it to invoke commands anywhere",
    )

    if plugins_config := config.get("plugins"):
        if (admin_config := plugins_config.get("admin")) and admin_config["enabled"]:
            bot.load_plugin(admin.AdminPlugin(bot, admin_config))

        if (afk_config := plugins_config.get("afk_mover")) and afk_config["enabled"]:
            bot.load_plugin(afk_mover.AFKMover(afk_config))

        if (banned_names_cfg := plugins_config.get("banned_names")) and banned_names_cfg["enabled"]:
            bot.load_plugin(banned_names.BannedNamesPlugin(bot, banned_names_cfg))

        if (error_events_cfg := plugins_config.get("error_events")) and error_events_cfg["enabled"]:
            bot.load_plugin(error_events.ErrorEventsPlugin(logger, error_events_cfg))

        if (fun_config := plugins_config.get("fun")) and fun_config["enabled"]:
            bot.load_plugin(fun.FunPlugin())

        if (greeter_config := plugins_config.get("greeter")) and greeter_config["enabled"]:
            bot.load_plugin(greeter.GreeterPlugin(greeter_config))

        if (jokes_config := plugins_config.get("jokes")) and jokes_config["enabled"]:
            bot.load_plugin(jokes.JokesPlugin())

        if (notify_config := plugins_config.get("notify")) and notify_config["enabled"]:
            bot.load_plugin(notify.NotifyPlugin(notify_config))

    raise SystemExit(asyncio.run(async_main(bot)))


if __name__ == "__main__":
    main()
