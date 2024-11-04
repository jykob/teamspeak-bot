from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Mapping


def deep_merge[T, K, V](from_: Mapping[K, V], to: T) -> T:
    for key, value in from_.items():
        if key in to and isinstance(to[key], dict) and isinstance(value, dict):  # type: ignore
            to[key] = deep_merge(to[key], value)  # type: ignore
        else:
            to[key] = value  # type: ignore

    return to
