"""
Comprehensive FT-ICR-MS + DOM bibliometric pull with subdiscipline tagging.
- Expanded query set covering FT-ICR, FTICR, Fourier transform ion cyclotron, ultrahigh-resolution MS, van Krevelen, molecular formula assignment
- Year range 2000-2025
- Per-paper subdiscipline tags from title + abstract keyword matching (multi-label)
- Year-over-year stacked breakdown
"""
import requests, time, json, csv, re
from pathlib import Path
from collections import Counter, defaultdict
import matplotlib.pyplot as plt

base = "https://api.openalex.org/works"
mail = "erika.freeman@igb-berlin.de"

# Comprehensive query set - all use strict title_and_abstract.search with AND boolean
QUERIES = [
    'title_and_abstract.search:"FT-ICR" AND "dissolved organic matter"',
    'title_and_abstract.search:"FT-ICR" AND "natural organic matter"',
    'title_and_abstract.search:"FTICR" AND "DOM"',
    'title_and_abstract.search:"FTICR" AND "natural organic matter"',
    'title_and_abstract.search:"FT ICR" AND "dissolved organic matter"',
    'title_and_abstract.search:"Fourier transform ion cyclotron" AND "dissolved organic"',
    'title_and_abstract.search:"ultrahigh resolution mass" AND "dissolved organic"',
    'title_and_abstract.search:"ultra-high resolution mass" AND "dissolved organic"',
    'title_and_abstract.search:"van Krevelen" AND "dissolved organic"',
    'title_and_abstract.search:"molecular formula assignment" AND "dissolved organic"',
    'title_and_abstract.search:"Orbitrap" AND "dissolved organic matter"',
]

def fetch_query(filter_str):
    works = {}
    cursor = "*"
    while cursor:
        params = {
            "filter": filter_str + ",publication_year:2000-2025",
            "per-page": 200,
            "select": "id,doi,title,publication_year,authorships,primary_location,abstract_inverted_index,topics,keywords",
            "cursor": cursor, "mailto": mail,
        }
        r = requests.get(base, params=params, timeout=60)
        if not r.ok:
            print("  [err {}] {}".format(r.status_code, r.text[:120]))
            break
        data = r.json()
        for w in data.get("results", []):
            works[w["id"]] = w
        cursor = data.get("meta", {}).get("next_cursor")
        if not cursor or not data.get("results"):
            break
        time.sleep(0.1)
    return works

print("Fetching comprehensive corpus...")
all_works = {}
for q in QUERIES:
    w = fetch_query(q)
    new = len(set(w.keys()) - set(all_works.keys()))
    all_works.update(w)
    print("  {} -> +{} new (total {})".format(q[:75], new, len(all_works)))

print("\n=== TOTAL DEDUPLICATED CORPUS: {} works ===\n".format(len(all_works)))

# Reconstruct abstracts from inverted index
def reconstruct_abstract(inv_idx):
    if not inv_idx:
        return ""
    positions = {}
    for word, idxs in inv_idx.items():
        for i in idxs:
            positions[i] = word
    return " ".join(positions[i] for i in sorted(positions))

