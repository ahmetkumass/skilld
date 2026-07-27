"""skilld CLI: scan -> review -> sync, plus repo exports and scheduling."""

import argparse
import sys
from pathlib import Path

from . import __version__, adapters, apply as apply_mod, distill, report, signals, store


def cmd_scan(args):
    adapter = adapters.get(args.agent)
    state = store.load()
    if not args.project and not getattr(args, "all", False):
        print("Pick a scope: skilld scan --project <substring>  (or --all)")
        projects = list(adapter.list_projects())
        print(f"\nAvailable projects ({len(projects)}):")
        for p in projects:
            print(f"  {p.name}")
        sys.exit(1)

    total_new = total_upd = 0
    for pdir in adapter.list_projects(args.project):
        sessions = []
        for sf in adapter.list_sessions(pdir):
            mtime = sf.stat().st_mtime
            if not args.force and not store.needs_scan(state, sf, mtime):
                continue
            msgs = list(adapter.human_messages(sf))
            if msgs:
                sessions.append((sf.stem, msgs))
            store.mark_scanned(state, sf, mtime)
        if not sessions:
            continue
        all_msgs = [m for _, msgs in sessions for m in msgs]
        label = adapter.project_label(pdir)
        print(f"» {pdir.name}: {len(sessions)} new session(s), {len(all_msgs)} messages")
        if not signals.worth_distilling(all_msgs):
            print("    low signal, skipped (no LLM call)")
            continue
        cands = distill.distill(sessions, project=label)
        new, upd = store.add_candidates(state, cands)
        total_new += new
        total_upd += upd
        print(f"    {len(cands)} candidates -> {new} new, {upd} updated")

    store.save(state)
    pending = len(store.by_status(state, "proposed"))
    print(f"\nScan complete: {total_new} new candidates, {total_upd} updated.")
    if pending:
        print(f"{pending} candidates awaiting review -> `skilld review`")


def cmd_status(args):
    state = store.load()
    for status in ("proposed", "accepted", "rejected"):
        cands = store.by_status(state, status)
        if not cands:
            continue
        print(f"\n{status.upper()} ({len(cands)})")
        for c in cands:
            stars = "*" * c.get("confidence", 1)
            print(
                f"  [{c['id']}] {stars:3s} {c.get('domain', '?')}/{c.get('type', '?')} — "
                f"{c.get('title', '')}"
            )
    if not state["candidates"]:
        print("No candidates yet. Start with: skilld scan --project <name>")


def cmd_review(args):
    state = store.load()
    pending = store.by_status(state, "proposed")
    if not pending:
        print("Nothing to review.")
        return
    if not getattr(args, "tty", False):
        from . import webreview

        acc, rej = webreview.serve(state)
        print(f"\n{acc} accepted, {rej} rejected.")
        if acc:
            _auto_sync(state)
        return
    print(f"{len(pending)} candidates. [a]ccept  [r]eject  [e]dit  [s]kip  [q]uit\n")
    for i, c in enumerate(pending, 1):
        stars = "*" * c.get("confidence", 1)
        print(f"--- {i}/{len(pending)} · {c.get('domain')}/{c.get('type')} · {stars}")
        print(f"    {c.get('title', '')}")
        print(f"    {c['statement']}")
        for e in c.get("evidence", [])[:3]:
            print(f"      > {e.get('session', '?')}: \"{e.get('quote', '')[:90]}\"")
        try:
            choice = input("    > ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\nPaused; progress saved.")
            break
        if choice == "a":
            c["status"] = "accepted"
        elif choice == "r":
            c["status"] = "rejected"
        elif choice == "e":
            new = input("    new text: ").strip()
            if new:
                c["statement"] = new
                c["status"] = "accepted"
        elif choice == "q":
            break
        store.save(state)
    store.save(state)
    _auto_sync(state)


def _auto_sync(state):
    """Review approval IS the approval — sync accepted lessons to every tool."""
    accepted = store.by_status(state, "accepted")
    if not accepted:
        return
    from . import export

    written = export.sync_all(accepted)
    print(f"{len(accepted)} lessons synced:")
    for name, path in written:
        print(f"  {name:12s} -> {path}")
    print("Your agents will know these from their next session on.")


def cmd_apply(args):
    state = store.load()
    accepted = store.by_status(state, "accepted")
    if not accepted:
        print("No accepted lessons. Run: skilld review")
        return
    written = apply_mod.apply(accepted, Path(args.out))
    for p in written:
        print(f"  wrote: {p}")
    print(f"\n{len(accepted)} lessons written to {len(written)} files.")


def cmd_sync(args):
    """Re-compile all accepted lessons into every detected tool's format."""
    from . import export

    state = store.load()
    accepted = store.by_status(state, "accepted")
    if not accepted:
        print("No accepted lessons yet. Run: skilld scan, then skilld review")
        return
    written = export.sync_all(accepted)
    print(f"{len(accepted)} lessons synced:")
    for name, path in written:
        print(f"  {name:12s} -> {path}")
    detected = ", ".join(n for n, ok in export.detect_targets() if ok)
    print(f"Detected tools: {detected}")
    print("Per-repo targets: skilld export agents|cursor|copilot --dir <repo>")


