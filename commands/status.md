---
description: Show skilld lesson candidates and sync status
---

Show the current skilld state.

1. Check the CLI is available with `command -v skilld` (Bash tool). If missing,
   tell the user to install it with `pip install skilld` and stop.
2. Run `skilld status` with the Bash tool.
3. Summarize the output for the user: how many lessons are proposed, accepted,
   and rejected, grouped by domain. If anything is proposed, suggest
   `/skilld:review`.
