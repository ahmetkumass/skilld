"""Adapter for Claude Code transcripts (~/.claude/projects/*/*.jsonl)."""

import json
from pathlib import Path

ROOT = Path.home() / ".claude" / "projects"

# Message prefixes that are meta/noise, not human teaching signal.
_SKIP_PREFIXES = (
    "Caveat:",
    "[Request interrupted",
    "[Image:",
    "Base directory for this skill:",
    "<",
)

MAX_MSG_CHARS = 900  # long pastes (docs, logs) are truncated; the head carries the intent


def encode_path(path) -> str:
    """Claude Code's directory encoding: every non-alphanumeric char becomes '-'.

    /Users/x/my_app -> -Users-x-my-app
    """
    import re

    return re.sub(r"[^A-Za-z0-9]", "-", str(path))


def list_projects(name_filter: str | None = None):
    """Yield project directories, optionally filtered by substring."""
    if not ROOT.exists():
        return
    for d in sorted(ROOT.iterdir()):
        if not d.is_dir():
            continue
        if name_filter and name_filter not in d.name:
            continue
        yield d


def list_sessions(project_dir: Path):
    """Yield session .jsonl files in a project."""
    yield from sorted(project_dir.glob("*.jsonl"))


def human_messages(session_file: Path):
    """Yield (timestamp, text) for real human messages in a session.

    Skips tool results, meta messages, image placeholders, and skill dumps.
    """
    try:
        lines = session_file.read_text(errors="replace").splitlines()
    except OSError:
        return
    for line in lines:
        try:
            d = json.loads(line)
        except (json.JSONDecodeError, ValueError):
            continue
        if d.get("type") != "user":
            continue
        msg = d.get("message") or {}
        content = msg.get("content")
        if isinstance(content, list):
            texts = [
                b.get("text", "")
                for b in content
                if isinstance(b, dict) and b.get("type") == "text"
            ]
            content = " ".join(texts)
        if not isinstance(content, str):
            continue
        content = content.strip()
        if not content or content.startswith(_SKIP_PREFIXES):
            continue
        if len(content) > MAX_MSG_CHARS:
            content = content[:MAX_MSG_CHARS] + " …[truncated paste]"
        yield d.get("timestamp") or "", content


def project_label(project_dir: Path) -> str:
    """Human-friendly project name from the encoded directory name."""
    return project_dir.name.split("-")[-1] if project_dir.name else project_dir.name
