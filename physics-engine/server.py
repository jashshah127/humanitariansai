"""
HTTP service. This is the deployable artifact.

ZERO DEPENDENCIES -- standard library only. No FastAPI, no uvicorn, nothing to install.
That is deliberate: a demo that needs a working pip install before anyone can see it is
a demo that does not get seen.

Run:
    export GEMINI_API_KEY=...          # free key from aistudio.google.com/apikey
    python3 server.py

Then open http://localhost:8000

Deploy free (Render / Railway / Fly):
    build:  pip install -r requirements.txt
    start:  python3 server.py
    env:    GEMINI_API_KEY, PORT

WHAT IS AND IS NOT SAFE HERE: no authentication, and nothing is stored. That is fine --
it is a demo surface, not a student-facing deployment. No student-identified data should
be sent to it until Q6 (data processing agreement / IRB) is answered.
"""
import json
import os
import sys
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "engine"))

from parse import GeminiLLM, ClaudeLLM, OllamaLLM, parse_problem
from physics_mode import PhysicsEngineMode
from grade_mode import grade
from event_log import EventLog
from formula_kb import ALL_CARDS

_log = EventLog()


def _llm():
    """Pick a provider from whatever credentials exist, preferring the free one."""
    if os.environ.get("GEMINI_API_KEY"):
        return GeminiLLM()
    if os.environ.get("ANTHROPIC_API_KEY"):
        return ClaudeLLM()
    return OllamaLLM()


def api_health():
    return {"status": "ok", "cards": len(ALL_CARDS), "provider": type(_llm()).__name__}


def api_cards():
    """What the engine can actually solve -- useful for setting expectations before
    someone types a problem it will decline."""
    return {"count": len(ALL_CARDS), "cards": [
        {"id": c.id, "name": c.name, "topic": c.topic, "subtopic": c.subtopic,
         "solves_for": c.solves_for, "applies_when": c.applicability}
        for c in ALL_CARDS]}


def api_stats():
    return {"routes": _log.route_split(), "latency": _log.latency_summary(),
            "coverage_gaps": len(_log.coverage_gaps())}


def api_solve(body):
    mode = PhysicsEngineMode(_llm(), event_log=_log)
    result = mode.solve(body.get("query", ""),
                        session_id=body.get("session_id", "web"),
                        render=body.get("render", "solve"))
    d = result.to_dict()
    d.pop("trace", None)     # too large for a UI response; still in the event log
    return d


def api_grade(body):
    parsed = parse_problem(body.get("query", ""), _llm())
    r = grade("web", body.get("query", ""), parsed["knowns"], parsed["unknowns"],
              body.get("student_answer", {}), body.get("student_steps"),
              parsed.get("topic_hint"))
    return r.to_dict()


