"""Mainnet gate — blocks mainnet actions unless fresh approval token exists.

Token format: .live-approved-by-rad-YYYY-MM-DD at rad-lab root.
Token must exist, dated today UTC, less than 24h old.
"""
from __future__ import annotations
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
TOKEN_PREFIX = ".live-approved-by-rad-"
MAX_AGE_HOURS = 24


def check_mainnet_approval() -> tuple[bool, str]:
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    token = REPO_ROOT / f"{TOKEN_PREFIX}{today}"

    if not token.exists():
        return False, f"no approval token ({token.name}) at {REPO_ROOT}"

    mtime = datetime.fromtimestamp(token.stat().st_mtime, tz=timezone.utc)
    age_hours = (datetime.now(timezone.utc) - mtime).total_seconds() / 3600

    if age_hours > MAX_AGE_HOURS:
        return False, f"approval expired ({age_hours:.1f}h old, max {MAX_AGE_HOURS}h)"

    return True, f"approval valid ({age_hours:.1f}h old)"


if __name__ == "__main__":
    ok, reason = check_mainnet_approval()
    print(f"[mainnet_gate] {'ALLOWED' if ok else 'BLOCKED'} - {reason}")
    sys.exit(0 if ok else 1)
