import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

"""Run a full E2E pipeline keeping all traces (for dashboard demo).

WARNING: Pollutes DB. Reset: python scripts/init_db.py (after manually dropping the file).
"""
from core.exploration.grid_runner import queue_family
from core.exploration.backtest_worker import run_worker
from core.exploration.decision_pipeline import process_family
from core.orchestrator.routers.mock import MockRouter
from core.orchestrator.agents.result_synthesizer import ResultSynthesizer
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
fam_file = REPO / "families" / "initial" / "families.yaml"

print("=== Demo run (leaves traces in DB) ===")
s = queue_family(fam_file)
n = run_worker(limit=321, edge_per_family={"F001-volatility-regime": 0.10})
print(f"Queued: {s['total_queued']}, processed: {n}")

synth = ResultSynthesizer(MockRouter("MOCK BRIEF: top strategies validated."))
for fam in s["families"]:
    r = process_family(fam["id"], mission="megakichta", synthesizer=synth)
    print(f"  {fam['id']}: {r['n_survivors']} survivors")

print("\nDemo data left. Reset via: rm research/index.sqlite && python scripts/init_db.py")
