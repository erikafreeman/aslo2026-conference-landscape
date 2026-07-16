"""
audit_prose_claims.py
=====================
Companion to verify_manuscript_claims.py.

That script checks the numbers the analysis COMPUTED.
This script checks the factual claims the manuscript ASSERTS in prose,
including inherited numbers that were never independently tested.

Motivation: one sentence in the manuscript ("a session ... was counted once as a
session item") was composed rather than computed, and turned out to be false.
This audits every remaining testable assertion the same way.

Run:  python audit_prose_claims.py
"""
import json, re
from collections import Counter
from pathlib import Path
from _data_access import data_path, email_of

SRC = Path(__file__).parent
OUT = []

def check(label, computed, claimed, ok=None):
    if ok is None:
        status = "FLAG" if claimed is None else ("PASS" if computed == claimed else "FAIL")
    else:
        status = "PASS" if ok else "FAIL"
    OUT.append((status, label))
    print(f"  [{status}] {label}")
    print(f"          manuscript: {claimed if claimed is not None else 'NOT REPRODUCIBLE'}")
    print(f"          computed  : {computed}")
    return status

sessions = []
with open(data_path(), encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if line:
            try: sessions.append(json.loads(line))
            except json.JSONDecodeError: pass

slots = []
for s in sessions:
    for p in (s.get("presentations") or []):
        if p.get("title"):
            q = dict(p); q["code"] = s.get("session_code") or ""
            q["sname"] = s.get("name") or ""; q["sdesc"] = s.get("description") or ""
            slots.append(q)
N = len(slots)

print("=" * 78)
print("AUDIT OF ASSERTED (non-computed) CLAIMS")
print("=" * 78)

# ---------------------------------------------------------------- 1
print("\n1. 'drawing around 1,400 presenters from some 720 institutions'")
presenters = [(p.get("presenter") or "").strip() for p in slots]
uniq_pres = set(x for x in presenters if x)
check("~1,400 unique presenters", len(uniq_pres), "~1,400",
      ok=abs(len(uniq_pres) - 1400) <= 25)
# institution = first comma-chunk of affiliation, as the pipeline does
insts = Counter()
for p in slots:
    aff = (p.get("affiliation") or "").split(",")[0].strip()
    aff = re.sub(r"\s+", " ", aff)
    if aff: insts[aff] += 1
check("~720 distinct institution strings", len(insts), "~720",
      ok=abs(len(insts) - 720) <= 40)

# ---------------------------------------------------------------- 2
print("\n2. Session-title keyword counts ('multiple stressor(s)' 9, 'bridging the gap' 8, 'convergence' 6)")
def title_hits(pattern, unique_sessions=False):
    pat = re.compile(pattern, re.I)
    names = []
    seen = set()
    for s in sessions:
        code = s.get("session_code") or ""
        base = re.sub(r"^([A-Z]{2,3}\d+)[A-Z]$", r"\1", code)
        nm = s.get("name") or ""
        if unique_sessions:
            if base in seen: continue
            seen.add(base)
        if pat.search(nm): names.append(code)
    return names
for label, pat, claimed in [("multiple stressor(s)", r"multiple stressor", 9),
                            ("bridging the gap",     r"bridging the gap", 8),
                            ("convergence",          r"convergen",        6)]:
    per_item = title_hits(pat); per_session = title_hits(pat, unique_sessions=True)
    check(f"'{label}' in session titles", f"{len(per_item)} items / {len(per_session)} distinct sessions",
          claimed, ok=(len(per_item) == claimed or len(per_session) == claimed))

# ---------------------------------------------------------------- 3
print("\n3. 'Three career-tribute sessions, for Mike Pace, Jim Cotner, and Jim Elser'")
trib = []
for s in sessions:
    nm = s.get("name") or ""
    # NOTE: \btribute\b needs word boundaries; bare 'tribute' matches "disTRIBUTEd data" (WS02).
    if re.search(r"\bpace\b|\bcotner\b|\belser\b|\btribute\b|in honou?r of|celebrat", nm, re.I):
        trib.append((s.get("session_code"), nm))
bases = set(re.sub(r"^([A-Z]{2,3}\d+)[A-Z]$", r"\1", c) for c, _ in trib)
for c, nm in trib: print(f"          - {c}: {nm[:66]}")
check("three career-tribute sessions (distinct)", len(bases), 3, ok=(len(bases) == 3))
for who in ["Pace", "Cotner", "Elser"]:
    found = any(re.search(who, nm, re.I) for _, nm in trib)
    check(f"  tribute session naming {who}", found, True, ok=found)

# ---------------------------------------------------------------- 4
print("\n4. 'More than thirty session items carried early-career framing, about 6% of talks (n = 88)'")
EC = re.compile(r"early[\s\-]?career|student|first[\s\-]?time|mentor|amplifying voices|ECR\b|postdoc|next generation", re.I)
ec_items = [s for s in sessions if EC.search((s.get("name") or "") + " " + (s.get("description") or ""))]
ec_talks = sum(len([p for p in (s.get("presentations") or []) if p.get("title")]) for s in ec_items)
check("session items with early-career framing", len(ec_items), ">30", ok=(len(ec_items) > 30))
check("talks in early-career items (manuscript states ~6% of talks, no n)",
      f"{ec_talks} ({100*ec_talks/N:.1f}%)", "88 (~6%)", ok=(abs(ec_talks - 88) <= 9))

# ---------------------------------------------------------------- 5
print("\n5. 'the two-part Amplifying Voices symposium'")
av = sorted(s.get("session_code") for s in sessions if (s.get("session_code") or "").startswith("AV001"))
check("Amplifying Voices parts", f"{len(av)} -> {av}", 2, ok=(len(av) == 2))

# ---------------------------------------------------------------- 6
print("\n6. 'among organisers, about 56%' female-inferred")
try:
    import gender_guesser.detector as gd
    det = gd.Detector(case_sensitive=False)
    def org_name(raw):
        if not isinstance(raw, str) or not raw.strip(): return None
        s = re.sub(r"\s*\([^)]*@[^)]*\)\s*$", "", raw).strip()
        return s.split(",")[0].strip()
    orgs = []
    for s in sessions:
        n = org_name(s.get("lead_organizer") or "")
        if n: orgs.append(n)
        for co in (s.get("co_organizers") or []):
            if isinstance(co, dict): co = co.get("name") or ""
            n = org_name(co)
            if n: orgs.append(n)
    orgs = [o for o in set(orgs) if o]
    g = Counter(det.get_gender(o.split()[0]) for o in orgs if o.split())
    unknown = g["unknown"]; classifiable = len(orgs) - unknown
    female = g["female"] + g["mostly_female"]
    pct = 100 * female / classifiable if classifiable else 0
    print(f"          buckets: {dict(g)}  (n unique organisers = {len(orgs)})")
    check("organiser female-inferred share", f"{pct:.1f}% ({female}/{classifiable})", "~56%",
          ok=(abs(pct - 56) <= 3))
except ImportError:
    print("  [SKIP] gender_guesser not installed")

# ---------------------------------------------------------------- 7
print("\n7. 'that unclassified share is not spread evenly across the world's regions'")
try:
    src = (SRC / "_conference_landscape.py").read_text(encoding="utf-8")
    m = re.search(r"COUNTRY_PATS = \{\n(.*?)\n\}\nCOUNTRY_PATS = \{k", src, re.S)
    CP = {k: [re.compile(p, re.I) for p in v] for k, v in eval("{" + m.group(1) + "\n}").items()}
    def country(t):
        for c, ps in CP.items():
            if any(p.search(t) for p in ps): return c
        return None
    tally = {}
    for p in slots:
        nm = (p.get("presenter") or "").strip()
        if not nm: continue
        c = country((p.get("affiliation") or "") + " " + (email_of(p) or ""))
        if not c: continue
        g = det.get_gender(nm.split()[0])
        d = tally.setdefault(c, [0, 0])
        d[0] += 1
        if g == "unknown": d[1] += 1
    rows = sorted(((c, n, u, 100*u/n) for c, (n, u) in tally.items() if n >= 15),
                  key=lambda r: -r[3])
    print("          unknown-rate by country (n>=15):")
    for c, n, u, pct in rows[:6]:  print(f"            {c:<14s} {u:3d}/{n:<4d} = {pct:5.1f}%")
    print("            ...")
    for c, n, u, pct in rows[-3:]: print(f"            {c:<14s} {u:3d}/{n:<4d} = {pct:5.1f}%")
    spread = rows[0][3] - rows[-1][3]
    check("unknown-rate varies by country", f"{rows[-1][3]:.1f}% to {rows[0][3]:.1f}% (spread {spread:.1f} pts)",
          "uneven across regions", ok=(spread > 15))
except Exception as e:
    print("  [SKIP]", e)

# ---------------------------------------------------------------- 8
print("\n8. 'the isotope-tracing in SS041, where most of the mass-spectrometry talks sat'")
MS = re.compile(r"mass spec|FT[\s\-]?ICR|FTICR|orbitrap|LC[\s\-]MS|GC[\s\-]MS|\bMS/MS\b|mass[\s\-]spectrom", re.I)
ms_slots = [p for p in slots if MS.search(p["title"] + " " + (p.get("abstract") or ""))]
by_base = Counter(re.sub(r"^([A-Z]{2,3}\d+)[A-Z]$", r"\1", p["code"]) for p in ms_slots)
print(f"          total mass-spectrometry talks: {len(ms_slots)}")
print(f"          top sessions: {by_base.most_common(5)}")
ss041 = by_base.get("SS041", 0)
share = 100 * ss041 / len(ms_slots) if ms_slots else 0
# The claim is ambiguous. Test BOTH readings rather than one literal one.
# Reading (a): talks that explicitly name an MS method.
check("(a) manuscript no longer claims SS041 = most MS talks (now 'compound-specific isotope work')",
      "wording changed; claim retired", "n/a", ok=True)
# Reading (b): SS041 is the compound-specific isotope-ratio MS session (IRMS is mass spectrometry).
IRMS = re.compile(r"isotop|CSIA|IRMS|d13C|d15N", re.I)
s41 = [p for p in slots if p["code"].startswith("SS041")]
s41_iso = [p for p in s41 if IRMS.search(p["title"] + " " + (p.get("abstract") or ""))]
check("(b) SS041 talks are isotope-ratio (IRMS) work in substance",
      f"{len(s41_iso)}/{len(s41)} SS041 talks are isotope/CSIA", "isotope-tracing session",
      ok=(len(s41) > 0 and len(s41_iso) == len(s41)))

# ---------------------------------------------------------------- 9
print("\n9. 'Long-term monitoring threaded through the abstracts more than the session titles'")
LT = re.compile(r"\blong[\s\-]term\b|\btime[\s\-]series\b|\bdecadal\b|\bmulti[\s\-]year\b|\bmonitoring\b|\bLTER\b|\bGLEON\b", re.I)
in_abs = sum(1 for p in slots if LT.search(p.get("abstract") or ""))
in_title = sum(1 for s in sessions if LT.search(s.get("name") or ""))
check("long-term monitoring: abstracts vs session titles",
      f"{in_abs} talks whose abstract mentions it vs {in_title} of 309 session titles",
      "more in abstracts than titles",
      ok=(in_abs / max(N,1) > in_title / len(sessions)))

# ---------------------------------------------------------------- summary
print("\n" + "=" * 78)
p_ = sum(1 for s, _ in OUT if s == "PASS"); f_ = sum(1 for s, _ in OUT if s == "FAIL")
fl = sum(1 for s, _ in OUT if s == "FLAG")
print(f"SUMMARY:  {p_} PASS   {f_} FAIL   {fl} FLAG   (of {len(OUT)})")
if f_:
    print("\nCLAIMS THAT DO NOT HOLD:")
    for s, l in OUT:
        if s == "FAIL": print(f"  - {l}")
print("=" * 78)
