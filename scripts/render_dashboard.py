"""Render static HTML dashboard from SQLite + brain.

Usage: python scripts/render_dashboard.py
Output: brain/dashboard.html
"""
import sqlite3
from datetime import datetime
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DB = REPO / "research" / "index.sqlite"
OUTPUT = REPO / "brain" / "dashboard.html"

CSS = """
body { font-family: -apple-system, system-ui, sans-serif; max-width: 1200px; margin: 2em auto; padding: 0 1em; color: #222; background: #fafafa; }
h1, h2 { color: #1a1a1a; border-bottom: 2px solid #ddd; padding-bottom: 0.3em; }
h2 { margin-top: 2em; }
.grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1em; margin: 1em 0; }
.card { background: white; padding: 1em; border-radius: 6px; box-shadow: 0 1px 3px rgba(0,0,0,0.08); }
.metric-big { font-size: 2.4em; font-weight: 700; line-height: 1; }
.metric-label { color: #666; font-size: 0.85em; text-transform: uppercase; letter-spacing: 0.05em; margin-top: 0.3em; }
table { width: 100%; border-collapse: collapse; background: white; margin: 1em 0; }
th, td { text-align: left; padding: 0.5em 0.8em; border-bottom: 1px solid #eee; font-size: 0.9em; }
th { background: #f0f0f0; font-weight: 600; }
tr:hover { background: #f8f8f8; }
.p-critical { color: #c0392b; font-weight: 700; }
.p-high { color: #d35400; font-weight: 600; }
.p-normal { color: #555; }
.p-low { color: #999; }
.timestamp { color: #999; font-size: 0.85em; }
.muted { color: #888; font-style: italic; }
code { background: #eef; padding: 1px 5px; border-radius: 3px; font-size: 0.88em; }
"""


def render():
    if not DB.exists():
        return "<h1>No DB. Run: python scripts/init_db.py</h1>"

    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    counts = {
        "hypotheses": c.execute("SELECT COUNT(*) FROM hypotheses").fetchone()[0],
        "exp_queued": c.execute("SELECT COUNT(*) FROM experiments WHERE status='queued'").fetchone()[0],
        "exp_done": c.execute("SELECT COUNT(*) FROM experiments WHERE status='done'").fetchone()[0],
        "inbox_pending": c.execute("SELECT COUNT(*) FROM inbox WHERE status='pending'").fetchone()[0],
        "backtest_results": c.execute("SELECT COUNT(*) FROM backtest_results").fetchone()[0],
        "agent_calls": c.execute("SELECT COUNT(*) FROM agent_metrics").fetchone()[0],
    }

    inbox = c.execute(
        "SELECT created_at, type, title, priority FROM inbox "
        "WHERE status='pending' ORDER BY created_at DESC LIMIT 20"
    ).fetchall()

    agents = c.execute(
        "SELECT agent_id, COUNT(*) as n, AVG(duration_ms) as avg_ms, "
        "SUM(tokens_input + tokens_output) as tot_tokens, "
        "AVG(CAST(success AS REAL)) as success_rate "
        "FROM agent_metrics WHERE invoked_at >= datetime('now', '-7 days') "
        "GROUP BY agent_id ORDER BY n DESC"
    ).fetchall()

    hypotheses = c.execute(
        "SELECT id, mission, title, status, updated_at FROM hypotheses "
        "ORDER BY updated_at DESC LIMIT 10"
    ).fetchall()

    conn.close()

    briefs_dir = REPO / "brain" / "briefs"
    recent_briefs = []
    if briefs_dir.exists():
        for f in sorted(briefs_dir.rglob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True)[:10]:
            recent_briefs.append({
                "path": f.relative_to(REPO).as_posix(),
                "mtime": datetime.fromtimestamp(f.stat().st_mtime).strftime("%Y-%m-%d %H:%M"),
            })

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    parts = [f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>rad-lab dashboard</title>
<style>{CSS}</style></head><body>
<h1>rad-lab dashboard</h1>
<p class="timestamp">Generated {now} - Refresh: <code>python scripts/render_dashboard.py</code></p>

<h2>Metrics</h2>
<div class="grid">
  <div class="card"><div class="metric-big">{counts['hypotheses']}</div><div class="metric-label">Hypotheses</div></div>
  <div class="card"><div class="metric-big">{counts['exp_queued']}</div><div class="metric-label">Queued</div></div>
  <div class="card"><div class="metric-big">{counts['exp_done']}</div><div class="metric-label">Done</div></div>
  <div class="card"><div class="metric-big">{counts['inbox_pending']}</div><div class="metric-label">Inbox pending</div></div>
  <div class="card"><div class="metric-big">{counts['backtest_results']}</div><div class="metric-label">Backtest results</div></div>
  <div class="card"><div class="metric-big">{counts['agent_calls']}</div><div class="metric-label">Agent calls</div></div>
</div>

<h2>Inbox pending</h2>
<table><tr><th>Created</th><th>Type</th><th>Priority</th><th>Title</th></tr>"""]

    for r in inbox:
        parts.append(f'<tr><td class="timestamp">{r["created_at"][:16]}</td><td>{r["type"]}</td>'
                     f'<td class="p-{r["priority"]}">{r["priority"]}</td><td>{r["title"]}</td></tr>')
    if not inbox:
        parts.append('<tr><td colspan="4" class="muted">No pending items</td></tr>')
    parts.append("</table>")

    parts.append("<h2>Agent metrics (last 7 days)</h2><table>")
    parts.append("<tr><th>Agent</th><th>Calls</th><th>Avg ms</th><th>Total tokens</th><th>Success</th></tr>")
    for r in agents:
        sr = (r['success_rate'] or 0) * 100
        avg_ms = int(r['avg_ms'] or 0)
        tot = r['tot_tokens'] or 0
        parts.append(f'<tr><td>{r["agent_id"]}</td><td>{r["n"]}</td><td>{avg_ms}</td>'
                     f'<td>{tot}</td><td>{sr:.0f}%</td></tr>')
    if not agents:
        parts.append('<tr><td colspan="5" class="muted">No agent metrics yet</td></tr>')
    parts.append("</table>")

    parts.append("<h2>Hypotheses</h2><table>")
    parts.append("<tr><th>ID</th><th>Mission</th><th>Title</th><th>Status</th><th>Updated</th></tr>")
    for r in hypotheses:
        title = (r['title'] or '')[:60]
        upd = (r['updated_at'] or '')[:16]
        parts.append(f'<tr><td><code>{r["id"]}</code></td><td>{r["mission"]}</td>'
                     f'<td>{title}</td><td>{r["status"]}</td>'
                     f'<td class="timestamp">{upd}</td></tr>')
    if not hypotheses:
        parts.append('<tr><td colspan="5" class="muted">No hypotheses yet</td></tr>')
    parts.append("</table>")

    parts.append("<h2>Brain - recent briefs</h2><ul>")
    for b in recent_briefs:
        parts.append(f'<li><span class="timestamp">{b["mtime"]}</span> <code>{b["path"]}</code></li>')
    if not recent_briefs:
        parts.append('<li class="muted">No briefs yet</li>')
    parts.append("</ul></body></html>")

    return "\n".join(parts)


if __name__ == "__main__":
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(render(), encoding="utf-8")
    print(f"Written: {OUTPUT}")
    print(f"Open: file://{OUTPUT}")
