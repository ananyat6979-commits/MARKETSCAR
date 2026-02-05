# src/utils/canonical.py
import json
from typing import Any


def canonical_bytes(obj: Any) -> bytes:
    """
    Deterministic JSON serialization: sorted keys, minimal separators, UTF-8 bytes.
    Suitable for hashing and signing.
    """
    return json.dumps(
        obj, separators=(",", ":"), sort_keys=True, ensure_ascii=False
    ).encode("utf-8")
