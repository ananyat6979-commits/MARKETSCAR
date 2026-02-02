#!/usr/bin/env python3
# scripts/replay_log.py

# ensure repo root is on sys.path so `import src.*` works in CI/script-runner
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

"""
scripts/replay_log.py

Replay a JSONL canonical case through the ReplayEngine and GateController
and assert the produced decision.action matches expectation.

Usage (CI):
python scripts/replay_log.py --case replay-cases/benign.jsonl --expect-action OPEN
"""
import argparse
import json
from pathlib import Path

from src.data.replay import ReplayEngine
from src.gate.gate_controller import GateController
from src.infra.crypto_signer import CryptoSigner

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--case", required=True, help="Path to canonical replay jsonl")
    p.add_argument("--expect-action", required=True, help="Expected action (OPEN/THROTTLE/HARD_LOCK)")
    p.add_argument("--manifest-verify", action="store_true", help="Verify manifest (default disabled in demo)")
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

    # small deterministic signer (uses env keys if present)
    signer = CryptoSigner()
    gc = GateController(signer=signer, thresholds={"jsd_global_99": 0.99, "jsd_global_95": 0.5})

    # For each event in the case: feed it to gate.execute_pricing_action with context
    last_decision = None
    for ev in events:
        # expected case schema: { "timestamp": "...", "sku":"SKU-1", "price": 10.02, "inventory": 100, "ip":"1.2.3.4", "jsd_global": 0.0 }
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
