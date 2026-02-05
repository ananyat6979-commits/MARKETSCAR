import pandas as pd
from src.diagnostic.jsd_calculator import compute_jsd_distribution

def test_jsd_empty_and_singleton():
    df_empty = pd.DataFrame({"price": []})
    out = compute_jsd_distribution(df_empty, seed=0, n_bootstrap=5)
    assert out == [0.0]*5

    df_single = pd.DataFrame({"price": [42.0] * 10})
    out2 = compute_jsd_distribution(df_single, seed=0, n_bootstrap=5, sample_size=5)
    assert all(0.0 <= v <= 1.0 for v in out2)
