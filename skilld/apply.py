"""Write accepted candidates out as SKILL.md files, grouped by domain."""

import time
from pathlib import Path

TYPE_HEADINGS = {
    "fact": "Context",
    "rule": "Rules",
    "recipe": "Recipes",
}
STARS = {1: "★", 2: "★★", 3: "★★★"}


def apply(accepted: list[dict], out_dir: Path) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    written = []
    domains: dict[str, list[dict]] = {}
    for c in accepted:
        domains.setdefault(c.get("domain", "general"), []).append(c)

    for domain, cands in sorted(domains.items()):
        ddir = out_dir / domain
        ddir.mkdir(exist_ok=True)
        written.append(_write_skill(ddir / "SKILL.md", domain, cands))
        written.append(_write_evidence(ddir / "EVIDENCE.md", domain, cands))
    return written


def _description(domain: str, cands: list[dict]) -> str:
    """Trigger-quality description: tells the agent WHEN to load this skill.

    Claude Code only reads this line at session start; the full SKILL.md loads
    when the description matches the task. Modeled on well-authored skills:
    what it is, when to trigger, and how to treat it (personal standards,
    applied proactively).
    """
    ordered = sorted(cands, key=lambda c: -c.get("confidence", 1))
    topics = "; ".join(t for t in (c.get("title", "") for c in ordered[:5]) if t)
    n_recipes = sum(1 for c in cands if c.get("type") == "recipe")
    recipe_note = " Includes step-by-step workflows the user taught." if n_recipes else ""
    return (
        f"The user's personal standards and workflows for {domain}, distilled from "
        f"their past agent sessions. Trigger whenever the current task touches any of: "
        f"{topics}.{recipe_note} These are learned preferences — apply them proactively "
        f"and silently, without being asked and without mentioning this skill."
    )


def _write_skill(path: Path, domain: str, cands: list[dict]) -> Path:
    lines = [
        "---",
        f"name: {domain}",
        f"description: {_description(domain, cands)}",
        f"generated_by: skilld on {time.strftime('%Y-%m-%d')}",
        "---",
        "",
        f"# {domain} — distilled personal standards",
        "",
        "These rules were learned from the user's past sessions. Apply them",
        "proactively without mentioning this skill; if the user says otherwise,",
        "the user wins. Every rule's provenance is in EVIDENCE.md.",
        "",
    ]
    for tkey, heading in TYPE_HEADINGS.items():
        group = [c for c in cands if c.get("type") == tkey]
        if not group:
            continue
        lines.append(f"## {heading}")
        lines.append("")
        if tkey == "recipe":
            # Recipes are workflows — give each its own section so steps read
            # as a procedure, not a bullet in a list.
            for c in sorted(group, key=lambda c: -c.get("confidence", 1)):
                stars = STARS.get(c.get("confidence", 1), "★")
                lines.append(f"### {c.get('title', 'Workflow')} ({stars})")
                lines.append("")
                lines.append(c["statement"])
                lines.append("")
        else:
            for c in sorted(group, key=lambda c: -c.get("confidence", 1)):
                stars = STARS.get(c.get("confidence", 1), "★")
                lines.append(
                    f"- **{c.get('title', 'Lesson')}** ({stars}) — {c['statement']}"
                )
            lines.append("")
    path.write_text("\n".join(lines))
    return path


def _write_evidence(path: Path, domain: str, cands: list[dict]) -> Path:
    lines = [f"# Evidence — {domain}", ""]
    for c in cands:
        lines.append(f"## {c.get('title', 'Lesson')} (`{c['id']}`)")
        lines.append(f"> {c['statement']}")
        lines.append("")
        for e in c.get("evidence", []):
            lines.append(
                f"- `{e.get('session', '?')}` {e.get('timestamp', '')} — \"{e.get('quote', '')}\""
            )
        lines.append("")
    path.write_text("\n".join(lines))
    return path
