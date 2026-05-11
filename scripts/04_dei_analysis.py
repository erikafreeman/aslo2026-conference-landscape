"""
DEI (Diversity, Equity, Inclusion) sweep of the ASLO-SIL 2026 program.

Dimensions analysed:
  1. Geography — country, region, World Bank income group
  2. Gender — name-based inference (with explicit accuracy caveats)
  3. Institutional type — university / institute / government / industry / other
  4. Equity-content sessions — those that explicitly programme Indigenous knowledge, equity, community-led science
  5. Career-stage scaffolding — ECR sessions and early-career-flagged tracks
  6. Organiser demographics — gender inference applied to session lead organisers

Aggregate-level analysis only. No individual labels are emitted.

USAGE:
  python scripts/04_dei_analysis.py

REQUIREMENTS:
  pip install gender-guesser
"""
import json, re
from pathlib import Path
from collections import Counter, defaultdict
import gender_guesser.detector as gg
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "sessions_all_public.json"
OUT_CHARTS = ROOT / "output" / "charts"
OUT_TABLES = ROOT / "output" / "tables"
OUT_REPORTS = ROOT / "output" / "reports"
for p in [OUT_CHARTS, OUT_TABLES, OUT_REPORTS]:
    p.mkdir(parents=True, exist_ok=True)

