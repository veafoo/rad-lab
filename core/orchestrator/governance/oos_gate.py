"""OOS Reserve gate — enforce that no exploration reads OOS-reserved data (R4).

The last 12 months are FROZEN. Only the final verdict phase can touch them.
Any function reading price data must validate via this gate.
"""
from __future__ import annotations
from datetime import datetime, timezone
from pathlib import Path
import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]
FAMILIES_DIR = REPO_ROOT / "families"

# Default OOS reserve (overridable per family)
OOS_START_DEFAULT = "2025-05-01"
OOS_END_DEFAULT = "2026-05-01"


def parse_date(d) -> datetime:
    if isinstance(d, datetime):
        return d.replace(tzinfo=timezone.utc) if d.tzinfo is None else d
    if isinstance(d, str):
        for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%SZ"):
            try:
                dt = datetime.strptime(d, fmt)
                return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt
            except ValueError:
                continue
    raise ValueError(f"Cannot parse date: {d}")


def check_oos_overlap(
    date_start, date_end,
    oos_start: str = OOS_START_DEFAULT,
    oos_end: str = OOS_END_DEFAULT,
) -> tuple[bool, str]:
    """Returns (allowed, reason). True if date range does NOT overlap OOS reserve."""
    ds = parse_date(date_start)
    de = parse_date(date_end)
    os_s = parse_date(oos_start)
    os_e = parse_date(oos_end)
    overlaps = not (de <= os_s or ds >= os_e)
    if overlaps:
        return False, f"range [{date_start}->{date_end}] overlaps OOS [{oos_start}->{oos_end}]"
    return True, f"range [{date_start}->{date_end}] OK (no OOS touch)"


def parse_period_string(s: str) -> tuple[str, str] | None:
    """Parse 'YYYY-MM-DD to YYYY-MM-DD'."""
    if not s or "to" not in s:
        return None
    parts = s.split(" to ")
    if len(parts) != 2:
        return None
    return parts[0].strip(), parts[1].strip()


def check_family_compliance(family: dict) -> tuple[bool, list[str]]:
    """Verify IS and validation periods don't touch OOS reserve."""
    issues = []
    is_p = parse_period_string(family.get("period_in_sample", ""))
    val_p = parse_period_string(family.get("period_validation", ""))
    oos_p = parse_period_string(family.get("period_oos_reserved", "")) or (
        OOS_START_DEFAULT, OOS_END_DEFAULT
    )

    if is_p:
        ok, reason = check_oos_overlap(is_p[0], is_p[1], oos_p[0], oos_p[1])
        if not ok:
            issues.append(f"IS: {reason}")
    if val_p:
        ok, reason = check_oos_overlap(val_p[0], val_p[1], oos_p[0], oos_p[1])
        if not ok:
            issues.append(f"validation: {reason}")
    return len(issues) == 0, issues


if __name__ == "__main__":
    print("=== Smoke test oos_gate ===\n")

    cases = [
        ("2020-01-01", "2024-01-01", "IS strict (OK attendu)"),
        ("2024-01-01", "2025-12-01", "validation qui depasse (BLOCKED)"),
        ("2025-08-01", "2025-10-01", "milieu OOS (BLOCKED)"),
        ("2026-06-01", "2027-01-01", "post-OOS (OK)"),
    ]
    for ds, de, label in cases:
        ok, reason = check_oos_overlap(ds, de)
        status = "OK" if ok else "BLOCKED"
        print(f"  {label:35s} -> {status} - {reason}")

    fam_file = FAMILIES_DIR / "initial" / "families.yaml"
    if fam_file.exists():
        print("\n=== Check des 5 familles initiales ===")
        with fam_file.open() as f:
            data = yaml.safe_load(f)
        for fam in data.get("families", []):
            ok, issues = check_family_compliance(fam)
            status = "OK" if ok else "VIOLATION"
            print(f"  {fam['id']}: {status}")
            for issue in issues:
                print(f"    - {issue}")
