"""PLACEHOLDER backtest worker — generates synthetic PnL series.

NOT a real backtester. Validates the flow: experiments(queued)->results->done.
Phase B will replace with calls to Megakichta canonical or other engines.
Seed is derived from experiment id => reproducible.
"""
import hashlib, json, math, random, sqlite3
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = REPO_ROOT / "research" / "index.sqlite"

def now_iso(): return datetime.now(timezone.utc).isoformat()

def synthetic_pnls(exp_id, n=100, edge=0.0):
    seed = int(hashlib.sha256(exp_id.encode()).hexdigest()[:8], 16)
    rng = random.Random(seed)
    out = []
    for _ in range(n):
        win = rng.random() < (0.5 + edge)
        out.append(abs(rng.gauss(0, 1.0)) * (1.0 if win else -1.0))
    return out

def run_worker(limit=10, edge_per_family=None):
    edge_per_family = edge_per_family or {}
    conn = sqlite3.connect(DB_PATH); conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            "SELECT id, hypothesis_id FROM experiments WHERE status='queued' LIMIT ?", (limit,)
        ).fetchall()
        processed = 0
        for row in rows:
            exp_id, fam = row["id"], row["hypothesis_id"]
            edge = edge_per_family.get(fam, 0.0)
            pnls = synthetic_pnls(exp_id, 100, edge)
            wins, losses = [p for p in pnls if p > 0], [-p for p in pnls if p < 0]
            pf = sum(wins)/sum(losses) if losses else 999.0
            wr = len(wins)/len(pnls)
            mean = sum(pnls)/len(pnls)
            std = math.sqrt(sum((p-mean)**2 for p in pnls)/len(pnls)) if len(pnls)>1 else 0
            sharpe = mean/std if std > 0 else 0
            eq, peak, dd_max = 0, 0, 0
            for p in pnls:
                eq += p
                if eq > peak: peak = eq
                if peak - eq > dd_max: dd_max = peak - eq
            conn.execute(
                "INSERT OR REPLACE INTO backtest_results "
                "(id, experiment_id, ran_at, dataset_id, oos_used, profit_factor, win_rate, "
                " max_drawdown, sharpe_ratio, n_trades, raw_metrics_json) "
                "VALUES (?, ?, ?, ?, 0, ?, ?, ?, ?, ?, ?)",
                (f"res_{exp_id}", exp_id, now_iso(), "synthetic", pf, wr, dd_max, sharpe, len(pnls),
                 json.dumps({"pnls": pnls, "edge_used": edge}))
            )
            conn.execute("UPDATE experiments SET status='done' WHERE id=?", (exp_id,))
            processed += 1
        conn.commit()
        return processed
    finally:
        conn.close()

if __name__ == "__main__":
    from core.exploration.grid_runner import queue_family
    fam = REPO_ROOT / "families" / "initial" / "families.yaml"
    s = queue_family(fam)
    print(f"Queued: {s['total_queued']}")
    n = run_worker(limit=50, edge_per_family={"F001-volatility-regime": 0.05})
    print(f"Worker processed: {n}")
    conn = sqlite3.connect(DB_PATH); conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT experiment_id, profit_factor, win_rate FROM backtest_results LIMIT 5").fetchall()
    for r in rows:
        print(f"  {r['experiment_id'][:50]:50s} PF={r['profit_factor']:.2f} WR={r['win_rate']*100:.1f}%")
    conn.close()
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM backtest_results WHERE experiment_id LIKE 'F00%'")
    conn.execute("DELETE FROM experiments WHERE id LIKE 'F00%'")
    conn.execute("DELETE FROM hypotheses WHERE id LIKE 'F00%'")
    conn.commit(); conn.close()
    print("Cleanup OK")
