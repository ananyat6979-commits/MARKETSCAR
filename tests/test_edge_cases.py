import pandas as pd
from src.diagnostic.jsd_calculator import compute_jsd_distribution

def test_partial_columns_and_unicode_dates():
    # Partial columns (missing price)
    df1 = pd.DataFrame({"sku": ["A", "B"]})
    # Should raise TypeError because price column missing
    try:
        compute_jsd_distribution(df1)
        raised = False
    except Exception:
        raised = True
    assert raised

    # unicode names and timezone-normalized dates should not break the function when price exists
    df2 = pd.DataFrame({
        "sku": ["Å", "Bö"],
        "price": [10.0, 12.0],
        "InvoiceDate": pd.to_datetime(["2020-01-01T00:00:00+05:30", "2020-01-02T00:00:00+00:00"])
    })
    out = compute_jsd_distribution(df2, seed=1, n_bootstrap=5)
    assert len(out) == 5
