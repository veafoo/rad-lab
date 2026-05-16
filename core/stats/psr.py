"""Probabilistic Sharpe Ratio (Bailey & Lopez de Prado, 2012).

PSR(SR*) = Pr(true_SR > SR*) given observed Sharpe.
Accounts for skewness and kurtosis of returns (Sharpe alone assumes normality).

PSR > 0.95 = strong evidence that true SR > benchmark.
PSR < 0.50 = no evidence.

Usage:
    from core.stats.psr import sharpe_ratio, probabilistic_sharpe_ratio
    psr = probabilistic_sharpe_ratio(daily_returns, sr_benchmark=0.0)
"""
from __future__ import annotations
import numpy as np
from scipy.stats import norm, skew as scipy_skew, kurtosis as scipy_kurt
from typing import Sequence


def sharpe_ratio(returns: Sequence[float], periods_per_year: int = 252) -> float:
    """Annualized Sharpe (risk-free = 0). Standard formula."""
    arr = np.asarray(returns, dtype=np.float64)
    if len(arr) < 2:
        return 0.0
    mean_r = arr.mean()
    std_r = arr.std(ddof=1)
    if std_r == 0:
        return 0.0
    return float(mean_r / std_r * np.sqrt(periods_per_year))


def probabilistic_sharpe_ratio(
    returns: Sequence[float],
    sr_benchmark: float = 0.0,
    periods_per_year: int = 252,
) -> dict:
    """PSR : probability that true SR exceeds benchmark.

    Args:
        returns: per-period returns (not annualized)
        sr_benchmark: SR threshold to beat (annualized, e.g. 0 for "any edge")
        periods_per_year: 252 for daily, 12 for monthly, etc.
    """
    arr = np.asarray(returns, dtype=np.float64)
    T = len(arr)
    if T < 30:
        raise ValueError(f"Need >=30 observations for PSR, got {T}")

    sr_obs_ann = sharpe_ratio(arr, periods_per_year)
    sr_obs_period = sr_obs_ann / np.sqrt(periods_per_year)
    sr_bench_period = sr_benchmark / np.sqrt(periods_per_year)

    skew_r = float(scipy_skew(arr))
    kurt_r = float(scipy_kurt(arr, fisher=False))  # Pearson kurtosis (3 = normal)

    numerator = (sr_obs_period - sr_bench_period) * np.sqrt(T - 1)
    denominator_sq = 1 - skew_r * sr_obs_period + (kurt_r - 1) / 4 * sr_obs_period**2
    if denominator_sq <= 0:
        denominator_sq = 1e-9
    denominator = np.sqrt(denominator_sq)

    psr = float(norm.cdf(numerator / denominator))

    return {
        "T": int(T),
        "sr_observed_annualized": sr_obs_ann,
        "sr_benchmark_annualized": sr_benchmark,
        "skewness": skew_r,
        "kurtosis_pearson": kurt_r,
        "psr": psr,
        "significant_at_95": psr >= 0.95,
        "significant_at_99": psr >= 0.99,
    }


if __name__ == "__main__":
    # Synthetic returns with positive expected SR
    rng = np.random.default_rng(42)
    daily_returns = rng.normal(0.001, 0.015, 500)  # mean 0.1%/day, vol 1.5%/day

    sr = sharpe_ratio(daily_returns)
    print(f"Observed annualized Sharpe: {sr:.3f}")

    r = probabilistic_sharpe_ratio(daily_returns, sr_benchmark=0.0)
    print(f"PSR(SR > 0)   = {r['psr']:.4f}  -> {'STAT-SIG' if r['significant_at_95'] else 'NOT'}")

    r2 = probabilistic_sharpe_ratio(daily_returns, sr_benchmark=1.0)
    print(f"PSR(SR > 1.0) = {r2['psr']:.4f}  -> {'STAT-SIG' if r2['significant_at_95'] else 'NOT'}")

    r3 = probabilistic_sharpe_ratio(daily_returns, sr_benchmark=2.0)
    print(f"PSR(SR > 2.0) = {r3['psr']:.4f}  -> {'STAT-SIG' if r3['significant_at_95'] else 'NOT'}")
