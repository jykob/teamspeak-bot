from __future__ import annotations

from typing import Final

from tsbot import query

CLIENT_LIST_QUERY: Final = query("clientlist").option("times")
