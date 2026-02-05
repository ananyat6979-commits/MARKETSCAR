import fcntl, json, os
from src.utils.canonical import canonical_bytes

def append_receipt_atomic(path: str, receipt: dict):
    b = canonical_bytes(receipt)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "ab") as fh:
        fcntl.flock(fh, fcntl.LOCK_EX)
        fh.write(b + b"\n")
        fh.flush()
        os.fsync(fh.fileno())
        fcntl.flock(fh, fcntl.LOCK_UN)
