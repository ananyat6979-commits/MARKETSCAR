from __future__ import annotations
from typing import List
import numpy as np

def compute_jsd_distribution(df, seed: int = 42) -> List[float]:
    """
    Deterministic stub for JSD distribution values used by calibrate.
    Produces a reproducible list of floats given seed.
    Replace with a real KDE-normalized JSD implementation in Phase 2.
    """
    rng = np.random.default_rng(seed)
    # produce 200 deterministic "jsd-like" numbers in 0..1
    vals = rng.random(200).tolist()
    return vals