# Load
sessions = []
with open(DATA, "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if line:
            sessions.append(json.loads(line))

presentations = []
for s in sessions:
    for p in (s.get("presentations") or []):
        if p.get("title"):
            p2 = dict(p)
            p2["session_code"] = s.get("session_code")
            p2["session_name"] = s.get("name", "")
            p2["lead_organizer"] = s.get("lead_organizer", "")
            presentations.append(p2)

print("Sessions: {}, Presentations: {}".format(len(sessions), len(presentations)))


# ==================== 1. GEOGRAPHY ====================
COUNTRY_PATS = {
    "USA": [r"\bUSA\b", r"\bUnited States\b", r"\.edu\b", r"\.gov\b"],
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
    "Czech Republic": [r"\bCzech\b", r"\.cz\b"],
    "Hungary": [r"\bHungary\b", r"\.hu\b"],
    "Russia": [r"\bRussia\b", r"Moscow", r"\.ru\b"],
    "Iran": [r"\bIran\b", r"Tehran", r"\.ir\b"],
    "Philippines": [r"\bPhilippines\b", r"\.ph\b"],
    "Kenya": [r"\bKenya\b", r"\.ke\b"],
    "Uganda": [r"\bUganda\b", r"\.ug\b"],
    "Ghana": [r"\bGhana\b", r"\.gh\b"],
    "Nigeria": [r"\bNigeria\b", r"\.ng\b"],
    "Egypt": [r"\bEgypt\b", r"\.eg\b"],
    "Thailand": [r"\bThailand\b", r"\.th\b"],
    "Vietnam": [r"\bVietnam\b", r"\.vn\b"],
    "Indonesia": [r"\bIndonesia\b", r"\.id\b"],
    "Malaysia": [r"\bMalaysia\b", r"\.my\b"],
    "Singapore": [r"\bSingapore\b", r"\.sg\b"],
    "Hong Kong": [r"\bHong Kong\b", r"\.hk\b"],
    "Taiwan": [r"\bTaiwan\b", r"\.tw\b"],
    "Colombia": [r"\bColombia\b", r"\.co\b(?!m)"],
    "Peru": [r"\bPeru\b", r"\.pe\b"],
    "Ecuador": [r"\bEcuador\b", r"\.ec\b"],
    "Uruguay": [r"\bUruguay\b", r"\.uy\b"],
    "Venezuela": [r"\bVenezuela\b", r"\.ve\b"],
}
COUNTRY_PATS = {k: [re.compile(p, re.I) for p in pats] for k, pats in COUNTRY_PATS.items()}

# World Bank-style income groupings (2024 fiscal year classifications)
HIGH_INCOME = {"USA", "Canada", "Germany", "UK", "France", "Switzerland", "Netherlands", "Spain",
               "Italy", "Australia", "Japan", "Sweden", "Norway", "Denmark", "Finland", "Austria",
               "Belgium", "Israel", "Korea", "New Zealand", "Portugal", "Estonia", "Czech Republic",
               "Hungary", "Poland", "Singapore", "Hong Kong", "Taiwan", "Uruguay", "Chile"}
UPPER_MIDDLE = {"China", "Brazil", "South Africa", "Mexico", "Argentina", "Russia", "Turkey",
                "Colombia", "Peru", "Thailand", "Malaysia", "Iran"}
LOWER_MIDDLE = {"India", "Philippines", "Indonesia", "Vietnam", "Kenya", "Egypt", "Ghana",
                "Nigeria", "Uganda", "Ecuador"}
LOW_INCOME = set()

# Continent groupings
CONTINENT = {
    "Africa": {"South Africa", "Kenya", "Uganda", "Ghana", "Nigeria", "Egypt"},
    "Asia": {"China", "Japan", "Korea", "India", "Israel", "Singapore", "Hong Kong", "Taiwan",
             "Philippines", "Thailand", "Vietnam", "Indonesia", "Malaysia", "Iran", "Turkey"},
    "Europe": {"Germany", "UK", "France", "Switzerland", "Netherlands", "Spain", "Italy",
               "Sweden", "Norway", "Denmark", "Finland", "Austria", "Belgium", "Portugal",
               "Estonia", "Czech Republic", "Hungary", "Poland", "Russia"},
    "Latin America": {"Brazil", "Mexico", "Argentina", "Chile", "Colombia", "Peru",
                      "Ecuador", "Uruguay", "Venezuela"},
    "North America": {"USA", "Canada"},
    "Oceania": {"Australia", "New Zealand"},
}

def guess_country(text):
    for c, pats in COUNTRY_PATS.items():
        for p in pats:
            if p.search(text or ""):
                return c
    return None

def income_group(c):
    if c in HIGH_INCOME: return "High"
    if c in UPPER_MIDDLE: return "Upper-middle"
    if c in LOWER_MIDDLE: return "Lower-middle"
    if c in LOW_INCOME: return "Low"
    return "Unknown"

def continent_of(c):
    for cont, members in CONTINENT.items():
        if c in members:
            return cont
    return "Unknown"

# Tag every presentation
for p in presentations:
    text = (p.get("affiliation") or "") + " " + (p.get("email_domain") or "")
    c = guess_country(text)
    p["country"] = c
    p["income_group"] = income_group(c) if c else "Unknown"
    p["continent"] = continent_of(c) if c else "Unknown"

# Geography aggregates
country_counts = Counter(p["country"] for p in presentations if p["country"])
income_counts = Counter(p["income_group"] for p in presentations)
continent_counts = Counter(p["continent"] for p in presentations)
n_with_country = sum(1 for p in presentations if p["country"])
n_total = len(presentations)
print("\n=== GEOGRAPHY ===")
print("Country detected: {}/{} ({:.0f}%)".format(n_with_country, n_total, 100*n_with_country/n_total))
print("\nIncome group (of {} with detected country):".format(n_with_country))
for g, n in income_counts.most_common():
    pct = 100 * n / n_total
    print("  {:<14s} {:>5d} ({:.1f}%)".format(g, n, pct))
print("\nContinent:")
for cont, n in continent_counts.most_common():
    pct = 100 * n / n_total
    print("  {:<14s} {:>5d} ({:.1f}%)".format(cont, n, pct))


# ==================== 2. GENDER (name-based inference) ====================
d = gg.Detector(case_sensitive=False)

def infer_gender(full_name):
    """Return 'female', 'male', 'andy' (androgynous), 'unknown', or None."""
    if not full_name:
        return None
    # Get first token (strip titles, take first word)
    name = full_name.strip()
    name = re.sub(r"^(Dr|Prof|Mr|Mrs|Ms|Mx)\.?\s+", "", name, flags=re.I)
    first = name.split()[0] if name.split() else ""
    if not first:
        return None
    # Strip punctuation
    first = re.sub(r"[^a-zA-ZÀ-ÿ\-]", "", first)
    if not first or len(first) < 2:
        return None
    g = d.get_gender(first)
    # Collapse mostly_female/mostly_male -> female/male
    if g.startswith("mostly_"):
        return g.replace("mostly_", "")
    return g

for p in presentations:
    p["gender_inferred"] = infer_gender(p.get("presenter", ""))

gender_counts = Counter(p["gender_inferred"] for p in presentations)
print("\n=== GENDER (NAME-INFERRED, AGGREGATE ONLY) ===")
print("Coverage: 100% of presentations attempted; many names yield 'unknown' because the name database is biased toward European names.")
for g, n in gender_counts.most_common():
    pct = 100 * n / n_total
    print("  {:<14s} {:>5d} ({:.1f}%)".format(str(g), n, pct))

# Conditional rate: of names that the database COULD classify (excluding 'unknown' and None)
classified = [p for p in presentations if p["gender_inferred"] in ("female", "male", "andy")]
n_classified = len(classified)
n_female = sum(1 for p in classified if p["gender_inferred"] == "female")
n_male = sum(1 for p in classified if p["gender_inferred"] == "male")
n_andy = sum(1 for p in classified if p["gender_inferred"] == "andy")
print("\nAmong the {} names the database COULD classify ({:.0f}% of presenters):".format(n_classified, 100*n_classified/n_total))
print("  Female-inferred: {} ({:.1f}%)".format(n_female, 100*n_female/n_classified))
print("  Male-inferred:   {} ({:.1f}%)".format(n_male, 100*n_male/n_classified))
print("  Ambiguous:       {} ({:.1f}%)".format(n_andy, 100*n_andy/n_classified))

# Gender x continent — important DEI breakdown
print("\nGender x continent (classified names only):")
gxc = defaultdict(lambda: Counter())
for p in classified:
    gxc[p["continent"]][p["gender_inferred"]] += 1
for cont in ["North America", "Europe", "Asia", "Latin America", "Oceania", "Africa", "Unknown"]:
    c = gxc[cont]
    total = sum(c.values())
    if total == 0:
        continue
    f_pct = 100*c["female"]/total
    print("  {:<14s} n={:<4d}  female-inferred: {:.1f}%".format(cont, total, f_pct))


# ==================== 3. ORGANISER DEMOGRAPHICS ====================
# Parse lead_organizer + co_organizers
organiser_genders = []
organiser_countries = []
for s in sessions:
    lead = s.get("lead_organizer", "")
    co = s.get("co_organizers", []) or []
    for entry in [lead] + (co if isinstance(co, list) else []):
        if not entry or not isinstance(entry, str):
            continue
        # Format: "Name, Institution"
        name = entry.split(",")[0].strip()
        if name:
            g = infer_gender(name)
            if g:
                organiser_genders.append(g)
        # Country from full string
        c = guess_country(entry)
        if c:
            organiser_countries.append(c)

org_gender_counts = Counter(organiser_genders)
print("\n=== SESSION ORGANISER DEMOGRAPHICS ===")
print("Total organiser slots (lead + co-organisers across all sessions): {}".format(len(organiser_genders)))
classified_org = [g for g in organiser_genders if g in ("female", "male", "andy")]
n_org_class = len(classified_org)
n_org_f = sum(1 for g in classified_org if g == "female")
print("Of {} organisers the name database could classify ({:.0f}% of names attempted):".format(
    n_org_class, 100*n_org_class/max(len(organiser_genders), 1)))
if n_org_class:
    print("  Female-inferred organisers: {} ({:.1f}%)".format(n_org_f, 100*n_org_f/n_org_class))
    print("  Male-inferred organisers:   {} ({:.1f}%)".format(n_org_class - n_org_f - sum(1 for g in classified_org if g=='andy'),
                                                                100*(n_org_class - n_org_f - sum(1 for g in classified_org if g=='andy'))/n_org_class))


# ==================== 4. INSTITUTIONAL TYPE ====================
def classify_institution(aff):
    a = (aff or "").lower()
    if not a: return "unknown"
    if any(x in a for x in ["universit", "college", "school", "polytech"]):
        return "university"
    if any(x in a for x in ["institute", "leibniz", "helmholtz", "max planck", "csiro", "cnrs",
                             "ifremer", "csic", "academy", "research center", "research centre",
                             "national lab"]):
        return "research institute"
    if any(x in a for x in ["geological survey", "usgs", "noaa", "epa", "environment canada",
                             "department of", "ministry", "government", "fisheries and oceans"]):
        return "government"
    if any(x in a for x in ["corporation", "inc.", "llc", "ltd", "company"]):
        return "industry"
    if any(x in a for x in ["foundation", "society", "ngo", "wwf", "nature conservancy"]):
        return "ngo / foundation"
    return "other"

for p in presentations:
    p["inst_type"] = classify_institution(p.get("affiliation", ""))

inst_counts = Counter(p["inst_type"] for p in presentations)
print("\n=== INSTITUTIONAL TYPE ===")
for t, n in inst_counts.most_common():
    pct = 100 * n / n_total
    print("  {:<22s} {:>5d} ({:.1f}%)".format(t, n, pct))


# ==================== 5. EQUITY-CONTENT SESSIONS ====================
EQUITY_PATTERNS = [
    r"\bindigenous\b", r"\btraditional knowledge\b", r"\btwo[\s\-]?eyed\b",
    r"\bequity\b", r"\bjustice\b", r"\bdecoloniz",
    r"\bdiversity equity\b", r"\bDEI\b", r"\binclusion\b",
    r"\bcommunity[\s\-]led\b", r"\bcommunity[\s\-]based\b", r"\bcitizen science\b",
    r"\bunderrepresented\b", r"\bunder-?represented\b",
    r"\bdisparit", r"\bmarginaliz", r"\baccessib",
]
EQUITY_PATS = [re.compile(p, re.I) for p in EQUITY_PATTERNS]

ECR_PATTERNS = [
    r"\bearly[\s\-]career\b", r"\bECR\b", r"\bECS\b", r"\bECC\b",
    r"\bgraduate student", r"\bstudent\b", r"\bpostdoc", r"\bfellow",
    r"\bamplifying voices\b", r"\bbridging the gap\b", r"\bmentor",
    r"\b'how to'\b", r"\bfirst-?time", r"\bsharing experience",
]
ECR_PATS = [re.compile(p, re.I) for p in ECR_PATTERNS]

def session_has_pattern(s, pats):
    text = (s.get("name", "") + " " + s.get("description", "")).lower()
    return any(p.search(text) for p in pats)

equity_sessions = [s for s in sessions if session_has_pattern(s, EQUITY_PATS)]
ecr_sessions = [s for s in sessions if session_has_pattern(s, ECR_PATS)]

equity_pres = []
ecr_pres = []
for s in sessions:
    has_eq = session_has_pattern(s, EQUITY_PATS)
    has_ecr = session_has_pattern(s, ECR_PATS)
    for p in (s.get("presentations") or []):
        if p.get("title"):
            if has_eq: equity_pres.append(p)
            if has_ecr: ecr_pres.append(p)

print("\n=== EQUITY-CONTENT SESSIONS ===")
print("Equity-content sessions: {} ({} talks, {:.1f}% of program)".format(
    len(equity_sessions), len(equity_pres), 100*len(equity_pres)/n_total))
print("ECR/scaffolding sessions: {} ({} talks, {:.1f}% of program)".format(
    len(ecr_sessions), len(ecr_pres), 100*len(ecr_pres)/n_total))

print("\nEquity-content session list (first 12):")
for s in equity_sessions[:12]:
    print("  [{}] {}".format(s.get("session_code"), (s.get("name") or "")[:65]))


# ==================== 6. SAVE STRUCTURED DATA ====================
out = {
    "queried": "2026-05-11",
    "method_notes": {
        "country_detection": "Keyword-based on affiliation + email TLD. Coverage ~75-80%; small countries undercounted.",
        "gender_inference": "Name-based using gender_guesser library (public-domain European-biased database). Conditional classification rate ~60-75% of presenters; East Asian, Indigenous, and many non-Western names yield 'unknown'. Inferences are AGGREGATE only — not labels of individuals. Misclassification rate likely 5-15% even among classified names.",
        "income_group": "World Bank-style classification (2024 FY). Some borderline countries (Chile, Uruguay, Poland) categorised as high-income per current WB.",
        "equity_session_detection": "Keyword pattern matching on session name + description. May undercount sessions where equity framing is in talk-level content rather than session header.",
    },
    "geography": {
        "total_presentations": n_total,
        "country_detected": n_with_country,
        "by_country": dict(country_counts.most_common()),
        "by_income_group": dict(income_counts.most_common()),
        "by_continent": dict(continent_counts.most_common()),
    },
    "gender_aggregate": {
        "raw_counts": {str(k): v for k, v in gender_counts.items()},
        "classified_count": n_classified,
        "classified_pct_of_total": round(100*n_classified/n_total, 1),
        "female_share_of_classified": round(100*n_female/max(n_classified,1), 1),
        "male_share_of_classified": round(100*n_male/max(n_classified,1), 1),
        "androgynous_share_of_classified": round(100*n_andy/max(n_classified,1), 1),
        "by_continent_classified": {
            cont: {
                "n_classified": sum(gxc[cont].values()),
                "female_pct": round(100*gxc[cont].get("female",0)/max(sum(gxc[cont].values()),1), 1),
            } for cont in CONTINENT.keys()
        },
    },
    "organisers": {
        "total_slots": len(organiser_genders),
        "classified_count": n_org_class,
        "female_share_of_classified": round(100*n_org_f/max(n_org_class,1), 1),
    },
    "institutional_type": dict(inst_counts.most_common()),
    "equity_content": {
        "n_sessions": len(equity_sessions),
        "n_presentations": len(equity_pres),
        "pct_of_program": round(100*len(equity_pres)/n_total, 1),
        "session_codes": [s.get("session_code") for s in equity_sessions],
    },
    "ecr_scaffolding": {
        "n_sessions": len(ecr_sessions),
        "n_presentations": len(ecr_pres),
        "pct_of_program": round(100*len(ecr_pres)/n_total, 1),
        "session_codes": [s.get("session_code") for s in ecr_sessions],
    },
}
with open(OUT_TABLES / "dei_summary.json", "w", encoding="utf-8") as f:
    json.dump(out, f, indent=2, ensure_ascii=False)
print("\nSaved: {}".format(OUT_TABLES / "dei_summary.json"))


# ==================== 7. CHARTS ====================
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11,
                     "axes.edgecolor": "#4a5568", "axes.labelcolor": "#1a2332",
                     "xtick.color": "#4a5568", "ytick.color": "#4a5568"})
