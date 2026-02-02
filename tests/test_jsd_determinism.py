from src.diagnostic.jsd_calculator import compute_jsd_distribution
import pandas as pd

def test_jsd_seed_determinism():
    # create a tiny synthetic dataframe - content isn't used by stub but keeps API consistent
    df = pd.DataFrame({"sku": ["A", "B"] * 50, "price": [10.0, 11.0] * 50})
    a = compute_jsd_distribution(df, seed=123)
    b = compute_jsd_distribution(df, seed=123)
    assert a == b
    assert len(a) == 200