INDEX = """<!doctype html>
<html><head><meta charset="utf-8"><title>Physics Engine</title>
<style>
 :root{--ink:#1a1a1a;--mute:#5a6b78;--line:#dde5ea;--deep:#065a82;--mid:#21295c}
 *{box-sizing:border-box}
 body{font:16px/1.55 -apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;
      max-width:760px;margin:0 auto;padding:48px 24px;color:var(--ink)}
 h1{font-size:28px;margin:0 0 6px;color:var(--mid)}
 .sub{color:var(--mute);margin:0 0 28px;font-size:15px}
 textarea{width:100%;height:100px;padding:14px;font:inherit;
          border:1px solid var(--line);border-radius:10px;resize:vertical}
 .row{display:flex;gap:10px;margin-top:12px;align-items:center}
 button{padding:11px 20px;font:inherit;font-weight:600;background:var(--deep);
        color:#fff;border:0;border-radius:10px;cursor:pointer}
 button:disabled{opacity:.5;cursor:default}
 select{padding:11px;font:inherit;border:1px solid var(--line);border-radius:10px}
 #out{margin-top:26px}
 .badge{display:inline-block;padding:6px 13px;border-radius:20px;font-size:13px;
        font-weight:700;color:#fff;margin-bottom:14px}
 .verified{background:#1e7a34}.needs_review{background:#b26a00}.unverified{background:#a32020}
 .ans{font-size:26px;font-weight:700;margin:10px 0;color:var(--mid)}
 .meta{color:var(--mute);font-size:14px;margin:5px 0}
 .card{border:1px solid var(--line);border-radius:12px;padding:18px;margin-top:14px}
 ol{padding-left:20px}li{margin:8px 0}
 .ex{color:var(--deep);cursor:pointer;text-decoration:underline;font-size:14px}
</style></head><body>
<h1>Physics Engine</h1>
<p class="sub">Every answer says whether it was symbolically verified &mdash; or admits it wasn't.</p>
<textarea id="q" placeholder="A car starts from rest and accelerates at 2.5 m/s^2 for 12 s. Find its final speed and distance."></textarea>
<div class="row">
  <button id="go" onclick="run()">Solve</button>
  <select id="mode"><option value="solve">Answer</option><option value="tutor">Hints</option></select>
  <span class="ex" onclick="ex('Two blocks of 4 kg and 6 kg hang from a frictionless pulley. Find the acceleration and tension.')">example</span>
  <span class="ex" onclick="ex('Two masses m1 and m2 hang from a frictionless pulley. Find the acceleration and tension.')">symbolic</span>
  <span class="ex" onclick="ex('A 0.5 kg mass on a spring with damping constant 1.2 kg/s. Find the damped frequency.')">out of scope</span>
</div>
<div id="out"></div>
<script>
function ex(t){document.getElementById('q').value=t}
async function run(){
  const q=document.getElementById('q').value.trim(); if(!q)return;
  const b=document.getElementById('go'), o=document.getElementById('out');
  b.disabled=true; b.textContent='Solving...'; o.innerHTML='';
  try{
    const r=await fetch('/solve',{method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({query:q,render:document.getElementById('mode').value})});
    const d=await r.json();
    let h=`<span class="badge ${d.verification}">${d.badge}</span>`;
    if(d.answer&&Object.keys(d.answer).length)
      h+=`<div class="ans">${Object.entries(d.answer).map(([k,v])=>
         `${k} = ${typeof v==='number'?(+v).toPrecision(5):v}`).join('&nbsp;&nbsp;&nbsp;')}</div>`;
    if(d.hints)h+=`<div class="card"><ol>${d.hints.map(x=>`<li>${x}</li>`).join('')}</ol></div>`;
    if(d.candidates)h+=`<div class="card">${d.candidates.map(c=>
      `<div class="meta"><b>${c.principle}</b><br>applies when: ${c.applies_when}<br>
       gives: ${JSON.stringify(c.answer)}</div>`).join('<hr>')}</div>`;
    h+=`<div class="meta">${d.explanation}</div>`;
    if(d.formula_used)h+=`<div class="meta">Formula: ${d.formula_used}</div>`;
    if(d.assumptions&&d.assumptions.length)h+=`<div class="meta">Assumes: ${d.assumptions.join('; ')}</div>`;
    if(d.sources&&Object.keys(d.sources).length)h+=`<div class="meta">Read from your text: `+
      Object.entries(d.sources).filter(([k,v])=>v).map(([k,v])=>`${k} &larr; "${v}"`).join(', ')+`</div>`;
    h+=`<div class="meta">${(+d.latency_ms).toFixed(0)} ms</div>`;
    o.innerHTML=h;
  }catch(e){o.innerHTML=`<div class="meta">Error: ${e}</div>`}
  b.disabled=false; b.textContent='Solve';
}
</script></body></html>"""

class Handler(BaseHTTPRequestHandler):
    def _send(self, code, payload, content_type="application/json"):
        raw = (payload if isinstance(payload, str) else json.dumps(payload, default=str))
        data = raw.encode()
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        path = self.path.split("?")[0]
        try:
            if path == "/":
                return self._send(200, INDEX, "text/html; charset=utf-8")
            if path == "/health":
                return self._send(200, api_health())
            if path == "/cards":
                return self._send(200, api_cards())
            if path == "/stats":
                return self._send(200, api_stats())
            return self._send(404, {"error": "not found"})
        except Exception as e:
            traceback.print_exc()
            return self._send(500, {"error": str(e)})

    def do_POST(self):
        path = self.path.split("?")[0]
        length = int(self.headers.get("Content-Length") or 0)
        try:
            body = json.loads(self.rfile.read(length) or b"{}")
        except json.JSONDecodeError:
            return self._send(400, {"error": "invalid JSON body"})
        try:
            if path == "/solve":
                return self._send(200, api_solve(body))
            if path == "/grade":
                return self._send(200, api_grade(body))
            return self._send(404, {"error": "not found"})
        except Exception as e:
            traceback.print_exc()
            # Fail as an honest unverified answer rather than a stack trace, so a
            # provider outage degrades the same way an uncovered problem does.
            return self._send(200, {
                "verification": "unverified",
                "badge": "Unverified - engine error",
                "needs_llm_completion": True,
                "explanation": f"Could not process this problem: {e}",
                "route": "error", "latency_ms": 0,
            })

    def log_message(self, fmt, *args):
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))


def main():
    port = int(os.environ.get("PORT", 8000))
    provider = type(_llm()).__name__
    print(f"Physics Engine  |  {len(ALL_CARDS)} formula cards  |  parser: {provider}")
    if not (os.environ.get("GEMINI_API_KEY") or os.environ.get("ANTHROPIC_API_KEY")):
        print("WARNING: no API key set. Parsing will fail unless Ollama is running.")
        print("         Free key: https://aistudio.google.com/apikey")
    print(f"Listening on http://localhost:{port}")
    ThreadingHTTPServer(("0.0.0.0", port), Handler).serve_forever()


if __name__ == "__main__":
    main()
