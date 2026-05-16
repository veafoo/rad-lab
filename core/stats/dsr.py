"""Deflated Sharpe Ratio (Bailey & Lopez de Prado, 2014).

DSR = PSR with benchmark adjusted for multi-testing.
Accounts for the maximum Sharpe expected under null hypothesis given N trials.

If you test N hypotheses, the best one will have an inflated SR even if all are null.
DSR deflates the observed SR by the expected max under null.

DSR > 0.95 = strong evidence the strategy's edge survives multi-testing.

Usage:
    from core.stats.dsr import deflated_sharpe_ratio
    dsr = deflated_sharpe_ratio(returns, sr_trials_variance=0.5, n_trials=50)
"""
from __future__ import annotations
import numpy as np
from scipy.stats import norm
from typing import Sequence

from .psr import probabilistic_sharpe_ratio

EULER_MASCHERONI = 0.5772156649015328606


def expected_max_sharpe(n_trials: int, sr_trials_variance: float) -> float:
    """Expected maximum Sharpe under null hypothesis given N trials.

    E[max(SR_k)] ≈ sqrt(V[SR]) * ((1-γ)·Φ^-1(1-1/N) + γ·Φ^-1(1-1/(N·e)))
    where γ = Euler-Mascheroni constant.

    The SR variance V[SR] is the empirical variance of all trial Sharpes.

    Returns annualized expected max SR (assuming sr_trials_variance is annualized).
    """
    if n_trials < 1:
        raise ValueError("n_trials must be >= 1")
    if sr_trials_variance < 0:
        raise ValueError("sr_trials_variance must be >= 0")
    if n_trials == 1:
        return 0.0  # no max effect with single trial

    sigma = np.sqrt(sr_trials_variance)
    gamma = EULER_MASCHERONI
    a = (1 - gamma) * norm.ppf(1 - 1 / n_trials)
    b = gamma * norm.ppf(1 - 1 / (n_trials * np.e))
    return float(sigma * (a + b))


def deflated_sharpe_ratio(
    returns: Sequence[float],
    sr_trials_variance: float,
    n_trials: int,
    periods_per_year: int = 252,
) -> dict:
    """Deflated Sharpe Ratio.

    Args:
        returns: per-period returns of the candidate strategy
        sr_trials_variance: empirical variance of annualized SRs across all N trials
        n_trials: number of strategies/variants tested
        periods_per_year: 252 daily, 12 monthly, etc.

    Returns dict with dsr (probability), expected max SR under null, and all PSR fields.
    """
    sr_max_null = expected_max_sharpe(n_trials, sr_trials_variance)
    psr_result = probabilistic_sharpe_ratio(returns, sr_benchmark=sr_max_null, periods_per_year=periods_per_year)
    return {
        **psr_result,
        "n_trials": int(n_trials),
        "sr_trials_variance": float(sr_trials_variance),
        "expected_max_sr_under_null": sr_max_null,
        "dsr": psr_result["psr"],
        "significant_at_95": psr_result["psr"] >= 0.95,
        "significant_at_99": psr_result["psr"] >= 0.99,
    }


if __name__ == "__main__":
    rng = np.random.default_rng(42)
    daily_returns = rng.normal(0.001, 0.015, 500)

    print("=== Expected max SR under null (Bailey-Lopez de Prado) ===")
    for n in [1, 10, 50, 100, 500, 1000]:
        e_max = expected_max_sharpe(n, sr_trials_variance=0.5)
        print(f"  N={n:5d}, V[SR]=0.5 -> E[max SR] = {e_max:.3f}")

    print("\n=== DSR for synthetic strat ===")
    for n_trials in [1, 50, 384]:
        r = deflated_sharpe_ratio(daily_returns, sr_trials_variance=0.5, n_trials=n_trials)
        sig = "STAT-SIG" if r["significant_at_95"] else "NOT"
        print(f"  N trials={n_trials:4d}: SR_obs={r['sr_observed_annualized']:.2f}, "
              f"SR_max_null={r['expected_max_sr_under_null']:.2f}, DSR={r['dsr']:.4f} -> {sig}")
