"""Bootstrap for trading metrics — non-parametric confidence intervals.

PF is a ratio (gross_profit / gross_loss), not a mean. T-test is invalid.
Bootstrap = resample trades with replacement, recompute metric, get distribution.

Usage:
    from core.stats.bootstrap import bootstrap_profit_factor
    pf_ci = bootstrap_profit_factor(trade_pnls, n_iter=10000, ci=0.95)
    # returns: {"mean": 2.31, "ci_low": 1.78, "ci_high": 2.94, "pct_above_1": 0.987}
"""
from __future__ import annotations
import numpy as np
from typing import Sequence


def profit_factor(pnls: np.ndarray) -> float:
    """Sum(gains) / |Sum(losses)|. Returns inf if no losses."""
    gains = pnls[pnls > 0].sum()
    losses = abs(pnls[pnls < 0].sum())
    if losses == 0:
        return float("inf") if gains > 0 else 0.0
    return float(gains / losses)


def bootstrap_profit_factor(
    pnls: Sequence[float],
    n_iter: int = 10_000,
    ci: float = 0.95,
    seed: int | None = 42,
) -> dict:
    """Bootstrap CI for Profit Factor.

    Args:
        pnls: array of per-trade PnL (positives = wins, negatives = losses)
        n_iter: number of bootstrap resamples (default 10k for stability)
        ci: confidence interval width (0.95 = 95% CI)
        seed: RNG seed for reproducibility

    Returns:
        dict with keys: mean, median, ci_low, ci_high, pct_above_1, n_trades
    """
    arr = np.asarray(pnls, dtype=np.float64)
    n = len(arr)
    if n < 30:
        raise ValueError(f"Need >=30 trades for reliable bootstrap, got {n}")

    rng = np.random.default_rng(seed)
    pfs = np.empty(n_iter, dtype=np.float64)
    for i in range(n_iter):
        sample = arr[rng.integers(0, n, size=n)]
        pfs[i] = profit_factor(sample)

    pfs_finite = pfs[np.isfinite(pfs)]
    alpha = (1 - ci) / 2

    return {
        "n_trades": int(n),
        "n_iter": int(n_iter),
        "mean": float(np.mean(pfs_finite)),
        "median": float(np.median(pfs_finite)),
        "ci_low": float(np.quantile(pfs_finite, alpha)),
        "ci_high": float(np.quantile(pfs_finite, 1 - alpha)),
        "pct_above_1": float(np.mean(pfs_finite > 1.0)),
        "pct_above_1_5": float(np.mean(pfs_finite > 1.5)),
    }


def bootstrap_win_rate(
    pnls: Sequence[float],
    n_iter: int = 10_000,
    ci: float = 0.95,
    seed: int | None = 42,
) -> dict:
    """Bootstrap CI for win rate."""
    arr = np.asarray(pnls, dtype=np.float64)
    n = len(arr)
    if n < 30:
        raise ValueError(f"Need >=30 trades for reliable bootstrap, got {n}")

    rng = np.random.default_rng(seed)
    wrs = np.empty(n_iter, dtype=np.float64)
    for i in range(n_iter):
        sample = arr[rng.integers(0, n, size=n)]
        wrs[i] = (sample > 0).mean()

    alpha = (1 - ci) / 2
    return {
        "n_trades": int(n),
        "mean": float(np.mean(wrs)),
        "ci_low": float(np.quantile(wrs, alpha)),
        "ci_high": float(np.quantile(wrs, 1 - alpha)),
    }


if __name__ == "__main__":
    # Smoke test : synthetic trade series with known edge
    rng = np.random.default_rng(123)
    n = 200
    # Win 55%, avg win 2.0, avg loss -1.0
    pnls = np.where(rng.random(n) < 0.55, rng.normal(2.0, 0.5, n), rng.normal(-1.0, 0.3, n))

    pf_result = bootstrap_profit_factor(pnls.tolist(), n_iter=5000)
    print(f"Profit Factor bootstrap (n={n}, 5k iter):")
    print(f"  mean={pf_result['mean']:.3f}  median={pf_result['median']:.3f}")
    print(f"  95% CI=[{pf_result['ci_low']:.3f}, {pf_result['ci_high']:.3f}]")
    print(f"  pct PF>1.0={pf_result['pct_above_1']:.1%}")
    print(f"  pct PF>1.5={pf_result['pct_above_1_5']:.1%}")

    wr_result = bootstrap_win_rate(pnls.tolist(), n_iter=5000)
    print(f"\nWin Rate bootstrap:")
    print(f"  mean={wr_result['mean']:.1%}  95% CI=[{wr_result['ci_low']:.1%}, {wr_result['ci_high']:.1%}]")
