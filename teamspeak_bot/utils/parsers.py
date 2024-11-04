from __future__ import annotations

TIME_MAP = (
    ("h", 3600),
    ("m", 60),
    ("s", 1),
)


def parse_time(time: str) -> int:
    "Parse given time str (raw seconds or format XXhXXmXXs) into its seconds"

    if time.isnumeric():
        return int(time)

    unparsed = time
    parsed_time = 0

    for unit, multiplier in TIME_MAP:
        raw_time, sep, rest = unparsed.partition(unit)

        if not sep:
            continue

        parsed_time += int(raw_time) * multiplier

        if not rest:
            return parsed_time

        unparsed = rest

    raise ValueError("Incorrect time format")