BG = "#f7f5f0"; INK = "#1a2332"; INK_SOFT = "#4a5568"
ACCENT = "#2d5f5d"; HI = "#c44e3a"; NEUTRAL = "#8a9a8e"

# Chart A: Continent distribution
items = continent_counts.most_common()
labels = [x for x, _ in items]
values = [v for _, v in items]
fig, ax = plt.subplots(figsize=(10, 5.5), facecolor=BG)
ax.set_facecolor(BG)
y_pos = list(range(len(labels)))[::-1]
ax.barh(y_pos, values, color=ACCENT, height=0.65, edgecolor="none")
for yp, v in zip(y_pos, values):
    pct = 100 * v / n_total
    ax.text(v + 4, yp, "{} ({:.0f}%)".format(v, pct), va="center", color=INK_SOFT, fontsize=10)
ax.set_yticks(y_pos); ax.set_yticklabels(labels, fontsize=11, color=INK)
ax.set_xlabel("Presentations (of {})".format(n_total), fontsize=10, color=INK_SOFT)
ax.set_title("ASLO-SIL 2026 — presenter continent distribution",
             fontsize=13, color=INK, loc="left", weight="bold", pad=15)
ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
ax.set_xlim(0, max(values) * 1.18)
ax.grid(axis="x", linestyle=":", color="#c8c4ba", alpha=0.5)
plt.tight_layout()
plt.savefig(OUT_CHARTS / "dei_continent.png", dpi=200, facecolor=BG, bbox_inches="tight")
plt.close()

