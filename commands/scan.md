---
description: Scan agent transcripts and propose lesson candidates
---

Run the skilld scanner over the user's transcript history.

1. First check the CLI is available: run `command -v skilld` with the Bash tool.
   If it is missing, tell the user to install it with `pip install skilld`
   (or `uvx skilld` for a no-install run) and stop.
2. Run `skilld scan --all` with the Bash tool. This can take a few minutes on
   a large history — run it in the background if it exceeds the timeout, and
   report progress from its output.
3. When it finishes, summarize: how many new candidates were found, and tell
   the user to run `/skilld:review` to approve them.
