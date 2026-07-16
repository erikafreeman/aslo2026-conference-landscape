"""
ASLO-SIL 2026 conference landscape analysis.
Extracts: community structure, methodologies, keywords, disciplines, themes.
Outputs: structured JSON + narrative MD + supporting charts.
"""
import json, re
from pathlib import Path
from collections import Counter, defaultdict
import matplotlib.pyplot as plt

SRC = Path(r"C:\Users\erika\Organise\aslo2026")
OUT_DIR = Path(r"G:\My Drive\3-WorkAndPurpose\0-ABC_Lab\06-Teaching_Outreach\1-ConferenceTalks\ASLO2026\_ConferenceLandscape")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# --- Load sessions (JSONL) ---
sessions = []
with open(SRC / "sessions_all.json", "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if line:
            try:
                sessions.append(json.loads(line))
            except json.JSONDecodeError:
                pass

print("Sessions: {}".format(len(sessions)))

# --- Flatten presentations ---
presentations = []
for s in sessions:
    for p in (s.get("presentations") or []):
        if p.get("title"):
            p2 = dict(p)
            p2["session_code"] = s.get("session_code")
            p2["session_name"] = s.get("name")
            p2["session_description"] = s.get("description") or ""
            p2["date"] = s.get("date")
            p2["room"] = s.get("room")
            presentations.append(p2)

print("Presentations with titles: {}".format(len(presentations)))

# --- Community structure ---
presenters = []
affiliations = []
emails_domains = []
countries = Counter()  # rough guess from affiliation strings

# Country detection (rough — match common country names + ".XX" emails)
COUNTRY_PATS = {
    "USA": [r"\bUSA\b", r"\bUnited States\b", r", US\b", r"\.edu\b", r"\.gov\b"],
    "Canada": [r"\bCanada\b", r"\bQu[eé]bec\b(?!.*France)", r"Ontario", r"British Columbia", r"\.ca\b"],
    "Germany": [r"\bGermany\b", r"Berlin\b(?! State)", r"M[uü]nchen", r"Bremen", r"Leibniz", r"Helmholtz", r"\.de\b"],
    "UK": [r"\bUK\b", r"\bUnited Kingdom\b", r"\bEngland\b", r"\bScotland\b", r"Cambridge\b", r"Oxford\b", r"\.uk\b"],
    "France": [r"\bFrance\b", r"\bParis\b(?!.*USA)", r"CNRS", r"IFREMER", r"\.fr\b"],
    "China": [r"\bChina\b", r"Beijing", r"Shanghai", r"Nanjing", r"\.cn\b"],
    "Switzerland": [r"\bSwitzerland\b", r"ETH\b", r"EPFL", r"Eawag", r"\.ch\b"],
    "Netherlands": [r"\bNetherlands\b", r"Wageningen", r"\bNIOZ\b", r"\.nl\b"],
    "Spain": [r"\bSpain\b", r"\bMadrid\b", r"Barcelona\b(?!.*Brazil)", r"CSIC", r"\.es\b"],
    "Italy": [r"\bItaly\b", r"\bRoma\b", r"Milano", r"\.it\b"],
    "Australia": [r"\bAustralia\b", r"CSIRO", r"\.au\b"],
    "Brazil": [r"\bBrazil\b", r"S[aã]o Paulo", r"Rio de Janeiro", r"\.br\b"],
    "Japan": [r"\bJapan\b", r"Tokyo", r"\.jp\b"],
    "Sweden": [r"\bSweden\b", r"Uppsala", r"Stockholm", r"\.se\b"],
    "Norway": [r"\bNorway\b", r"\.no\b"],
    "Denmark": [r"\bDenmark\b", r"\.dk\b"],
    "Finland": [r"\bFinland\b", r"Helsinki\b", r"\.fi\b"],
    "Austria": [r"\bAustria\b", r"Vienna", r"WasserCluster", r"\.at\b"],
    "Belgium": [r"\bBelgium\b", r"\bGhent\b", r"\.be\b"],
    "Israel": [r"\bIsrael\b", r"\.il\b"],
    "South Africa": [r"South Africa", r"\.za\b"],
    "Korea": [r"\bKorea\b", r"\.kr\b"],
    "Mexico": [r"\bMexico\b", r"UNAM", r"\.mx\b"],
    "Argentina": [r"\bArgentina\b", r"\.ar\b"],
    "Chile": [r"\bChile\b", r"\.cl\b"],
    "Poland": [r"\bPoland\b", r"\.pl\b"],
    "Turkey": [r"\bTurkey\b", r"T[uü]rkiye", r"\.tr\b"],
    "India": [r"\bIndia\b", r"\.in\b"],
    "New Zealand": [r"New Zealand", r"\.nz\b"],
    "Portugal": [r"\bPortugal\b", r"Lisbon", r"\.pt\b"],
    "Estonia": [r"\bEstonia\b", r"\.ee\b"],
    "Czech": [r"\bCzech\b", r"\.cz\b"],
    "Hungary": [r"\bHungary\b", r"\.hu\b"],
    "Russia": [r"\bRussia\b", r"Moscow", r"\.ru\b"],
}
COUNTRY_PATS = {k: [re.compile(p, re.I) for p in pats] for k, pats in COUNTRY_PATS.items()}

def guess_country(text):
    for c, pats in COUNTRY_PATS.items():
        for p in pats:
            if p.search(text or ""):
                return c
    return None

institutional_strings = []
for p in presentations:
    aff = p.get("affiliation") or ""
    email = p.get("email") or ""
    presenters.append(p.get("presenter") or "")
    affiliations.append(aff)
    if email and "@" in email:
        emails_domains.append(email.rsplit("@", 1)[-1].lower())
    c = guess_country(aff + " " + email)
    if c:
        countries[c] += 1
    institutional_strings.append(aff)

# Top institutions: split on commas and aggregate the FIRST chunk (institution name)
inst_first_chunk = Counter()
for aff in affiliations:
    if not aff: continue
    first = aff.split(",")[0].strip()
    if first:
        # Light cleanup
        first = re.sub(r"\s+", " ", first)
        inst_first_chunk[first] += 1

# Also try organizer affiliations
organizer_insts = Counter()
for s in sessions:
    lead = s.get("lead_organizer") or ""
    if "," in lead:
        # Format: "Name, Institution (email)"
        # Strip email parens then split on first comma
        no_email = re.sub(r"\s*\([^)]*@[^)]*\)\s*$", "", lead).strip()
        if "," in no_email:
            inst = no_email.split(",", 1)[1].strip()
            organizer_insts[inst] += 1
    for co in (s.get("co_organizers") or []):
        if isinstance(co, dict):
            co = co.get("name") or co.get("affiliation") or ""
        if not isinstance(co, str):
            continue
        no_email = re.sub(r"\s*\([^)]*@[^)]*\)\s*$", "", co).strip()
        if "," in no_email:
            inst = no_email.split(",", 1)[1].strip()
            organizer_insts[inst] += 1

# --- Keyword extraction from session names ---
SESSION_STOPWORDS = set("""a an and or but the of in on at for to from with by as is are was were be been being
have has had do does did this that these those it its their there here we you they our your his her them him
he she which what who whom where when why how all also any not no nor through across between during among
into onto under over within without around about than then so such some other many much more most less few
both either neither each every same different new old can may might shall should will would could ought
ASLO SIL session symposium oral poster talk meeting conference""".split())

def tokenize(text):
    if not text: return []
    text = re.sub(r"[–—]", " ", text)
    text = re.sub(r"[^a-zA-Z\-]+", " ", text)
    return [w.lower() for w in text.split() if len(w) > 2 and w.lower() not in SESSION_STOPWORDS]

session_word_freq = Counter()
for s in sessions:
    for w in tokenize(s.get("name", "")):
        session_word_freq[w] += 1

# Bigrams in session names
def bigrams(text):
    toks = tokenize(text)
    return [" ".join(toks[i:i+2]) for i in range(len(toks)-1)]

session_bigram_freq = Counter()
for s in sessions:
    for bg in bigrams(s.get("name", "")):
        session_bigram_freq[bg] += 1

# --- Methodology / approach keyword detection ---
METHODS = {
    "Genomics / eDNA / -omics": [r"\beDNA\b", r"\bmetagenomic", r"\b16S\b", r"\bgenomic", r"\btranscriptomic", r"\bproteomic", r"\bmetabolomic", r"\bsequencing\b", r"\bamplicon", r"\bphylogenetic", r"\bgenome\b", r"\bsingle[\s\-]cell"],
    "FT-ICR / UHR-MS / chemical fingerprinting": [r"\bFT[\s\-]?ICR\b", r"\bFTICR\b", r"\bultrahigh[\s\-]?resolution", r"\bultra[\s\-]?high[\s\-]?resolution", r"\bOrbitrap\b", r"\bvan Krevelen", r"\bmolecular formula", r"\bmolecular fingerprint", r"\bchemodiversity\b"],
    "Stable isotopes": [r"\bisotop\b", r"\bisotopic", r"\bd13C\b", r"\bd15N\b", r"\b18O\b", r"\bradiocarbon", r"\b14C\b", r"\btracer experiment"],
    "Modelling / simulation": [r"\bmodel[\s\-]ing\b", r"\bmodel\b", r"\bsimulation\b", r"\bnumerical\b", r"\bBayesian\b", r"\bAgent[\s\-]based", r"\bmechanistic", r"\bprocess[\s\-]based\b", r"\bensemble model"],
    "Machine learning / AI": [r"\bmachine learning\b", r"\bdeep learning\b", r"\bneural network\b", r"\bAI\b(?!.*intelligence officer)", r"\brandom forest\b", r"\bartificial intelligence", r"\bdata[\s\-]driven\b", r"\bclassifier\b", r"\bgradient boost"],
    "Remote sensing / satellite": [r"\bremote sensing\b", r"\bsatellite\b", r"\bLandsat\b", r"\bSentinel[\s\-]\d", r"\bMODIS\b", r"\bdrone\b", r"\bUAV\b", r"\bhyperspectral\b", r"\baerial imag"],
    "Long-term monitoring / time series": [r"\blong[\s\-]term\b", r"\btime[\s\-]series\b", r"\bdecadal\b", r"\bmulti[\s\-]year\b", r"\bmonitoring\b", r"\btrend analysis\b", r"\bGLEON\b", r"\bLTER\b"],
    "Experimental / mesocosm": [r"\bmesocosm\b", r"\bexperimental\b", r"\bmanipul", r"\bincubation\b", r"\bbioassay\b", r"\bchamber\b", r"\bflume\b", r"\bin situ experiment"],
    "Optical / fluorescence": [r"\bfluorescen", r"\bPARAFAC\b", r"\bCDOM\b", r"\bFDOM\b", r"\babsorbance\b", r"\boptical propert"],
    "Network / co-occurrence analysis": [r"\bnetwork\b", r"\bco[\s\-]occurrence\b", r"\bbipartite\b", r"\bgraph\b", r"\bcommunity assembly\b"],
    "Tracer / mass-balance": [r"\bmass balance\b", r"\bbudget\b", r"\bflux measurement", r"\bdye tracer", r"\beddy covariance\b"],
    "Citizen science / community-based": [r"\bcitizen science\b", r"\bcommunity[\s\-]based\b", r"\bparticipatory\b", r"\bindigenous knowledge\b", r"\btraditional ecological"],
    "Paleo / sediment cores": [r"\bpaleo\b", r"\bsediment core\b", r"\bcore record\b", r"\bdiatom record\b", r"\bvarve\b"],
    "Hydrology / hydrodynamic": [r"\bhydrolog", r"\bhydrodynam", r"\bdischarge\b", r"\bflow regime\b", r"\bcatchment\b", r"\bwatershed\b"],
}
METHODS = {k: [re.compile(p, re.I) for p in pats] for k, pats in METHODS.items()}

def detect_methods(text):
    if not text: return set()
    found = set()
    for m, pats in METHODS.items():
        for p in pats:
            if p.search(text):
                found.add(m)
                break
    return found

# --- Disciplinary / conceptual frame detection ---
FRAMES = {
    "Biogeochemistry / C cycle": [r"\bbiogeochem", r"\bcarbon cycle\b", r"\bcarbon flux\b", r"\bgreenhouse gas", r"\bCO2\b", r"\bmethane\b", r"\bN2O\b", r"\bnutrient cycl"],
    "Microbial ecology": [r"\bmicrobial\b", r"\bmicrobiome\b", r"\bbacteri", r"\barchaea\b", r"\bvirome\b", r"\bphytoplankton\b", r"\bzooplankton\b", r"\bplankton\b"],
    "Community / metacommunity ecology": [r"\bcommunity ecology\b", r"\bmetacommunity\b", r"\bcommunity assembly\b", r"\bcommunity structure\b", r"\bbeta diversity\b", r"\balpha diversity\b"],
    "Food web / trophic": [r"\bfood web\b", r"\btrophic\b", r"\bpredator[\s\-]prey", r"\bfish.*diet", r"\bfeeding ecology"],
    "Functional ecology / traits": [r"\bfunctional ecology\b", r"\btrait[\s\-]based\b", r"\bfunctional diversity\b", r"\bfunctional trait", r"\bfunctional group"],
    "Biodiversity / biogeography": [r"\bbiodiversity\b", r"\bbiogeograph", r"\bspecies richness\b", r"\bendemism\b", r"\binvasive species\b"],
    "Climate change / global change": [r"\bclimate change\b", r"\bglobal change\b", r"\bwarming\b", r"\bdrought\b", r"\bheatwave\b", r"\bextreme event"],
    "Eutrophication / nutrient pollution": [r"\beutrophicat", r"\bnitrogen loading\b", r"\bphosphorus loading\b", r"\balgal bloom\b", r"\bharmful algal"],
    "Pollution / contaminants": [r"\bpollution\b", r"\bcontaminant\b", r"\bmicroplastic\b", r"\bpharmaceutical\b", r"\bPFAS\b", r"\bpesticide\b", r"\bheavy metal\b"],
    "DOM / NOM chemistry": [r"\bdissolved organic\b", r"\bDOM\b", r"\bnatural organic\b", r"\bNOM\b", r"\bhumic\b", r"\bfulvic\b"],
    "Carbon export / blue carbon": [r"\bblue carbon\b", r"\bcarbon export\b", r"\bcarbon sequestrat", r"\bsoil carbon\b", r"\bcarbon stor"],
    "Ecosystem function / services": [r"\becosystem function\b", r"\becosystem service\b", r"\bsecondary production\b", r"\bdecomposition\b", r"\brespiration\b"],
    "Conservation / restoration": [r"\bconservation\b", r"\brestoration\b", r"\brewilding\b", r"\bprotected area\b"],
    "Fisheries / aquaculture": [r"\bfisher", r"\baquacultur", r"\bstock assess"],
    "Cryosphere / ice": [r"\bice\b(?! cream)", r"\bglacial\b", r"\bpermafrost\b", r"\bsnowpack\b"],
    "Estuarine / coastal": [r"\bestuar", r"\bcoastal\b", r"\bmangrove\b", r"\bsalt marsh"],
    "Marine / oceanography": [r"\bmarine\b", r"\bocean\b", r"\bpelagic\b", r"\bseawater\b", r"\babyssal\b"],
    "Lakes / limnology": [r"\blake\b", r"\blimnolog", r"\bpond\b", r"\breservoir\b"],
    "Rivers / streams": [r"\briver\b", r"\bstream\b", r"\bfluvial\b", r"\bheadwater\b", r"\bdrainage\b"],
    "Wetlands / peatlands": [r"\bwetland\b", r"\bpeatland\b", r"\bbog\b", r"\bmarsh\b(?!.*salt)"],
    "Groundwater / aquifer": [r"\bgroundwater\b", r"\baquifer\b", r"\bhyporheic\b"],
    "Indigenous / equity / social": [r"\bindigenous\b", r"\bequity\b", r"\bjustice\b", r"\bdecoloniz", r"\bdiversity equity\b", r"\binclusion\b", r"\bDEI\b", r"\bcommunity-led", r"\btraditional knowledge"],
    "Disturbance / fire / land use": [r"\bwildfire\b", r"\bdeforestation\b", r"\blogging\b", r"\bland[\s\-]use\b", r"\burbanization\b", r"\bagricultural runoff"],
    "Cross-ecosystem / land-water": [r"\bland[\s\-]water\b", r"\bterrestrial[\s\-]aquatic\b", r"\bcross[\s\-]ecosystem\b", r"\baquatic[\s\-]terrestrial\b"],
}
FRAMES = {k: [re.compile(p, re.I) for p in pats] for k, pats in FRAMES.items()}

def detect_frames(text):
    if not text: return set()
    found = set()
    for f, pats in FRAMES.items():
        for p in pats:
            if p.search(text):
                found.add(f)
                break
    return found

# Tag each session and each presentation
session_methods = defaultdict(set)
session_frames = defaultdict(set)
for s in sessions:
    text = (s.get("name", "") + " " + s.get("description", ""))
    session_methods[s["session_code"]] = detect_methods(text)
    session_frames[s["session_code"]] = detect_frames(text)

pres_methods = []
pres_frames = []
for p in presentations:
    text = (p.get("title", "") + " " + p.get("session_description", ""))
    pres_methods.append(detect_methods(text))
    pres_frames.append(detect_frames(text))

# Method totals (session-level, multi-label)
method_session_counts = Counter()
for s_code, ms in session_methods.items():
    for m in ms:
        method_session_counts[m] += 1

# Frame totals (session-level, multi-label)
frame_session_counts = Counter()
for s_code, fs in session_frames.items():
    for f in fs:
        frame_session_counts[f] += 1

# Method totals (presentation-level)
method_pres_counts = Counter()
for ms in pres_methods:
    for m in ms:
        method_pres_counts[m] += 1
frame_pres_counts = Counter()
for fs in pres_frames:
    for f in fs:
        frame_pres_counts[f] += 1

# --- Output structured JSON ---
total_sess = len(sessions)
total_pres = len(presentations)
n_unique_presenters = len(set(p for p in presenters if p))
n_unique_inst_chunks = len(inst_first_chunk)

data = {
    "queried": "2026-05-11",
    "conference": "ASLO-SIL 2026 Joint Meeting (Quebec City, 12-16 May 2026)",
    "community_structure": {
        "total_sessions": total_sess,
        "total_presentations_with_titles": total_pres,
        "n_unique_presenters": n_unique_presenters,
        "n_distinct_institutional_strings": n_unique_inst_chunks,
        "top_30_institutions": dict(inst_first_chunk.most_common(30)),
        "top_organizing_institutions": dict(organizer_insts.most_common(20)),
        "top_25_countries": dict(countries.most_common(25)),
        "note_on_country_detection": "Country detection is keyword-based on affiliation + email TLD. Coverage ~70-80%. Some countries (e.g. China) caught via city names + .cn emails; smaller countries may be undercounted.",
    },
    "session_keywords": {
        "top_60_words": dict(session_word_freq.most_common(60)),
        "top_30_bigrams": dict(session_bigram_freq.most_common(30)),
    },
    "methods_distribution": {
        "session_level": dict(method_session_counts.most_common()),
        "presentation_level": dict(method_pres_counts.most_common()),
        "n_sessions_with_any_method_tag": sum(1 for s_code, ms in session_methods.items() if ms),
        "n_presentations_with_any_method_tag": sum(1 for ms in pres_methods if ms),
    },
    "frames_distribution": {
        "session_level": dict(frame_session_counts.most_common()),
        "presentation_level": dict(frame_pres_counts.most_common()),
    },
}

with open(OUT_DIR / "aslo2026_landscape_data.json", "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
print("Saved data JSON: {}".format(OUT_DIR / "aslo2026_landscape_data.json"))

# --- Print summary tables for console + later MD ---
print("\n=== COMMUNITY STRUCTURE ===")
print("Sessions: {} | Presentations with titles: {}".format(total_sess, total_pres))
print("Unique presenters: {} | Distinct institutional strings: {}".format(n_unique_presenters, n_unique_inst_chunks))

print("\nTop 15 countries:")
for c, n in countries.most_common(15):
    print("  {:<20s} {:>4d}".format(c, n))

print("\nTop 15 organizing institutions:")
for inst, n in organizer_insts.most_common(15):
    print("  {:<55s} {:>3d}".format(inst[:55], n))

print("\nTop 15 institutions by presentation count:")
for inst, n in inst_first_chunk.most_common(15):
    print("  {:<55s} {:>3d}".format(inst[:55], n))

print("\n=== METHODS (session-level, multi-label) ===")
for m, n in method_session_counts.most_common():
    pct = 100.0 * n / total_sess
    print("  {:<48s} {:>3d} sessions ({:.1f}%)".format(m, n, pct))

print("\n=== FRAMES / DISCIPLINES (session-level) ===")
for f_name, n in frame_session_counts.most_common():
    pct = 100.0 * n / total_sess
    print("  {:<48s} {:>3d} sessions ({:.1f}%)".format(f_name, n, pct))

print("\n=== TOP 25 SESSION-NAME WORDS ===")
for w, n in session_word_freq.most_common(25):
    print("  {:<25s} {:>3d}".format(w, n))

print("\n=== TOP 15 SESSION-NAME BIGRAMS ===")
for bg, n in session_bigram_freq.most_common(15):
    print("  {:<35s} {:>3d}".format(bg, n))

# --- Charts ---
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11,
                     "axes.edgecolor": "#4a5568", "axes.labelcolor": "#1a2332",
                     "xtick.color": "#4a5568", "ytick.color": "#4a5568"})
