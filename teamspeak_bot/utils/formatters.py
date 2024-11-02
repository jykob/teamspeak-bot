from __future__ import annotations


def seconds_to_time(seconds: int) -> str:
    if seconds < 60:
        return f"{seconds}s"

    if seconds < 3600:
        m, s = divmod(seconds, 60)
        return f"{m}m{f' {s}s' if s else ''}"

    h, remaining = divmod(seconds, 3600)
    m, s = divmod(remaining, 60)
    return f"{h}h{f' {m}m' if m or s else ''}{f' {s}s' if s else ''}"