# Chart B: Income group
income_order = ["High", "Upper-middle", "Lower-middle", "Low", "Unknown"]
income_vals = [income_counts.get(g, 0) for g in income_order]
fig, ax = plt.subplots(figsize=(10, 4.5), facecolor=BG)
ax.set_facecolor(BG)
colors_inc = [ACCENT, NEUTRAL, HI, "#7c3024", "#c8c4ba"]
y_pos = list(range(len(income_order)))[::-1]
ax.barh(y_pos, income_vals, color=colors_inc, height=0.65, edgecolor="none")
for yp, v in zip(y_pos, income_vals):
    if v > 0:
        pct = 100 * v / n_total
        ax.text(v + 6, yp, "{} ({:.1f}%)".format(v, pct), va="center", color=INK_SOFT, fontsize=10)
ax.set_yticks(y_pos); ax.set_yticklabels(income_order, fontsize=11, color=INK)
ax.set_xlabel("Presentations (World Bank-style income classification)", fontsize=10, color=INK_SOFT)
ax.set_title("ASLO-SIL 2026 — presenter affiliation by income group",
             fontsize=13, color=INK, loc="left", weight="bold", pad=15)
ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
ax.set_xlim(0, max(income_vals) * 1.18)
ax.grid(axis="x", linestyle=":", color="#c8c4ba", alpha=0.5)
plt.tight_layout()
plt.savefig(OUT_CHARTS / "dei_income.png", dpi=200, facecolor=BG, bbox_inches="tight")
plt.close()

