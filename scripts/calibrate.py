#!/usr/bin/env python3
# scripts/calibrate.py
"""
Deterministic calibrate script used in CI.

Usage:
python scripts/calibrate.py --input data/raw/online_retail_II.csv --rows 1000 --seed 42 --out config/frozen_thresholds.json
"""

import argparse
import json
import os
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

from src.diagnostic.jsd_calculator import compute_jsd_distribution


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--input", required=True, help="Path to CSV baseline")
    p.add_argument(
        "--rows",
        type=int,
        default=10000,
        help="Rows to sample from top for calibration",
    )
    p.add_argument(
        "--seed", type=int, default=42, help="Deterministic RNG seed"
    )
    p.add_argument(
        "--out",
        required=True,
        help="Output JSON path (config/frozen_thresholds.json)",
    )
    p.add_argument(
        "--n-bins",
        type=int,
        default=128,
        help="Bins used by histogram fallback / grid size",
    )
    p.add_argument(
        "--bw",
        type=float,
        default=None,
        help="bandwidth for gaussian_kde if available",
    )
    p.add_argument(
        "--n-bootstrap", type=int, default=200, help="Bootstrap iterations"
    )
    p.add_argument(
        "--sample-size",
        type=int,
        default=None,
        help="Sample size per bootstrap (None => full length)",
    )
    p.add_argument(
        "--price-col",
        type=str,
        default=None,
        help="Price column name (auto-detected if not set)",
    )
    return p.parse_args()


def ensure_out_path(out_path: str):
    out_dir = os.path.dirname(out_path)
    if out_dir and not os.path.exists(out_dir):
        os.makedirs(out_dir, exist_ok=True)


def _detect_price_column(df: pd.DataFrame, explicit: str | None) -> str:
    if explicit:
        if explicit in df.columns:
            return explicit
        raise KeyError(
            f"Requested price column '{explicit}' not present. Available: {list(df.columns)}"
        )
    # common candidates
    candidates = [
        "price",
        "Price",
        "unit_price",
        "UnitPrice",
        "Unit Price",
        "Unit price",
        "Unit_Price",
    ]
    for c in candidates:
        if c in df.columns:
            return c
    # fallback: try numeric columns that look like price
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    if len(numeric_cols) == 1:
        return numeric_cols[0]
    raise KeyError(
        f"Could not auto-detect price column. Candidates: {candidates}. Available columns: {list(df.columns)}"
    )


def main():
    args = parse_args()
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"ERROR: input file not found: {input_path}")
        raise SystemExit(2)

    ensure_out_path(args.out)

    # Read CSV deterministically; keep InvoiceDate parse attempt but don't fail if absent
    df = pd.read_csv(input_path)
    if "InvoiceDate" in df.columns:
        df["InvoiceDate"] = pd.to_datetime(
            df["InvoiceDate"], errors="coerce", utc=True
        )

    if args.rows and len(df) > args.rows:
        df = df.head(args.rows)

    price_col = _detect_price_column(df, args.price_col)

    # Compute deterministic JSD distribution using provided knobs
    jsd_vals = compute_jsd_distribution(
        df,
        seed=args.seed,
        price_col=price_col,
        n_bootstrap=args.n_bootstrap,
        sample_size=args.sample_size,
        n_bins=args.n_bins,
        bw=args.bw,
    )
    jsd_arr = np.array(jsd_vals, dtype=float)

    p95 = float(np.percentile(jsd_arr, 95))
    p99 = float(np.percentile(jsd_arr, 99))

    out = {
        "seed": int(args.seed),
        "price_col": price_col,
        "sample_size": int(len(df)),
        "percentiles": {"95": p95, "99": p99},
        "calibration_timestamp_utc": datetime.utcnow().isoformat() + "Z",
        "notes": "Calibration produced by compute_jsd_distribution (KDE/histogram fallback).",
    }

    with open(args.out, "w") as fh:
        json.dump(out, fh, indent=2)

    print(f"WROTE: {args.out}")
    print(
        f"seed={args.seed} price_col={price_col} sample_size={len(df)} p95={p95:.6f} p99={p99:.6f}"
    )


if __name__ == "__main__":
    main()
