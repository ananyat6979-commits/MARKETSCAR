# MARKETSCAR - Phase 1: Data & Baseline Freezing

## Overview

Phase 1 establishes the **immutable data foundation** for MARKETSCAR's governance system.

**Key Principle:** Baselines must never drift. Any modification must be detectable cryptographically.

---

## Components

### 1. Synthetic Data Generator
**File:** `scripts/generate_synthetic_data.py`

Creates UCI Online Retail II-compatible dataset for development/demo purposes.

**CRITICAL:** Production deployments must use real UCI dataset from:
```
https://archive.ics.uci.edu/ml/machine-learning-databases/00502/online_retail_II.xlsx
```

**Features:**
- Deterministic generation (fixed random seed: 42)
- Matches UCI schema exactly
- ~42,000 transactions spanning 1 year
- Realistic price/quantity distributions

**Usage:**
```bash
cd scripts
python3 generate_synthetic_data.py
```

**Output:**
- `data/raw/online_retail_II.csv` - Transaction data
- `data/raw/metadata.json` - Generation metadata

---

### 2. Baseline Freezer
**File:** `scripts/baseline_freezer.py`

Generates cryptographic manifest for data provenance.

**Features:**
- SHA256 hashing (industry standard)
- Schema validation
- Statistical fingerprinting
- Immutable manifest generation

**Usage:**
```bash
cd scripts
python3 baseline_freezer.py
```

**Output:**
- `data/baselines/manifest.json` - Cryptographic manifest

**Manifest Structure:**
```json
{
  "version": "1.0.0",
  "frozen_at": "2026-01-31T...",
  "file": {
    "name": "online_retail_II.csv",
    "hash_algorithm": "sha256",
    "hash": "674c2e817ff525ce5945937ca41d2119cc26df0a93ceb25225454728b85d0a53"
  },
  "source": {
    "url": "SYNTHETIC_DATA",
    "type": "synthetic"
  },
  "schema": {
    "columns": ["Invoice", "StockCode", "Description", ...],
    "validated": true
  },
  "statistics": {
    "num_records": 42528,
    "num_unique_skus": 500,
    ...
  }
}
```

---

### 3. Replay Engine
**File:** `src/data/replay.py`

Streams frozen baseline as simulated live events.

**Features:**
- Hash verification on initialization
- Deterministic playback
- Configurable speed (1x, 10x, 100x)
- Time-window extraction (for 14-day baselines)
- Adversarial scenario injection (for testing)

**Usage:**
```python
from src.data.replay import ReplayEngine

# Initialize with verification
engine = ReplayEngine(
    csv_path='data/raw/online_retail_II.csv',
    verify_hash=True
)

# Stream first 100 events
for txn in engine.stream(max_events=100):
    print(f"{txn.invoice_date} | {txn.stock_code} | £{txn.price}")

# Get 14-day baseline window
window = engine.get_window(
    end_date=datetime(2010, 1, 1),
    window_days=14
)

# Inject adversarial scenario
spoof_df = engine.inject_scenario(
    'adversarial_spoof',
    base_date=datetime(2010, 6, 1),
    params={'n_transactions': 50, 'price_spike': 1.4}
)
```

---

## Reproducibility Guarantees

### Third-Party Verification

Anyone can verify MARKETSCAR's baseline integrity:

```bash
# 1. Clone repository
git clone https://github.com/your-org/marketscar.git
cd marketscar

# 2. Generate data (if using synthetic)
python3 scripts/generate_synthetic_data.py

# 3. Freeze baseline
python3 scripts/baseline_freezer.py

# 4. Verify hash matches
# Expected: 674c2e817ff525ce5945937ca41d2119cc26df0a93ceb25225454728b85d0a53
```

**Critical Test:** If generated hash does NOT match, reproducibility is broken.

---

## Unit Tests

**File:** `tests/test_phase1.py`

**Test Coverage:**
1. ✅ Hash determinism (same input → same hash)
2. ✅ Tamper detection (modified data → different hash)
3. ✅ Replay verification (engine detects tampering)
4. ✅ Stream determinism (same replay → same events)
5. ✅ Schema validation (correct columns enforced)
6. ✅ Bit-for-bit reproducibility

**Run Tests:**
```bash
python3 tests/test_phase1.py
```

**Expected Output:**
```
============================================================
PHASE 1 UNIT TESTS - DATA & BASELINE FREEZING
============================================================

test_bit_for_bit_reproducibility ... ok
test_hash_determinism ... ok
test_tamper_detection ... ok
test_adversarial_injection ... ok
test_replay_initialization_with_verification ... ok
test_replay_tamper_detection ... ok
test_stream_determinism ... ok
test_window_extraction ... ok
test_extra_columns ... ok
test_missing_columns ... ok
test_valid_schema ... ok

----------------------------------------------------------------------
Ran 11 tests in 0.050s

OK

============================================================
✓ ALL TESTS PASSED
============================================================
```

---

## Data Schema (UCI Online Retail II)

| Column       | Type     | Description                |
|--------------|----------|----------------------------|
| Invoice      | string   | Transaction ID             |
| StockCode    | string   | Product SKU                |
| Description  | string   | Product name               |
| Quantity     | int      | Units purchased            |
| InvoiceDate  | datetime | Transaction timestamp      |
| Price        | float    | Unit price (GBP)           |
| Customer ID  | int      | Customer identifier        |
| Country      | string   | Customer country           |

---

## Security Properties

### Cryptographic Guarantees

1. **Collision Resistance:** SHA256 makes accidental hash collisions computationally infeasible
2. **Tamper Evidence:** Any modification (even 1 bit) produces different hash
3. **Determinism:** Same file always produces same hash
4. **Immutability:** Once frozen, baseline cannot be changed without detection

### Attack Scenarios Defended

| Attack                  | Defense                          |
|-------------------------|----------------------------------|
| Data modification       | Hash mismatch detected on load   |
| Baseline substitution   | Different hash in manifest       |
| Silent drift            | Runtime verification enforced    |
| Replay manipulation     | Verification on engine init      |

---

## Phase 1 Acceptance Criteria

- [x] Synthetic UCI-compatible data generated (deterministic)
- [x] SHA256 manifest created and verified
- [x] Replay engine operational with hash verification
- [x] All 11 unit tests passing
- [x] Bit-for-bit reproducibility demonstrated
- [x] Third-party verification possible (documented process)

**Status:** ✅ PHASE 1 COMPLETE

---

## Next Phase

**PHASE 2:** Diagnostic Engine (Jensen-Shannon Divergence computation)

**Inputs Required:**
- Frozen baseline (from Phase 1) ✅
- Transaction stream (from Replay Engine) ✅

**Outputs Delivered:**
- Deterministic drift metrics
- Per-SKU anomaly scores
- Structural consistency checks
- Adversarial detection signals
