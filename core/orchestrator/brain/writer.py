"""Obsidian-compatible markdown vault writer."""
import yaml
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

REPO_ROOT = Path(__file__).resolve().parents[3]
BRAIN_ROOT = REPO_ROOT / "brain"


def _slugify(title, maxlen=80):
    out = "".join(c if c.isalnum() or c in "-_" else "_" for c in title)
    return out[:maxlen].strip("_") or "untitled"


def write_note(category, title, body, frontmatter=None, subdir_date=True, tags=None):
    fm = dict(frontmatter or {})
    now = datetime.now(timezone.utc)
    fm.setdefault("created", now.isoformat())
    fm.setdefault("category", category)
    if tags:
        fm["tags"] = sorted(set(fm.get("tags", []) + tags))
    else:
        fm.setdefault("tags", [])
    dir_path = BRAIN_ROOT / category
    if subdir_date:
        dir_path = dir_path / now.strftime("%Y-%m-%d")
    dir_path.mkdir(parents=True, exist_ok=True)
    fname = f"{now.strftime('%H%M%S')}_{_slugify(title)}.md"
    file_path = dir_path / fname
    content = "---\n" + yaml.dump(fm, allow_unicode=True, sort_keys=False) + "---\n\n"
    content += f"# {title}\n\n" + body
    file_path.write_text(content, encoding="utf-8")
    return file_path


def append_to_index(file_path, summary=""):
    idx = BRAIN_ROOT / "00-index.md"
    BRAIN_ROOT.mkdir(parents=True, exist_ok=True)
    if not idx.exists():
        idx.write_text("# Brain Index\n\nAll notes written by rad-lab.\n\n## Recent\n\n", encoding="utf-8")
    rel = file_path.relative_to(BRAIN_ROOT).with_suffix("").as_posix()
    line = f"- [[{rel}]] - {summary}\n" if summary else f"- [[{rel}]]\n"
    with idx.open("a", encoding="utf-8") as f:
        f.write(line)


def list_notes(category, limit=20):
    base = BRAIN_ROOT / category
    if not base.exists():
        return []
    files = sorted(base.rglob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True)
    return files[:limit]