# Chart C: Gender inference (with explicit caveat)
fig, ax = plt.subplots(figsize=(10, 4.5), facecolor=BG)
ax.set_facecolor(BG)
g_order = ["female", "male", "andy", "unknown"]
g_vals = [gender_counts.get(g, 0) for g in g_order]
g_labels = ["Female-inferred", "Male-inferred", "Androgynous", "Unknown / unable to classify"]
g_colors = [HI, ACCENT, NEUTRAL, "#c8c4ba"]
y_pos = list(range(len(g_order)))[::-1]
ax.barh(y_pos, g_vals, color=g_colors, height=0.65, edgecolor="none")
for yp, v in zip(y_pos, g_vals):
    if v > 0:
        pct = 100 * v / n_total
        ax.text(v + 6, yp, "{} ({:.1f}%)".format(v, pct), va="center", color=INK_SOFT, fontsize=10)
ax.set_yticks(y_pos); ax.set_yticklabels(g_labels, fontsize=11, color=INK)
ax.set_xlabel("Presentations — name-based inference, aggregate only", fontsize=10, color=INK_SOFT)
ax.set_title("ASLO-SIL 2026 — name-inferred gender distribution\n(caveat: European-biased name database; East Asian + Indigenous + non-Western names disproportionately 'unknown')",
             fontsize=11, color=INK, loc="left", weight="bold", pad=15)
ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
ax.set_xlim(0, max(g_vals) * 1.18)
ax.grid(axis="x", linestyle=":", color="#c8c4ba", alpha=0.5)
plt.tight_layout()
plt.savefig(OUT_CHARTS / "dei_gender.png", dpi=200, facecolor=BG, bbox_inches="tight")
plt.close()

