"""Multi-tool sync: compile lessons once, load them in every agent.

Canonical source: ~/.skilld/state.json. Every target below is a compiled
representation — regenerating is always safe, nothing lives only in a target.

Shared files (AGENTS.md, copilot-instructions.md) are written between skilld
markers so anything the user wrote by hand is preserved.
"""

import time
from pathlib import Path

from . import apply as apply_mod

MARK_START = "<!-- skilld:start · auto-generated; change via `skilld review`, not by editing here -->"
MARK_END = "<!-- skilld:end -->"

CODEX_DIR = Path.home() / ".codex"


# ---------------------------------------------------------------- content

def _grouped(accepted, domains=None):
    out = {}
    for c in accepted:
        d = c.get("domain", "general")
        if domains and d not in domains:
            continue
        out.setdefault(d, []).append(c)
    return dict(sorted(out.items()))


def _body(accepted, domains=None) -> str:
    """Tool-neutral markdown block of all lessons."""
    lines = [
        "# Personal standards (distilled by skilld)",
        "",
        "These are the user's learned preferences and workflows, distilled from",
        "their past AI-agent sessions. Apply them proactively, without being asked.",
        "",
    ]
    for domain, cands in _grouped(accepted, domains).items():
        lines.append(f"## {domain}")
        lines.append("")
        for c in sorted(cands, key=lambda c: -c.get("confidence", 1)):
            title = c.get("title", "Lesson")
            lines.append(f"- **{title}** — {c['statement']}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _write_marked(path: Path, block: str) -> Path:
    """Insert/replace the skilld block in a shared file, keeping user content."""
    stamped = f"{MARK_START}\n{block}\n{MARK_END}\n"
    if path.exists():
        text = path.read_text()
        if MARK_START in text and MARK_END in text:
            head, rest = text.split(MARK_START, 1)
            _, tail = rest.split(MARK_END, 1)
            text = head + stamped.rstrip("\n") + tail
        else:
            text = text.rstrip("\n") + "\n\n" + stamped
    else:
        text = stamped
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return path


# ---------------------------------------------------------------- global sync

def sync_claude(accepted) -> Path:
    out = Path.home() / ".claude" / "skills"
    apply_mod.apply(accepted, out)
    return out


def sync_codex(accepted) -> Path:
    """Codex reads global guidance from ~/.codex/AGENTS.md."""
    return _write_marked(CODEX_DIR / "AGENTS.md", _body(accepted))


def detect_targets() -> list[tuple[str, bool]]:
    return [
        ("claude-code", (Path.home() / ".claude").exists()),
        ("codex", CODEX_DIR.exists()),
    ]


def sync_all(accepted) -> list[tuple[str, Path]]:
    """Write every detected tool's format. Claude Code is always written."""
    written = [("claude-code", sync_claude(accepted))]
    if CODEX_DIR.exists():
        written.append(("codex", sync_codex(accepted)))
    return written


# ---------------------------------------------------------------- repo export

def export_agents(accepted, root: Path, domains=None) -> Path:
    """AGENTS.md at repo root — read by Codex, Cursor, Copilot, Zed and more."""
    return _write_marked(root / "AGENTS.md", _body(accepted, domains))


def export_copilot(accepted, root: Path, domains=None) -> Path:
    return _write_marked(
        root / ".github" / "copilot-instructions.md", _body(accepted, domains)
    )


def export_cursor(accepted, root: Path, domains=None) -> Path:
    """Cursor project rules: one .mdc per domain under .cursor/rules/."""
    rules = root / ".cursor" / "rules"
    rules.mkdir(parents=True, exist_ok=True)
    for domain, cands in _grouped(accepted, domains).items():
        desc = apply_mod._description(domain, cands).replace("\n", " ")
        lines = [
            "---",
            f"description: {desc}",
            "alwaysApply: false",
            "---",
            "",
            f"# {domain} — user's distilled standards (skilld, {time.strftime('%Y-%m-%d')})",
            "",
        ]
        for c in sorted(cands, key=lambda c: -c.get("confidence", 1)):
            lines.append(f"- **{c.get('title', 'Lesson')}** — {c['statement']}")
        (rules / f"skilld-{domain}.mdc").write_text("\n".join(lines) + "\n")
    return rules


REPO_TARGETS = {
    "agents": export_agents,
    "cursor": export_cursor,
    "copilot": export_copilot,
}
