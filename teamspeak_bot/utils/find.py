from __future__ import annotations

import operator
from typing import TYPE_CHECKING, overload

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Mapping


@overload
def from_iterable[K: str, V: str](
    haystack: Iterable[Mapping[K, V]],
    search: str,
    key: K,
    result: None = None,
    *,
    strict: bool = False,
    predicate: Callable[[Mapping[K, V]], bool] | None = None,
) -> Mapping[K, V] | None: ...


@overload
def from_iterable[K: str, V: str](
    haystack: Iterable[Mapping[K, V]],
    search: str,
    key: K,
    result: K,
    *,
    strict: bool = False,
    predicate: Callable[[Mapping[K, V]], bool] | None = None,
) -> V | None: ...


def from_iterable[K: str, V: str](
    haystack: Iterable[Mapping[K, V]],
    search: str,
    key: K,
    result: K | None = None,
    *,
    strict: bool = False,
    predicate: Callable[[Mapping[K, V]], bool] | None = None,
) -> V | Mapping[K, V] | None:
    op = operator.eq if strict else operator.contains

    for item in haystack:
        if op(item[key], search) and (predicate(item) if predicate else True):
            return item[result] if result else item

    return None
