"""
Uptime, error-rate and latency monitoring for the deployed engine API.
Standard library only, so it runs anywhere Python does.

Run from physics-engine/:
    python eval/monitor.py probe --url https://physics-engine-staging.onrender.com --out monitoring/staging.csv
    python eval/monitor.py probe --url ... --out monitoring/staging.csv --every 300 --count 12
    python eval/monitor.py summary monitoring/staging.csv

probe    GETs /health, measures how long it took and whether the reply is healthy, and
         appends one row to the CSV. Exit code 0 = healthy, 1 = not healthy, so a
         scheduler or a CI job can alert on it.
         --solve also sends one known problem to /solve and checks that the answer is
         verified and correct (a = 1.96, T = 47.04). It needs a minted token in the
         MONITOR_TOKEN environment variable. Each solve costs one model request, and
         the parser's default model allows only 20 a day on the free tier, so use it
         rarely (once before a demo, not every hour).
summary  Prints uptime, error rate and latency from the CSV.

Free Render instances sleep after 15 idle minutes, and the first request after that
takes about a minute. Probes slower than SLOW_MS are counted as slow (likely a cold
start). A probe also wakes the service, which uses the workspace's 750 shared free
hours, so probe hourly, not every minute, except in a short demo window.
"""
import argparse
import csv
import json
import os
import statistics
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

SLOW_MS = 10_000
FIELDS = ["timestamp_utc", "url", "kind", "http_status", "latency_ms", "ok", "detail"]
SOLVE_QUERY = "Two blocks of 4 kg and 6 kg hang from a frictionless pulley. Find the acceleration and tension."
EXPECTED = {"a": 1.96, "T": 47.04}


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def request(url, data=None, headers=None, timeout=90):
    """Returns (status, body_text, seconds). Status 0 means no HTTP reply at all."""
    req = urllib.request.Request(url, data=data, headers=headers or {})
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read().decode("utf-8", "replace"), time.time() - t0
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace"), time.time() - t0
    except Exception as e:  # timeout, DNS, refused connection
        return 0, f"{type(e).__name__}: {e}", time.time() - t0


def probe_health(base):
    status, body, secs = request(base.rstrip("/") + "/health")
    ok, detail = False, ""
    if status == 200:
        try:
            d = json.loads(body)
            ok = d.get("status") == "ok"
            detail = f"provider={d.get('provider')} cards={d.get('cards')} frontend={d.get('frontend')}"
            if not ok:
                detail = "status field is not ok: " + detail
        except ValueError:
            detail = "reply is not JSON"
    else:
        detail = body[:120].replace("\n", " ")
    return dict(timestamp_utc=now(), url=base, kind="health", http_status=status,
                latency_ms=int(secs * 1000), ok=int(ok), detail=detail)


def probe_solve(base):
    token = os.environ.get("MONITOR_TOKEN")
    if not token:
        return None
    body = json.dumps({"query": SOLVE_QUERY, "render": "solve"}).encode()
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}
    status, text, secs = request(base.rstrip("/") + "/solve", data=body, headers=headers, timeout=120)
    ok, detail = False, ""
    if status == 200:
        try:
            d = json.loads(text)
            ans = d.get("answer") or {}
            right = all(k in ans and abs(float(ans[k]) - v) / v < 0.01 for k, v in EXPECTED.items())
            ok = d.get("verification") == "verified" and right
            detail = f"verification={d.get('verification')} answer_correct={right}"
        except (ValueError, TypeError):
            detail = "reply could not be read"
    else:
        detail = f"HTTP {status}: " + text[:100].replace("\n", " ")
    return dict(timestamp_utc=now(), url=base, kind="solve", http_status=status,
                latency_ms=int(secs * 1000), ok=int(ok), detail=detail)


def append(path, row):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    new = not os.path.exists(path)
    with open(path, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        if new:
            w.writeheader()
        w.writerow(row)


def cmd_probe(a):
    exit_code = 0
    for i in range(a.count):
        rows = [probe_health(a.url)]
        if a.solve:
            s = probe_solve(a.url)
            if s is None:
                print("MONITOR_TOKEN is not set, so the solve check was skipped.")
            else:
                rows.append(s)
        for r in rows:
            append(a.out, r)
            flag = "OK  " if r["ok"] else "FAIL"
            print(f"{r['timestamp_utc']} {flag} {r['kind']:6} HTTP {r['http_status']} {r['latency_ms']} ms  {r['detail']}")
            if not r["ok"]:
                exit_code = 1
        if i < a.count - 1:
            time.sleep(a.every)
    return exit_code


def pct(sorted_vals, p):
    if not sorted_vals:
        return None
    k = max(0, min(len(sorted_vals) - 1, round(p / 100 * (len(sorted_vals) - 1))))
    return sorted_vals[k]


def cmd_summary(a):
    with open(a.csv, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        print("no probes recorded yet")
        return 0
    print(f"{len(rows)} probes, {rows[0]['timestamp_utc']} to {rows[-1]['timestamp_utc']}")
    for kind in sorted({r["kind"] for r in rows}):
        rs = [r for r in rows if r["kind"] == kind]
        good = [r for r in rs if r["ok"] == "1"]
        lat = sorted(int(r["latency_ms"]) for r in good)
        slow = sum(1 for r in good if int(r["latency_ms"]) > SLOW_MS)
        print(f"\n{kind}: {len(rs)} probes")
        print(f"  uptime (healthy / probes): {len(good)}/{len(rs)} = {len(good) / len(rs):.1%}")
        print(f"  error rate: {(len(rs) - len(good)) / len(rs):.1%}")
        if lat:
            print(f"  latency of healthy probes: median {int(statistics.median(lat))} ms, "
                  f"p95 {pct(lat, 95)} ms, max {lat[-1]} ms")
            print(f"  slow (over {SLOW_MS // 1000} s, likely a cold start): {slow}")
        bad = [r for r in rs if r["ok"] != "1"][-3:]
        for r in bad:
            print(f"  last failures: {r['timestamp_utc']} HTTP {r['http_status']} {r['detail']}")
    return 0


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("probe")
    p.add_argument("--url", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--solve", action="store_true")
    p.add_argument("--every", type=int, default=3600, help="seconds between probes when --count > 1")
    p.add_argument("--count", type=int, default=1)
    s = sub.add_parser("summary")
    s.add_argument("csv")
    a = ap.parse_args()
    sys.exit(cmd_probe(a) if a.cmd == "probe" else cmd_summary(a))


if __name__ == "__main__":
    main()
