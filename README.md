# MARKETSCAR

> "MARKETSCAR doesn't predict prices. It tells you when your automation no longer understands the market it's operating in."

**A governance system for algorithmic pricing risk.**

---

## Project Status

- ✅ **Phase 1:** Data & Baseline Freezing - COMPLETE
- ⏳ **Phase 2:** Diagnostic Engine - PENDING
- ⏳ **Phase 3:** Calibration - PENDING
- ⏳ **Phase 4:** Policy Gate - PENDING
- ⏳ **Phase 5:** Audit & Cryptographic Receipts - PENDING
- ⏳ **Phase 6:** AI Narrator (Amazon Bedrock) - PENDING
- ⏳ **Phase 7:** UI/UX - PENDING
- ⏳ **Phase 8:** QA Matrix - PENDING
- ⏳ **Phase 9:** Demo & Pitch - PENDING

---

## What MARKETSCAR Is

A **circuit breaker for algorithmic pricing systems** that:

- Detects when market behavior diverges from statistical baselines
- Physically blocks or throttles automated pricing actions under risk
- Generates cryptographically signed audit receipts
- Uses AI ONLY to explain decisions (never to make them)

---

## What MARKETSCAR Is NOT

❌ A price optimization system  
❌ A demand forecasting tool  
❌ A recommendation engine  
❌ An AI decision maker  
❌ A replacement for human judgment

---

## Problem Statement

**Algorithmic pricing systems fail catastrophically when:**

1. **Flash crashes:** Self-reinforcing feedback loops
2. **Adversarial spoofing:** Coordinated price manipulation
3. **Regime changes:** Market structure shifts (Black Friday, supply shocks)
4. **Bot wars:** Competing algorithms create unstable equilibria

**Impact:** Billions in losses, reputational damage, regulatory scrutiny.

---

## Solution Architecture

```
┌────────────────────────────────────────────────────────────┐
│                   PRICING AUTOMATION                       │
│            (Your existing pricing agent)                   │
└───────────────────────┬────────────────────────────────────┘
                        │
                        ▼
        ┌───────────────────────────────┐
        │    MARKETSCAR GOVERNANCE      │
        │                               │
        │  1. Statistical Diagnostics   │◄─── Frozen Baselines
        │     (Jensen-Shannon Div)      │
        │                               │
        │  2. Policy Gate               │◄─── Business Config
        │     OPEN / THROTTLE / LOCK    │
        │                               │
        │  3. Audit Logger              │
        │     (Cryptographic Receipts)  │
        │                               │
        │  4. AI Narrator (Bedrock)     │◄─── Explain Only
        │     (Human-readable output)   │
        └───────────────┬───────────────┘
                        │
                        ▼
        ┌───────────────────────────────┐
        │     PRICING API               │
        │  (if gate allows execution)   │
        └───────────────────────────────┘
```

---

## Key Principles

### 1. DIAGNOSIS ≠ POLICY
- **Math** determines regime (JSD, distribution shift)
- **Business** determines action (OPEN/THROTTLE/LOCK)

### 2. FALSE APPROVALS ARE CATASTROPHIC
- System is conservative by design
- False abstentions (blocking safe actions) are acceptable
- False approvals (allowing risky actions) are not

### 3. DETERMINISM OVER CLEVERNESS
- Reproducible statistics (fixed RNG seeds)
- No black-box models
- Every decision is auditable

### 4. MONITORING ≠ INTERVENTION
- Detection alone is useless
- System must physically block execution

### 5. NO SILENT FAILURES
- Every decision generates cryptographic receipt
- Tampering is detectable

---

## Quick Start

### Prerequisites

```bash
python >= 3.10
pip
git
```

### Installation

```bash
# Clone repository
git clone https://github.com/your-org/marketscar.git
cd marketscar

# Install dependencies
pip install -r requirements.txt

# Generate synthetic baseline data
python3 scripts/generate_synthetic_data.py

# Freeze baseline with SHA256 hash
python3 scripts/baseline_freezer.py

# Verify installation
python3 tests/test_phase1.py
```

**Expected output:**
```
============================================================
✓ ALL TESTS PASSED
============================================================
```

---

## Repository Structure

```
marketscar/
├── data/
│   ├── raw/                    # Baseline datasets
│   │   ├── online_retail_II.csv
│   │   └── metadata.json
│   └── baselines/              # Frozen manifests
│       └── manifest.json       # SHA256 hashes
│
├── src/
│   ├── data/                   # Data layer
│   │   └── replay.py          # Event streamer
│   ├── diagnostics/           # Statistical engine (Phase 2)
│   ├── gate/                  # Policy enforcement (Phase 4)
│   ├── audit/                 # Cryptographic logging (Phase 5)
│   └── ui/                    # Dashboard (Phase 7)
│
├── scripts/
│   ├── generate_synthetic_data.py
│   ├── baseline_freezer.py
│   └── calibrate.py           # Threshold tuning (Phase 3)
│
├── tests/
│   └── test_phase1.py         # Unit tests
│
├── config/
│   ├── policy_config.json     # Business rules
│   └── frozen_thresholds.json # Statistical thresholds
│
├── docs/
│   └── PHASE1_README.md       # Detailed docs
│
├── requirements.txt
└── README.md
```

---

## Current Capabilities (Phase 1)

### Data Provenance ✅
- Deterministic synthetic data generation (UCI-compatible)
- SHA256 cryptographic baseline freezing
- Tamper-evident manifest generation

### Replay Engine ✅
- Stream historical data as live events
- Hash verification on load
- Configurable playback speed (1x - 100x)
- Time-window extraction (14-day baselines)
- Adversarial scenario injection

### Test Coverage ✅
- 11 unit tests passing
- Hash determinism verified
- Tamper detection validated
- Bit-for-bit reproducibility proven

---

## Production Deployment Note

**CRITICAL:** This repository uses **synthetic data** for development/demo.

Production deployments MUST use real UCI Online Retail II dataset:
```
https://archive.ics.uci.edu/ml/machine-learning-databases/00502/online_retail_II.xlsx
```

Replace synthetic data by:
1. Download UCI dataset in environment with network access
2. Convert to CSV: `data/raw/online_retail_II.csv`
3. Re-run baseline freezer: `python3 scripts/baseline_freezer.py`
4. Update manifest hash in deployment pipeline

---

## Technical Guarantees

| Property           | Guarantee                                    |
|--------------------|----------------------------------------------|
| Determinism        | Same input → same output (bit-for-bit)       |
| Tamper Detection   | Any modification detected via hash mismatch  |
| Auditability       | Every decision logged with cryptographic sig |
| Reproducibility    | Third parties can verify baselines           |
| Conservative       | False abstentions > false approvals          |

---

## License

[Specify license]

---

## Contact

[Project maintainer contact]

---

## Acknowledgments

- UCI Machine Learning Repository (Online Retail II dataset)
- Amazon Bedrock (AI narration, Phase 6)
- Constitution-driven execution methodology
