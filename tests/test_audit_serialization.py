from src.utils.canonical import canonical_bytes
def test_canonical_serialization():
    o = {"b": 2, "a": 1}
    assert canonical_bytes(o) == b'{"a":1,"b":2}'