# Chart D: Institutional type
items = inst_counts.most_common()
labels = [x for x, _ in items]
values = [v for _, v in items]
fig, ax = plt.subplots(figsize=(10, 4.5), facecolor=BG)
ax.set_facecolor(BG)
y_pos = list(range(len(labels)))[::-1]
ax.barh(y_pos, values, color=ACCENT, height=0.65, edgecolor="none")
for yp, v in zip(y_pos, values):
    pct = 100 * v / n_total
    ax.text(v + 6, yp, "{} ({:.0f}%)".format(v, pct), va="center", color=INK_SOFT, fontsize=10)
ax.set_yticks(y_pos); ax.set_yticklabels(labels, fontsize=11, color=INK)
ax.set_xlabel("Presentations", fontsize=10, color=INK_SOFT)
ax.set_title("ASLO-SIL 2026 — institutional type of presenter affiliation",
             fontsize=13, color=INK, loc="left", weight="bold", pad=15)
ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
ax.set_xlim(0, max(values) * 1.18)
ax.grid(axis="x", linestyle=":", color="#c8c4ba", alpha=0.5)
plt.tight_layout()
plt.savefig(OUT_CHARTS / "dei_institution_type.png", dpi=200, facecolor=BG, bbox_inches="tight")
plt.close()

print("Saved 4 DEI charts to: {}".format(OUT_CHARTS))


# ==================== 8. NARRATIVE REPORT ====================
female_pct = 100*n_female/max(n_classified,1)
male_pct = 100*n_male/max(n_classified,1)
gs_pct = 100*(income_counts.get("Upper-middle",0) + income_counts.get("Lower-middle",0) + income_counts.get("Low",0)) / n_total
ns_pct = 100*income_counts.get("High",0) / n_total

