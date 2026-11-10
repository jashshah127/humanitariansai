"""
Build a one-file status page for the team and the manager (plan item: "status page visible
to all three plus the manager"). No server and no model calls.

The page does two things:
  * LIVE: when someone opens it, their browser asks each service's /health and shows up or
    down, how long it took, and the card count. Free Render services sleep after 15 idle
    minutes, so the first answer can take about a minute; the page says so while it waits.
  * RECORDED: uptime, error rate and latency from the probe files in monitoring/ (written by
    eval/monitor.py), with a chart, embedded when this script runs.

Run from physics-engine/:
    python eval/status_page.py
    python eval/status_page.py --service "Live=https://physics-engine-hr0x.onrender.com" \
                               --service "Staging=https://physics-engine-staging.onrender.com"
Writes status/index.html (open it in a browser, or publish the status/ folder as a static site).
Re-run it after new probes to refresh the recorded numbers.

The live part needs the services to allow cross-origin requests from the page. If a browser
blocks it, the card says so and the recorded numbers still show.
"""
import argparse
import csv
import glob
import html
import json
import os
import statistics
from datetime import datetime, timezone

DEFAULT_SERVICES = [
    ("Live (main)", "https://physics-engine-hr0x.onrender.com"),
    ("Staging", "https://physics-engine-staging.onrender.com"),
]
SLOW_MS = 10_000


def read_probes(folder):
    by_url = {}
    for path in sorted(glob.glob(os.path.join(folder, "*.csv"))):
        with open(path, encoding="utf-8") as f:
            for r in csv.DictReader(f):
                if r.get("kind") == "health":
                    by_url.setdefault(r["url"].rstrip("/"), []).append(r)
    for rows in by_url.values():
        rows.sort(key=lambda r: r["timestamp_utc"])
    return by_url


def pct(sorted_vals, p):
    k = max(0, min(len(sorted_vals) - 1, round(p / 100 * (len(sorted_vals) - 1))))
    return sorted_vals[k]


def stats(rows):
    good = [r for r in rows if r["ok"] == "1"]
    lat = sorted(int(r["latency_ms"]) for r in good)
    return {
        "n": len(rows), "healthy": len(good),
        "uptime": len(good) / len(rows) if rows else 0,
        "median": int(statistics.median(lat)) if lat else None,
        "p95": pct(lat, 95) if lat else None,
        "max": lat[-1] if lat else None,
        "slow": sum(1 for x in lat if x > SLOW_MS),
        "first": rows[0]["timestamp_utc"], "last": rows[-1]["timestamp_utc"],
    }


def spark(rows, w=640, h=110):
    vals = [int(r["latency_ms"]) / 1000 for r in rows]
    top = max(max(vals), 12)
    xs = [10 + i * (w - 20) / max(len(vals) - 1, 1) for i in range(len(vals))]
    ys = [h - 12 - (v / top) * (h - 24) for v in vals]
    pts = " ".join(f"{x:.1f},{y:.1f}" for x, y in zip(xs, ys))
    slow_y = h - 12 - (SLOW_MS / 1000 / top) * (h - 24)
    dots = "".join(
        f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3" fill="{"#b42318" if r["ok"] != "1" else "#1d4ed8"}"/>'
        for x, y, r in zip(xs, ys, rows))
    return (f'<svg viewBox="0 0 {w} {h}" width="100%" role="img" aria-label="Latency of each recorded probe">'
            f'<line x1="10" x2="{w - 10}" y1="{slow_y:.1f}" y2="{slow_y:.1f}" stroke="#999" stroke-dasharray="4 4"/>'
            f'<text x="12" y="{slow_y - 4:.1f}" font-size="10" fill="#666">10 s</text>'
            f'<polyline points="{pts}" fill="none" stroke="#1d4ed8" stroke-width="1.5"/>{dots}</svg>')


def fmt_ms(v):
    return "n/a" if v is None else (f"{v / 1000:.1f} s" if v >= 1000 else f"{v} ms")


PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Physics Engine status</title>
<style>
:root{--bg:#fff;--fg:#1a1a1a;--mute:#5f6368;--line:#d0d5dd;--ok:#067647;--okbg:#ecfdf3;--bad:#b42318;--badbg:#fef3f2;--wait:#b54708;--waitbg:#fffaeb;--card:#f8f9fb}
@media (prefers-color-scheme:dark){:root{--bg:#14161a;--fg:#e8eaed;--mute:#9aa0a6;--line:#3c4043;--ok:#6ce9a6;--okbg:#0b2a1b;--bad:#fda29b;--badbg:#2b1210;--wait:#fec84b;--waitbg:#2b2008;--card:#1b1e23}}
body{margin:0;background:var(--bg);color:var(--fg);font:16px/1.5 system-ui,Segoe UI,Calibri,sans-serif}
main{max-width:860px;margin:0 auto;padding:28px 20px 60px}
h1{font-size:26px;margin:0 0 4px}h2{font-size:18px;margin:34px 0 10px}
.sub{color:var(--mute);margin:0 0 6px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:14px}
.card{border:1px solid var(--line);background:var(--card);border-radius:10px;padding:14px 16px}
.name{font-weight:600}.url{color:var(--mute);font-size:13px;word-break:break-all}
.chip{display:inline-block;margin-top:8px;padding:2px 10px;border-radius:999px;font-weight:600;font-size:14px}
.up{background:var(--okbg);color:var(--ok)}.down{background:var(--badbg);color:var(--bad)}.wait{background:var(--waitbg);color:var(--wait)}
.detail{margin-top:6px;color:var(--mute);font-size:14px}
table{border-collapse:collapse;width:100%;font-size:14px}th,td{border:1px solid var(--line);padding:6px 9px;text-align:left}th{background:var(--card)}
.scroll{overflow-x:auto}.note{color:var(--mute);font-size:13px}
ul{padding-left:20px}li{margin:3px 0}
</style></head><body><main>
<h1>Physics Engine status</h1>
<p class="sub">For the team and the manager. Generated %%GENERATED%% UTC.</p>

<h2>Live checks (from your browser, right now)</h2>
<div class="grid" id="live"></div>
<p class="note">Free instances sleep after 15 idle minutes, so the first answer can take about a minute. Opening this page wakes them.</p>

<h2>Recorded health probes</h2>
%%RECORDED%%

<h2>How deploys work</h2>
<ul>
<li>CI runs on every pull request and every push to <code>main</code> and <code>feature-harsh</code>.</li>
<li>Render deploys only after CI passes. A failing commit is not deployed.</li>
<li>Staging builds <code>feature-harsh</code>; the live service tracks <code>main</code>.</li>
<li>Rollback: Render, Events, Rollback to the previous deploy, then Revert the pull request on GitHub.</li>
</ul>
<p class="note">The recorded numbers update when <code>python eval/status_page.py</code> is run again and the result is pushed.</p>
</main>
<script>
const SERVICES = %%SERVICES%%;
const live = document.getElementById("live");
function showCache(base, line) {
  fetch(base + "/stats", { cache: "no-store" })
    .then(function (r) { return r.json(); })
    .then(function (d) {
      const c = d.cache;
      if (!c) { line.textContent = "cache: not in this version"; return; }
      if (!c.enabled) { line.textContent = "cache: off"; return; }
      if (c.backend === "not used yet") { line.textContent = "cache: on, not used yet"; return; }
      const rate = c.hit_rate === null || c.hit_rate === undefined ? "n/a" : Math.round(c.hit_rate * 100) + "%";
      line.textContent = "cache: on (" + c.backend + "), " + c.hits + " hits, " + c.misses + " misses, hit rate " + rate +
        ", " + c.entries + " stored, " + c.errors + " errors";
    })
    .catch(function () { line.textContent = "cache: could not read /stats"; });
}
SERVICES.forEach(function (s) {
  const card = document.createElement("div");
  card.className = "card";
  const name = document.createElement("div"); name.className = "name"; name.textContent = s.name;
  const url = document.createElement("div"); url.className = "url"; url.textContent = s.url;
  const chip = document.createElement("span"); chip.className = "chip wait"; chip.textContent = "checking...";
  const detail = document.createElement("div"); detail.className = "detail";
  const cacheLine = document.createElement("div"); cacheLine.className = "detail";
  card.append(name, url, chip, detail, cacheLine); live.append(card);
  const t0 = performance.now();
  const timer = setInterval(function () {
    detail.textContent = "waiting " + Math.round((performance.now() - t0) / 1000) + " s (the service may be waking up)";
  }, 1000);
  const ctl = new AbortController();
  const stop = setTimeout(function () { ctl.abort(); }, 90000);
  fetch(s.url + "/health", { signal: ctl.signal, cache: "no-store" })
    .then(function (r) { return r.json().then(function (d) { return { ok: r.ok, d: d }; }); })
    .then(function (x) {
      const secs = ((performance.now() - t0) / 1000).toFixed(1);
      if (x.ok && x.d.status === "ok") {
        chip.className = "chip up"; chip.textContent = "up";
        detail.textContent = "answered in " + secs + " s; " + x.d.cards + " cards; " + x.d.provider;
        showCache(s.url, cacheLine);
      } else {
        chip.className = "chip down"; chip.textContent = "problem";
        detail.textContent = "answered in " + secs + " s but did not report ok";
      }
    })
    .catch(function (e) {
      chip.className = "chip down"; chip.textContent = "not reachable from this browser";
      detail.textContent = e && e.name === "AbortError" ? "no answer within 90 s"
        : "the request failed or the browser blocked it; see the recorded probes below";
    })
    .finally(function () { clearInterval(timer); clearTimeout(stop); });
});
</script></body></html>
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--monitoring", default="monitoring")
    ap.add_argument("--out", default=os.path.join("status", "index.html"))
    ap.add_argument("--service", action="append", help='"Name=https://address" (repeatable)')
    args = ap.parse_args()

    services = DEFAULT_SERVICES
    if args.service:
        services = [tuple(x.split("=", 1)) for x in args.service]
    probes = read_probes(args.monitoring)

    if probes:
        head = "".join(f"<th>{h}</th>" for h in
                       ["Service address", "Probes", "Healthy", "Uptime", "Median", "95th pct", "Slowest", "Over 10 s", "First", "Last"])
        body = ""
        for url, rows in sorted(probes.items(), key=lambda kv: -len(kv[1])):
            s = stats(rows)
            cells = [html.escape(url), s["n"], s["healthy"], f'{s["uptime"]:.0%}', fmt_ms(s["median"]), fmt_ms(s["p95"]),
                     fmt_ms(s["max"]), s["slow"], s["first"][:16].replace("T", " "), s["last"][:16].replace("T", " ")]
            body += "<tr>" + "".join(f"<td>{c}</td>" for c in cells) + "</tr>"
        biggest = max(probes.values(), key=len)
        recorded = (f'<div class="scroll"><table><tr>{head}</tr>{body}</table></div>'
                    f'<p class="note">Probe times are UTC. Latency over 10 s is almost always a cold start on the free plan.</p>'
                    f'<h2>Latency of each probe ({html.escape(biggest[0]["url"])})</h2>{spark(biggest)}'
                    f'<p class="note">Blue dots are healthy probes, red dots failed. The dashed line is 10 seconds.</p>')
    else:
        recorded = '<p class="note">No probe files found in monitoring/ yet. Run <code>python eval/monitor.py probe ...</code> first.</p>'

    svc = json.dumps([{"name": n, "url": u.rstrip("/")} for n, u in services]).replace("</", "<\\/")
    page = (PAGE.replace("%%GENERATED%%", datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M"))
                .replace("%%RECORDED%%", recorded).replace("%%SERVICES%%", svc))
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(page)
    print(f"Wrote {args.out} ({len(page) // 1024} KB) from {sum(len(v) for v in probes.values())} probes across {len(probes)} address(es).")


if __name__ == "__main__":
    main()
