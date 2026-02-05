# tests/test_jsd_determinism.py
import pandas as pd

from src.diagnostic.jsd_calculator import compute_jsd_distribution


def test_jsd_seed_determinism():
    df = pd.DataFrame({"sku": ["A", "B"] * 50, "price": [10.0, 11.0] * 50})
    a = compute_jsd_distribution(
        df, seed=123, n_bootstrap=50, sample_size=50, n_bins=64
    )
    b = compute_jsd_distribution(
        df, seed=123, n_bootstrap=50, sample_size=50, n_bins=64
    )
    assert a == b  # same seed -> identical list
    # numeric range check
    assert all(0.0 <= v <= 1.0 for v in a)
    assert len(a) == 50
