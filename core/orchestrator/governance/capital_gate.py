"""Capital gate — detects mods to capital/risk files in paper-trading repo.

If any protected file is modified locally (staged/unstaged/untracked),
this gate returns BLOCKED. Caller must create a PR instead of direct merge.
"""
from __future__ import annotations
import subprocess
import sys
from pathlib import Path

PAPER_TRADING_PATH = Path.home() / "HQ/PROJECTS/Megakichta/megakichta-paper-trading-1"

PROTECTED_FILES = [
    "config/risk_params.yaml",
    "config/coins.yaml",
    "config/engine.yaml",
    "src/order_executor.py",
    "src/allocation.py",
    "src/binance_futures_client.py",
]


def get_modified_files(repo_path: Path = PAPER_TRADING_PATH) -> list[str]:
    if not repo_path.exists():
        return []
    result = subprocess.run(
        ["git", "-C", str(repo_path), "status", "--porcelain"],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        return []
    files = []
    for line in result.stdout.strip().split("\n"):
        if not line.strip():
            continue
        filename = line[3:].strip()
        files.append(filename)
    return files


def check_capital_modifications(repo_path: Path = PAPER_TRADING_PATH) -> tuple[bool, list[str]]:
    """Returns (any_protected_modified, list_of_protected_files_modified)."""
    modified = get_modified_files(repo_path)
    protected_modified = [f for f in modified if f in PROTECTED_FILES]
    return len(protected_modified) > 0, protected_modified


if __name__ == "__main__":
    has_protected, files = check_capital_modifications()
    if has_protected:
        print(f"[capital_gate] BLOCKED - protected files modified, PR required:")
        for f in files:
            print(f"  - {f}")
        sys.exit(1)
    print("[capital_gate] OK - no protected files modified")
    sys.exit(0)