# Subdiscipline classification rules
SUBDISCIPLINES = {
    "marine": [r"\bmarine\b", r"\bocean(?:ic|ography|s)?\b", r"\bseawater\b", r"\bpelagic\b", r"\babyssal\b", r"\bbathy", r"\barctic ocean", r"\bantarctic", r"\b(north|south|atlantic|pacific|indian|arctic) ocean", r"\bgulf of\b"],
    "freshwater_lake": [r"\blake[sd]?\b", r"\blacustrine\b", r"\blimnolog", r"\bpond[s]?\b", r"\breservoir"],
    "freshwater_river": [r"\briver[s]?\b", r"\bstream[s]?\b", r"\bfluvial\b", r"\bcreek\b", r"\bheadwater"],
    "estuary_coastal": [r"\bestuar(?:y|ies|ine)\b", r"\bcoast(?:al)?\b", r"\bmangrove\b", r"\btidal\b", r"\bdelta\b", r"\bbay\b(?!esian)", r"\bnearshore\b"],
    "soil_terrestrial": [r"\bsoil\b", r"\bterrestrial\b", r"\bpodzol\b", r"\bsoils\b", r"\bforest floor\b", r"\bleaf litter", r"\blitter (decomposition|leachate)"],
    "groundwater": [r"\bgroundwater\b", r"\baquifer\b", r"\bhyporheic\b", r"\bsubsurface\b", r"\bunsaturated zone"],
    "atmosphere_aerosol": [r"\baerosol", r"\batmospher", r"\brainwater\b", r"\bprecipitation\b(?!.*reaction)", r"\bfog\b", r"\bcloud water", r"\bwet deposition\b"],
    "cryosphere": [r"\bpermafrost\b", r"\bglacial\b", r"\bglacier", r"\bsnow\b", r"\bcryosphere\b", r"\bsupraglacial\b", r"\bice (sheet|core|melt)"],
    "sediment_porewater": [r"\bsediment[s]?\b", r"\bpore[\s\-]?water\b", r"\bbenth(?:ic|os)\b", r"\bdiagenesis\b"],
    "wetland_peatland": [r"\bwetland", r"\bpeatland", r"\bpeat\b", r"\bbog\b", r"\bmire\b", r"\bmarsh"],
    "wastewater_drinking": [r"\bwastewater\b", r"\bdrinking water\b", r"\bsewage\b", r"\beffluent\b", r"\bdisinfection (by-?product|residual)\b", r"\bDBP\b", r"\bnanofiltration\b", r"\bcoagulation\b", r"\bmembrane\b", r"\bozonation\b", r"\bUV.{0,15}(treatment|disinfection)\b", r"\bactivated carbon\b"],
    "petroleum_fossil": [r"\bpetroleum\b", r"\bcrude oil\b", r"\boil sands?\b", r"\bcoal\b(?!.*derived)", r"\bbitumen\b", r"\bproduced water\b", r"\bhydrocarbon[s]? (analysis|characterization)\b"],
    "biochar_black_carbon": [r"\bbiochar\b", r"\bblack carbon\b", r"\bpyrogenic\b", r"\bchar\b", r"\bpyrolys"],
    "microbial_coupling": [r"\bmicrobial\b", r"\bmicrob(?:e|iome)\b", r"\bbacteri(?:a|al)\b", r"\barchaea", r"\bfungal\b", r"\bbiodegradation\b", r"\bmicrobiota\b"],
    "biogeochem_carbon": [r"\bbiogeochem", r"\bcarbon (cycl|export|flux|sequestr|stor|fixation|fate)", r"\b(re|recalcitr)", r"\blability\b", r"\bremineraliz"],
    "methods_instrumentation": [r"\b(novel|new) method", r"\bworkflow\b", r"\binter(?:lab|comparison)\b", r"\boptimization of\b", r"\bionization\b", r"\bsoftware\b", r"\bpipeline\b", r"\bdata processing\b", r"\bbenchmark"],
    "disturbance_anthropogenic": [r"\bwildfire\b", r"\bdeforestation\b", r"\blogging\b", r"\bland[\s\-]use\b", r"\bagricultur", r"\burban(?:iz|ization)\b", r"\bmine drainage\b", r"\bacid (mine|rock) drainage"],
}
SUBDISC_PATTERNS = {k: [re.compile(p, re.I) for p in pats] for k, pats in SUBDISCIPLINES.items()}

def classify_paper(title, abstract, topics, keywords):
    text = " ".join([title or "", abstract or ""]).lower()
    # Also pull topic display names
    topic_text = " ".join([(t.get("display_name") or "").lower() for t in (topics or [])])
    kw_text = " ".join([(k.get("display_name") or "").lower() for k in (keywords or [])])
    search_text = " ".join([text, topic_text, kw_text])
    tags = set()
    for sd, pats in SUBDISC_PATTERNS.items():
        for pat in pats:
            if pat.search(search_text):
                tags.add(sd)
                break
    return sorted(tags)

