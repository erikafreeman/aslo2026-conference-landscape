"""
verify_manuscript_claims.py
===========================
Recomputes EVERY quantitative claim in the L&O Bulletin manuscript
"Reading the Room at ASLO-SIL 2026" directly from the raw scraped schedule,
and checks each against the value asserted in the manuscript.

Run:  python verify_manuscript_claims.py
Deps: gender_guesser  (pip install gender-guesser)

Single source of truth: sessions_all.json (JSONL, one session object per line).
Classifier patterns are imported textually from _conference_landscape.py so this
script cannot silently drift from the pipeline that produced the figures.

Every claim below prints as:  [PASS|FAIL|FLAG]  claim  ->  computed (expected)
"""
import json, re, sys
from collections import Counter, defaultdict
from pathlib import Path
from _data_access import data_path, email_of

SRC = Path(__file__).parent
RESULTS = []

def check(label, computed, expected, tol=0):
    """Compare computed vs the value asserted in the manuscript."""
    if expected is None:
        status = "FLAG"; ok = None
    elif isinstance(expected, float) or isinstance(computed, float):
        ok = abs(float(computed) - float(expected)) <= tol
        status = "PASS" if ok else "FAIL"
    else:
        ok = (computed == expected)
        status = "PASS" if ok else "FAIL"
    RESULTS.append((status, label, computed, expected))
    exp = "unreproducible" if expected is None else expected
    print(f"  [{status}] {label:<52s} -> {computed}   (manuscript: {exp})")
    return ok

