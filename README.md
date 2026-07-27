# skilld

**Memory tools help your agent remember. skilld makes it learn.**

I found out I had told my coding agent *"stop writing filler"* six separate times — the proof was sitting in my own transcripts. Every correction you give your agent is recorded on your disk and then forgotten. skilld mines those transcripts, shows you each lesson with your own words as evidence, and — once you approve — makes it permanent across all your tools.

Free. MIT. Local-first. No account, no cloud, no telemetry.

> **Early release** — tested on macOS with Claude Code. More adapters and platforms on the way.

## Quick start

```bash
git clone https://github.com/ahmetkumass/skilld.git
cd skilld && pip install .   # PyPI release coming
skilld scan --all            # mine your transcript history
skilld review                # approve lessons in your browser (a / r keys)
```

That's it. Approved lessons are written to every tool skilld detects. Your next session starts already knowing them.

**Or use it as a Claude Code plugin** — inside Claude Code:

```
/plugin marketplace add ahmetkumass/skilld
/plugin install skilld@skilld
/reload-plugins
```

This gives you `/skilld:scan`, `/skilld:review` and `/skilld:status` right inside Claude Code, plus an optional session-end hook that scans quietly after every session — no scheduler needed. (The plugin drives the CLI, so install it once with `pip install skilld`.)

## How it's different

**Memory tools help your agent remember. skilld makes it learn.**

Tools like claude-mem and Claude Code's built-in auto-memory record *what happened* and inject summaries back as context. Useful — but your agent's behavior doesn't change, and notes keep piling up. skilld closes a learning loop instead: your corrections become a small set of approved skill files that change *how* the agent works. Notes accumulate; skills compound.

| | claude-mem | auto-memory (built-in) | SpecStory | rulesync & co. | **skilld** |
|---|---|---|---|---|---|
| Core job | remember sessions | notes Claude keeps for itself | save chats, derive Cursor rules | sync rules you write by hand | **learn your preferences** |
| Output | context injected each session | memory files per project | `.cursor/rules` file | converted rule files | **skill files that change behavior** |
| Mines your existing history | – | – | only its own saved chats | – | **yes, all of it** |
| Evidence + your approval before saving | – | – | – | you author them | **yes — your own quotes** |
| Lessons cross projects | per project | per project | per repo | manual | **yes, by domain** |
| Compiles to multiple tools (skills, AGENTS.md, Cursor, Copilot) | – | – | Cursor only | yes | **yes** |
| Local-first, no account | yes | yes | – | yes | **yes** |

To be fair: if you want your agent to recall *what you were doing last session*, use a memory tool — they're good at that. If you want it to *stop making the same mistakes*, that's skilld. They compose fine; different jobs.

## How it works

```
transcripts ──> scan ──> lesson candidates ──> you review ──> synced everywhere
              (local)    (with your quotes      (one key         Claude Code · Codex
                          as evidence)           per lesson)     AGENTS.md · Cursor
```

1. **Scan** — reads agent transcripts on your machine, finds teaching moments: corrections, repeated instructions, workflows you explained. Uses your existing Claude Code login for distillation; nothing leaves your machine otherwise.
2. **Review** — a clean browser UI shows each candidate lesson with verbatim quotes from your own sessions. Accept, reject, or skip. Nothing is ever saved without your approval.
3. **Sync** — approved lessons compile to every format automatically: Claude Code skills, Codex `AGENTS.md`, Cursor rules, Copilot instructions. One source of truth, every agent speaks it.

## Commands

```bash
skilld scan --all              # mine all projects (or --project <name>)
skilld review                  # approve/reject in browser; auto-syncs after
skilld sync                    # re-compile lessons to all detected tools
skilld export agents --dir .   # drop an AGENTS.md into a repo (Codex/Cursor/Zed/...)
skilld export cursor --dir .   # .cursor/rules/*.mdc
skilld schedule install        # nightly auto-scan + notification (macOS)
skilld report                  # HTML overview of everything learned
```

Scans are incremental — new sessions merge fresh evidence into existing lessons instead of duplicating them. Set-and-forget: `skilld schedule install` scans nightly and notifies you only when enough new lessons pile up.

## What a lesson looks like

Every lesson ships with its provenance:

```markdown
- **Keep it short, no filler** — Every deliverable (slides, answers, copy)
  should be the shortest version that lands the message.
```

...and an `EVIDENCE.md` linking back to the exact sessions and quotes it was distilled from, so you can always audit *why* your agent believes something.

## Requirements

Python 3.10+ and either the [Claude Code](https://claude.com/claude-code) CLI (zero config) or an `ANTHROPIC_API_KEY` with `pip install anthropic`.

## License

MIT — free, forever, for everyone.
