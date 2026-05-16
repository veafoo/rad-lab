"""Hard rules entry point — runs all gates, returns global status.

Usage:
    python -m core.orchestrator.governance.hard_rules
    python -m core.orchestrator.governance.hard_rules --check mainnet
    python -m core.orchestrator.governance.hard_rules --check capital
"""
from __future__ import annotations
import argparse
import sys

from .mainnet_gate import check_mainnet_approval
from .capital_gate import check_capital_modifications


def run_gate(name: str) -> tuple[bool, str]:
    if name == "mainnet":
        return check_mainnet_approval()
    elif name == "capital":
        has_protected, files = check_capital_modifications()
        if has_protected:
            return False, f"protected files modified: {', '.join(files)}"
        return True, "no protected files modified"
    return False, f"unknown gate: {name}"


def run_all_gates() -> tuple[bool, dict]:
    results = {}
    all_ok = True
    for name in ("mainnet", "capital"):
        ok, reason = run_gate(name)
        results[name] = {"ok": ok, "reason": reason}
        if not ok:
            all_ok = False
    return all_ok, results


def main():
    parser = argparse.ArgumentParser(description="Run safety gates")
    parser.add_argument("--check", default="all", choices=["all", "mainnet", "capital"])
    args = parser.parse_args()

    if args.check == "all":
        all_ok, results = run_all_gates()
        for name, r in results.items():
            status = "OK" if r["ok"] else "BLOCKED"
            print(f"[{name}] {status} - {r['reason']}")
        sys.exit(0 if all_ok else 1)

    ok, reason = run_gate(args.check)
    status = "OK" if ok else "BLOCKED"
    print(f"[{args.check}] {status} - {reason}")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
