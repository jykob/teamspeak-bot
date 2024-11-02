from __future__ import annotations

from typing import TypedDict


class BasePluginConfig(TypedDict, total=False):
    enabled: bool