# ---------------------------------------------------------------- load
sessions = []
with open(data_path(), encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if line:
            try: sessions.append(json.loads(line))
            except json.JSONDecodeError: pass

# Flatten to presentation slots (a slot counts if it carries a title)
slots = []
for s in sessions:
    for p in (s.get("presentations") or []):
        if p.get("title"):
            q = dict(p)
            q["session_code"] = s.get("session_code") or ""
            q["session_name"] = s.get("name") or ""
            q["session_description"] = s.get("description") or ""
            q["date"] = s.get("date")
            slots.append(q)

PLACEHOLDER = "[EMPTY/WITHDRAWN SLOT]"
real = [p for p in slots if p["title"].strip().upper() != PLACEHOLDER]

# Import the classifier patterns textually from the pipeline script
src = (SRC / "_conference_landscape.py").read_text(encoding="utf-8")
def grab(name):
    m = re.search(rf"{name} = \{{\n(.*?)\n\}}\n{name} = \{{k", src, re.S)
    return eval("{" + m.group(1) + "\n}")
COUNTRY_PATS = {k: [re.compile(p, re.I) for p in v] for k, v in grab("COUNTRY_PATS").items()}
FRAMES       = {k: [re.compile(p, re.I) for p in v] for k, v in grab("FRAMES").items()}
METHODS      = {k: [re.compile(p, re.I) for p in v] for k, v in grab("METHODS").items()}

def any_match(pats, text): return any(p.search(text) for p in pats)

# ================================================================ 1. COUNTS
print("\n1. PRESENTATION AND SESSION COUNTS")
check("Scheduled slots with a title", len(slots), 1461)
check("Placeholder [EMPTY/WITHDRAWN SLOT] rows", len(slots) - len(real), 3)
check("Real presentations (the manuscript denominator)", len(real), 1458)
slots = real   # every check below uses REAL presentations, matching the manuscript
check("Session items (rows in the schedule)", len(sessions), 309)

# Distinct sessions: strip a single trailing block letter (SS050A/B/C/P -> SS050)
def base_code(code): return re.sub(r"^([A-Z]{2,3}\d+)[A-Z]$", r"\1", code)
bases = [base_code(s.get("session_code") or "") for s in sessions]
check("Distinct sessions (block suffix collapsed)", len(set(bases)), 143)
multi = {b: c for b, c in Counter(bases).items() if c > 1}
check("Base codes spanning >1 session item", len(multi), 88)
print(f"        e.g. {sorted(multi.items(), key=lambda x: -x[1])[:4]}")

# ================================================================ 2. NO DOUBLE COUNTING
print("\n2. IS ANY ABSTRACT COUNTED TWICE?")
ids = [p.get("abstract_id") for p in slots if p.get("abstract_id")]
check("Slots carrying an abstract_id", len(ids), 1458)
check("Unique abstract_ids", len(set(ids)), 1458)
check("abstract_ids appearing more than once", len(ids) - len(set(ids)), 0)

# ================================================================ 3. ORAL vs POSTER BY DAY
print("\n3. ORAL vs POSTER BY DAY  (poster = session met in room 517C, the poster hall)")
# WARNING / history: this originally used `session_code.endswith('P')`, which is WRONG.
# It misses LBP01 and LBP02 ("Late Breaking Posters", 10 talks each) because their codes
# end in a digit. That rule counted 20 posters as orals and produced 259/258 instead of
# 249/248. The manuscript's original numbers came from the same flawed rule, so the check
# PASSED while ratifying the bug. Room is the sound discriminator: all 85 P-suffixed
# sessions meet in 517C, LBP01/LBP02 also meet in 517C, and no oral session ever uses it.
POSTER_ROOM = "517C"
room_by_code = {s.get("session_code"): s.get("room") for s in sessions}
def norm_day(d):
    """Schedule stores dates in two formats: '14/5/2026' and '2026-05-14'."""
    if not d: return None
    if "/" in d:
        dd, mm, yy = d.split("/"); return f"{int(yy):04d}-{int(mm):02d}-{int(dd):02d}"
    return d
# Guard: the room rule must be a strict superset of the old code rule.
_p_suffix = {s.get("session_code") for s in sessions if (s.get("session_code") or "").rstrip().endswith("P")}
assert all(room_by_code[c] == POSTER_ROOM for c in _p_suffix), "a P-suffixed session sits outside the poster hall"
by_day = defaultdict(lambda: [0, 0])   # day -> [oral, poster]
for p in slots:
    is_poster = room_by_code.get(p["session_code"]) == POSTER_ROOM
    by_day[norm_day(p["date"])][1 if is_poster else 0] += 1
for day in sorted(by_day):
    o, po = by_day[day]
    print(f"        {day}:  oral={o:4d}  poster={po:4d}  total={o+po:4d}")
check("Thu 14 May oral",   by_day["2026-05-14"][0], 248)
check("Thu 14 May poster", by_day["2026-05-14"][1], 239)
check("Fri 15 May oral",   by_day["2026-05-15"][0], 247)
check("Fri 15 May poster", by_day["2026-05-15"][1], 240)
poster_days = sorted(d for d, v in by_day.items() if v[1] > 0)
check("Days with any posters", poster_days, ["2026-05-14", "2026-05-15"])
check("All days sum to the real-presentation total", sum(o + p for o, p in by_day.values()), 1458)

# ================================================================ 4. COUNTRY
print("\n4. COUNTRY  (institution gazetteer first, then institutional ccTLD, generic .edu/.gov last)")
# TWO earlier rules were wrong and BOTH were ratified by this script, because it imported
# the rule from the pipeline it was checking:
#   (a) generic `\.edu`/`\.gov` matched before the country code, so .edu.au / .edu.cn -> USA
#       (56 rows). The script passed 422/29% while Australian universities were "American".
#   (b) resolving from email/English names only made institutions named in Portuguese or
#       Spanish invisible whenever their authors used consumer mail. That undercounted
#       Brazil ~3x while leaving US/Canada fully resolved: a DIRECTIONAL error that
#       inflated the manuscript's own under-representation finding.
# country_resolver_v2 resolves institution first and the mail provider last.
from country_resolver_v2 import resolve as _resolve
countries = Counter()
for p in slots:
    c, _rule = _resolve(p.get("affiliation"), email_of(p))
    if c: countries[c] += 1
detect = sum(countries.values())
N = len(slots)
check("Presentations with a resolved country", detect, 1444)
check("  as % of all", round(100 * detect / N, 1), 99.0, tol=0.2)
check("USA count", countries["USA"], 480)
check("  USA as % of 1,458", round(100 * countries["USA"] / N, 1), 32.9, tol=0.1)
check("Canada count", countries["Canada"], 428)
check("  Canada as % of 1,458", round(100 * countries["Canada"] / N, 1), 29.4, tol=0.1)
check("US + Canada as % of all", round(100 * (countries["USA"] + countries["Canada"]) / N, 1), 62.3, tol=0.2)
check("Brazil count (old rule undercounted it 3x)", countries["Brazil"], 52)
check("  Brazil as % of 1,458", round(100 * countries["Brazil"] / N, 1), 3.6, tol=0.1)
check("Japan count", countries["Japan"], 20)
check("India count (manuscript: present, not absent)", countries["India"], 3)
check("Peru count (manuscript: present)", countries["Peru"], 1)
check("Colombia count (manuscript: present)", countries["Colombia"], 1)
for _c in ["Russia", "Indonesia", "Myanmar"]:
    check(f"{_c} not resolved to any talk", countries[_c], 0)

# ================================================================ 5. GENDER
print("\n5. GENDER  (gender-guesser on the presenter's first name)")
try:
    import gender_guesser.detector as gd
    det = gd.Detector(case_sensitive=False)
    named = [(p.get("presenter") or "").strip() for p in slots]
    named = [n for n in named if n]
    g = Counter(det.get_gender(n.split()[0]) for n in named)
    print(f"        raw buckets: {dict(g)}")
    # NOTE: the base is names the tool RECOGNISED (= named - unknown). It includes the
    # 'andy' (unisex) bucket, which the tool recognised but declined to gender. Those 81
    # sit in the denominator and can enter neither the female nor the male numerator, so
    # the female and male shares deliberately do NOT sum to 100%. Calling this base
    # "classifiable" was a mislabel: 81 of them were never classified to a gender.
    unknown = g["unknown"]
    recognised = len(named) - unknown
    female = g["female"] + g["mostly_female"]
    male = g["male"] + g["mostly_male"]
    unisex = g["andy"]
    check("Presentations with a presenter name", len(named), 1458)
    check("Unrecognised ('unknown')", unknown, 174)
    check("  as % of named", round(100 * unknown / len(named), 1), 11.9, tol=0.2)
    check("Recognised base (named minus unknown)", recognised, 1284)
    check("Female-inferred (female + mostly_female)", female, 682)
    check("  as % of recognised", round(100 * female / recognised, 1), 53.1, tol=0.1)
    check("Male-inferred (male + mostly_male)", male, 521)
    check("  as % of recognised", round(100 * male / recognised, 1), 40.6, tol=0.1)
    check("Unisex ('andy'), recognised but not gendered", unisex, 81)
    check("Base closes: female + male + unisex == recognised", female + male + unisex, recognised)
except ImportError:
    # Must NOT skip silently: an absent dependency previously dropped all 6 gender checks
    # with no FAIL and no FLAG, and the script still exited 0.
    RESULTS.append(("FAIL", "gender checks could not run (gender_guesser not installed)"))
    print("  [FAIL] gender_guesser not installed - gender claims are UNVERIFIED")

# ================================================================ 6. DISCIPLINES (Figure 1)
print("\n6. DISCIPLINARY FRAMES (Figure 1 scope: presentation title + session description)")
FRAMES_SPLIT = dict(FRAMES)
del FRAMES_SPLIT["Lakes / limnology"]
FRAMES_SPLIT["Lakes, ponds & reservoirs"] = [re.compile(p, re.I) for p in [r"\blake\b", r"\bpond\b", r"\breservoir\b"]]
FRAMES_SPLIT["Limnology / inland waters"] = [re.compile(p, re.I) for p in [r"\blimnolog"]]
fc = Counter()
for p in slots:
    text = p["title"] + " " + p["session_description"]
    for f, pats in FRAMES_SPLIT.items():
        if any_match(pats, text): fc[f] += 1
check("Lakes, ponds & reservoirs", fc["Lakes, ponds & reservoirs"], 346)
check("  as % of 1,458", round(100 * fc["Lakes, ponds & reservoirs"] / N, 1), 23.7, tol=0.1)
check("Limnology / inland waters (separate bar)", fc["Limnology / inland waters"], 65)
check("  as % of 1,458", round(100 * fc["Limnology / inland waters"] / N, 1), 4.4, tol=0.1)
check("Microbial ecology", fc["Microbial ecology"], 269)
check("  as % of 1,458", round(100 * fc["Microbial ecology"] / N, 1), 18.4, tol=0.1)
check("Biogeochemistry / C cycle", fc["Biogeochemistry / C cycle"], 246)
check("  as % of 1,458", round(100 * fc["Biogeochemistry / C cycle"] / N, 1), 16.8, tol=0.1)
check("DOM / NOM chemistry", fc["DOM / NOM chemistry"], 47)

# ================================================================ 7. MICROBIAL ∩ DOM
print("\n7. MICROBIAL x DOM OVERLAP  (same scope as Figure 1, so text and figure agree)")
mic, dom = FRAMES["Microbial ecology"], FRAMES["DOM / NOM chemistry"]
n_mic = n_both = 0
for p in slots:
    text = p["title"] + " " + p["session_description"]
    m, d = any_match(mic, text), any_match(dom, text)
    if m: n_mic += 1
    if m and d: n_both += 1
check("Microbial-ecology talks", n_mic, 269)
check("Also carrying a DOM tag", n_both, 14)
check("  overlap as % of microbial talks", round(100 * n_both / n_mic, 1), 5.2, tol=0.2)

# ================================================================ 8. METHOD TAGS
print("\n8. METHOD TAGS  (n values quoted in the text)")
mc = Counter()
for p in slots:
    text = p["title"] + " " + p["session_description"]
    for m, pats in METHODS.items():
        if any_match(pats, text): mc[m] += 1
lt = mc["Long-term monitoring / time series"]; ml = mc["Machine learning / AI"]
check("Long-term monitoring / time series", lt, 131)
check("  as % of 1,458", round(100 * lt / N, 1), 9.0, tol=0.5)
check("Machine learning / AI", ml, 35)
check("  as % of 1,458", round(100 * ml / N, 1), 2.4, tol=0.3)

# ================================================================ 9. EQUITY BUNDLE
print("\n9. EQUITY BUNDLE  (manuscript asserts 58 talks / 14 session items)")
eq = FRAMES["Indigenous / equity / social"]; cs = METHODS["Citizen science / community-based"]
n_eq = n_union = 0
for p in slots:
    text = p["title"] + " " + p["session_description"]
    e, c = any_match(eq, text), any_match(cs, text)
    if e: n_eq += 1
    if e or c: n_union += 1
check("Indigenous/equity/social frame (Figure 1 bar)", n_eq, 28)
check("Union with citizen-science/community method", n_union, 41)
check("Equity union quoted in the manuscript", n_union, 41)
print("        The unreproducible '58' is gone: the text now quotes this union and names the rule in the SI.")

# ================================================================ 10. FIGURE PIPELINE
# A 60-PASS run once coexisted with a Figure 1 that said "1,461 presentations" in its
# title while its caption said 1,458, because Figure 1 was built by an ad-hoc inline
# script that was never committed and so was never regenerated when the denominator
# changed. Counts alone cannot catch that: check the generators themselves.
print("\n10. FIGURE PIPELINE (both figures must be reproducible and use the right denominator)")
for fig in ["make_figure1.py", "make_figure2.py"]:
    exists = (SRC / fig).exists()
    check("%s is committed (figure is reproducible)" % fig, exists, True)
    if not exists:
        continue
    code = (SRC / fig).read_text(encoding="utf-8")
    # Only inspect what the figure RENDERS (title / axis label), not comments or the
    # docstring, which legitimately discuss the 1,461 -> 1,458 correction. An earlier
    # version of this check flagged its own documentation.
    rendered = [ln for ln in code.splitlines()
                if ("set_title(" in ln or "set_xlabel(" in ln) and not ln.lstrip().startswith("#")]
    bad = [ln.strip() for ln in rendered if re.search(r"1[,]?461", ln)]
    check("  %s renders no '1,461' in its title or axis" % fig, len(bad), 0)
    if bad:
        print("        offending render calls: %s" % bad[:2])
check("Figure 1 asserts the 1,458 denominator",
      "== 1458" in (SRC / "make_figure1.py").read_text(encoding="utf-8"), True)

# ================================================================ SUMMARY
print("\n" + "=" * 78)
p_ = sum(1 for r in RESULTS if r[0] == "PASS")
f_ = sum(1 for r in RESULTS if r[0] == "FAIL")
fl = sum(1 for r in RESULTS if r[0] == "FLAG")
print(f"SUMMARY:  {p_} PASS   {f_} FAIL   {fl} FLAG   (of {len(RESULTS)} checks)")
if f_:
    print("\nFAILURES:")
    for st, lab, comp, exp in RESULTS:
        if st == "FAIL": print(f"  - {lab}: computed {comp}, manuscript says {exp}")
print("=" * 78)
sys.exit(1 if f_ else 0)