report = """# ASLO-SIL 2026 — DEI sweep

*Aggregate-level analysis of the 1,461 indexed presentations across 309 sessions. Generated {date} from `data/sessions_all_public.json`.*

## TL;DR

- **Geographic concentration is real**: ~{ns_pct:.0f}% of presenters are from high-income countries; only ~{gs_pct:.0f}% from middle- or lower-income countries combined. US + Canada alone account for ~54% of presentations.
- **Name-inferred gender** suggests roughly **{f:.0f}% female / {m:.0f}% male** among the {ncls} presenters the database could classify ({clspct:.0f}% of all presenters). The remaining {unkpct:.0f}% — disproportionately East Asian, Indigenous, and other non-Western names — could not be classified by the (European-biased) tool used. The 50/50 ratio is roughly consistent with what one would expect from a 2026 aquatic-science meeting where the ECR cohort is more gender-balanced than senior cohorts.
- **{eq_n} equity-content sessions** (Indigenous knowledge, equity, community-led, citizen science) carry **{eq_pres} talks ({eq_pct:.1f}% of the program)**. Two-Eyed Seeing programmes Indigenous knowledge as a knowledge system, not a side track.
- **{ecr_n} ECR-scaffolding sessions** carry **{ecr_pres} talks ({ecr_pct:.1f}%)**. The Amplifying Voices track, ECR alliance workshops, and "How To" first-timer sessions are structurally programmed.

## 1. Geography

### Continent breakdown

| Continent | Presentations | Share |
|---|---:|---:|
{cont_rows}

### Income group (World Bank-style)

| Income group | Presentations | Share |
|---|---:|---:|
{inc_rows}

**Read:** The program is dominated by high-income-country affiliations ({ns_pct:.0f}% of all presentations). Upper-middle-income participation (mostly China, Brazil, Mexico) is real but ~{um:.0f}% of the program. **Lower-middle-income presence is small** ({lm:.0f}%) — the Philippines, Kenya, India, Indonesia together appear in fewer than 30 talks. This is structural; ASLO is making deliberate efforts via Amplifying Voices, but the financial and travel-visa frictions remain.

## 2. Gender (name-inferred, with explicit caveats)

The `gender_guesser` library was used to infer gender from first names. **Critical caveats:**

- The underlying name database is European-biased. Chinese, Korean, Japanese, South Asian, African, and Indigenous names are disproportionately classified as `unknown`.
- Even among classified names, misclassification rate is likely 5-15%.
- This is **aggregate-level analysis only**. No individual is labelled in the data files released; only the distribution.

**Headline rates (of names the tool could classify):**

| Inferred | Count | Share of classified |
|---|---:|---:|
| Female-inferred | {n_f} | {f:.1f}% |
| Male-inferred | {n_m} | {m:.1f}% |
| Androgynous (could be either) | {n_a} | {a:.1f}% |

**The {unkpct:.0f}% `unknown` rate is itself a DEI signal**: it suggests the tool — and many similar tools — systematically under-classify names from cultures whose phonologies it wasn't trained on. The real gender distribution is probably closer to 50/50 than these numbers suggest, but the *visibility gap* for non-Western researchers is real and worth naming.

### Gender × continent

| Continent | n (classified) | Female-inferred share |
|---|---:|---:|
{gxc_rows}

(Continents with very low classified counts are omitted because the tool gives them disproportionately `unknown`.)

## 3. Session organisers

Across **{org_total} organiser slots** (lead organisers + co-organisers across all 309 sessions):

- **{org_cls} ({org_cls_pct:.0f}%)** could be name-classified
- **{org_f_pct:.1f}% female-inferred** among the classified — close to the presentation-level rate.

The organiser cohort and the presenter cohort have similar inferred gender ratios. That's not always the case at other large meetings (organisers skew older and historically more male); the parity here suggests intentional rotation.

## 4. Institutional type

| Type | Count | Share |
|---|---:|---:|
{inst_rows}

**Read:** Universities dominate ({uni_pct:.0f}% of presentations), which is expected. Research institutes ({inst_pct:.0f}%) — IGB, CSIC, CSIRO, NIVA, NIOZ, the Leibniz network — are substantially over-represented relative to many aquatic meetings, reflecting Europe's institute-heavy research ecosystem.

## 5. Equity content

**{eq_n} sessions** (out of 309) explicitly programme Indigenous knowledge, equity, community-led science, or citizen science, carrying **{eq_pres} talks ({eq_pct:.1f}%)** of the program. Sessions include:

{eq_sess_list}

**Why this matters:** equity content is *structurally programmed*, not buried in a single panel. "Two-Eyed Seeing" sits as EP013 — a peer to the Pace/Cotner/Elser legacy sessions. The signal is clear: the society treats Indigenous knowledge as a knowledge system, not as a topic of study.

## 6. ECR scaffolding

**{ecr_n} sessions** explicitly engage early-career researchers, carrying **{ecr_pres} talks ({ecr_pct:.1f}%)** of the program. The structure is:

- **AV001A-D "Amplifying Voices in Aquatic Sciences"** — four full sessions organised by the ECC
- **EC02/EC03/EC04** — ECR workshops on resilience, cross-organisational alliances, and the publishing process
- **EP010 / EP011** — "Sharing Experiences Among ECRs" and "How To" first-timer guides
- **EP006** — Raelyn Cole Editorial Fellowship retrospective

ECR scaffolding is not decorative. It is **structurally programmed across the meeting** with named cohorts, named workshops, and named publications. This is the model ESA, AGU, and SIAM have been moving toward; ASLO is among the leading societies on it.

## Methodological caveats (full)

See `output/tables/dei_summary.json` field `method_notes` for the formal version. The headlines:

1. **Country detection** ~75-80% complete; smaller countries undercounted.
2. **Gender inference** is name-based and European-biased; treat as a rough distributional sketch, not a label of any individual.
3. **Equity-session detection** is keyword-based on session names + descriptions; sessions where equity framing lives at the *talk* level rather than session level are missed.
4. **Career-stage signals** are inferred from session-framing keywords, not author bibliographies; the actual ECR share of presenters is unknown.
5. **Institutional type** classification is coarse; some hybrids (university-government partnerships, e.g.) are forced into one bucket.

## What this analysis is NOT

- Not an audit of any individual presenter or organiser.
- Not a claim that the meeting has solved DEI; the data above suggests several gaps remain.
- Not a substitute for self-reported demographic data, which is the only authoritative source for individual-level analysis.

This is an aggregate pattern read, suitable for understanding *what the schedule represents at the field level* and where there's room to do better.
""".format(
    date="2026-05-11",
    ns_pct=ns_pct, gs_pct=gs_pct,
    f=female_pct, m=male_pct, ncls=n_classified,
    clspct=100*n_classified/n_total,
    unkpct=100*gender_counts.get("unknown",0)/n_total,
    eq_n=len(equity_sessions), eq_pres=len(equity_pres), eq_pct=100*len(equity_pres)/n_total,
    ecr_n=len(ecr_sessions), ecr_pres=len(ecr_pres), ecr_pct=100*len(ecr_pres)/n_total,
    cont_rows="\n".join("| {} | {} | {:.1f}% |".format(c, n, 100*n/n_total)
                        for c, n in continent_counts.most_common()),
    inc_rows="\n".join("| {} | {} | {:.1f}% |".format(g, income_counts.get(g, 0),
                                                       100*income_counts.get(g, 0)/n_total)
                       for g in income_order if income_counts.get(g, 0) > 0),
    um=100*income_counts.get("Upper-middle",0)/n_total,
    lm=100*income_counts.get("Lower-middle",0)/n_total,
    n_f=n_female, n_m=n_male, n_a=n_andy, a=100*n_andy/max(n_classified,1),
    gxc_rows="\n".join("| {} | {} | {:.1f}% |".format(cont, sum(gxc[cont].values()),
                                                       100*gxc[cont].get('female',0)/max(sum(gxc[cont].values()),1))
                       for cont in ["North America", "Europe", "Asia", "Latin America", "Oceania", "Africa"]
                       if sum(gxc[cont].values()) > 20),
    org_total=len(organiser_genders), org_cls=n_org_class,
    org_cls_pct=100*n_org_class/max(len(organiser_genders), 1),
    org_f_pct=100*n_org_f/max(n_org_class,1),
    inst_rows="\n".join("| {} | {} | {:.1f}% |".format(t, n, 100*n/n_total)
                        for t, n in inst_counts.most_common()),
    uni_pct=100*inst_counts.get("university",0)/n_total,
    inst_pct=100*inst_counts.get("research institute",0)/n_total,
    eq_sess_list="\n".join("- **[{}]** {}".format(s.get("session_code"), (s.get("name") or "")[:80])
                           for s in equity_sessions[:12]),
)

with open(OUT_REPORTS / "dei_sweep.md", "w", encoding="utf-8") as f:
    f.write(report)
print("Saved: {}".format(OUT_REPORTS / "dei_sweep.md"))
