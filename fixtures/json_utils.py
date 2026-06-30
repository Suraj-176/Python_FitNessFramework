"""
Shared utility: extract a value from a parsed JSON dict using either
a flat key ("token") or a simple JSONPath-style expression ("$.data.access_token",
"$.users.0.email"). Used by BaseRequestFixture and AuthFixture so both behave
identically — critical for a framework meant to work against ANY API, where
auth responses are just as likely to be nested as regular API responses.
"""
from typing import Any

def extract_json_field(data: dict, key: str) -> str:
    """
    Returns the string value at `key` within `data`.
    Returns "key not found" if the path doesn't resolve.
    Returns "no key set" if `key` is empty.
    """
    if not key:
        return "no key set"
    try:
        if key.startswith("$."):
            parts = key[2:].split(".")
            val: Any = data
            for part in parts:
                val = val[int(part)] if isinstance(val, list) else val[part]
            return str(val)
        return str(data.get(key, "key not found"))
    except (KeyError, IndexError, TypeError, AttributeError):
        return "key not found"
