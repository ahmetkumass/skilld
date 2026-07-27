"""Browser-based review: one candidate at a time, keyboard a/r/s.

`skilld review` starts a tiny localhost server, opens the browser, records
decisions into the state file as you click (or press a/r/s), and shuts down
when you finish. Accepted lessons are written by the CLI right after.
"""

import json
import socket
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from . import store

PAGE = """<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>skilld review</title><style>
:root{
  --bg:#191C21;--surface:#1F232A;--raise:#252A32;--line:#2E343D;--hair:#3A414C;
  --ink:#DCE0E6;--dim:#8B93A0;--faint:#697180;
  --ok:#69A88C;--ok-deep:#121B17;--no:#B96A74;
  --serif:'Iowan Old Style',Palatino,Georgia,serif;
  --sans:-apple-system,'SF Pro Text','Segoe UI',Roboto,sans-serif;
  --mono:ui-monospace,'SF Mono',Menlo,Consolas,monospace;
}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);color:var(--ink);font-family:var(--sans);
  min-height:100vh;display:flex;flex-direction:column;align-items:center;
  padding:2.2rem 1.2rem 3rem}
.top{width:100%;max-width:620px;display:flex;justify-content:space-between;
  align-items:baseline;margin-bottom:.9rem}
.mark{font-family:var(--mono);font-size:.85rem;color:var(--dim);letter-spacing:.02em}
.mark b{color:var(--ink);font-weight:600}
.count{font-family:var(--mono);font-size:.8rem;color:var(--faint);font-variant-numeric:tabular-nums}
.count b{color:var(--ink);font-weight:500}
.track{width:100%;max-width:620px;height:1px;background:var(--hair);margin-bottom:2.2rem;position:relative}
.track i{position:absolute;left:0;top:0;height:1px;background:var(--ok);transition:width .3s ease}
.card{width:100%;max-width:620px;background:var(--surface);border:1px solid var(--line);
  border-radius:10px;padding:2rem 2.1rem 1.8rem;animation:enter .18s ease}
@keyframes enter{from{opacity:0;transform:translateY(5px)}to{opacity:1;transform:none}}
@media (prefers-reduced-motion:reduce){.card{animation:none}.track i{transition:none}}
.eyebrow{display:flex;justify-content:space-between;align-items:baseline;
  font-family:var(--mono);font-size:.68rem;text-transform:uppercase;
  letter-spacing:.09em;color:var(--dim);margin-bottom:1.1rem}
.eyebrow .dots{color:var(--ok);letter-spacing:.15em}
.eyebrow .dots span{color:var(--hair)}
h2{font-family:var(--serif);font-size:1.55rem;font-weight:600;
  letter-spacing:-.01em;line-height:1.25;margin-bottom:.8rem}
.stmt{font-size:.95rem;line-height:1.7;color:var(--ink);opacity:.88;
  max-width:56ch;margin-bottom:1.5rem}
.ev{border-top:1px solid var(--line);padding-top:1.1rem}
.ev h3{font-family:var(--mono);font-size:.65rem;text-transform:uppercase;
  letter-spacing:.11em;color:var(--faint);margin-bottom:.85rem}
.q{padding-left:.95rem;border-left:2px solid var(--hair);margin-bottom:.85rem}
.q .src{display:block;font-family:var(--mono);font-size:.68rem;color:var(--faint);
  margin-bottom:.15rem;font-variant-numeric:tabular-nums}
.q em{font-family:var(--serif);font-style:italic;font-size:.92rem;
  line-height:1.55;color:var(--dim)}
.btns{width:100%;max-width:620px;display:flex;gap:.6rem;margin-top:1.3rem}
button{display:flex;align-items:center;justify-content:center;gap:.55rem;
  height:46px;border-radius:8px;font-family:var(--sans);font-size:.88rem;
  font-weight:600;cursor:pointer;transition:background .12s,border-color .12s}
button:focus-visible{outline:2px solid var(--ok);outline-offset:2px}
kbd{font-family:var(--mono);font-size:.66rem;font-weight:400;
  border:1px solid currentColor;border-radius:4px;padding:.06rem .32rem;opacity:.55}
.acc{flex:1.4;background:var(--ok);border:1px solid var(--ok);color:var(--ok-deep)}
.acc:hover{background:#79B79B}
.rej{flex:1;background:transparent;border:1px solid var(--line);color:var(--no)}
.rej:hover{border-color:var(--no)}
.skp{flex:.8;background:transparent;border:1px solid transparent;color:var(--faint)}
.skp:hover{color:var(--dim)}
.done{text-align:left;padding:2.4rem 2.1rem}
.done .eyebrow{margin-bottom:1rem}
.done h2{margin-bottom:.9rem}
.done p{font-size:.92rem;line-height:1.65;color:var(--dim);max-width:52ch}
.done code{font-family:var(--mono);font-size:.8rem;color:var(--ink);
  background:var(--raise);border:1px solid var(--line);border-radius:5px;padding:.1rem .45rem}
</style></head><body>
<div class="top"><span class="mark"><b>skilld</b> · review</span><span class="count" id="counts"></span></div>
<div class="track"><i id="prog" style="width:0"></i></div>
<div id="app"></div>
<div class="btns" id="btns"></div>
<script>
const CANDS = __CANDS__;
let i = 0, acc = 0, rej = 0;
const app = document.getElementById("app");
const btns = document.getElementById("btns");
function esc(s){const d=document.createElement("div");d.textContent=s??"";return d.innerHTML}
function dots(n){let s="";for(let k=1;k<=3;k++)s+=k<=n?"●":"<span>●</span>";return s}
function render(){
  document.getElementById("counts").innerHTML =
    `<b>${String(Math.min(i+1,CANDS.length)).padStart(2,"0")}</b> / ${String(CANDS.length).padStart(2,"0")}`;
  document.getElementById("prog").style.width = (i/CANDS.length*100)+"%";
  if(i >= CANDS.length){
    app.innerHTML = `<div class="card done">
      <div class="eyebrow"><span>review complete</span></div>
      <h2>${acc} lessons saved.</h2>
      <p>${rej} rejected. Accepted lessons are being written to
      <code>~/.claude/skills</code>; your agent will know them from its next
      session on. You can close this window.</p></div>`;
    btns.innerHTML = "";
    fetch("/quit",{method:"POST"});
    return;
  }
  const c = CANDS[i];
  const evs = (c.evidence||[]).slice(0,4).map(e=>
    `<div class="q"><span class="src">${esc(e.session)} · ${esc((e.timestamp||"").slice(0,16))}</span>
     <em>&ldquo;${esc(e.quote)}&rdquo;</em></div>`).join("");
  app.innerHTML = `<div class="card">
    <div class="eyebrow"><span>${esc(c.domain)} · ${esc(c.type)}</span>
      <span class="dots">${dots(c.confidence||1)}</span></div>
    <h2>${esc(c.title)}</h2>
    <div class="stmt">${esc(c.statement)}</div>
    ${evs ? `<div class="ev"><h3>Evidence — in your own words</h3>${evs}</div>` : ""}
  </div>`;
  btns.innerHTML = `
    <button class="rej" onclick="decide('rejected')">Reject <kbd>R</kbd></button>
    <button class="skp" onclick="skip()">Skip <kbd>S</kbd></button>
    <button class="acc" onclick="decide('accepted')">Accept <kbd>A</kbd></button>`;
}
function decide(status){
  const c = CANDS[i];
  fetch("/decide",{method:"POST",body:JSON.stringify({id:c.id,status})});
  if(status==="accepted") acc++; else rej++;
  i++; render();
}
function skip(){ i++; render(); }
document.addEventListener("keydown",e=>{
  if(i>=CANDS.length) return;
  const k=e.key.toLowerCase();
  if(k==="a") decide("accepted");
  if(k==="r") decide("rejected");
  if(k==="s") skip();
});
render();
</script></body></html>"""


