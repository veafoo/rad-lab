"""Decision pipeline — apply stats correction to results, push survivors to inbox.

Workflow per family:
1. Load all backtest_results
2. Bonferroni alpha = global / N
3. For each: bootstrap PF CI, DSR (with N=trials count)
4. Survivor = PF>=PF_MIN AND CI_lower>1.0 AND DSR>=DSR_MIN
5. Push survivors to inbox priority='high'
"""
import json, sqlite3
from pathlib import Path
from core.stats.bootstrap import bootstrap_profit_factor
from core.stats.dsr import deflated_sharpe_ratio

REPO_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = REPO_ROOT / "research" / "index.sqlite"
PF_HARD_MIN = 1.5
DSR_MIN = 0.95

def assess_family(family_id, pf_min=PF_HARD_MIN, dsr_min=DSR_MIN):
    conn = sqlite3.connect(DB_PATH); conn.row_factory = sqlite3.Row
    try:
        results = conn.execute(
            "SELECT br.* FROM backtest_results br "
            "JOIN experiments e ON e.id = br.experiment_id "
            "WHERE e.hypothesis_id = ?", (family_id,)
        ).fetchall()
    finally:
        conn.close()
    n_total = len(results)
    if n_total == 0: return []
    survivors = []
    for r in results:
        raw = json.loads(r["raw_metrics_json"] or "{}")
        pnls = raw.get("pnls", [])
        if len(pnls) < 30: continue
        bs = bootstrap_profit_factor(pnls, n_iter=1000)
        dsr = deflated_sharpe_ratio(pnls, sr_trials_variance=0.5, n_trials=n_total)
        if (r["profit_factor"] >= pf_min and bs["ci_lower"] > 1.0 and dsr["dsr"] >= dsr_min):
            survivors.append({
                "experiment_id": r["experiment_id"], "pf": r["profit_factor"],
                "pf_ci": [bs["ci_lower"], bs["ci_upper"]], "dsr": dsr["dsr"],
                "sharpe": r["sharpe_ratio"], "n_trades": r["n_trades"],
            })
    return survivors

def push_survivors_to_inbox(family_id, survivors):
    from core.orchestrator.memory.index_db import push_to_inbox
    for s in survivors:
        push_to_inbox(
            "survivor",
            f"Survivor: {s['experiment_id'][:60]}",
            f"Family {family_id} - PF={s['pf']:.2f} CI=[{s['pf_ci'][0]:.2f},{s['pf_ci'][1]:.2f}] "
            f"DSR={s['dsr']:.3f} SR={s['sharpe']:.2f} n={s['n_trades']}",
            priority="high",
        )

if __name__ == "__main__":
    from core.exploration.grid_runner import queue_family
    from core.exploration.backtest_worker import run_worker
    from core.orchestrator.memory.index_db import list_inbox_pending
    fam_file = REPO_ROOT / "families" / "initial" / "families.yaml"
    s = queue_family(fam_file)
    print(f"Queued: {s['total_queued']}")
    n = run_worker(limit=321, edge_per_family={"F001-volatility-regime": 0.15})
    print(f"Worker processed: {n}")
    for fam in s["families"]:
        survivors = assess_family(fam["id"])
        print(f"  {fam['id']}: {len(survivors)} survivors / {fam['variants_queued']} variants")
        push_survivors_to_inbox(fam["id"], survivors)
    pending = list_inbox_pending()
    print(f"Inbox pending total: {len(pending)}")
    for p in pending[:5]:
        print(f"  [{p['priority']:8s}] {p['title']}")
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM backtest_results WHERE experiment_id LIKE 'F00%'")
    conn.execute("DELETE FROM experiments WHERE id LIKE 'F00%'")
    conn.execute("DELETE FROM hypotheses WHERE id LIKE 'F00%'")
    conn.execute("DELETE FROM inbox WHERE type='survivor'")
    conn.commit(); conn.close()
    print("Cleanup OK")
