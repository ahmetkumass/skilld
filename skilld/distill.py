"""Turn a corpus of human messages into candidate lessons via LLM distillation."""

import json

from . import engine, signals

MAX_CHUNK_CHARS = 60_000

PROMPT = """You are the distillation engine of `skilld`, a tool that mines AI-agent
transcripts for durable lessons. Below are the HUMAN messages a user sent to a
coding agent across sessions in one project. Your job: extract candidate lessons
that would change the agent's behavior in FUTURE sessions.

## The one question every candidate must pass
"Would knowing this have changed the agent's behavior in a future session?"

## Filters
1. RECURRENCE — prefer patterns stated/corrected 2+ times. A one-off instruction
   is at most a low-confidence candidate.
2. GENERALIZABILITY — strip task-specific detail, keep the rule.
   "crop minutes 1-6" is task detail (discard); "always crop the video to the
   useful segment; the user supplies the range" is a rule (keep).
3. SIGNAL TYPE — weight: correction ("no, not like that") > frustration >
   repeated instruction > explicit preference > one-time fact.
   Messages are pre-tagged [CORRECTION]/[FRUSTRATION]/[PREFERENCE] by a heuristic;
   trust your own reading over the tags.
4. EXCLUSIONS — never emit: task output content itself; secrets/passwords/tokens;
   things any codebase already documents; expiring situational info ("interview
   is tomorrow"). IP addresses/hostnames of the user's OWN local devices are
   allowed (they are workflow context, not secrets).

## Candidate types
- "fact"   — stable context (product specs, team roles, ongoing processes)
- "rule"   — preference or standard ("no filler text", "always version files")
- "recipe" — reusable step-by-step workflow the user taught

## Output — STRICT JSON only, no prose around it:
{"candidates": [
  {"type": "rule",
   "domain": "<short-kebab-slug grouping related lessons, e.g. vision-machine, presentation-style>",
   "title": "<max 8 words>",
   "statement": "<the lesson, 1-3 sentences, written as an instruction to a future agent>",
   "confidence": 1|2|3,
   "evidence": [{"session": "<8-char session prefix>", "timestamp": "<ts>", "quote": "<short verbatim quote>"}]
  }]}

confidence: 3 = 3+ independent evidence items or strong correction pattern;
2 = 2 items or one clear correction; 1 = single occurrence, plausible.
Write `statement` and `title` in the user's own language (mirror the corpus language).
Aim for quality over quantity — a tight list of real lessons beats a long list of noise.
Use FEW, BROAD domains — at most 4 per corpus. Group related lessons under one
domain (e.g. all presentation/writing-style rules under one domain) instead of
inventing a micro-domain per lesson. A domain with a single lesson is a smell.

## Corpus
{CORPUS}
"""


def build_corpus(sessions: list[tuple[str, list[tuple[str, str]]]]) -> list[str]:
    """sessions: [(session_id, [(ts, text), ...])] -> chunked corpus strings."""
    lines = []
    for sid, msgs in sessions:
        short = sid[:8]
        for ts, text in msgs:
            lines.append(f"[{short}|{ts[:16]}] {signals.tag(text)}{text}")
    chunks, cur, size = [], [], 0
    for ln in lines:
        if size + len(ln) > MAX_CHUNK_CHARS and cur:
            chunks.append("\n".join(cur))
            cur, size = [], 0
        cur.append(ln)
        size += len(ln) + 1
    if cur:
        chunks.append("\n".join(cur))
    return chunks


def distill(sessions, project: str, log=print) -> list[dict]:
    """Run distillation over a project's sessions; return candidate dicts."""
    chunks = build_corpus(sessions)
    out = []
    for i, chunk in enumerate(chunks, 1):
        if len(chunks) > 1:
            log(f"    LLM call {i}/{len(chunks)} ({len(chunk)} chars)…")
        else:
            log(f"    LLM call ({len(chunk)} chars)…")
        raw = engine.complete(PROMPT.replace("{CORPUS}", chunk))
        try:
            data = engine.extract_json(raw)
        except (engine.EngineError, json.JSONDecodeError) as e:
            log(f"    ! parse failure, skipping chunk: {e}")
            continue
        for c in data.get("candidates", []):
            if not c.get("statement"):
                continue
            c.setdefault("type", "rule")
            c.setdefault("domain", project)
            c.setdefault("confidence", 1)
            c.setdefault("evidence", [])
            c["project"] = project
            out.append(c)
    return out