# Process all works
records = []
for wid, w in all_works.items():
    title = (w.get("title") or "").strip()
    abstract = reconstruct_abstract(w.get("abstract_inverted_index"))
    topics = w.get("topics", [])
    keywords = w.get("keywords", [])
    authors = [a.get("author", {}).get("display_name") for a in w.get("authorships", []) if a.get("author")]
    authors = [n for n in authors if n]
    journal = ((w.get("primary_location") or {}).get("source") or {}).get("display_name", "") or ""
    year = w.get("publication_year")
    tags = classify_paper(title, abstract, topics, keywords)
    records.append({
        "year": year,
        "title": title,
        "authors": authors,
        "journal": journal,
        "doi": w.get("doi", "") or "",
        "subdisciplines": tags,
        "n_subdisciplines": len(tags),
        "openalex_id": wid,
    })

# Year totals
year_totals = Counter(r["year"] for r in records if r["year"])
print("Year totals (deduplicated):")
for y in sorted(year_totals):
    print("  {}: {}".format(y, year_totals[y]))

# Subdiscipline counts by year
subd_year = defaultdict(lambda: defaultdict(int))  # subd -> year -> count
for r in records:
    if not r["year"]:
        continue
    for sd in r["subdisciplines"]:
        subd_year[sd][r["year"]] += 1
    if not r["subdisciplines"]:
        subd_year["unclassified"][r["year"]] += 1

# Subdiscipline totals (across all years)
subd_total = {sd: sum(yrs.values()) for sd, yrs in subd_year.items()}
print("\n=== SUBDISCIPLINE TOTALS (2000-2025, multi-label so sums exceed corpus size) ===")
for sd in sorted(subd_total, key=lambda x: -subd_total[x]):
    print("  {:<28s} {:5d}".format(sd, subd_total[sd]))

# 2025-specific subdiscipline breakdown
subd_2025 = [(sd, yrs.get(2025, 0)) for sd, yrs in subd_year.items()]
subd_2025.sort(key=lambda x: -x[1])
print("\n=== 2025 SUBDISCIPLINE BREAKDOWN (multi-label) ===")
for sd, n in subd_2025:
    if n > 0:
        print("  {:<28s} {:5d}".format(sd, n))

# Save data
base_dir = Path(r"C:\Users\erika\Organise\aslo2026\presentation\figures")

out_json = base_dir / "fticr_comprehensive_subdiscipline.json"
with open(out_json, "w", encoding="utf-8") as f:
    json.dump({
        "method": "OpenAlex strict title_and_abstract.search, 11 keyword strategies unioned, deduplicated by OpenAlex work-id",
        "queried": "2026-05-11",
        "year_range": "2000-2025",
        "queries": QUERIES,
        "total_unique_works": len(records),
        "year_totals": dict(sorted(year_totals.items())),
        "subdiscipline_year_breakdown": {sd: dict(sorted(yrs.items())) for sd, yrs in subd_year.items()},
        "subdiscipline_totals_2000_2025": subd_total,
        "subdiscipline_2025_breakdown": dict(subd_2025),
        "subdiscipline_rules": {sd: pats for sd, pats in SUBDISCIPLINES.items()},
        "multi_label_note": "Each paper can have multiple subdiscipline tags. Sums of subdiscipline counts exceed the corpus size because a marine biogeochemistry paper, e.g., gets both 'marine' and 'biogeochem_carbon' tags.",
    }, f, indent=2)
print("\nSaved comprehensive data: {}".format(out_json))

