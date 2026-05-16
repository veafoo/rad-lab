"""Grid runner — reads family YAML, generates parameter grid, queues experiments.

Planning layer ONLY. Does NOT run backtests.
Pushes 1 row per (family, params) combo into experiments table (status='queued').
A Phase B worker will consume the queue and run the actual backtests.
"""
from __future__ import annotations
import hashlib
import itertools
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = REPO_ROOT / "research" / "index.sqlite"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_schema():
    conn = sqlite3.connect(DB_PATH)
    try:
        cols = [r[1] for r in conn.execute("PRAGMA table_info(experiments)").fetchall()]
        if "params_json" not in cols:
            conn.execute("ALTER TABLE experiments ADD COLUMN params_json TEXT")
            conn.commit()
    finally:
        conn.close()


def generate_grid(family: dict) -> Iterator[dict]:
    variables = family.get("variables", {})
    if not variables:
        return
    keys = list(variables.keys())
    value_lists = [
        variables[k] if isinstance(variables[k], list) else [variables[k]]
        for k in keys
    ]
    for combo in itertools.product(*value_lists):
        yield dict(zip(keys, combo))


def config_hash(family_id: str, params: dict) -> str:
    payload = json.dumps({"family": family_id, "params": params}, sort_keys=True)
    return hashlib.sha256(payload.encode()).hexdigest()[:16]


def upsert_hypothesis_from_family(family: dict) -> None:
    conn = sqlite3.connect(DB_PATH)
    try:
        existing = conn.execute(
            "SELECT 1 FROM hypotheses WHERE id = ?", (family["id"],)
        ).fetchone()
        if existing:
            return
        cols = ("id", "mission", "title", "h0", "h1", "predictions", "metric_primary",
                "status", "priority_score", "created_at", "updated_at", "rationale", "md_path")
        mission = family.get("mission", "megakichta")
        title = family.get("name", family["id"])
        h0 = family.get("h0", "")
        h1 = family.get("h1", "")
        predictions = family.get("hypothesis", "")
        metric = family.get("metric_primary", "profit_factor")
        rationale = family.get("theory", "")
        conn.execute(
            f"INSERT INTO hypotheses ({', '.join(cols)}) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (family["id"], mission, title, h0, h1, predictions, metric,
             "backlog", None, now_iso(), now_iso(), rationale, None),
        )
        conn.commit()
    finally:
        conn.close()


def push_experiment(family: dict, params: dict) -> str:
    family_id = family["id"]
    cfg_hash = config_hash(family_id, params)
    exp_id = f"{family_id}__{cfg_hash}"
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute(
            "INSERT OR REPLACE INTO experiments "
            "(id, hypothesis_id, plan_md_path, in_sample_period, validation_period, oos_period, "
            " stat_test, stopping_criteria, created_at, status, params_json) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'queued', ?)",
            (
                exp_id, family_id, None,
                family.get("period_in_sample"),
                family.get("period_validation"),
                family.get("period_oos_reserved"),
                "bootstrap+bonferroni+psr+dsr",
                None, now_iso(),
                json.dumps(params),
            ),
        )
        conn.commit()
    finally:
        conn.close()
    return exp_id


def queue_family(family_yaml_path: Path) -> dict:
    ensure_schema()
    with Path(family_yaml_path).open() as f:
        data = yaml.safe_load(f)
    summary = {"file": str(family_yaml_path), "families": []}
    for family in data.get("families", []):
        upsert_hypothesis_from_family(family)
        combos = list(generate_grid(family))
        for params in combos:
            push_experiment(family, params)
        summary["families"].append({
            "id": family["id"],
            "name": family.get("name"),
            "variants_queued": len(combos),
        })
    summary["total_queued"] = sum(f["variants_queued"] for f in summary["families"])
    return summary


def list_queued(limit: int = 10) -> list[dict]:
    ensure_schema()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            "SELECT id, hypothesis_id, params_json, status, created_at "
            "FROM experiments WHERE status = 'queued' "
            "ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
    finally:
        conn.close()
    return [dict(r) for r in rows]


def stats_summary() -> dict:
    ensure_schema()
    conn = sqlite3.connect(DB_PATH)
    try:
        rows = conn.execute(
            "SELECT status, COUNT(*) FROM experiments GROUP BY status"
        ).fetchall()
    finally:
        conn.close()
    return {status: count for status, count in rows}


if __name__ == "__main__":
    fam_file = REPO_ROOT / "families" / "initial" / "families.yaml"
    print("=== Smoke test grid_runner ===")
    summary = queue_family(fam_file)
    print(f"Family file: {summary['file']}")
    print(f"Total queued: {summary['total_queued']}")
    for f in summary["families"]:
        print(f"  {f['id']}: {f['variants_queued']} variants - {f['name']}")
    print("Global stats by status:")
    for status, count in stats_summary().items():
        print(f"  {status}: {count}")
    print("Sample queued (5 first):")
    for exp in list_queued(limit=5):
        params_preview = (exp["params_json"] or "")[:70]
        print(f"  {exp['id']}")
        print(f"    {params_preview}...")
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM experiments WHERE id LIKE 'F00%'")
    conn.execute("DELETE FROM hypotheses WHERE id LIKE 'F00%'")
    conn.commit()
    conn.close()
    print("Cleanup done.")
    print("OK")
