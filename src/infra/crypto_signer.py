import os
import binascii
from typing import Union
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.serialization import load_pem_private_key, load_pem_public_key
from src.utils.canonical import canonical_bytes

class CryptoSigner:
    """
    Local PEM signer. Looks for env DEV_PRIVATE_KEY_PATH and DEV_PUBLIC_KEY_PATH.
    Methods:
      sign(payload_dict) -> signature_hex
      verify(payload_dict, signature_hex) -> True/False
    """
    def __init__(self, private_key_path=None, public_key_path=None):
        self.private_key_path = private_key_path or os.getenv("DEV_PRIVATE_KEY_PATH")
        self.public_key_path = public_key_path or os.getenv("DEV_PUBLIC_KEY_PATH")
        self._load_keys()

    def _load_keys(self):
        self._priv = None
        self._pub = None
        if self.private_key_path and os.path.exists(self.private_key_path):
            with open(self.private_key_path, "rb") as fh:
                self._priv = load_pem_private_key(fh.read(), password=None)
        if self.public_key_path and os.path.exists(self.public_key_path):
            with open(self.public_key_path, "rb") as fh:
                self._pub = load_pem_public_key(fh.read())

    def sign(self, payload_bytes: bytes) -> str:
        if not self._priv:
            raise RuntimeError("Private key not loaded (set DEV_PRIVATE_KEY_PATH)")
        sig = self._priv.sign(
            payload_bytes,
            padding.PKCS1v15(),
            hashes.SHA256()
        )
        return binascii.hexlify(sig).decode()

    def verify(self, payload_bytes: bytes, signature_hex: str) -> bool:
        if not self._pub:
            raise RuntimeError("Public key not loaded (set DEV_PUBLIC_KEY_PATH)")
        sig = binascii.unhexlify(signature_hex)
        try:
            self._pub.verify(sig, payload_bytes, padding.PKCS1v15(), hashes.SHA256())
            return True
        except Exception:
            return False
from __future__ import annotations
import os, binascii
from typing import Union
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.serialization import load_pem_private_key, load_pem_public_key
from src.utils.canonical import canonical_bytes

class CryptoSigner:
    """
    Local PEM signer for tests and local dev.
    Accepts payload as bytes OR dict/object (will canonicalize).
    Environment variables:
      DEV_PRIVATE_KEY_PATH, DEV_PUBLIC_KEY_PATH
    Methods:
      sign(payload) -> hex signature (str)
      verify(payload, signature_hex) -> bool
    """
    def __init__(self, private_key_path: str | None = None, public_key_path: str | None = None):
        self.private_key_path = private_key_path or os.getenv("DEV_PRIVATE_KEY_PATH")
        self.public_key_path = public_key_path or os.getenv("DEV_PUBLIC_KEY_PATH")
        self._priv = None
        self._pub = None
        self._load_keys()

    def _load_keys(self):
        if self.private_key_path and os.path.exists(self.private_key_path):
            with open(self.private_key_path, "rb") as fh:
                self._priv = load_pem_private_key(fh.read(), password=None)
        if self.public_key_path and os.path.exists(self.public_key_path):
            with open(self.public_key_path, "rb") as fh:
                self._pub = load_pem_public_key(fh.read())

    def _to_bytes(self, payload: Union[bytes, dict, object]) -> bytes:
        if isinstance(payload, (bytes, bytearray)):
            return bytes(payload)
        # Assume dict-like / object: canonicalize
        return canonical_bytes(payload)

    def sign(self, payload: Union[bytes, dict, object]) -> str:
        """
        Sign payload and return hex-encoded signature.
        """
        if not self._priv:
            raise RuntimeError("Private key not loaded. Set DEV_PRIVATE_KEY_PATH or pass key paths to CryptoSigner().")
        payload_bytes = self._to_bytes(payload)
        sig = self._priv.sign(payload_bytes, padding.PKCS1v15(), hashes.SHA256())
        return binascii.hexlify(sig).decode("ascii")

    def verify(self, payload: Union[bytes, dict, object], signature_hex: str) -> bool:
        """
        Verify signature; returns True if valid, False otherwise.
        """
        if not self._pub:
            raise RuntimeError("Public key not loaded. Set DEV_PUBLIC_KEY_PATH or pass key paths to CryptoSigner().")
        payload_bytes = self._to_bytes(payload)
        sig = binascii.unhexlify(signature_hex)
        try:
            self._pub.verify(sig, payload_bytes, padding.PKCS1v15(), hashes.SHA256())
            return True
        except Exception:
            return False
from __future__ import annotations
import os, binascii
from typing import Union
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.serialization import load_pem_private_key, load_pem_public_key
from src.utils.canonical import canonical_bytes

class CryptoSigner:
    """
    Local PEM signer for tests and local dev.
    Accepts payload as bytes OR dict/object (will canonicalize).
    Environment variables:
      DEV_PRIVATE_KEY_PATH, DEV_PUBLIC_KEY_PATH
    Methods:
      sign(payload) -> hex signature (str)
      verify(payload, signature_hex) -> bool
    """
    def __init__(self, private_key_path: str | None = None, public_key_path: str | None = None):
        self.private_key_path = private_key_path or os.getenv("DEV_PRIVATE_KEY_PATH")
        self.public_key_path = public_key_path or os.getenv("DEV_PUBLIC_KEY_PATH")
        self._priv = None
        self._pub = None
        self._load_keys()

    def _load_keys(self):
        if self.private_key_path and os.path.exists(self.private_key_path):
            with open(self.private_key_path, "rb") as fh:
                self._priv = load_pem_private_key(fh.read(), password=None)
        if self.public_key_path and os.path.exists(self.public_key_path):
            with open(self.public_key_path, "rb") as fh:
                self._pub = load_pem_public_key(fh.read())

    def _to_bytes(self, payload: Union[bytes, dict, object]) -> bytes:
        if isinstance(payload, (bytes, bytearray)):
            return bytes(payload)
        # Assume dict-like / object: canonicalize
        return canonical_bytes(payload)

    def sign(self, payload: Union[bytes, dict, object]) -> str:
        """
        Sign payload and return hex-encoded signature.
        """
        if not self._priv:
            raise RuntimeError("Private key not loaded. Set DEV_PRIVATE_KEY_PATH or pass key paths to CryptoSigner().")
        payload_bytes = self._to_bytes(payload)
        sig = self._priv.sign(payload_bytes, padding.PKCS1v15(), hashes.SHA256())
        return binascii.hexlify(sig).decode("ascii")

    def verify(self, payload: Union[bytes, dict, object], signature_hex: str) -> bool:
        """
        Verify signature; returns True if valid, False otherwise.
        """
        if not self._pub:
            raise RuntimeError("Public key not loaded. Set DEV_PUBLIC_KEY_PATH or pass key paths to CryptoSigner().")
        payload_bytes = self._to_bytes(payload)
        sig = binascii.unhexlify(signature_hex)
        try:
            self._pub.verify(sig, payload_bytes, padding.PKCS1v15(), hashes.SHA256())
            return True
        except Exception:
            return False