# Save full record list (CSV) - papers with subdiscipline tags as semicolon-separated string
out_csv = base_dir / "fticr_comprehensive_all_papers_tagged.csv"
with open(out_csv, "w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["year", "title", "authors_short", "all_authors", "journal", "doi", "subdisciplines", "n_subdisciplines"])
    w.writeheader()
    for r in sorted(records, key=lambda x: (x["year"] or 0, x["journal"].lower())):
        w.writerow({
            "year": r["year"],
            "title": r["title"],
            "authors_short": (", ".join(r["authors"][:3]) + (" et al. (n={})".format(len(r["authors"])) if len(r["authors"]) > 3 else "")),
            "all_authors": "; ".join(r["authors"]),
            "journal": r["journal"],
            "doi": r["doi"],
            "subdisciplines": "; ".join(r["subdisciplines"]),
            "n_subdisciplines": r["n_subdisciplines"],
        })
print("Saved full tagged CSV: {}".format(out_csv))

# ---- Visualization 1: comprehensive cumulative growth chart ----
years_full = list(range(2000, 2026))
counts_per_year = [year_totals.get(y, 0) for y in years_full]
cumulative_total, run = [], 0
for c in counts_per_year:
    run += c
    cumulative_total.append(run)

plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11,
                     "axes.edgecolor": "#4a5568", "axes.labelcolor": "#1a2332",
                     "xtick.color": "#4a5568", "ytick.color": "#4a5568"})
BG = "#f7f5f0"; INK = "#1a2332"; INK_SOFT = "#4a5568"
BAR = "#2d5f5d"; LINE = "#c44e3a"

fig, ax1 = plt.subplots(figsize=(11, 6.5), facecolor=BG)
ax1.set_facecolor(BG)
ax1.bar(years_full, counts_per_year, color=BAR, alpha=0.85, width=0.7, edgecolor="none",
        label="Publications per year")
ax1.set_xlabel("Year", fontsize=12, color=INK_SOFT)
ax1.set_ylabel("Publications per year", fontsize=12, color=BAR)
ax1.tick_params(axis="y", labelcolor=BAR)
ax1.set_xlim(1999.5, 2025.5)
ax1.set_ylim(0, max(counts_per_year) * 1.15 if counts_per_year else 1)
ax1.spines["top"].set_visible(False)
ax1.spines["right"].set_color(LINE)
ax1.grid(axis="y", linestyle=":", color="#c8c4ba", alpha=0.6)

ax2 = ax1.twinx()
ax2.plot(years_full, cumulative_total, color=LINE, linewidth=2.4, marker="o",
         markersize=5, markeredgecolor=BG, markeredgewidth=1.2, label="Cumulative")
ax2.set_ylabel("Cumulative publications", fontsize=12, color=LINE)
ax2.tick_params(axis="y", labelcolor=LINE)
ax2.spines["top"].set_visible(False)
ax2.spines["left"].set_visible(False)
ax2.set_ylim(0, cumulative_total[-1] * 1.08 if cumulative_total[-1] else 1)

fig.suptitle("FT-ICR-MS and ultra-high-resolution MS in DOM science  -  {} publications, 2000-2025".format(cumulative_total[-1]),
             fontsize=13, color=INK, x=0.06, ha="left", y=0.97, weight="bold")
fig.text(0.06, 0.015,
         "Source: OpenAlex (queried 2026-05-11)  -  11 strict title-or-abstract queries unioned: FT-ICR / FTICR / Fourier transform ion cyclotron / ultrahigh-resolution MS / Orbitrap / van Krevelen, each AND 'dissolved organic matter' or 'natural organic matter'  -  Deduplicated by work ID",
         fontsize=7, color=INK_SOFT, style="italic", ha="left")

h1, l1 = ax1.get_legend_handles_labels()
h2, l2 = ax2.get_legend_handles_labels()
ax1.legend(h1 + h2, l1 + l2, loc="upper left", frameon=False, fontsize=10, labelcolor=INK)
plt.tight_layout(rect=[0, 0.04, 1, 0.95])
plt.savefig(base_dir / "fticr_growth_comprehensive.png", dpi=200, facecolor=BG, bbox_inches="tight", pad_inches=0.25)
print("Saved comprehensive growth chart: {}".format(base_dir / "fticr_growth_comprehensive.png"))

