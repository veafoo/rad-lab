"""Decision pipeline - apply stats, optionally synthesize, push to inbox.

Workflow per family:
1. Load backtest_results
2. Bootstrap PF CI + DSR
3. Survivor criteria: PF>=PF_MIN AND CI_low>1.0 AND DSR>=DSR_MIN
4. If synthesizer given: run agent, push 1 brief to inbox
5. Else: push 1 inbox item per raw survivor (legacy mode)
"""
import json, sqlite3
from pathlib import Path
from core.stats.bootstrap import bootstrap_profit_factor
from core.stats.dsr import deflated_sharpe_ratio
from core.exploration.anti_overfit_audit import audit_batch

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
    if n_total == 0:
        return []
    survivors = []
    for r in results:
        raw = json.loads(r["raw_metrics_json"] or "{}")
        pnls = raw.get("pnls", [])
        if len(pnls) < 30:
            continue
        bs = bootstrap_profit_factor(pnls, n_iter=1000)
        dsr = deflated_sharpe_ratio(pnls, sr_trials_variance=0.5, n_trials=n_total)
        if (r["profit_factor"] >= pf_min and bs["ci_low"] > 1.0 and dsr["dsr"] >= dsr_min):
            survivors.append({
                "experiment_id": r["experiment_id"], "pf": r["profit_factor"],
                "pf_ci": [bs["ci_low"], bs["ci_high"]], "dsr": dsr["dsr"],
                "sharpe": r["sharpe_ratio"], "n_trades": r["n_trades"],
            })
    return survivors


def push_survivors_to_inbox_raw(family_id, survivors):
    """Legacy: 1 inbox row per survivor."""
    from core.orchestrator.memory.index_db import push_to_inbox
    for s in survivors:
        push_to_inbox(
            type_="survivor",
            title=f"Survivor: {s['experiment_id'][:60]}",
            description=(f"Family {family_id} - PF={s['pf']:.2f} "
                         f"CI=[{s['pf_ci'][0]:.2f},{s['pf_ci'][1]:.2f}] "
                         f"DSR={s['dsr']:.3f} SR={s['sharpe']:.2f} n={s['n_trades']}"),
            priority="high",
        )


def process_family(family_id, mission="unknown", synthesizer=None,
                   pf_min=PF_HARD_MIN, dsr_min=DSR_MIN):
    """Full pipeline for one family: assess -> (synthesize) -> inbox."""
    from core.orchestrator.memory.index_db import push_to_inbox
    raw_survivors = assess_family(family_id, pf_min=pf_min, dsr_min=dsr_min)
    if not raw_survivors:
        return {"family_id": family_id, "n_survivors": 0, "audit_summary": None, "brain_path": None}
    audit_result = audit_batch(raw_survivors)
    survivors = audit_result["audited"]
    audit_summary = audit_result["summary"]
    if synthesizer is not None:
        r = synthesizer.run({"survivors": survivors, "mission": mission})
        brief = r["output"] or ""
        push_to_inbox(
            type_="survivor_brief",
            title=f"{family_id}: {len(survivors)} survivors",
            description=(brief[:500] + (f"\n\n[brain] {r['brain_path']}" if r.get("brain_path") else "")),
            priority="high",
        )
        return {"family_id": family_id, "n_survivors": len(survivors), "audit_summary": audit_summary,
                "brain_path": r.get("brain_path"), "brief": brief}
    else:
        push_survivors_to_inbox_raw(family_id, survivors)
        return {"family_id": family_id, "n_survivors": len(survivors), "audit_summary": audit_summary, "brain_path": None}


if __name__ == "__main__":
    from core.exploration.grid_runner import queue_family
    from core.exploration.backtest_worker import run_worker
    from core.orchestrator.routers.mock import MockRouter
    from core.orchestrator.agents.result_synthesizer import ResultSynthesizer
    from core.orchestrator.memory.index_db import list_inbox_pending

    fam_file = REPO_ROOT / "families" / "initial" / "families.yaml"
    s = queue_family(fam_file)
    n = run_worker(limit=321, edge_per_family={"F001-volatility-regime": 0.10})
    print(f"Queued: {s['total_queued']}, processed: {n}")

    synth = ResultSynthesizer(MockRouter("MOCK BRIEF: top strategies validated."))
    print("\n--- Processing each family with synthesizer ---")
    for fam in s["families"]:
        result = process_family(fam["id"], mission="megakichta", synthesizer=synth)
        marker = "OK" if result["brain_path"] else "skip"
        print(f"  [{marker}] {fam['id']}: {result['n_survivors']} survivors")

    pending = list_inbox_pending()
    print(f"\nInbox pending: {len(pending)}")
    for p in pending[:5]:
        print(f"  [{p['priority']:8s}] {p['title']}")

    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM backtest_results WHERE experiment_id LIKE 'F00%'")
    conn.execute("DELETE FROM experiments WHERE id LIKE 'F00%'")
    conn.execute("DELETE FROM hypotheses WHERE id LIKE 'F00%'")
    conn.execute("DELETE FROM inbox WHERE type IN ('survivor', 'survivor_brief')")
    conn.commit(); conn.close()
    print("Cleanup OK")
