#!/usr/bin/env python3
"""
scripts/calibrate.py

Minimal calibration runner used in CI and locally.
- Reads the first N rows (rows arg) of the input CSV.
- Calls compute_jsd_distribution(df, seed).
- Computes the 95th and 99th percentiles.
- Emits config/frozen_thresholds.json with metadata.

This is deterministic and intentionally simple so CI is reproducible.
Replace compute_jsd_distribution with the production KDE+JSD implementation later.
"""
import argparse
import json
import os
from datetime import datetime
from pathlib import Path

import pandas as pd
import numpy as np

from src.diagnostic.jsd_calculator import compute_jsd_distribution


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--input", required=True, help="Path to CSV baseline")
    p.add_argument("--rows", type=int, default=10000, help="Rows to sample from top for calibration")
    p.add_argument("--seed", type=int, default=42, help="Deterministic RNG seed")
    p.add_argument("--out", required=True, help="Output JSON path (config/frozen_thresholds.json)")
    return p.parse_args()


def ensure_out_path(out_path: str):
    out_dir = os.path.dirname(out_path)
    if out_dir and not os.path.exists(out_dir):
        os.makedirs(out_dir, exist_ok=True)


def main():
    args = parse_args()
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"ERROR: input file not found: {input_path}")
        raise SystemExit(2)

    ensure_out_path(args.out)

    # Read first N rows deterministically
    df = pd.read_csv(input_path, parse_dates=["InvoiceDate"])
    if args.rows and len(df) > args.rows:
        df = df.head(args.rows)

    # Compute deterministic JSD-like distribution (stub or real)
    jsd_vals = compute_jsd_distribution(df, seed=args.seed)
    jsd_arr = np.array(jsd_vals, dtype=float)

    p95 = float(np.percentile(jsd_arr, 95))
    p99 = float(np.percentile(jsd_arr, 99))

    out = {
        "seed": int(args.seed),
        "sample_size": int(len(df)),
        "percentiles": {"95": p95, "99": p99},
        "calibration_timestamp_utc": datetime.utcnow().isoformat() + "Z",
        "notes": "Deterministic stub run. Replace compute_jsd_distribution with KDE-JSD for production."
    }

    with open(args.out, "w") as fh:
        json.dump(out, fh, indent=2)

    print(f"WROTE: {args.out}")
    print(f"seed={args.seed} sample_size={len(df)} p95={p95:.6f} p99={p99:.6f}")


if __name__ == "__main__":
    main()