# ---- Visualization 2: subdiscipline distribution (horizontal bar, 2000-2025 totals + 2025 inset) ----
# Get top 12 subdisciplines by total count
top_subdisc = sorted([(sd, n) for sd, n in subd_total.items() if sd != "unclassified"], key=lambda x: -x[1])[:14]
subd_names = [sd for sd, n in top_subdisc]
totals_all = [n for sd, n in top_subdisc]
totals_2025 = [subd_year[sd].get(2025, 0) for sd in subd_names]

# Pretty labels
LABEL_MAP = {
    "marine": "Marine / ocean",
    "freshwater_lake": "Freshwater - lake",
    "freshwater_river": "Freshwater - river/stream",
    "estuary_coastal": "Estuary / coastal",
    "soil_terrestrial": "Soil / terrestrial",
    "groundwater": "Groundwater / aquifer",
    "atmosphere_aerosol": "Atmosphere / aerosol",
    "cryosphere": "Cryosphere",
    "sediment_porewater": "Sediment / porewater",
    "wetland_peatland": "Wetland / peatland",
    "wastewater_drinking": "Wastewater / drinking water",
    "petroleum_fossil": "Petroleum / fossil",
    "biochar_black_carbon": "Biochar / black carbon",
    "microbial_coupling": "Microbial coupling",
    "biogeochem_carbon": "Biogeochem / C cycle",
    "methods_instrumentation": "Methods / instrumentation",
    "disturbance_anthropogenic": "Disturbance / anthropogenic",
    "unclassified": "Unclassified",
}
display_names = [LABEL_MAP.get(sd, sd) for sd in subd_names]

fig, ax = plt.subplots(figsize=(11, 7), facecolor=BG)
ax.set_facecolor(BG)
y_pos = list(range(len(display_names)))[::-1]
ax.barh(y_pos, totals_all, color="#c8c4ba", height=0.65, label="All years (2000-2025)")
ax.barh(y_pos, totals_2025, color=BAR, height=0.65, label="2025 only")

for i, (yp, tot, t25) in enumerate(zip(y_pos, totals_all, totals_2025)):
    ax.text(tot + 8, yp, str(tot), va="center", color=INK_SOFT, fontsize=10)
    if t25 > 0:
        ax.text(t25 / 2 if t25 > 25 else t25 + 3, yp, str(t25),
                va="center", ha="center" if t25 > 25 else "left",
                color="white" if t25 > 25 else BAR, fontsize=9, fontweight="bold")

ax.set_yticks(y_pos)
ax.set_yticklabels(display_names, fontsize=11, color=INK)
ax.set_xlabel("Publications (multi-label: a paper may appear in multiple subdisciplines)", fontsize=10, color=INK_SOFT)
ax.set_title("FT-ICR-MS + UHR-MS in DOM science - distribution by subdiscipline",
             fontsize=13, color=INK, loc="left", weight="bold", pad=15)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.legend(loc="lower right", frameon=False, fontsize=10, labelcolor=INK)
ax.grid(axis="x", linestyle=":", color="#c8c4ba", alpha=0.6)

fig.text(0.06, 0.015,
         "Source: OpenAlex (queried 2026-05-11)  -  Subdiscipline tags from title + abstract + topic keyword matching  -  Multi-label classification",
         fontsize=8, color=INK_SOFT, style="italic", ha="left")
plt.tight_layout(rect=[0, 0.03, 1, 0.96])
plt.savefig(base_dir / "fticr_subdisciplines.png", dpi=200, facecolor=BG, bbox_inches="tight", pad_inches=0.25)
print("Saved subdiscipline chart: {}".format(base_dir / "fticr_subdisciplines.png"))
