"""Multi-testing correction — Bonferroni and Holm-Bonferroni.

When testing N hypotheses simultaneously, raw p-values lie. Bonferroni divides alpha by N.
Holm-Bonferroni is a step-down procedure, more powerful (rejects more truly-null hypotheses).

Usage:
    from core.stats.bonferroni import bonferroni_correction, holm_bonferroni
    result = bonferroni_correction([0.001, 0.02, 0.04, 0.06], alpha=0.05)
    # corrected_alpha = 0.0125, only first is significant
"""
from __future__ import annotations
from typing import Sequence


def bonferroni_correction(p_values: Sequence[float], alpha: float = 0.05) -> dict:
    """Simple Bonferroni: divide alpha by N."""
    n = len(p_values)
    if n == 0:
        raise ValueError("Empty p_values list")
    corrected_alpha = alpha / n
    significant = [p < corrected_alpha for p in p_values]
    return {
        "method": "bonferroni",
        "n_tests": n,
        "original_alpha": alpha,
        "corrected_alpha": corrected_alpha,
        "significant_count": sum(significant),
        "significant_mask": significant,
        "p_values": list(p_values),
    }


def holm_bonferroni(p_values: Sequence[float], alpha: float = 0.05) -> dict:
    """Holm-Bonferroni step-down: sort p-values, test against alpha/(n-rank).

    More powerful than basic Bonferroni when several true positives exist.
    """
    n = len(p_values)
    if n == 0:
        raise ValueError("Empty p_values list")
    indexed = sorted(enumerate(p_values), key=lambda x: x[1])
    significant = [False] * n
    for rank, (orig_idx, p) in enumerate(indexed):
        threshold = alpha / (n - rank)
        if p < threshold:
            significant[orig_idx] = True
        else:
            break  # stop at first non-significant
    return {
        "method": "holm-bonferroni",
        "n_tests": n,
        "original_alpha": alpha,
        "min_corrected_alpha": alpha / n,
        "max_corrected_alpha": alpha,
        "significant_count": sum(significant),
        "significant_mask": significant,
        "p_values": list(p_values),
    }


if __name__ == "__main__":
    p_vals = [0.001, 0.012, 0.025, 0.04, 0.06, 0.08, 0.12, 0.2]

    print("=== Bonferroni ===")
    r1 = bonferroni_correction(p_vals, alpha=0.05)
    print(f"  corrected_alpha = {r1['corrected_alpha']:.5f}")
    print(f"  significant: {r1['significant_count']}/{r1['n_tests']}")
    print(f"  mask: {r1['significant_mask']}")

    print("\n=== Holm-Bonferroni ===")
    r2 = holm_bonferroni(p_vals, alpha=0.05)
    print(f"  significant: {r2['significant_count']}/{r2['n_tests']}")
    print(f"  mask: {r2['significant_mask']}")
