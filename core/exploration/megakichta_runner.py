"""Real backtest wrapper for Megakichta canonical.

Chains run_meta_choose_v10_2.py -> replay_meta_pnl.py via subprocess.
Returns parsed metrics. For now accepts native meta_choose params only.
Family-specific params mapping (F001, F002, ...) = TODO next session.
"""
import json
import subprocess
import tempfile
from pathlib import Path

CANONICAL = Path.home() / "HQ" / "PROJECTS" / "Megakichta" / "Megakichta"
FEATURES_DIR = Path.home() / "HQ" / "PROJECTS" / "Megakichta" / "grid_search" / "features"
META_SCRIPT = CANONICAL / "scripts" / "run_meta_choose_v10_2.py"
REPLAY_SCRIPT = CANONICAL / "scripts" / "replay_meta_pnl.py"


def run_real_backtest(coin, params=None, capital=10000, timeout=180):
    """Returns {success, summary, error, coin, params}."""
    params = params or {}
    price_csv = FEATURES_DIR / f"{coin}_2h_fvg.csv"
    if not price_csv.exists():
        return {"success": False, "error": f"Features missing: {price_csv}", "coin": coin}

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        trace_dir = tmpdir / "trace"
        replay_dir = tmpdir / "replay"
        trace_dir.mkdir()
        replay_dir.mkdir()

        # Step 1: meta_choose
        meta_args = ["python", str(META_SCRIPT), "--input", str(price_csv), "--out", str(trace_dir)]
        for k, v in params.items():
            flag = "--" + k.replace("_", "-")
            if isinstance(v, bool):
                meta_args.append(flag if v else f"--no-{k.replace('_', '-')}")
            else:
                meta_args.extend([flag, str(v)])
        r1 = subprocess.run(meta_args, capture_output=True, text=True, timeout=timeout)
        if r1.returncode != 0:
            return {"success": False, "error": f"meta_choose: {r1.stderr[:300]}", "coin": coin}

        trace_csv = trace_dir / "meta_choose_trace.csv"
        if not trace_csv.exists():
            return {"success": False, "error": "trace not produced", "coin": coin}

        # Step 2: replay
        replay_args = ["python", str(REPLAY_SCRIPT),
                       "--price-csv", str(price_csv),
                       "--trace-csv", str(trace_csv),
                       "--out", str(replay_dir)]
        r2 = subprocess.run(replay_args, capture_output=True, text=True, timeout=timeout)
        if r2.returncode != 0:
            return {"success": False, "error": f"replay: {r2.stderr[:300]}", "coin": coin}

        summary_file = replay_dir / "replay_summary.json"
        if not summary_file.exists():
            return {"success": False, "error": "summary not produced", "coin": coin}

        summary = json.loads(summary_file.read_text())
        return {"success": True, "summary": summary, "coin": coin, "params": params}


if __name__ == "__main__":
    import time
    print("=== Real backtest BTCUSDT with defaults locked ===")
    t0 = time.time()
    r = run_real_backtest("BTCUSDT", params={})
    elapsed = time.time() - t0
    if r["success"]:
        s = r["summary"]
        print(f"OK in {elapsed:.1f}s")
        print(f"  n_trades:    {s.get('n_trades', '?')}")
        print(f"  PF:          {s.get('profit_factor', s.get('PF', '?'))}")
        print(f"  Win rate:    {s.get('win_rate', '?')}")
        print(f"  Max DD:      {s.get('max_drawdown', s.get('max_dd', '?'))}")
        print(f"  Total ret:   {s.get('total_return', s.get('return_total', '?'))}")
        print(f"  Sharpe:      {s.get('sharpe', s.get('sharpe_ratio', '?'))}")
        print(f"\nAll keys in summary: {list(s.keys())[:15]}")
    else:
        print(f"FAILED in {elapsed:.1f}s")
        print(f"  Error: {r['error']}")
