---
description: Scan this project's transcripts for lesson candidates (pass "all" for full history)
---

Run the skilld scanner.

1. First check the CLI is available: run `command -v skilld` with the Bash tool.
   If it is missing, tell the user to install it with `pip install skilld`
   (or `uvx skilld` for a no-install run) and stop.
2. Decide the scope:
   - Default: scan only the current project — run `skilld scan --here`.
   - If the user asked for everything (passed "all" or said so), run
     `skilld scan --all` instead, and warn them first that a first full-history
     scan can take several minutes and many LLM calls; run it in the background
     if it exceeds the timeout.
3. When it finishes, summarize: how many new candidates were found, and tell
   the user to run `/skilld:review` to approve them.
