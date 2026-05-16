"""Budget gate — token usage hard cap enforcement (R3).

Reads core/budgets/budget_cap.yaml for caps.
Reads research/index.sqlite budget_log for current usage.
Logs every API/router call with consumed tokens.

Pro plan + Ollama : currently no caps (caps are null/0).
When external API activated : caps in YAML drive enforcement.
"""
from __future__ import annotations
import sqlite3
import yaml
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

REPO_ROOT = Path(__file__).resolve().parents[3]
DB_PATH = REPO_ROOT / "research" / "index.sqlite"
CAP_PATH = REPO_ROOT / "core" / "budgets" / "budget_cap.yaml"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_caps() -> dict:
    if not CAP_PATH.exists():
        return {
            "daily_tokens": None,
            "monthly_tokens": None,
            "daily_cost_usd": 0.0,
            "monthly_cost_usd": 0.0,
        }
    with CAP_PATH.open() as f:
        return yaml.safe_load(f) or {}


def get_current_usage() -> dict:
    """Aggregate tokens and cost for current day and current month (UTC)."""
    if not DB_PATH.exists():
        return {"day_tokens": 0, "day_cost": 0.0, "month_tokens": 0, "month_cost": 0.0}

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    month = datetime.now(timezone.utc).strftime("%Y-%m")

    conn = sqlite3.connect(DB_PATH)
    try:
        row_day = conn.execute(
            "SELECT COALESCE(SUM(tokens_consumed), 0), COALESCE(SUM(cost_usd), 0) "
            "FROM budget_log WHERE date(timestamp) = ?",
            (today,),
        ).fetchone()
        row_month = conn.execute(
            "SELECT COALESCE(SUM(tokens_consumed), 0), COALESCE(SUM(cost_usd), 0) "
            "FROM budget_log WHERE strftime('%Y-%m', timestamp) = ?",
            (month,),
        ).fetchone()
    finally:
        conn.close()

    return {
        "day_tokens": int(row_day[0]),
        "day_cost": float(row_day[1] or 0),
        "month_tokens": int(row_month[0]),
        "month_cost": float(row_month[1] or 0),
    }


def check_budget(router: Optional[str] = None) -> tuple[bool, str]:
    """Returns (allowed, reason).

    Skip caps for local-free routers (claude_code_cli uses Pro quota, ollama is free).
    Apply caps only for anthropic_api router or globally.
    """
    if router in ("ollama", "claude_code_cli"):
        return True, f"router={router} not counted in caps"

    caps = load_caps()
    usage = get_current_usage()

    issues = []
    if caps.get("daily_tokens") is not None and usage["day_tokens"] >= caps["daily_tokens"]:
        issues.append(f"daily_tokens exceeded: {usage['day_tokens']}/{caps['daily_tokens']}")
    if caps.get("monthly_tokens") is not None and usage["month_tokens"] >= caps["monthly_tokens"]:
        issues.append(f"monthly_tokens exceeded: {usage['month_tokens']}/{caps['monthly_tokens']}")
    if caps.get("daily_cost_usd", 0) > 0 and usage["day_cost"] >= caps["daily_cost_usd"]:
        issues.append(f"daily_cost exceeded: ${usage['day_cost']:.2f}/${caps['daily_cost_usd']}")
    if caps.get("monthly_cost_usd", 0) > 0 and usage["month_cost"] >= caps["monthly_cost_usd"]:
        issues.append(f"monthly_cost exceeded: ${usage['month_cost']:.2f}/${caps['monthly_cost_usd']}")

    if issues:
        return False, "; ".join(issues)
    return True, (
        f"OK day={usage['day_tokens']}tk/{caps.get('daily_tokens', 'inf')} "
        f"month={usage['month_tokens']}tk/{caps.get('monthly_tokens', 'inf')}"
    )


def log_usage(
    agent_id: Optional[str],
    mission: Optional[str],
    tokens: int,
    router: str,
    cost_usd: float = 0.0,
) -> None:
    """Append a token consumption event to budget_log table."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    ts = now_iso()
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    month = datetime.now(timezone.utc).strftime("%Y-%m")

    conn = sqlite3.connect(DB_PATH)
    try:
        day_cum_before = conn.execute(
            "SELECT COALESCE(SUM(tokens_consumed), 0) FROM budget_log WHERE date(timestamp) = ?",
            (today,),
        ).fetchone()[0]
        month_cum_before = conn.execute(
            "SELECT COALESCE(SUM(tokens_consumed), 0) FROM budget_log WHERE strftime('%Y-%m', timestamp) = ?",
            (month,),
        ).fetchone()[0]

        conn.execute(
            "INSERT INTO budget_log (timestamp, agent_id, mission, tokens_consumed, router, cost_usd, cumulative_day_tokens, cumulative_month_tokens) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                ts, agent_id, mission, tokens, router, cost_usd,
                day_cum_before + tokens, month_cum_before + tokens,
            ),
        )
        conn.commit()
    finally:
        conn.close()


if __name__ == "__main__":
    print("=== Smoke test budget_gate ===\n")

    caps = load_caps()
    print(f"  caps loaded: daily_tokens={caps.get('daily_tokens')}, monthly_tokens={caps.get('monthly_tokens')}")

    usage = get_current_usage()
    print(f"  current usage: day={usage['day_tokens']} month={usage['month_tokens']}")

    allowed, reason = check_budget(router="ollama")
    print(f"  check ollama: allowed={allowed} - {reason}")

    allowed, reason = check_budget(router="claude_code_cli")
    print(f"  check claude_code_cli: allowed={allowed} - {reason}")

    allowed, reason = check_budget(router="anthropic_api")
    print(f"  check anthropic_api: allowed={allowed} - {reason}")

    # Test logging
    log_usage("test-agent", "megakichta", tokens=500, router="anthropic_api", cost_usd=0.005)
    usage_after = get_current_usage()
    print(f"\n  after log 500 tokens: day={usage_after['day_tokens']}")

    # Cleanup
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM budget_log WHERE agent_id = 'test-agent'")
    conn.commit()
    conn.close()
    print("\n  cleanup done")
    print("OK")
