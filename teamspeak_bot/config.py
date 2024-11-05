from __future__ import annotations

import importlib
import importlib.util
import sys
from typing import Final, Literal, NotRequired, Required, TypedDict, cast

from result import Err, Ok, Result

from teamspeak_bot.plugins import (
    admin,
    afk_mover,
    banned_names,
    error_events,
    fun,
    greeter,
    jail,
    jokes,
    notify,
)
from teamspeak_bot.utils import merge


class LoggingConfig(TypedDict, total=False):
    console_format: str
    file_format: str


class PluginsConfig(TypedDict, total=False):
    admin: admin.AdminConfig
    afk_mover: afk_mover.AFKMoverConfig
    banned_names: banned_names.BannedNamesConfig
    error_events: error_events.ErrorEventsConfig
    fun: fun.FunConfig
    greeter: greeter.GreeterConfig
    jail: jail.JailConfig
    jokes: jokes.JokesPluginConfig
    notify: notify.NotifyConfig


class BotConfig(TypedDict):
    username: Required[str]
    password: Required[str]
    address: Required[str]
    port: NotRequired[int]

    protocol: NotRequired[Literal["ssh", "raw"]]
    server_id: NotRequired[int]
    nickname: NotRequired[str | None]
    invoker: NotRequired[str]
    connection_retries: NotRequired[int]
    connection_retry_timeout: NotRequired[float]
    ratelimited: NotRequired[bool]
    ratelimit_calls: NotRequired[int]
    ratelimit_period: NotRequired[float]
    query_timeout: NotRequired[float]

    plugins: NotRequired[PluginsConfig]

    logging: NotRequired[LoggingConfig]


DEFAULT_PLUGINS_CONFIG: Final[PluginsConfig] = {
    "admin": admin.DEFAULT_CONFIG,
    "afk_mover": afk_mover.DEFAULT_CONFIG,
    "banned_names": banned_names.DEFAULT_CONFIG,
    "error_events": error_events.DEFAULT_CONFIG,
    "fun": fun.DEFAULT_CONFIG,
    "greeter": greeter.DEFAULT_CONFIG,
    "jail": jail.DEFAULT_CONFIG,
    "jokes": jokes.DEFAULT_CONFIG,
    "notify": notify.DEFAULT_CONFIG,
}

DEFAULT_CONFIG: BotConfig = {
    "plugins": DEFAULT_PLUGINS_CONFIG,
    "logging": {
        "console_format": "[%(name)s][%(levelname)s] %(message)s",
        "file_format": "%(asctime)s | %(name)-10s | %(levelname)-8s | %(message)s",
    },
}  # type: ignore


def get_config(config_path: str) -> Result[BotConfig, str]:
    spec = importlib.util.spec_from_file_location("config", config_path)
    if spec is None or spec.loader is None:
        return Err("Unable to find 'config' module")

    module = importlib.util.module_from_spec(spec)
    sys.modules["config"] = module
    spec.loader.exec_module(module)

    imported_config = cast(BotConfig | None, getattr(module, "CONFIG", None))
    if imported_config is None:
        return Err("Config module doesn't have CONFIG attribute")

    default_config = DEFAULT_CONFIG.copy()
    return Ok(merge.deep_merge(imported_config, default_config))
