"""Persistent state: candidates + their review status + scanned-session ledger.

Lives in ~/.skilld/state.json. Candidates are keyed by a hash of the normalized
statement so re-scans merge evidence into existing candidates instead of
duplicating them — this is the seed of semantic versioning: new evidence for a
known lesson raises its confidence rather than creating a twin.
"""

import hashlib
import json
import time
from pathlib import Path

STATE_DIR = Path.home() / ".skilld"
STATE_FILE = STATE_DIR / "state.json"


def load() -> dict:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {"candidates": {}, "scanned": {}}


def save(state: dict):
    STATE_DIR.mkdir(exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2))


def cand_id(statement: str) -> str:
    norm = " ".join(statement.lower().split())
    return hashlib.sha1(norm.encode()).hexdigest()[:12]


def add_candidates(state: dict, cands: list[dict]) -> tuple[int, int]:
    """Merge new candidates in. Returns (new, updated)."""
    new = updated = 0
    for c in cands:
        cid = cand_id(c["statement"])
        existing = state["candidates"].get(cid)
        if existing:
            known = {(e.get("timestamp"), e.get("quote")) for e in existing["evidence"]}
            grew = False
            for e in c.get("evidence", []):
                key = (e.get("timestamp"), e.get("quote"))
                if key not in known:
                    existing["evidence"].append(e)
                    known.add(key)
                    grew = True
            if grew:
                existing["confidence"] = max(
                    existing.get("confidence", 1), c.get("confidence", 1)
                )
                existing["updated"] = _today()
                # New evidence on a rejected candidate re-opens the question.
                if existing["status"] == "rejected":
                    existing["status"] = "proposed"
                updated += 1
        else:
            c["id"] = cid
            c["status"] = "proposed"
            c["created"] = _today()
            state["candidates"][cid] = c
            new += 1
    return new, updated


def mark_scanned(state: dict, session_file, mtime: float):
    state["scanned"][str(session_file)] = mtime


def needs_scan(state: dict, session_file, mtime: float) -> bool:
    return state["scanned"].get(str(session_file)) != mtime


def by_status(state: dict, status: str) -> list[dict]:
    return sorted(
        (c for c in state["candidates"].values() if c["status"] == status),
        key=lambda c: (-c.get("confidence", 1), c.get("domain", "")),
    )


def _today() -> str:
    return time.strftime("%Y-%m-%d")
