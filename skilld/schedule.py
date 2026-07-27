"""Background automation: nightly scan + macOS notification.

Design principle: scanning is automatic, approval stays human.
Notification etiquette: only nudge when >= NOTIFY_MIN candidates are pending,
and only when the count changed since the last nudge (no nagging).
"""

import os
import plistlib
import shutil
import subprocess
import sys
from pathlib import Path

from . import store

LABEL = "dev.skilld.scan"
PLIST = Path.home() / "Library" / "LaunchAgents" / f"{LABEL}.plist"
LOG = store.STATE_DIR / "cron.log"
NOTIFY_MIN = 3


def install(hour: int = 21):
    """Register a nightly `skilld cron` run via launchd (macOS)."""
    if sys.platform != "darwin":
        raise SystemExit("Scheduling is macOS-only for now (launchd). Linux cron support is planned.")
    store.STATE_DIR.mkdir(exist_ok=True)
    # launchd jobs get a minimal PATH (/usr/bin:/bin); the engine shells out to
    # the `claude` CLI, so bake the install-time PATH into the job environment.
    path = os.environ.get("PATH", "")
    claude = shutil.which("claude")
    if claude and str(Path(claude).parent) not in path.split(":"):
        path = f"{Path(claude).parent}:{path}"
    plist = {
        "Label": LABEL,
        "ProgramArguments": [sys.executable, "-m", "skilld", "cron"],
        "StartCalendarInterval": {"Hour": hour, "Minute": 0},
        "StandardOutPath": str(LOG),
        "StandardErrorPath": str(LOG),
        "EnvironmentVariables": {"PATH": path},
    }
    PLIST.parent.mkdir(parents=True, exist_ok=True)
    PLIST.write_bytes(plistlib.dumps(plist))
    subprocess.run(["launchctl", "unload", str(PLIST)], capture_output=True)
    subprocess.run(["launchctl", "load", str(PLIST)], check=True, capture_output=True)
    return PLIST, hour


def remove():
    subprocess.run(["launchctl", "unload", str(PLIST)], capture_output=True)
    if PLIST.exists():
        PLIST.unlink()


def status() -> str:
    if not PLIST.exists():
        return "not installed"
    r = subprocess.run(["launchctl", "list", LABEL], capture_output=True, text=True)
    return f"installed ({PLIST}), launchd: {'active' if r.returncode == 0 else 'not loaded'}"


def notify(title: str, message: str):
    if sys.platform == "darwin":
        subprocess.run(
            ["osascript", "-e",
             f'display notification "{message}" with title "{title}"'],
            capture_output=True,
        )


def maybe_notify(state: dict):
    """Nudge only when it's worth the user's attention."""
    pending = len(store.by_status(state, "proposed"))
    last = state.get("last_notified_pending", 0)
    if pending >= NOTIFY_MIN and pending != last:
        notify(
            "skilld",
            f"You taught your agent {pending} new things. Make them permanent: skilld review",
        )
        state["last_notified_pending"] = pending
        return True
    return False


def baseline(adapter):
    """Mark all existing sessions as scanned WITHOUT distilling them.

    Use when you want automation to start 'from today' instead of paying for
    a full history scan on the first nightly run.
    """
    state = store.load()
    n = 0
    for pdir in adapter.list_projects():
        for sf in adapter.list_sessions(pdir):
            store.mark_scanned(state, sf, sf.stat().st_mtime)
            n += 1
    store.save(state)
    return n
