from __future__ import annotations

import operator
from typing import TYPE_CHECKING, overload

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping


@overload
def from_iterable[K: str, V: str](
    search_list: Iterable[Mapping[K, V]],
    search_str: str,
    search_attr: K,
    result_attr: None = None,
    *,
    strict: bool = False,
) -> Mapping[K, V] | None: ...


@overload
def from_iterable[K: str, V: str](
    search_list: Iterable[Mapping[K, V]],
    search_str: str,
    search_attr: K,
    result_attr: K,
    *,
    strict: bool = False,
) -> V | None: ...


def from_iterable[K: str, V: str](
    search_list: Iterable[Mapping[K, V]],
    search_str: str,
    search_attr: K,
    result_attr: K | None = None,
    *,
    strict: bool = False,
) -> V | Mapping[K, V] | None:
    op = operator.eq if strict else operator.contains

    for item in search_list:
        if op(search_str, item[search_attr]):
            return item[result_attr] if result_attr else item

    return None
