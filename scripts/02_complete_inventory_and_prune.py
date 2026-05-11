"""
Two-phase cleanup:
  Phase 1: identify withdrawn entries (captured abstract_ids NOT in live page) -> mark for pruning
  Phase 2: fetch abstract text for any presentation that has title but no 'abstract' field
Saves periodically so the run is resumable.
"""
import json, re, time, requests
from pathlib import Path
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed

SESS_FILE = Path(r"C:\Users\erika\Organise\aslo2026\sessions_all.json")
sessions = []
with open(SESS_FILE, "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if line:
            sessions.append(json.loads(line))

session_by_id = {s["session_id"]: s for s in sessions}
BASE = "https://aslo.secure-platform.com/2026/solicitations/18/sessiongallery"


def fetch(url, max_retries=2):
    for attempt in range(max_retries + 1):
        try:
            r = requests.get(url, timeout=25)
            if r.status_code == 200:
                return r.text
            return None
        except Exception:
            if attempt == max_retries:
                return None
            time.sleep(0.5 + attempt)


def get_live_ids(session_id):
    text = fetch("{}/{}".format(BASE, session_id))
    if not text:
        return None
    return sorted(set(int(x) for x in re.findall(r"/application/(\d+)", text)))


def parse_app_page(session_id, app_id):
    """Extract title, presenter, affiliation, email, time, authors, abstract."""
    text = fetch("{}/{}/application/{}".format(BASE, session_id, app_id))
    if not text:
        return None
    soup = BeautifulSoup(text, "html.parser")
    out = {"abstract_id": str(app_id)}

    h3 = soup.find("h3")
    if h3:
        out["title"] = h3.get_text(strip=True)

    # Helper: parse <strong>Label:</strong> -> value patterns
    def grab(label_text):
        for st in soup.find_all("strong"):
            if st.get_text(strip=True).rstrip(":").strip().lower() == label_text.lower():
                parts = []
                for sib in st.next_siblings:
                    if getattr(sib, "name", None) == "strong":
                        break
                    if hasattr(sib, "get_text"):
                        parts.append(sib.get_text(" ", strip=True))
                    else:
                        s = str(sib).strip()
                        if s:
                            parts.append(s)
                return " ".join(p for p in parts if p).strip()
        return None

    primary = grab("Primary Presenter")
    if primary:
        em = re.search(r"\(([^)]+@[^)]+)\)", primary)
        if em:
            out["email"] = em.group(1).strip()
            primary = primary[:em.start()].rstrip(" ,").strip()
        if "," in primary:
            name, aff = primary.split(",", 1)
            out["presenter"] = name.strip()
            out["affiliation"] = aff.strip()
        else:
            out["presenter"] = primary.strip()

    auth = grab("Authors")
    if auth and auth.lower() != "authors":
        out["authors"] = auth

    t = grab("Time")
    if t:
        out["time"] = t

    # Abstract body: look for <strong>Abstract:</strong> or a labelled section
    # Often the abstract is in a <p> or <div> that follows an "Abstract" label
    abstract_text = None
    for label in ["Abstract", "Description"]:
        for st in soup.find_all("strong"):
            if st.get_text(strip=True).rstrip(":").strip().lower() == label.lower():
                # Walk siblings collecting text
                parts = []
                for sib in st.parent.next_siblings if st.parent else st.next_siblings:
                    if getattr(sib, "name", None) in ("h3", "h2", "footer"):
                        break
                    if hasattr(sib, "get_text"):
                        s = sib.get_text(" ", strip=True)
                    else:
                        s = str(sib).strip()
                    if s:
                        parts.append(s)
                joined = " ".join(parts).strip()
                if len(joined) > 50:
                    abstract_text = joined
                    break
        if abstract_text:
            break

    # Fallback: find the longest <p> that looks like prose
    if not abstract_text:
        ps = soup.find_all("p")
        candidates = [p.get_text(" ", strip=True) for p in ps]
        candidates = [c for c in candidates if len(c) > 200 and not c.lower().startswith(("click here", "program time", "view", "back to"))]
        if candidates:
            abstract_text = max(candidates, key=len)

    if abstract_text:
        # Clean common boilerplate trailing
        abstract_text = re.sub(r"\s+", " ", abstract_text).strip()
        # Cap at reasonable length to avoid runaway
        if len(abstract_text) > 8000:
            abstract_text = abstract_text[:8000] + "..."
        out["abstract"] = abstract_text

    # Strip non-breaking spaces from string fields
    for k, v in list(out.items()):
        if isinstance(v, str):
            out[k] = v.replace(" ", " ").strip().strip(",").strip()

    return out


# ============== PHASE 1: PRUNE WITHDRAWALS ==============
print("=== PHASE 1: identifying withdrawals ===")
live_ids_by_session = {}
session_ids = sorted(session_by_id.keys())
with ThreadPoolExecutor(max_workers=8) as ex:
    futs = {ex.submit(get_live_ids, sid): sid for sid in session_ids}
    done = 0
    for fut in as_completed(futs):
        sid = futs[fut]
        try:
            live_ids_by_session[sid] = fut.result() or []
        except Exception:
            live_ids_by_session[sid] = []
        done += 1
        if done % 50 == 0:
            print("  fetched live IDs for {}/{}".format(done, len(session_ids)))

withdrawn = []  # (session_id, abstract_id, title)
for sid, s in session_by_id.items():
    live = set(live_ids_by_session.get(sid, []))
    if not live:
        # If we couldn't fetch this session's live page, don't prune (be conservative)
        continue
    new_pres = []
    for p in (s.get("presentations") or []):
        aid_raw = p.get("abstract_id")
        if aid_raw and str(aid_raw).isdigit():
            aid = int(aid_raw)
            if aid not in live:
                withdrawn.append((sid, aid, (p.get("title") or "")[:60]))
                continue
        new_pres.append(p)
    s["presentations"] = new_pres

print("Withdrawals identified and pruned: {}".format(len(withdrawn)))
if withdrawn:
    print("Sample of pruned (first 10):")
    for sid, aid, t in withdrawn[:10]:
        print("  sess={} abs={} -- {}".format(sid, aid, t))

# Save after phase 1
with open(SESS_FILE, "w", encoding="utf-8") as f:
    for s in sessions:
        f.write(json.dumps(s, ensure_ascii=False) + "\n")
print("Saved after phase 1.\n")

# ============== PHASE 2: FETCH MISSING ABSTRACTS ==============
print("=== PHASE 2: fetching missing abstract text ===")
missing = []  # (session_id, abstract_id, presentation_dict_ref)
for s in sessions:
    for p in (s.get("presentations") or []):
        if p.get("title") and not p.get("abstract"):
            aid = p.get("abstract_id")
            if aid and str(aid).isdigit():
                missing.append((s["session_id"], int(aid), p))

print("Presentations needing abstract fetch: {}".format(len(missing)))

# Fetch concurrently
def fetch_and_merge(item):
    sid, aid, p = item
    parsed = parse_app_page(sid, aid)
    if parsed:
        # Merge — only fill in fields that are missing or replace abstract
        for k, v in parsed.items():
            if k == "abstract" or k not in p or not p.get(k):
                p[k] = v
        return True
    return False

filled = 0
fails = 0
with ThreadPoolExecutor(max_workers=8) as ex:
    futs = {ex.submit(fetch_and_merge, item): item for item in missing}
    done = 0
    for fut in as_completed(futs):
        try:
            if fut.result():
                filled += 1
            else:
                fails += 1
        except Exception:
            fails += 1
        done += 1
        if done % 25 == 0:
            print("  processed {}/{} (filled {}, fails {})".format(done, len(missing), filled, fails))
            # Save periodically
            with open(SESS_FILE, "w", encoding="utf-8") as f:
                for s in sessions:
                    f.write(json.dumps(s, ensure_ascii=False) + "\n")

# Final save
with open(SESS_FILE, "w", encoding="utf-8") as f:
    for s in sessions:
        f.write(json.dumps(s, ensure_ascii=False) + "\n")

# Summary
total_after = sum(len([p for p in (s.get("presentations") or []) if p.get("title")]) for s in sessions)
with_abs_after = sum(1 for s in sessions for p in (s.get("presentations") or []) if p.get("title") and p.get("abstract"))
print("\n=== FINAL ===")
print("Total presentations: {}".format(total_after))
print("With abstract text: {}".format(with_abs_after))
print("Missing abstract (still): {}".format(total_after - with_abs_after))
print("Withdrawals pruned: {}".format(len(withdrawn)))
print("Newly filled abstracts: {}".format(filled))
print("Fetch failures: {}".format(fails))

# Save the withdrawal record for posterity
with open(r"C:\Users\erika\Organise\aslo2026\_pruned_withdrawals.json", "w", encoding="utf-8") as f:
    json.dump([{"session_id": sid, "abstract_id": aid, "title": t} for sid, aid, t in withdrawn], f, indent=2)
print("Withdrawal record saved.")
