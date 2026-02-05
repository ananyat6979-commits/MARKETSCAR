# src/diagnostic/jsd_calculator.py
"""
Deterministic Jensen-Shannon Distance (JSD) estimator with KDE + histogram fallback.

Functions:
  compute_jsd_distribution(df, seed=42, price_col="price", n_bootstrap=200,
                           sample_size=None, n_bins=128, bw=None, log_transform=True)

Return:
  list of floats in [0.0, 1.0] - one JSD value per bootstrap iteration.

Notes:
- Deterministic: uses numpy.RandomState(seed).
- Normalizes JSD to be in [0,1] by dividing by log2(2) (explicit).
- If scipy is available, uses gaussian_kde but will gracefully fallback if KDE fails.
- Histogram fallback is deterministic and stable.
"""

import math
from typing import List, Optional

import numpy as np

try:
    from scipy.stats import gaussian_kde  # type: ignore

    _HAVE_SCIPY = True
except Exception:
    _HAVE_SCIPY = False

EPS = 1e-12


def _safe_normalize(arr: np.ndarray) -> np.ndarray:
    """Ensure arr sums to 1 and contains no zeros (add small eps)."""
    arr = np.asarray(arr, dtype=float)
    arr = arr + EPS
    s = arr.sum()
    if s <= 0:
        arr = np.ones_like(arr, dtype=float)
        s = arr.sum()
    return arr / float(s)


def _kl_div(p: np.ndarray, q: np.ndarray) -> float:
    """KL divergence KL(p || q); assumes p and q are PMFs and nonzero due to EPS."""
    p = np.asarray(p, dtype=float)
    q = np.asarray(q, dtype=float)
    return float(np.sum(p * np.log2(p / q)))


def _jsd_from_pmfs(p: np.ndarray, q: np.ndarray) -> float:
    """Return Jensen-Shannon divergence normalized to [0,1]."""
    p = _safe_normalize(p)
    q = _safe_normalize(q)
    m = 0.5 * (p + q)
    jsd = 0.5 * _kl_div(p, m) + 0.5 * _kl_div(q, m)
    # JSD is in [0, log2], normalize by log2 -> [0,1]
    return float(jsd / math.log2(2.0))


def _histogram_pmf_from_edges(
    edges: np.ndarray, samples: np.ndarray
) -> np.ndarray:
    """
    Build a PMF over provided bin edges deterministically using np.histogram.
    edges: bin edges array (len = n_bins+1)
    returns a length n_bins PMF.
    """
    hist_density, _ = np.histogram(samples, bins=edges, density=True)
    widths = edges[1:] - edges[:-1]
    mass = hist_density * widths
    return _safe_normalize(mass)


def _kde_pmf(
    grid_edges: np.ndarray, samples: np.ndarray, bw: Optional[float] = None
) -> np.ndarray:
    """
    Return PMF estimates on grid using gaussian_kde if available and stable.
    If KDE raises or produces degenerate covariance (e.g. all samples identical),
    fallback deterministically to histogram mass per bin edge.
    `grid_edges` is expected to be bin edges (length n_bins+1).
    """
    samples = np.asarray(samples, dtype=float)
    if samples.size == 0:
        # empty -> uniform
        return _safe_normalize(np.ones(len(grid_edges) - 1, dtype=float))

    # If all samples are (nearly) identical, avoid KDE (singular covariance).
    if np.unique(samples).size == 1:
        # place all mass in the bin containing the constant value
        val = float(samples[0])
        # find bin index
        idx = np.searchsorted(grid_edges, val, side="right") - 1
        idx = max(0, min(len(grid_edges) - 2, idx))
        pmf = np.zeros(len(grid_edges) - 1, dtype=float)
        pmf[idx] = 1.0
        return _safe_normalize(pmf)

    # Try scipy KDE if available; guard against exceptions / singularities.
    if _HAVE_SCIPY:
        try:
            # gaussian_kde expects 1-D array for 1D data.
            kde = gaussian_kde(samples, bw_method=bw)
            # Evaluate KDE at bin centers (better than edges)
            centers = 0.5 * (grid_edges[:-1] + grid_edges[1:])
            vals = kde(centers)
            return _safe_normalize(vals)
        except Exception:
            # fallback to histogram deterministic path
            return _histogram_pmf_from_edges(grid_edges, samples)

    # No scipy -> histogram fallback
    return _histogram_pmf_from_edges(grid_edges, samples)


def compute_jsd_distribution(
    df,
    seed: int = 42,
    price_col: str = "price",
    n_bootstrap: int = 200,
    sample_size: Optional[int] = None,
    n_bins: int = 128,
    bw: Optional[float] = None,
    log_transform: bool = True,
) -> List[float]:
    """
    Compute a distribution of JSD values by bootstrapping.

    Parameters
    ----------
    df : pandas.DataFrame
      DataFrame containing at least `price_col`.
    seed : int
      Deterministic RNG seed.
    price_col : str
      Column name with price numbers.
    n_bootstrap : int
      Number of bootstrap resamples.
    sample_size : int | None
      Number of rows to sample per bootstrap; if None uses len(df).
    n_bins : int
      Number of histogram bins (used for histogram fallback and grid size).
    bw : float | None
      Bandwidth for gaussian_kde (if scipy available); if None, gaussian_kde default used.
    log_transform : bool
      Whether to apply log1p transform to prices to reduce heavy tails.
    """
    import pandas as pd

    if not isinstance(df, pd.DataFrame):
        raise TypeError("df must be a pandas.DataFrame")

    if price_col not in df.columns:
        raise KeyError(
            f"price column '{price_col}' not found in DataFrame (cols: {list(df.columns)})"
        )

    prices = df[price_col].dropna().astype(float).values
    if log_transform:
        prices = np.log1p(prices)

    if prices.size == 0:
        return [0.0] * int(n_bootstrap)

    rng = np.random.RandomState(int(seed))
    n = int(sample_size) if sample_size is not None else len(prices)

    # Construct fixed edges for bins using robust quantiles (avoid extreme tails)
    lo, hi = np.percentile(prices, [0.5, 99.5])
    if hi <= lo:
        lo = float(prices.min())
        hi = float(prices.max())
    pad = max(1e-6, (hi - lo) * 0.1)
    grid_edges = np.linspace(lo - pad, hi + pad, num=int(n_bins) + 1)

    # Baseline PMF (anchor)
    baseline = prices.copy()
    p_baseline = _kde_pmf(grid_edges, baseline, bw=bw)

    jsd_vals: List[float] = []
    for i in range(int(n_bootstrap)):
        idx = rng.randint(0, len(prices), size=n)
        sample = prices[idx]
        try:
            q_sample = _kde_pmf(grid_edges, sample, bw=bw)
            jsd = _jsd_from_pmfs(p_baseline, q_sample)
        except Exception:
            # If something unexpected occurs, record max distance conservatively (1.0)
            jsd = 1.0
        jsd = float(max(0.0, min(1.0, jsd)))
        jsd_vals.append(jsd)

    return jsd_vals