def serve(state: dict) -> tuple[int, int]:
    """Run the review UI; returns (accepted, rejected) counts for this run."""
    pending = store.by_status(state, "proposed")
    if not pending:
        return (0, 0)
    lock = threading.Lock()
    stats = {"accepted": 0, "rejected": 0}
    done = threading.Event()

    cands_json = json.dumps(
        [
            {k: c.get(k) for k in ("id", "domain", "type", "title", "statement", "confidence", "evidence")}
            for c in pending
        ],
        ensure_ascii=False,
    ).replace("</", "<\\/")
    page = PAGE.replace("__CANDS__", cands_json).encode()

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def do_GET(self):
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(page)

        def do_POST(self):
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length) if length else b"{}"
            if self.path == "/decide":
                try:
                    d = json.loads(body)
                except json.JSONDecodeError:
                    d = {}
                with lock:
                    c = state["candidates"].get(d.get("id"))
                    if c and d.get("status") in ("accepted", "rejected"):
                        c["status"] = d["status"]
                        stats[d["status"]] += 1
                        store.save(state)
            elif self.path == "/quit":
                done.set()
            self.send_response(204)
            self.end_headers()

    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    url = f"http://127.0.0.1:{port}/"
    print(f"Review UI opened in your browser: {url}", flush=True)
    print("Close the window when done; Ctrl-C here also works.", flush=True)
    webbrowser.open(url)
    try:
        done.wait()
    except KeyboardInterrupt:
        pass
    server.shutdown()
    return stats["accepted"], stats["rejected"]
