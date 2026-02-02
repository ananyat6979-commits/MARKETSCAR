# src/infra/keys.py
"""
Ephemeral RSA keypair generator helpers for tests and local dev.
Provides:
- generate_rsa_keypair(priv_path, pub_path, key_size=2048, overwrite=False)
- generate_ephemeral_keypair_bytes(key_size=2048)
- write_ephemeral_rsa_keypair (alias for generate_rsa_keypair) for compatibility
"""

from pathlib import Path
from typing import Tuple
import os

from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization


def generate_rsa_keypair(
    priv_path: str,
    pub_path: str,
    key_size: int = 2048,
    overwrite: bool = False,
) -> Tuple[str, str]:
    priv_path = Path(priv_path)
    pub_path = Path(pub_path)

    priv_path.parent.mkdir(parents=True, exist_ok=True)
    pub_path.parent.mkdir(parents=True, exist_ok=True)

    if not overwrite:
        if priv_path.exists() or pub_path.exists():
            raise FileExistsError("Key path already exists (use overwrite=True to replace)")

    key = rsa.generate_private_key(public_exponent=65537, key_size=key_size)

    priv_bytes = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    )

    pub_bytes = key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )

    with open(priv_path, "wb") as fh:
        fh.write(priv_bytes)
    with open(pub_path, "wb") as fh:
        fh.write(pub_bytes)

    try:
        os.chmod(priv_path, 0o600)
    except Exception:
        pass

    return str(priv_path), str(pub_path)


def generate_ephemeral_keypair_bytes(key_size: int = 2048) -> Tuple[bytes, bytes]:
    key = rsa.generate_private_key(public_exponent=65537, key_size=key_size)
    priv_bytes = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    )
    pub_bytes = key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    return priv_bytes, pub_bytes


# Backwards-compatible alias expected by some scripts/tests
def write_ephemeral_rsa_keypair(priv_path: str, pub_path: str, key_size: int = 2048, overwrite: bool = True) -> Tuple[str, str]:
    return generate_rsa_keypair(priv_path, pub_path, key_size=key_size, overwrite=overwrite)
