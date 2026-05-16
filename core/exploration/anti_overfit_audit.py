"""Anti-overfit auditor - static heuristic checks for risk flags on survivors.

No LLM needed. Detects red flags:
- n_trades < 50 (sample too small)
- PF > 5 (suspicious), PF > 10 (critical)
- Sharpe > 4 (suspicious), > 6 (critical)
- Single trade dominates total wins (>30%)
- (future: streak concentration, period concentration, etc.)

Returns audit dict: {flags, risk_score 0-3, risk_level, recommendation}
"""
import json
import sqlite3
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = REPO_ROOT / "research" / "index.sqlite"

N_TRADES_MIN = 50
PF_SUSPICIOUS = 5.0
PF_CRITICAL = 10.0
SHARPE_SUSPICIOUS = 4.0
SHARPE_CRITICAL = 6.0
TRADE_DOMINANCE_PCT = 0.30


def audit_survivor(survivor):
    flags = []
    risk_score = 0
    exp_id = survivor.get("experiment_id", "")

    # Fetch raw pnls if available
    pnls = []
    try:
        conn = sqlite3.connect(DB_PATH)
        row = conn.execute(
            "SELECT raw_metrics_json FROM backtest_results WHERE experiment_id = ?",
            (exp_id,),
        ).fetchone()
        conn.close()
        if row and row[0]:
            pnls = json.loads(row[0]).get("pnls", [])
    except Exception:
        pass

    n = survivor.get("n_trades", len(pnls))
    pf = survivor.get("pf", 0)
    sharpe = survivor.get("sharpe", 0)

    if n < N_TRADES_MIN:
        flags.append(f"low_sample(n={n})")
        risk_score = max(risk_score, 2)
    if pf > PF_CRITICAL:
        flags.append(f"pf_critical({pf:.2f})")
        risk_score = max(risk_score, 3)
    elif pf > PF_SUSPICIOUS:
        flags.append(f"pf_suspicious({pf:.2f})")
        risk_score = max(risk_score, 2)
    if sharpe > SHARPE_CRITICAL:
        flags.append(f"sharpe_critical({sharpe:.2f})")
        risk_score = max(risk_score, 3)
    elif sharpe > SHARPE_SUSPICIOUS:
        flags.append(f"sharpe_suspicious({sharpe:.2f})")
        risk_score = max(risk_score, 2)
    if pnls:
        wins = [p for p in pnls if p > 0]
        total_win = sum(wins) if wins else 0
        if total_win > 0:
            max_w = max(wins)
            if max_w / total_win > TRADE_DOMINANCE_PCT:
                pct = max_w / total_win * 100
                flags.append(f"trade_dominance(max={pct:.0f}%)")
                risk_score = max(risk_score, 1)

    levels = ["low", "medium", "high", "critical"]
    risk_level = levels[min(risk_score, 3)]
    rec = "discard" if risk_score >= 3 else "hold" if risk_score >= 2 else "ship"

    return {"flags": flags, "risk_score": risk_score,
            "risk_level": risk_level, "recommendation": rec}


def audit_batch(survivors):
    audited = [{**s, "audit": audit_survivor(s)} for s in survivors]
    summary = {"ship": 0, "hold": 0, "discard": 0}
    for a in audited:
        summary[a["audit"]["recommendation"]] += 1
    return {"audited": audited, "summary": summary}


if __name__ == "__main__":
    print("=== Test heuristic audit ===")
    samples = [
        {"experiment_id": "t1", "pf": 2.5, "sharpe": 1.5, "n_trades": 100},
        {"experiment_id": "t2", "pf": 7.0, "sharpe": 1.5, "n_trades": 100},
        {"experiment_id": "t3", "pf": 2.5, "sharpe": 5.0, "n_trades": 30},
        {"experiment_id": "t4", "pf": 12.0, "sharpe": 6.5, "n_trades": 25},
        {"experiment_id": "t5", "pf": 3.0, "sharpe": 2.0, "n_trades": 200},
    ]
    batch = audit_batch(samples)
    for a in batch["audited"]:
        print(f"  {a['experiment_id']}: {a['audit']['recommendation']:8s} "
              f"({a['audit']['risk_level']:8s}) flags={a['audit']['flags']}")
    print(f"\nSummary: {batch['summary']}")
