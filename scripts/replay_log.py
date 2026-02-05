#!/usr/bin/env python3
# scripts/replay_log.py

# ensure repo root is on sys.path so `import src.*` works in CI/script-runner
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

"""
Replay a JSONL canonical case through the ReplayEngine and GateController
and assert the produced decision.action matches expectation.

Usage (CI):
python scripts/replay_log.py --case replay-cases/benign.jsonl --expect-action OPEN
"""
import argparse
import json
import os
import tempfile
from pathlib import Path

from src.data.replay import ReplayEngine
from src.gate.gate_controller import GateController
from src.infra.crypto_signer import CryptoSigner
from src.infra.keys import write_ephemeral_rsa_keypair


def get_runtime_signer(priv_arg=None, pub_arg=None):
    # 1) explicit paths
    if priv_arg and pub_arg:
        return CryptoSigner(private_key_path=priv_arg, public_key_path=pub_arg)

    # 2) env paths
    priv_env = os.getenv("DEV_PRIVATE_KEY_PATH")
    pub_env = os.getenv("DEV_PUBLIC_KEY_PATH")
    if priv_env and pub_env:
        return CryptoSigner(private_key_path=priv_env, public_key_path=pub_env)

    # 3) generate ephemeral keys in tmpdir
    tmp = tempfile.mkdtemp(prefix="marketscar-keys-")
    priv = os.path.join(tmp, "dev_rsa.pem")
    pub = os.path.join(tmp, "dev_rsa.pub")
    write_ephemeral_rsa_keypair(priv, pub)
    return CryptoSigner(private_key_path=priv, public_key_path=pub)


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--case", required=True, help="Path to canonical replay jsonl")
    p.add_argument(
        "--expect-action",
        required=True,
        help="Expected action (OPEN/THROTTLE/HARD_LOCK)",
    )
    p.add_argument(
        "--manifest-verify",
        action="store_true",
        help="Verify manifest (default disabled in demo)",
    )
    p.add_argument("--priv", help="Path to private key (optional)")
    p.add_argument("--pub", help="Path to public key (optional)")
    return p.parse_args()


def load_case(path):
    events = []
    with open(path, "r") as fh:
        for ln in fh:
            events.append(json.loads(ln.strip()))
    return events


def main():
    args = parse_args()
    case_path = Path(args.case)
    if not case_path.exists():
        print("Case not found:", case_path)
        raise SystemExit(2)

    events = load_case(case_path)

    # small deterministic signer (uses CLI args, env keys, or ephemeral keys)
    signer = get_runtime_signer(priv_arg=args.priv, pub_arg=args.pub)
    gc = GateController(
        signer=signer, thresholds={"jsd_global_99": 0.99, "jsd_global_95": 0.5}
    )

    # For each event in the case: feed it to gate.execute_pricing_action with context
    last_decision = None
    for ev in events:
        context = {"jsd_global": ev.get("jsd_global", 0.0)}
        payload = {"sku": ev.get("sku"), "price": ev.get("price")}
        decision = gc.execute_pricing_action("publish_price", payload, context=context)
        last_decision = decision

    if last_decision is None:
        print("No events found in case")
        raise SystemExit(2)

    actual = last_decision["action"]
    expected = args.expect_action
    if actual != expected:
        print(f"FAIL: expected {expected} but got {actual}")
        raise SystemExit(3)

    print(f"OK: case {case_path} produced expected action {expected}")
    print("receipt signature present:", "signature" in last_decision["receipt"])


if __name__ == "__main__":
    main()
