"""Transcript adapters. Each adapter yields (project, session_id, messages) tuples
where messages is a list of (timestamp, text) human messages.

skilld is agent-agnostic: add an adapter per agent (Claude Code, Cursor, ...).
"""

from . import claude_code

ADAPTERS = {
    "claude-code": claude_code,
}


def get(name: str):
    if name not in ADAPTERS:
        raise SystemExit(
            f"Unknown agent '{name}'. Available: {', '.join(ADAPTERS)}"
        )
    return ADAPTERS[name]
