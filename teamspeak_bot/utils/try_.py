from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable, Coroutine


def or_none[T, *Ts](func: Callable[[*Ts], T], *args: *Ts) -> T | None:
    try:
        return func(*args)
    except Exception:
        return None


def or_default[T, TD, *Ts](func: Callable[[*Ts], T], *args: *Ts, default: TD) -> T | TD:
    try:
        return func(*args)
    except Exception:
        return default


def or_call[T, TD, *Ts](
    func: Callable[[*Ts], T], *args: *Ts, on_error: Callable[[Exception], TD]
) -> T | TD:
    try:
        return func(*args)
    except Exception as e:
        return on_error(e)


async def async_or_call[T, TD](
    func: Coroutine[None, None, T], on_error: Callable[[Exception], TD]
) -> T | TD:
    try:
        return await func
    except Exception as e:
        return on_error(e)
