#!/usr/bin/env python3
"""
Baseline Freezer - Immutable Data Provenance System
====================================================

Generates cryptographic manifest for all baseline data.
Once frozen, any modification to baseline data will be detected.

Output: data/baselines/manifest.json
- SHA256 hash of raw data file
- Acquisition timestamp
- File size
- Source URL (for production UCI dataset)
- Schema validation
"""

import hashlib
import json
import os
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

# CRITICAL: These paths are FROZEN
DATA_DIR = Path(__file__).parent.parent / "data"
RAW_DIR = DATA_DIR / "raw"
BASELINES_DIR = DATA_DIR / "baselines"
MANIFEST_PATH = BASELINES_DIR / "manifest.json"

# Expected schema (UCI Online Retail II)
EXPECTED_SCHEMA = [
    "Invoice",
    "StockCode",
    "Description",
    "Quantity",
    "InvoiceDate",
    "Price",
    "Customer ID",
    "Country",
]


def compute_file_hash(filepath, algorithm="sha256", chunk_size=8192):
    """
    Compute cryptographic hash of file.
    Uses chunked reading to handle large files.

    Args:
        filepath: Path to file
        algorithm: Hash algorithm (default: sha256)
        chunk_size: Bytes per chunk (default: 8KB)

    Returns:
        Hex-encoded hash digest
    """
    hash_obj = hashlib.new(algorithm)

    with open(filepath, "rb") as f:
        while chunk := f.read(chunk_size):
            hash_obj.update(chunk)

    return hash_obj.hexdigest()


def validate_schema(df, expected_columns):
    """
    Validate dataframe has expected schema.

    Returns:
        (is_valid, missing_cols, extra_cols)
    """
    actual_cols = set(df.columns)
    expected_cols = set(expected_columns)

    missing = expected_cols - actual_cols
    extra = actual_cols - expected_cols

    is_valid = len(missing) == 0 and len(extra) == 0

    return is_valid, list(missing), list(extra)


def compute_baseline_statistics(df):
    """
    Compute statistical fingerprint of baseline data.
    These will be used for distribution comparison.
    """
    stats = {
        "num_records": len(df),
        "num_unique_skus": int(df["StockCode"].nunique()),
        "num_unique_customers": int(df["Customer ID"].nunique()),
        "num_unique_countries": int(df["Country"].nunique()),
        "date_range": {
            "start": df["InvoiceDate"].min(),
            "end": df["InvoiceDate"].max(),
        },
        "price_stats": {
            "mean": float(df["Price"].mean()),
            "std": float(df["Price"].std()),
            "min": float(df["Price"].min()),
            "max": float(df["Price"].max()),
            "median": float(df["Price"].median()),
        },
        "quantity_stats": {
            "mean": float(df["Quantity"].mean()),
            "std": float(df["Quantity"].std()),
            "min": int(df["Quantity"].min()),
            "max": int(df["Quantity"].max()),
            "median": float(df["Quantity"].median()),
        },
    }

    return stats


def freeze_baseline(csv_path, source_url=None):
    """
    Create immutable baseline manifest.

    Args:
        csv_path: Path to raw CSV data
        source_url: URL where data was acquired (None for synthetic)

    Returns:
        manifest dict
    """
    print(f"Freezing baseline: {csv_path}")

    # Compute file hash
    print("Computing SHA256 hash...")
    file_hash = compute_file_hash(csv_path)
    print(f"  Hash: {file_hash}")

    # Get file metadata
    file_stat = os.stat(csv_path)
    file_size = file_stat.st_size

    # Load and validate data
    print("Loading and validating data...")
    df = pd.read_csv(csv_path, parse_dates=["InvoiceDate"])

    is_valid, missing, extra = validate_schema(df, EXPECTED_SCHEMA)

    if not is_valid:
        raise ValueError(
            f"Schema validation failed!\n"
            f"Missing columns: {missing}\n"
            f"Extra columns: {extra}"
        )

    print(f"  ✓ Schema valid")
    print(f"  ✓ {len(df):,} records loaded")

    # Compute baseline statistics
    print("Computing baseline statistics...")
    stats = compute_baseline_statistics(df)

    # Build manifest
    manifest = {
        "version": "1.0.0",
        "frozen_at": datetime.now().isoformat(),
        "file": {
            "name": os.path.basename(csv_path),
            "path": str(csv_path),
            "size_bytes": file_size,
            "hash_algorithm": "sha256",
            "hash": file_hash,
        },
        "source": {
            "url": source_url or "SYNTHETIC_DATA",
            "type": "synthetic" if source_url is None else "real",
            "note": (
                "Production deployment must use real UCI Online Retail II dataset"
                if source_url is None
                else None
            ),
        },
        "schema": {"columns": EXPECTED_SCHEMA, "validated": True},
        "statistics": stats,
    }

    # Save manifest
    BASELINES_DIR.mkdir(parents=True, exist_ok=True)

    with open(MANIFEST_PATH, "w") as f:
        json.dump(manifest, f, indent=2, default=str)

    print(f"\n✓ Baseline frozen successfully")
    print(f"  Manifest saved to: {MANIFEST_PATH}")

    return manifest


def verify_baseline(csv_path, manifest_path=MANIFEST_PATH):
    """
    Verify that data file matches frozen manifest.
    """
    print(f"Verifying baseline integrity...")

    # Load manifest
    if not os.path.exists(manifest_path):
        print(f"Manifest not found: {manifest_path}", file=sys.stderr)
        sys.exit(2)

    with open(manifest_path, "r") as f:
        manifest = json.load(f)

    expected_hash = manifest["file"]["hash"]
    hash_algorithm = manifest["file"]["hash_algorithm"]

    # Compute current hash
    print(f"Computing {hash_algorithm} hash...")
    actual_hash = compute_file_hash(csv_path, algorithm=hash_algorithm)

    # Compare (CI-safe behavior)
    if expected_hash.lower() != actual_hash.lower():
        print("BASELINE HASH MISMATCH", file=sys.stderr)
        sys.exit(2)
    else:
        print("MANIFEST VERIFIED")
        sys.exit(0)


def main():
    """Freeze baseline data and verify"""

    csv_path = RAW_DIR / "online_retail_II.csv"

    if not csv_path.exists():
        print(f"ERROR: Data file not found: {csv_path}")
        print("Run generate_synthetic_data.py first")
        return 1

    # Freeze baseline
    manifest = freeze_baseline(csv_path, source_url=None)

    print("\n" + "=" * 60)
    print("MANIFEST SUMMARY")
    print("=" * 60)
    print(f"File:       {manifest['file']['name']}")
    print(f"Size:       {manifest['file']['size_bytes']:,} bytes")
    print(f"Hash:       {manifest['file']['hash'][:16]}...")
    print(f"Records:    {manifest['statistics']['num_records']:,}")
    print(f"SKUs:       {manifest['statistics']['num_unique_skus']:,}")
    print(f"Customers:  {manifest['statistics']['num_unique_customers']:,}")
    print(f"Date range: {manifest['statistics']['date_range']['start']} to")
    print(f"            {manifest['statistics']['date_range']['end']}")
    print("=" * 60)

    # Verify immediately
    print("\n" + "=" * 60)
    print("VERIFICATION TEST")
    print("=" * 60)

    verify_baseline(csv_path)

    print("=" * 60)

    return 0


if __name__ == "__main__":
    exit(main())