BG = "#f7f5f0"; INK = "#1a2332"; INK_SOFT = "#4a5568"; ACCENT = "#2d5f5d"; HI = "#c44e3a"

# Chart 1: methods horizontal bar
items = method_session_counts.most_common()
labels = [k for k, v in items]
values = [v for k, v in items]
fig, ax = plt.subplots(figsize=(11, 7), facecolor=BG)
ax.set_facecolor(BG)
y_pos = list(range(len(labels)))[::-1]
bars = ax.barh(y_pos, values, color=ACCENT, height=0.7, edgecolor="none")
for yp, v in zip(y_pos, values):
    pct = 100.0 * v / total_sess
    ax.text(v + 1.5, yp, "{} ({:.0f}%)".format(v, pct), va="center", color=INK_SOFT, fontsize=10)
ax.set_yticks(y_pos)
ax.set_yticklabels(labels, fontsize=11, color=INK)
ax.set_xlabel("Sessions (of {}) — multi-label".format(total_sess), fontsize=11, color=INK_SOFT)
ax.set_title("ASLO-SIL 2026 — methods/approaches by session", fontsize=13, color=INK, loc="left", weight="bold", pad=15)
ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
ax.set_xlim(0, max(values) * 1.18)
ax.grid(axis="x", linestyle=":", color="#c8c4ba", alpha=0.5)
plt.tight_layout()
plt.savefig(OUT_DIR / "aslo2026_methods.png", dpi=200, facecolor=BG, bbox_inches="tight")
plt.close()
print("Saved methods chart")

