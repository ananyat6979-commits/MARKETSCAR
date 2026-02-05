#!/usr/bin/env python3
"""
Unit Tests - Phase 1: Data & Baseline Freezing
===============================================

Tests verify:
1. Hash determinism (same data → same hash)
2. Tamper detection (modified data → different hash)
3. Replay integrity (baseline verification)
4. Schema validation
5. Reproducibility
"""

import hashlib
import json
import shutil
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

import pandas as pd

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "data"))

from src.data.replay import ReplayEngine


class TestBaselineHashing(unittest.TestCase):
    """Test cryptographic baseline freezing"""

    @classmethod
    def setUpClass(cls):
        """Create test fixtures"""
        cls.test_dir = Path(tempfile.mkdtemp())
        cls.test_csv = cls.test_dir / "test_data.csv"

        # Create minimal test dataset
        test_data = pd.DataFrame(
            {
                "Invoice": ["A001", "A002", "A003"],
                "StockCode": ["SKU1", "SKU2", "SKU1"],
                "Description": ["Product 1", "Product 2", "Product 1"],
                "Quantity": [1, 2, 3],
                "InvoiceDate": pd.date_range(
                    "2010-01-01", periods=3, freq="H"
                ),
                "Price": [10.0, 20.0, 10.0],
                "Customer ID": [1001, 1002, 1001],
                "Country": ["UK", "UK", "UK"],
            }
        )

        test_data.to_csv(cls.test_csv, index=False)
        cls.original_hash = cls._compute_hash(cls.test_csv)

    @classmethod
    def tearDownClass(cls):
        """Cleanup test fixtures"""
        shutil.rmtree(cls.test_dir)

    @staticmethod
    def _compute_hash(filepath):
        """Compute SHA256 hash of file"""
        hash_obj = hashlib.sha256()
        with open(filepath, "rb") as f:
            while chunk := f.read(8192):
                hash_obj.update(chunk)
        return hash_obj.hexdigest()

    def test_hash_determinism(self):
        """Test that same file produces same hash"""
        hash1 = self._compute_hash(self.test_csv)
        hash2 = self._compute_hash(self.test_csv)

        self.assertEqual(hash1, hash2, "Hash must be deterministic")
        self.assertEqual(hash1, self.original_hash, "Hash must match original")

    def test_tamper_detection(self):
        """Test that modified file produces different hash"""
        # Create tampered copy
        tampered_csv = self.test_dir / "tampered.csv"
        shutil.copy(self.test_csv, tampered_csv)

        # Modify data
        df = pd.read_csv(tampered_csv)
        df.loc[0, "Price"] = 999.99  # Change a price
        df.to_csv(tampered_csv, index=False)

        # Compute hashes
        original_hash = self._compute_hash(self.test_csv)
        tampered_hash = self._compute_hash(tampered_csv)

        self.assertNotEqual(
            original_hash,
            tampered_hash,
            "Tampered data must produce different hash",
        )

    def test_bit_for_bit_reproducibility(self):
        """Test that regenerating CSV produces identical hash"""
        # Read and re-save data
        df = pd.read_csv(self.test_csv)
        reproduced_csv = self.test_dir / "reproduced.csv"
        df.to_csv(reproduced_csv, index=False)

        # Compare hashes
        original_hash = self._compute_hash(self.test_csv)
        reproduced_hash = self._compute_hash(reproduced_csv)

        self.assertEqual(
            original_hash,
            reproduced_hash,
            "Reproduced CSV must be bit-for-bit identical",
        )