def cmd_export(args):
    """Write lessons into a specific repo in another tool's format."""
    from . import export

    state = store.load()
    accepted = store.by_status(state, "accepted")
    if not accepted:
        print("No accepted lessons yet. Run: skilld scan, then skilld review")
        return
    domains = set(args.domain) if args.domain else None
    if domains:
        known = {c.get("domain") for c in accepted}
        missing = domains - known
        if missing:
            print(f"Unknown domain(s): {', '.join(sorted(missing))}")
            print(f"Available: {', '.join(sorted(d for d in known if d))}")
            return
    fn = export.REPO_TARGETS[args.target]
    path = fn(accepted, Path(args.dir).resolve(), domains)
    scope = f" (domains: {', '.join(sorted(domains))})" if domains else ""
    print(f"Wrote -> {path}{scope}")


def cmd_cron(args):
    """Nightly job: incremental scan of everything + polite notification."""
    import argparse as _ap
    import time

    print(f"--- skilld cron {time.strftime('%Y-%m-%d %H:%M')}")
    scan_args = _ap.Namespace(agent="claude-code", project=None, all=True, force=False)
    try:
        cmd_scan(scan_args)
    except SystemExit:
        pass
    from . import schedule

    state = store.load()
    if schedule.maybe_notify(state):
        store.save(state)
        print("notification sent")


def cmd_schedule(args):
    from . import schedule

    if args.action == "install":
        plist, hour = schedule.install(args.hour)
        print(f"Installed: `skilld cron` will run nightly at {hour:02d}:00.")
        print(f"  plist: {plist}\n  log:   {schedule.LOG}")
        print("You'll get a notification when new lesson candidates pile up (threshold: 3).")
    elif args.action == "remove":
        schedule.remove()
        print("Schedule removed.")
    else:
        print(f"Status: {schedule.status()}")


def cmd_baseline(args):
    from . import schedule

    adapter = adapters.get(args.agent)
    n = schedule.baseline(adapter)
    print(f"Marked {n} existing sessions as scanned.")
    print("Future scans will only process NEW sessions (history skipped).")


def cmd_report(args):
    state = store.load()
    if not state["candidates"]:
        print("No candidates yet. Start with: skilld scan --project <name>")
        return
    out = report.generate(state, Path(args.out))
    print(f"Report: {out}")


def main(argv=None):
    p = argparse.ArgumentParser(
        prog="skilld",
        description="Distill reusable skills from your AI agent transcripts.",
    )
    p.add_argument("--version", action="version", version=f"skilld {__version__}")
    sub = p.add_subparsers(dest="cmd", required=True)

    ps = sub.add_parser("scan", help="scan transcripts, propose lesson candidates")
    ps.add_argument("--agent", default="claude-code", help="transcript source (default: claude-code)")
    ps.add_argument("--project", help="only projects whose name contains this substring")
    ps.add_argument("--all", action="store_true", help="scan every project")
    ps.add_argument("--force", action="store_true", help="rescan already-scanned sessions")
    ps.set_defaults(func=cmd_scan)

    st = sub.add_parser("status", help="list candidates by status")
    st.set_defaults(func=cmd_status)

    rv = sub.add_parser("review", help="review candidates in the browser (or --tty for terminal)")
    rv.add_argument("--tty", action="store_true", help="plain terminal flow instead of the browser")
    rv.set_defaults(func=cmd_review)

    ap = sub.add_parser("apply", help="write accepted lessons to SKILL.md files")
    ap.add_argument(
        "--out",
        default=str(Path.home() / ".claude" / "skills"),
        help="output directory (default: ~/.claude/skills)",
    )
    ap.set_defaults(func=cmd_apply)

    rp = sub.add_parser("report", help="generate an HTML report of all candidates")
    rp.add_argument("--out", default="./skilld-report.html")
    rp.set_defaults(func=cmd_report)

    sy = sub.add_parser("sync", help="re-compile lessons into every detected tool (Claude Code, Codex, ...)")
    sy.set_defaults(func=cmd_sync)

    ex = sub.add_parser("export", help="write lessons into a repo for another tool")
    ex.add_argument("target", choices=["agents", "cursor", "copilot"],
                    help="agents=AGENTS.md (Codex/Cursor/Zed), cursor=.cursor/rules, copilot=.github")
    ex.add_argument("--dir", default=".", help="repo root (default: current directory)")
    ex.add_argument("--domain", action="append",
                    help="only these domains (repeatable); default: all")
    ex.set_defaults(func=cmd_export)

    cr = sub.add_parser("cron", help="(internal) incremental scan + notification; run by the scheduler")
    cr.set_defaults(func=cmd_cron)

    sc = sub.add_parser("schedule", help="manage the nightly automatic scan")
    sc.add_argument("action", choices=["install", "remove", "status"])
    sc.add_argument("--hour", type=int, default=21, help="hour of the nightly run (default 21)")
    sc.set_defaults(func=cmd_schedule)

    bl = sub.add_parser("baseline", help="mark existing history as scanned; automation starts from today")
    bl.add_argument("--agent", default="claude-code")
    bl.set_defaults(func=cmd_baseline)

    args = p.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
