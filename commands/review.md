---
description: Review distilled lesson candidates in the browser
---

Open the skilld review UI so the user can approve or reject lesson candidates.

1. Check the CLI is available with `command -v skilld` (Bash tool). If missing,
   tell the user to install it with `pip install skilld` and stop.
2. Run `skilld review` with the Bash tool **in the background** — it starts a
   local web server, opens the user's browser, and blocks until the review is
   finished in the browser.
3. Tell the user the review UI is open in their browser: one lesson per card,
   keys `a` accept / `r` reject / `s` skip. Approved lessons sync automatically
   to every detected tool when they finish.
