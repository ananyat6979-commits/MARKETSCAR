Diagnostics algorithm (exact)
-----------------------------
We compute Jensen-Shannon Distance (JSD) between a frozen baseline price distribution and a sampled window using KDE when available and deterministic histogram fallback otherwise. Steps:

1. Optionally log1p-transform prices to reduce heavy tails.
2. Use a fixed grid derived from baseline quantiles (0.5% to 99.5%) with a configurable bin count.
3. Compute baseline PMF and sample PMF on this grid:
   - Prefer scipy.stats.gaussian_kde with a fixed bandwidth (configurable).
   - If scipy is not available, compute a histogram (density=True) and convert to PMF.
4. Compute JSD(p || q) and normalize to [0,1] (divide by log(2)).
5. Repeat with deterministic bootstrap (numpy.RandomState with provided seed) to produce a distribution of JSD values used for calibration.

This deterministic approach ensures CI reproducibility and auditable thresholds.
