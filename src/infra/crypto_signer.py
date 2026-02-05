# src/infra/crypto_signer.py
"""
CryptoSigner - local PEM signer used in tests and local dev.

- Loads PEM files from DEV_PRIVATE_KEY_PATH and DEV_PUBLIC_KEY_PATH by default.
- Accepts payload as raw bytes or a dict/object (dict/object -> canonical JSON bytes).
- Methods:
    sign(payload) -> hex signature (str)
    verify(payload, signature_hex) -> bool

Notes:
- Private keys MUST NOT be committed to the repo.
- Tests should generate ephemeral keys at runtime and point DEV_PRIVATE_KEY_PATH / DEV_PUBLIC_KEY_PATH at them.
"""
import binascii
import os
from typing import Optional, Union

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.serialization import (load_pem_private_key,
                                                          load_pem_public_key)

from src.utils.canonical import canonical_bytes

Payload = Union[bytes, bytearray, dict, object]


class CryptoSigner:
    def __init__(
        self,
        private_key_path: Optional[str] = None,
        public_key_path: Optional[str] = None,
    ):
        """
        If paths are not provided, environment variables DEV_PRIVATE_KEY_PATH and
        DEV_PUBLIC_KEY_PATH are used.
        """
        self.private_key_path = private_key_path or os.getenv("DEV_PRIVATE_KEY_PATH")
        self.public_key_path = public_key_path or os.getenv("DEV_PUBLIC_KEY_PATH")
        self._priv = None
        self._pub = None
        self._load_keys()

    def _load_keys(self) -> None:
        """Load PEM keys if paths exist. Silent if not present (tests can generate keys)."""
        if self.private_key_path and os.path.exists(self.private_key_path):
            with open(self.private_key_path, "rb") as fh:
                self._priv = load_pem_private_key(fh.read(), password=None)
        if self.public_key_path and os.path.exists(self.public_key_path):
            with open(self.public_key_path, "rb") as fh:
                self._pub = load_pem_public_key(fh.read())

    def _to_bytes(self, payload: Payload) -> bytes:
        """Convert payload to canonical bytes. Dict/object -> canonical JSON bytes."""
        if isinstance(payload, (bytes, bytearray)):
            return bytes(payload)
        # For dict-like / object payloads, canonicalize to deterministic JSON bytes
        return canonical_bytes(payload)

    def sign(self, payload: Payload) -> str:
        """
        Sign the payload and return hex-encoded signature.

        Raises RuntimeError if private key is not available.
        """
        if not self._priv:
            raise RuntimeError(
                "Private key not loaded. Set DEV_PRIVATE_KEY_PATH or pass private_key_path to CryptoSigner()."
            )
        payload_bytes = self._to_bytes(payload)
        signature = self._priv.sign(payload_bytes, padding.PKCS1v15(), hashes.SHA256())
        return binascii.hexlify(signature).decode("ascii")

    def verify(self, payload: Payload, signature_hex: str) -> bool:
        """
        Verify signature. Returns True if valid, False otherwise.

        Raises RuntimeError if public key is not available.
        """
        if not self._pub:
            raise RuntimeError(
                "Public key not loaded. Set DEV_PUBLIC_KEY_PATH or pass public_key_path to CryptoSigner()."
            )
        payload_bytes = self._to_bytes(payload)
        sig = binascii.unhexlify(signature_hex)
        try:
            self._pub.verify(sig, payload_bytes, padding.PKCS1v15(), hashes.SHA256())
            return True
        except Exception:
            return False
