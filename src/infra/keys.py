from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from pathlib import Path
from typing import Tuple

def write_ephemeral_rsa_keypair(priv_path: str, pub_path: str, bits: int = 2048) -> Tuple[str, str]:
    """
    Generate an RSA keypair and write PEMs to priv_path and pub_path.
    Returns (priv_path, pub_path).
    """
    key = rsa.generate_private_key(public_exponent=65537, key_size=bits)
    priv_bytes = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption()
    )
    pub_bytes = key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    Path(priv_path).parent.mkdir(parents=True, exist_ok=True)
    with open(priv_path, "wb") as fh:
        fh.write(priv_bytes)
    with open(pub_path, "wb") as fh:
        fh.write(pub_bytes)
    return priv_path, pub_path
