"""Audit: fetch live page for each session, count application links, compare to capture."""
import json, re, time, requests
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

with open(r"C:\Users\erika\Organise\aslo2026\sessions_all.json", "r", encoding="utf-8") as f:
    sessions = [json.loads(line) for line in f if line.strip()]

session_index = {s["session_id"]: s for s in sessions}

def fetch_count(sid):
    try:
        r = requests.get("https://aslo.secure-platform.com/2026/solicitations/18/sessiongallery/{}".format(sid),
                         timeout=20)
        if r.status_code != 200:
            return sid, 0, "http_{}".format(r.status_code)
        apps = set(int(x) for x in re.findall(r"/application/(\d+)", r.text))
        return sid, len(apps), "ok"
    except Exception as e:
        return sid, 0, "err_{}".format(str(e)[:40])

# Audit all 309 sessions
session_ids = sorted(session_index.keys())
print("Auditing {} sessions...".format(len(session_ids)))
results = {}
with ThreadPoolExecutor(max_workers=8) as ex:
    futs = {ex.submit(fetch_count, sid): sid for sid in session_ids}
    done = 0
    for fut in as_completed(futs):
        sid, live_count, status = fut.result()
        results[sid] = (live_count, status)
        done += 1
        if done % 30 == 0:
            print("  {}/{}".format(done, len(session_ids)))

# Compare
captured = {sid: len([p for p in (session_index[sid].get("presentations") or []) if p.get("title")])
            for sid in session_ids}

# Summary
total_captured = sum(captured.values())
total_live = sum(v[0] for v in results.values())
print("\n=== AUDIT SUMMARY ===")
print("Total presentations captured: {}".format(total_captured))
print("Total application links on live pages: {}".format(total_live))
print("Net under-capture: {} ({:.1f}%)".format(
    total_live - total_captured,
    100.0 * (total_live - total_captured) / max(total_live, 1)))

# Find sessions with significant under-capture
under = []
for sid in session_ids:
    cap = captured[sid]
    live = results[sid][0]
    delta = live - cap
    if delta > 0:
        under.append((sid, cap, live, delta))
under.sort(key=lambda x: -x[3])

print("\n=== TOP 30 UNDER-CAPTURED SESSIONS ===")
print("{:<10} {:>6} {:>6} {:>6}  {}".format("ID", "Cap", "Live", "Delta", "Code/Name"))
for sid, cap, live, delta in under[:30]:
    s = session_index[sid]
    code = s.get("session_code", "??")
    name = (s.get("name") or "")[:45]
    print("{:<10} {:>6} {:>6} {:>6}  [{}] {}".format(sid, cap, live, delta, code, name))

# Empty-capture sessions that DO have live content
empty_with_content = [(sid, results[sid][0]) for sid in session_ids
                      if captured[sid] == 0 and results[sid][0] > 0]
print("\n=== EMPTY-CAPTURE SESSIONS WITH LIVE CONTENT: {} ===".format(len(empty_with_content)))
for sid, n in empty_with_content[:15]:
    s = session_index[sid]
    print("  ID={} [{}] live={} -- {}".format(sid, s.get("session_code"), n, (s.get("name") or "")[:50]))

# Save audit data
audit = {
    "total_sessions": len(session_ids),
    "total_captured_presentations": total_captured,
    "total_live_application_links": total_live,
    "net_undercapture": total_live - total_captured,
    "undercapture_pct": round(100.0 * (total_live - total_captured) / max(total_live, 1), 2),
    "per_session": {str(sid): {"captured": captured[sid], "live": results[sid][0], "status": results[sid][1]}
                    for sid in session_ids},
}
with open(r"C:\Users\erika\Organise\aslo2026\_audit_capture_results.json", "w", encoding="utf-8") as f:
    json.dump(audit, f, indent=2)
print("\nSaved audit results to _audit_capture_results.json")