# Chart 2: frames/disciplines
items = frame_session_counts.most_common()
labels = [k for k, v in items]
values = [v for k, v in items]
fig, ax = plt.subplots(figsize=(11, 9), facecolor=BG)
ax.set_facecolor(BG)
y_pos = list(range(len(labels)))[::-1]
ax.barh(y_pos, values, color="#3d7a76", height=0.7, edgecolor="none")
for yp, v in zip(y_pos, values):
    pct = 100.0 * v / total_sess
    ax.text(v + 1.5, yp, "{} ({:.0f}%)".format(v, pct), va="center", color=INK_SOFT, fontsize=10)
ax.set_yticks(y_pos)
ax.set_yticklabels(labels, fontsize=11, color=INK)
ax.set_xlabel("Sessions (of {}) — multi-label".format(total_sess), fontsize=11, color=INK_SOFT)
ax.set_title("ASLO-SIL 2026 — disciplinary frames by session", fontsize=13, color=INK, loc="left", weight="bold", pad=15)
ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
ax.set_xlim(0, max(values) * 1.18)
ax.grid(axis="x", linestyle=":", color="#c8c4ba", alpha=0.5)
plt.tight_layout()
plt.savefig(OUT_DIR / "aslo2026_frames.png", dpi=200, facecolor=BG, bbox_inches="tight")
plt.close()
print("Saved frames chart")

