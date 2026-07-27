# skilld

**Your agent's memory, with receipts.**

Every correction you've ever given your AI coding agent — *"we use vitest here"*, *"stop writing filler"*, *"never overwrite, version the file"* — is sitting in transcript files on your disk, forgotten. skilld mines those transcripts, shows you what you taught with your own words as proof, and makes every lesson permanent across all your tools.

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

## How it's different

Agent memory exists — but it's silent, siloed, and locked in. skilld is the opposite:

| | Claude Code auto-memory | SpecStory | rulesync & co. | **skilld** |
|---|:---:|:---:|:---:|:---:|
| Mines your existing history | – | partial | – | **yes** |
| Shows evidence, you approve | – | – | – | **yes** |
| Lessons cross projects | – | – | – | **yes** |
| Works across tools (Claude, Codex, Cursor...) | – | – | yes | **yes** |
| No account required | yes | – | yes | **yes** |

The one-line version: other tools either *silently* remember (you can't see, audit, or move what they learned) or make you *write rules by hand*. skilld turns what you already taught into rules you can read, prove, and carry anywhere.

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
