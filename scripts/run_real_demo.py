"""Real backtest demo - small grid on 2 coins with varying params.

Demonstrates the integration potential of megakichta_runner.
Next step: wire this into backtest_worker.run_worker(use_real=True).
"""
import sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.exploration.megakichta_runner import run_real_backtest

COINS = ["BTCUSDT", "ETHUSDT"]
PARAM_GRID = [
    {},
    {"min_score": 0.70},
    {"cooldown_bars": 4, "min_score": 0.70},
]

results = []
t0 = time.time()
for coin in COINS:
    for params in PARAM_GRID:
        r = run_real_backtest(coin, params=params)
        if r["success"]:
            s = r["summary"]
            results.append({
                "coin": coin, "params": str(params) or "defaults",
                "n": s.get("n_trades", 0), "pf": s.get("profit_factor", 0),
                "wr": s.get("win_rate", 0), "dd": s.get("max_drawdown", 0),
                "ret": s.get("total_return", 0),
            })
        else:
            print(f"FAILED {coin} {params}: {r['error']}")

elapsed = time.time() - t0
print(f"\n=== Real Grid Demo ({elapsed:.1f}s, {len(results)} backtests) ===\n")
print(f"{'Coin':10s} {'Params':38s} {'N':>5} {'PF':>5} {'WR':>6} {'DD':>6} {'Ret%':>8}")
print("-" * 82)
for r in results:
    print(f"{r['coin']:10s} {r['params'][:38]:38s} {r['n']:>5} "
          f"{r['pf']:>5.2f} {r['wr']*100:>5.1f}% {r['dd']*100:>5.1f}% {r['ret']*100:>8.0f}")
