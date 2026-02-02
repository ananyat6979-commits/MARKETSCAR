from __future__ import annotations
import json, os
from src.utils.canonical import canonical_bytes

class AuditLogger:
    """
    Simple append-only audit logger writing canonical JSON lines.
    """

    def __init__(self, log_path: str = "data/audit/decisions.log"):
        self.log_path = log_path
        os.makedirs(os.path.dirname(self.log_path), exist_ok=True)

    def append(self, receipt: dict) -> None:
        b = canonical_bytes(receipt)
        # append binary canonical bytes + newline
        with open(self.log_path, "ab") as fh:
            fh.write(b + b"\n")
            fh.flush()
            os.fsync(fh.fileno())

    def read_all(self) -> list:
        if not os.path.exists(self.log_path):
            return []
        out = []
        with open(self.log_path, "rb") as fh:
            for ln in fh:
                try:
                    out.append(json.loads(ln.decode("utf-8")))
                except Exception:
                    # skip malformed lines
                    continue
        return out
