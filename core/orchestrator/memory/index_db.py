"""Wrapper for research/index.sqlite — typed helper methods for agents and hub.

Agents shouldn't write raw SQL. They call typed methods, this module handles
schema details and transaction management.

Read-mostly, occasional writes. Connection is per-call (SQLite is fast).
"""
from __future__ import annotations
import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Iterator

REPO_ROOT = Path(__file__).resolve().parents[3]
DB_PATH = REPO_ROOT / "research" / "index.sqlite"


@contextmanager
def get_conn() -> Iterator[sqlite3.Connection]:
    """Context manager for SQLite connection with Row factory."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ===== Hypotheses =====

def list_hypotheses(
    mission: Optional[str] = None, status: Optional[str] = None
) -> list[dict]:
    query = "SELECT * FROM hypotheses WHERE 1=1"
    params: list = []
    if mission:
        query += " AND mission = ?"
        params.append(mission)
    if status:
        query += " AND status = ?"
        params.append(status)
    query += " ORDER BY created_at DESC"
    with get_conn() as conn:
        rows = conn.execute(query, params).fetchall()
    return [dict(r) for r in rows]


def get_hypothesis(hyp_id: str) -> Optional[dict]:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM hypotheses WHERE id = ?", (hyp_id,)).fetchone()
    return dict(row) if row else None


def upsert_hypothesis(h: dict) -> None:
    """Insert or replace a hypothesis. Must contain id, mission, title, h0, h1, status."""
    required = ["id", "mission", "title", "h0", "h1", "status"]
    for k in required:
        if k not in h:
            raise ValueError(f"Hypothesis missing required field: {k}")
    cols = [
        "id", "mission", "title", "h0", "h1", "predictions", "metric_primary",
        "status", "priority_score", "created_at", "updated_at", "rationale", "md_path",
    ]
    if "created_at" not in h:
        h["created_at"] = now_iso()
    h["updated_at"] = now_iso()
    placeholders = ", ".join(["?"] * len(cols))
    values = [h.get(c) for c in cols]
    with get_conn() as conn:
        conn.execute(
            f"INSERT OR REPLACE INTO hypotheses ({', '.join(cols)}) VALUES ({placeholders})",
            values,
        )


def update_hypothesis_status(hyp_id: str, status: str) -> None:
    with get_conn() as conn:
        conn.execute(
            "UPDATE hypotheses SET status = ?, updated_at = ? WHERE id = ?",
            (status, now_iso(), hyp_id),
        )


# ===== Inbox (decisions Rad must take) =====

def push_to_inbox(
    type_: str,
    title: str,
    description: str = "",
    priority: str = "normal",
    action_url: Optional[str] = None,
) -> int:
    """Add an item for Rad to review."""
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO inbox (created_at, type, title, description, action_url, status, priority) "
            "VALUES (?, ?, ?, ?, ?, 'pending', ?)",
            (now_iso(), type_, title, description, action_url, priority),
        )
        return cur.lastrowid


def list_inbox_pending() -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM inbox WHERE status = 'pending' "
            "ORDER BY CASE priority "
            "  WHEN 'critical' THEN 0 "
            "  WHEN 'high' THEN 1 "
            "  WHEN 'normal' THEN 2 "
            "  WHEN 'low' THEN 3 END, created_at ASC"
        ).fetchall()
    return [dict(r) for r in rows]


def decide_inbox(inbox_id: int, decision: str, decided_by: str = "rad") -> None:
    """decision in 'approved', 'rejected', 'deferred', 'expired'."""
    valid = ("approved", "rejected", "deferred", "expired")
    if decision not in valid:
        raise ValueError(f"decision must be one of {valid}, got {decision}")
    with get_conn() as conn:
        conn.execute(
            "UPDATE inbox SET status = ?, decided_at = ?, decided_by = ? WHERE id = ?",
            (decision, now_iso(), decided_by, inbox_id),
        )


# ===== Observations (sensing output) =====

def push_observation(
    source: str,
    severity: str,
    title: str,
    description: str = "",
    mission: Optional[str] = None,
    raw_data: Optional[dict] = None,
    md_path: Optional[str] = None,
) -> int:
    if severity not in ("info", "warning", "critical"):
        raise ValueError(f"severity must be info/warning/critical, got {severity}")
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO observations (timestamp, source, mission, severity, title, description, raw_data_json, md_path) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                now_iso(), source, mission, severity, title, description,
                json.dumps(raw_data) if raw_data else None, md_path,
            ),
        )
        return cur.lastrowid


def list_observations_recent(days: int = 7, severity_min: Optional[str] = None) -> list[dict]:
    order = {"info": 0, "warning": 1, "critical": 2}
    query = "SELECT * FROM observations WHERE timestamp >= datetime('now', ?) "
    params: list = [f"-{days} days"]
    if severity_min:
        if severity_min not in order:
            raise ValueError(f"severity_min must be info/warning/critical")
        levels = ["info", "warning", "critical"][order[severity_min]:]
        placeholders = ",".join(["?"] * len(levels))
        query += f"AND severity IN ({placeholders}) "
        params.extend(levels)
    query += "ORDER BY timestamp DESC"
    with get_conn() as conn:
        rows = conn.execute(query, params).fetchall()
    return [dict(r) for r in rows]


# ===== Agent metrics =====

def log_agent_invocation(
    agent_id: str,
    duration_ms: int,
    tokens_input: int,
    tokens_output: int,
    router: str,
    success: bool,
    error: Optional[str] = None,
) -> None:
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO agent_metrics (agent_id, invoked_at, duration_ms, tokens_input, tokens_output, router_used, success, error_message) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (agent_id, now_iso(), duration_ms, tokens_input, tokens_output, router, success, error),
        )


def agent_stats(agent_id: str, days: int = 30) -> dict:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT COUNT(*) as n, "
            "AVG(duration_ms) as avg_ms, "
            "SUM(tokens_input) as in_tot, "
            "SUM(tokens_output) as out_tot, "
            "AVG(CAST(success AS REAL)) as success_rate "
            "FROM agent_metrics WHERE agent_id = ? AND invoked_at >= datetime('now', ?)",
            (agent_id, f"-{days} days"),
        ).fetchone()
    return dict(row) if row else {"n": 0}


if __name__ == "__main__":
    # Smoke test : roundtrip on each table
    print("=== Smoke test index_db ===\n")

    # Hypothesis
    upsert_hypothesis({
        "id": "TEST-001",
        "mission": "megakichta",
        "title": "Test hypothesis",
        "h0": "no edge",
        "h1": "edge exists",
        "status": "backlog",
    })
    h = get_hypothesis("TEST-001")
    print(f"  hypothesis roundtrip: id={h['id']}, status={h['status']}")

    # Inbox
    iid = push_to_inbox("test", "Test inbox item", "delete me", priority="low")
    pending = list_inbox_pending()
    print(f"  inbox pending: {len(pending)} (last id={iid})")
    decide_inbox(iid, "rejected")
    pending_after = list_inbox_pending()
    print(f"  after reject: {len(pending_after)}")

    # Observations
    push_observation("smoke_test", "info", "test obs", "delete me", mission="megakichta")
    obs = list_observations_recent(days=1)
    print(f"  observations 1d: {len(obs)}")

    # Agent metrics
    log_agent_invocation("test-agent", 123, 100, 50, "ollama", True)
    s = agent_stats("test-agent", days=1)
    print(f"  agent stats: n={s['n']}")

    # Cleanup
    with get_conn() as c:
        c.execute("DELETE FROM hypotheses WHERE id = 'TEST-001'")
        c.execute("DELETE FROM inbox WHERE type = 'test'")
        c.execute("DELETE FROM observations WHERE source = 'smoke_test'")
        c.execute("DELETE FROM agent_metrics WHERE agent_id = 'test-agent'")
    print("\n  cleanup done")
    print("OK")
