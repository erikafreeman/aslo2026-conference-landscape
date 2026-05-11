"""Correctly parse the 7 missing application pages and replace the bad entries."""
import json, re, requests, time
from pathlib import Path
from bs4 import BeautifulSoup

SESS_FILE = Path(r"C:\Users\erika\Organise\aslo2026\sessions_all.json")
sessions = []
with open(SESS_FILE, "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if line:
            sessions.append(json.loads(line))

session_by_id = {s["session_id"]: s for s in sessions}

# Sessions we worked on
TARGETS = {
    2640: 10190,
    2641: 11163,
    2642: 10603,
    2644: 12040,
    2711: 11841,
    2724: 10186,
    2725: 10607,
}

def parse_app_page(session_id, app_id):
    url = "https://aslo.secure-platform.com/2026/solicitations/18/sessiongallery/{}/application/{}".format(session_id, app_id)
    r = requests.get(url, timeout=20)
    if r.status_code != 200:
        return None
    soup = BeautifulSoup(r.text, "html.parser")
    out = {"abstract_id": str(app_id)}

    # Title is in the first <h3>
    h3 = soup.find("h3")
    if h3:
        out["title"] = h3.get_text(strip=True)

    # Parse <strong>Label:</strong> Value patterns
    def grab(label_text):
        for st in soup.find_all("strong"):
            if st.get_text(strip=True).rstrip(":").strip().lower() == label_text.lower():
                # Get following text up to next <strong> or end
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
        # Format usually: "Name, Affiliation (email@...)"
        # Split email out
        em = re.search(r"\(([^)]+@[^)]+)\)", primary)
        if em:
            out["email"] = em.group(1).strip()
            primary = primary[:em.start()].rstrip(" ,").strip()
        # Now split name, affiliation
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

    # Strip BOM-style hidden chars sometimes leading the value
    for k, v in list(out.items()):
        if isinstance(v, str):
            out[k] = v.replace(" ", " ").strip().strip(",").strip()

    return out

# Replace the broken entries
added_or_replaced = 0
for sid, aid in TARGETS.items():
    s = session_by_id[sid]
    pres_list = s.setdefault("presentations", [])
    # Remove any existing entry with this abstract_id
    pres_list[:] = [p for p in pres_list if str(p.get("abstract_id")) != str(aid)]

    parsed = parse_app_page(sid, aid)
    if parsed:
        pres_list.append(parsed)
        added_or_replaced += 1
        print("[{}] {} <- {} ({})".format(sid, parsed.get("title", "")[:60],
                                             parsed.get("presenter", "?"),
                                             parsed.get("affiliation", "?")))
    time.sleep(0.3)

# Rewrite JSONL
with open(SESS_FILE, "w", encoding="utf-8") as f:
    for s in sessions:
        f.write(json.dumps(s, ensure_ascii=False) + "\n")

# Recompute final totals
total = sum(len([p for p in (s.get("presentations") or []) if p.get("title")]) for s in sessions)
print("\nReplaced/added: {}".format(added_or_replaced))
print("Final total presentations with titles: {}".format(total))
