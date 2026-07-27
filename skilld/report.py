"""Generate a self-contained HTML review report of all candidates."""

import html
import time
from pathlib import Path

STATUS_LABEL = {"proposed": "proposed", "accepted": "accepted", "rejected": "rejected"}
STATUS_COLOR = {"proposed": "#ffc266", "accepted": "#41e0a0", "rejected": "#ff5d6c"}

CSS = """
:root{--bg:#0f1216;--panel:#171c22;--panel2:#1d242c;--border:#2a3340;--text:#e8edf2;
--muted:#8b97a5;--accent:#41e0a0;}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);color:var(--text);font-family:-apple-system,Segoe UI,Roboto,sans-serif;
line-height:1.55;padding:2rem 1rem 4rem}
.wrap{max-width:860px;margin:0 auto}
h1{font-size:1.5rem}h1 span{color:var(--accent)}
.sub{color:var(--muted);margin:.3rem 0 1.6rem;font-size:.9rem}
h2{font-size:.95rem;text-transform:uppercase;letter-spacing:.08em;color:var(--muted);
margin:2rem 0 .8rem;border-bottom:1px solid var(--border);padding-bottom:.35rem}
.card{background:var(--panel);border:1px solid var(--border);border-radius:12px;
margin-bottom:.8rem;overflow:hidden}
.head{padding:.9rem 1rem .5rem;display:flex;gap:.6rem;align-items:baseline;flex-wrap:wrap}
.badge{font-size:.68rem;font-weight:700;border-radius:6px;padding:.12rem .5rem;color:#0f1216}
.title{font-weight:650}
.meta{margin-left:auto;font-size:.75rem;color:var(--muted);white-space:nowrap}
.body{padding:0 1rem .8rem;color:var(--muted);font-size:.9rem}
details{border-top:1px solid var(--border);background:var(--panel2)}
summary{cursor:pointer;padding:.5rem 1rem;font-size:.8rem;color:var(--accent)}
.q{margin:.3rem 1rem .7rem;padding:.5rem .75rem;border-left:3px solid var(--accent);
background:rgba(65,224,160,.05);border-radius:0 8px 8px 0;font-size:.83rem}
.q .src{display:block;font-size:.7rem;color:var(--muted)}
"""


def generate(state: dict, out_file: Path) -> Path:
    cands = sorted(
        state["candidates"].values(),
        key=lambda c: (c["status"] != "proposed", -c.get("confidence", 1)),
    )
    n = {s: sum(1 for c in cands if c["status"] == s) for s in STATUS_LABEL}
    parts = [
        f"<!DOCTYPE html><html lang='en'><head><meta charset='utf-8'>"
        f"<meta name='viewport' content='width=device-width,initial-scale=1'>"
        f"<title>skilld report</title><style>{CSS}</style></head><body><div class='wrap'>",
        f"<h1><span>skilld</span> — distilled lesson candidates</h1>",
        f"<div class='sub'>{time.strftime('%Y-%m-%d %H:%M')} · "
        f"{n['proposed']} proposed · {n['accepted']} accepted · {n['rejected']} rejected · "
        f"review with <code>skilld review</code></div>",
    ]
    domains: dict[str, list[dict]] = {}
    for c in cands:
        domains.setdefault(c.get("domain", "general"), []).append(c)
    for domain, group in sorted(domains.items()):
        parts.append(f"<h2>{html.escape(domain)}</h2>")
        for c in group:
            color = STATUS_COLOR[c["status"]]
            stars = "★" * c.get("confidence", 1)
            parts.append(
                f"<div class='card'><div class='head'>"
                f"<span class='badge' style='background:{color}'>{STATUS_LABEL[c['status']]}</span>"
                f"<span class='title'>{html.escape(c.get('title', ''))}</span>"
                f"<span class='meta'>{c.get('type', 'rule')} · {stars} · "
                f"{len(c.get('evidence', []))} evidence</span></div>"
                f"<div class='body'>{html.escape(c['statement'])}</div>"
            )
            ev = c.get("evidence", [])
            if ev:
                parts.append(f"<details><summary>View evidence ({len(ev)})</summary>")
                for e in ev:
                    parts.append(
                        f"<div class='q'><span class='src'>{html.escape(str(e.get('session', '?')))} · "
                        f"{html.escape(str(e.get('timestamp', '')))}</span>"
                        f"<em>\"{html.escape(str(e.get('quote', '')))}\"</em></div>"
                    )
                parts.append("</details>")
            parts.append("</div>")
    parts.append("</div></body></html>")
    out_file.write_text("".join(parts))
    return out_file