class TestReplayEngine(unittest.TestCase):
    """Test replay engine functionality"""

    @classmethod
    def setUpClass(cls):
        """Setup test data"""
        cls.test_dir = Path(tempfile.mkdtemp())
        cls.test_csv = cls.test_dir / "test_data.csv"
        cls.manifest_path = cls.test_dir / "manifest.json"

        # Create test dataset
        cls.test_data = pd.DataFrame(
            {
                "Invoice": [f"INV{i:03d}" for i in range(100)],
                "StockCode": [f"SKU{i%10}" for i in range(100)],
                "Description": [f"Product {i%10}" for i in range(100)],
                "Quantity": [1] * 100,
                "InvoiceDate": pd.date_range(
                    "2010-01-01", periods=100, freq="H"
                ),
                "Price": [float(i % 20 + 1) for i in range(100)],
                "Customer ID": [1000 + (i % 20) for i in range(100)],
                "Country": ["UK"] * 100,
            }
        )

        cls.test_data.to_csv(cls.test_csv, index=False)

        # Create manifest
        hash_obj = hashlib.sha256()
        with open(cls.test_csv, "rb") as f:
            while chunk := f.read(8192):
                hash_obj.update(chunk)

        manifest = {
            "version": "1.0.0",
            "frozen_at": datetime.now().isoformat(),
            "file": {
                "name": "test_data.csv",
                "path": str(cls.test_csv),
                "size_bytes": cls.test_csv.stat().st_size,
                "hash_algorithm": "sha256",
                "hash": hash_obj.hexdigest(),
            },
            "source": {"url": "TEST", "type": "test"},
            "schema": {
                "columns": list(cls.test_data.columns),
                "validated": True,
            },
            "statistics": {},
        }

        with open(cls.manifest_path, "w") as f:
            json.dump(manifest, f, default=str)

    @classmethod
    def tearDownClass(cls):
        """Cleanup"""
        shutil.rmtree(cls.test_dir)

    def test_replay_initialization_with_verification(self):
        """Test that replay engine verifies baseline on init"""
        # Should succeed with valid manifest
        engine = ReplayEngine(
            self.test_csv, manifest_path=self.manifest_path, verify_hash=True
        )

        self.assertEqual(len(engine.df), 100, "Should load all records")

    def test_replay_tamper_detection(self):
        """Test that tampered baseline raises error"""
        # Tamper with CSV
        df = pd.read_csv(self.test_csv)
        df.loc[0, "Price"] = 9999.99
        df.to_csv(self.test_csv, index=False)

        # Should raise error
        with self.assertRaises(ValueError) as context:
            engine = ReplayEngine(
                self.test_csv,
                manifest_path=self.manifest_path,
                verify_hash=True,
            )

        self.assertIn("TAMPERING", str(context.exception).upper())

        # Restore original data for other tests
        self.test_data.to_csv(self.test_csv, index=False)

    def test_stream_determinism(self):
        """Test that streaming produces deterministic results"""
        engine = ReplayEngine(
            self.test_csv, manifest_path=self.manifest_path, verify_hash=True
        )

        # Stream twice
        stream1 = list(engine.stream(max_events=10, realtime=False))
        engine.reset()
        stream2 = list(engine.stream(max_events=10, realtime=False))

        # Should be identical
        self.assertEqual(len(stream1), len(stream2))

        for txn1, txn2 in zip(stream1, stream2):
            self.assertEqual(txn1.invoice, txn2.invoice)
            self.assertEqual(txn1.stock_code, txn2.stock_code)
            self.assertEqual(txn1.price, txn2.price)

    def test_window_extraction(self):
        """Test time window extraction"""
        engine = ReplayEngine(
            self.test_csv, manifest_path=self.manifest_path, verify_hash=True
        )

        # Get 1-day window
        end_date = datetime(2010, 1, 2, 0, 0, 0)
        window = engine.get_window(end_date, window_days=1)

        # Should contain transactions in range
        self.assertGreater(len(window), 0)
        self.assertTrue(all(window["InvoiceDate"] <= end_date))
        self.assertTrue(
            all(window["InvoiceDate"] >= end_date - pd.Timedelta(days=1))
        )

    def test_adversarial_injection(self):
        """Test adversarial scenario injection"""
        engine = ReplayEngine(
            self.test_csv, manifest_path=self.manifest_path, verify_hash=True
        )

        # Inject spoof scenario
        spoof_df = engine.inject_scenario(
            "adversarial_spoof",
            base_date=datetime(2010, 6, 1),
            params={"n_transactions": 20},
        )

        self.assertEqual(
            len(spoof_df), 20, "Should generate 20 spoof transactions"
        )
        self.assertEqual(
            spoof_df["Customer ID"].iloc[0],
            99999,
            "Should use synthetic customer ID",
        )


class TestSchemaValidation(unittest.TestCase):
    """Test schema validation logic"""

    def test_valid_schema(self):
        """Test that valid schema passes"""
        expected = ["A", "B", "C"]
        df = pd.DataFrame({"A": [1], "B": [2], "C": [3]})

        actual_cols = set(df.columns)
        expected_cols = set(expected)

        missing = expected_cols - actual_cols
        extra = actual_cols - expected_cols

        self.assertEqual(len(missing), 0, "Should have no missing columns")
        self.assertEqual(len(extra), 0, "Should have no extra columns")

    def test_missing_columns(self):
        """Test detection of missing columns"""
        expected = ["A", "B", "C"]
        df = pd.DataFrame({"A": [1], "B": [2]})  # Missing C

        actual_cols = set(df.columns)
        expected_cols = set(expected)

        missing = expected_cols - actual_cols

        self.assertEqual(missing, {"C"}, "Should detect missing column C")

    def test_extra_columns(self):
        """Test detection of extra columns"""
        expected = ["A", "B"]
        df = pd.DataFrame({"A": [1], "B": [2], "C": [3]})  # Extra C

        actual_cols = set(df.columns)
        expected_cols = set(expected)

        extra = actual_cols - expected_cols

        self.assertEqual(extra, {"C"}, "Should detect extra column C")


def run_tests():
    """Run all Phase 1 tests"""
    print("=" * 60)
    print("PHASE 1 UNIT TESTS - DATA & BASELINE FREEZING")
    print("=" * 60)
    print()

    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    suite.addTests(loader.loadTestsFromTestCase(TestBaselineHashing))
    suite.addTests(loader.loadTestsFromTestCase(TestReplayEngine))
    suite.addTests(loader.loadTestsFromTestCase(TestSchemaValidation))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print()
    print("=" * 60)
    if result.wasSuccessful():
        print("✓ ALL TESTS PASSED")
    else:
        print("✗ TESTS FAILED")
        print(f"  Failures: {len(result.failures)}")
        print(f"  Errors: {len(result.errors)}")
    print("=" * 60)

    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    exit(run_tests())
