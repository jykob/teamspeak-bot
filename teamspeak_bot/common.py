from __future__ import annotations

from tsbot import query

CLIENT_LIST_QUERY = query("clientlist").option("times")
CHANNEL_LIST_QUERY = query("channellist")
SERVER_GROUPS_QUERY = query("servergrouplist")
