import os
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from src.infra.crypto_signer import CryptoSigner
from src.gate.gate_controller import GateController

def write_temp_keypair(priv_path, pub_path):
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    priv_bytes = key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.TraditionalOpenSSL,
        serialization.NoEncryption()
    )
    pub_bytes = key.public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo
    )
    with open(priv_path, "wb") as fh:
        fh.write(priv_bytes)
    with open(pub_path, "wb") as fh:
        fh.write(pub_bytes)

def test_gate_hard_lock_blocks_and_receipt_verifies(tmp_path, monkeypatch):
    keydir = tmp_path / "keys"
    keydir.mkdir()
    priv = str(keydir / "dev_rsa.pem")
    pub = str(keydir / "dev_rsa.pub")

    # generate ephemeral keypair (pure python)
    write_temp_keypair(priv, pub)

    # set env so crypto_signer uses these
    monkeypatch.setenv("DEV_PRIVATE_KEY_PATH", priv)
    monkeypatch.setenv("DEV_PUBLIC_KEY_PATH", pub)

    signer = CryptoSigner()  # will read env
    gc = GateController(signer=signer, thresholds={"jsd_global_99": 0.0})  # force HARD_LOCK

    # call through gate with empty diagnostics -> context can set jsd, but threshold 0 -> HARD_LOCK
    payload = {"sku_id": "SKU-123", "new_price": 10.0}
    decision = gc.execute_pricing_action("publish_price", payload, context={})

    assert decision["action"] == "HARD_LOCK"

    receipt = decision["receipt"]
    # verify signature over canonicalized payload (CryptoSigner accepts dict)
    assert signer.verify(receipt["payload"], receipt["signature"]) is True