# Chart 3: top 20 countries
items = countries.most_common(20)
labels = [c for c, n in items]
values = [n for c, n in items]
fig, ax = plt.subplots(figsize=(11, 7), facecolor=BG)
ax.set_facecolor(BG)
y_pos = list(range(len(labels)))[::-1]
ax.barh(y_pos, values, color="#1f4747", height=0.7, edgecolor="none")
for yp, v in zip(y_pos, values):
    ax.text(v + 4, yp, str(v), va="center", color=INK_SOFT, fontsize=10)
ax.set_yticks(y_pos)
ax.set_yticklabels(labels, fontsize=11, color=INK)
ax.set_xlabel("Presentations (rough keyword-based detection on affiliation/email)", fontsize=10, color=INK_SOFT)
ax.set_title("ASLO-SIL 2026 — presenter countries (top 20)", fontsize=13, color=INK, loc="left", weight="bold", pad=15)
ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
ax.set_xlim(0, max(values) * 1.15)
ax.grid(axis="x", linestyle=":", color="#c8c4ba", alpha=0.5)
plt.tight_layout()
plt.savefig(OUT_DIR / "aslo2026_countries.png", dpi=200, facecolor=BG, bbox_inches="tight")
plt.close()
print("Saved countries chart")

print("\nDone. Output dir: {}".format(OUT_DIR))
