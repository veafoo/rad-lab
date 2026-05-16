"""Initialize research/index.sqlite from schema. Idempotent (CREATE IF NOT EXISTS)."""
import sqlite3
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DB = REPO / "research" / "index.sqlite"
SCHEMA = REPO / "scripts" / "init_schema.sql"

DB.parent.mkdir(parents=True, exist_ok=True)
with sqlite3.connect(DB) as conn:
    conn.executescript(SCHEMA.read_text())
print(f"Initialized: {DB}")

# Verify tables
with sqlite3.connect(DB) as conn:
    tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()]
print(f"Tables ({len(tables)}): {', '.join(tables)}")
