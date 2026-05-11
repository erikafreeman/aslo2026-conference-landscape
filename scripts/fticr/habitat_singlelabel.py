"""
Single-label habitat classification for FT-ICR-MS DOM corpus.
Each paper gets ONE primary habitat tag (priority chain, most specific first).
Themes (biogeochem, microbial, methods, disturbance) stay multi-label and are reported separately.
"""
import json, re
from pathlib import Path
from collections import Counter, defaultdict
import matplotlib.pyplot as plt

# Load the comprehensive corpus we already pulled
data_file = Path(r"C:\Users\erika\Organise\aslo2026\presentation\figures\fticr_comprehensive_subdiscipline.json")
with open(data_file, "r", encoding="utf-8") as f:
    prev = json.load(f)

# We also need the per-paper tagged CSV
import csv
csv_file = Path(r"C:\Users\erika\Organise\aslo2026\presentation\figures\fticr_comprehensive_all_papers_tagged.csv")
papers = []
with open(csv_file, "r", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        try:
            row["year"] = int(row["year"]) if row["year"] else None
        except ValueError:
            row["year"] = None
        row["tags"] = [t.strip() for t in (row.get("subdisciplines") or "").split(";") if t.strip()]
        papers.append(row)

# Habitat priority chain — NATURAL HABITAT wins over APPLICATION CONTEXT.
# A paper studying marine DOM that also mentions DBP formation goes to "marine", not "wastewater".
# Order: most specific natural habitat first, then broader natural habitats, then applications/methods last.
HABITAT_PRIORITY = [
    "cryosphere",            # specific natural compartment
    "wetland_peatland",      # specific natural habitat
    "groundwater",           # specific natural compartment
    "atmosphere_aerosol",    # specific natural compartment
    "estuary_coastal",       # specific natural habitat (between marine and fresh)
    "freshwater_lake",       # natural habitat
    "freshwater_river",      # natural habitat
    "marine",                # broad natural habitat — open ocean
    "sediment_porewater",    # broad compartment (overlaps many habitats)
    "soil_terrestrial",      # broad natural habitat
    "petroleum_fossil",      # specific application — fossil source
    "wastewater_drinking",   # application context — only assigned if no natural habitat
]

HABITAT_LABELS = {
    "cryosphere": "Cryosphere",
    "petroleum_fossil": "Petroleum / fossil",
    "wastewater_drinking": "Wastewater / drinking water",
    "atmosphere_aerosol": "Atmosphere / aerosol",
    "groundwater": "Groundwater / aquifer",
    "wetland_peatland": "Wetland / peatland",
    "sediment_porewater": "Sediment / porewater",
    "estuary_coastal": "Estuary / coastal",
    "freshwater_lake": "Freshwater - lake",
    "freshwater_river": "Freshwater - river/stream",
    "marine": "Marine / ocean",
    "soil_terrestrial": "Soil / terrestrial",
    "other": "Other / unspecified",
}

# Themes — kept multi-label, separate from habitat
THEME_TAGS = {"biogeochem_carbon", "microbial_coupling", "methods_instrumentation",
              "disturbance_anthropogenic", "biochar_black_carbon"}
THEME_LABELS = {
    "biogeochem_carbon": "Biogeochem / C cycle",
    "microbial_coupling": "Microbial coupling",
    "methods_instrumentation": "Methods / instrumentation",
    "disturbance_anthropogenic": "Disturbance / anthropogenic",
    "biochar_black_carbon": "Biochar / black carbon",
}

def assign_habitat(tags):
    s = set(tags)
    for h in HABITAT_PRIORITY:
        if h in s:
            return h
    return "other"

# Assign single-label habitat to each paper
for p in papers:
    p["habitat"] = assign_habitat(p["tags"])

# Now compute habitat distribution per year + theme distribution per year
year_filter = list(range(2021, 2026))   # last 5 years for the slide
all_years_2025 = [p for p in papers if p["year"] == 2025]
all_years_recent = [p for p in papers if p["year"] in year_filter]

def pct_breakdown(subset, key="habitat", labels=HABITAT_LABELS):
    n = len(subset)
    if n == 0:
        return [], 0
    c = Counter(p[key] for p in subset)
    rows = [(labels.get(k, k), v, 100.0 * v / n) for k, v in c.most_common()]
    return rows, n

def theme_pct(subset):
    n = len(subset)
    rows = []
    for theme in THEME_TAGS:
        count = sum(1 for p in subset if theme in p["tags"])
        rows.append((THEME_LABELS[theme], count, 100.0 * count / n if n else 0.0))
    rows.sort(key=lambda r: -r[1])
    return rows, n

habitat_2025, n_2025 = pct_breakdown(all_years_2025)
theme_2025, _ = theme_pct(all_years_2025)
habitat_all, n_all = pct_breakdown(papers)
theme_all, _ = theme_pct(papers)

# Habitat by year (for stacked-bar visualization 2021-2025)
years = year_filter
habitat_by_year = defaultdict(lambda: defaultdict(int))  # year -> habitat -> count
for p in all_years_recent:
    habitat_by_year[p["year"]][p["habitat"]] += 1

print("=== SINGLE-LABEL HABITAT BREAKDOWN — 2025 papers ===")
print("n = {} papers (each in exactly one habitat category)".format(n_2025))
print("{:<32s} {:>6s} {:>7s}".format("Habitat", "Count", "%"))
total_pct = 0
for label, c, p in habitat_2025:
    print("{:<32s} {:>6d} {:>6.1f}%".format(label, c, p))
    total_pct += p
print("{:<32s} {:>6d} {:>6.1f}%".format("TOTAL", n_2025, total_pct))

print("\n=== THEME OVERLAY (multi-label, does NOT add to 100%) — 2025 papers ===")
print("Of the {} papers, how many carry each theme tag:".format(n_2025))
for label, c, p in theme_2025:
    print("{:<32s} {:>6d} {:>6.1f}%".format(label, c, p))

# Save corrected breakdown JSON
out_json = Path(r"C:\Users\erika\Organise\aslo2026\presentation\figures\fticr_habitat_singlelabel.json")
with open(out_json, "w", encoding="utf-8") as f:
    json.dump({
        "method": "Single-label habitat assignment via priority chain (each paper in exactly ONE habitat). Themes kept multi-label.",
        "habitat_priority_order": HABITAT_PRIORITY,
        "habitat_2025": {
            "n": n_2025,
            "rows": [{"habitat": l, "count": c, "pct": round(p, 2)} for l, c, p in habitat_2025],
        },
        "habitat_all_years": {
            "n": n_all,
            "rows": [{"habitat": l, "count": c, "pct": round(p, 2)} for l, c, p in habitat_all],
        },
        "themes_2025": {
            "n": n_2025,
            "note": "Multi-label — a paper can carry multiple theme tags. Percentages are of n_2025.",
            "rows": [{"theme": l, "count": c, "pct": round(p, 2)} for l, c, p in theme_2025],
        },
        "themes_all_years": {
            "n": n_all,
            "rows": [{"theme": l, "count": c, "pct": round(p, 2)} for l, c, p in theme_all],
        },
        "habitat_by_year_2021_2025": {
            str(y): dict(habitat_by_year[y]) for y in years
        },
    }, f, indent=2)
print("\nSaved: {}".format(out_json))

# ---- Chart 1: 100% stacked bar by year, habitat ----
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11,
                     "axes.edgecolor": "#4a5568", "axes.labelcolor": "#1a2332",
                     "xtick.color": "#4a5568", "ytick.color": "#4a5568"})
BG = "#f7f5f0"; INK = "#1a2332"; INK_SOFT = "#4a5568"

# Order habitats by total count across years
total_per_habitat = Counter()
for y in years:
    for h, c in habitat_by_year[y].items():
        total_per_habitat[h] += c
habitats_ordered = [h for h, c in total_per_habitat.most_common() if h != "other"]
if total_per_habitat.get("other", 0) > 0:
    habitats_ordered.append("other")

# Color palette - sequential greens for habitat
palette = ["#1f4747", "#2d5f5d", "#3d7a76", "#5a948f", "#7eb0aa",
           "#a3c7c0", "#c2d7d1", "#d6e1db", "#c44e3a", "#a04030",
           "#7c3024", "#5c2018", "#8a9a8e", "#c8c4ba"]
habitat_color = {h: palette[i % len(palette)] for i, h in enumerate(habitats_ordered)}

fig, ax = plt.subplots(figsize=(11, 6.5), facecolor=BG)
ax.set_facecolor(BG)

# Compute pct per year per habitat
totals_per_year = {y: sum(habitat_by_year[y].values()) for y in years}
bottoms = [0.0] * len(years)
for h in habitats_ordered:
    pcts = [100.0 * habitat_by_year[y].get(h, 0) / max(totals_per_year[y], 1) for y in years]
    bars = ax.bar(years, pcts, bottom=bottoms, color=habitat_color[h],
                  width=0.65, edgecolor=BG, linewidth=0.8,
                  label=HABITAT_LABELS.get(h, h))
    # Annotate segments > 5%
    for i, (y, p, b) in enumerate(zip(years, pcts, bottoms)):
        if p >= 5:
            ax.text(y, b + p/2, "{}%".format(round(p)), ha="center", va="center",
                    color="white" if p > 8 else INK, fontsize=9,
                    fontweight="bold" if p > 10 else "normal")
    bottoms = [b + p for b, p in zip(bottoms, pcts)]

# Year total counts above bars
for y in years:
    ax.text(y, 102, "n = {}".format(totals_per_year[y]), ha="center", va="bottom",
            color=INK, fontsize=10, fontweight="bold")

ax.set_xticks(years)
ax.set_ylim(0, 110)
ax.set_xlabel("Year", fontsize=12, color=INK_SOFT)
ax.set_ylabel("Share of papers (%)", fontsize=12, color=INK_SOFT)
ax.set_title("FT-ICR-MS in DOM science - habitat distribution by year (single-label)",
             fontsize=13, color=INK, loc="left", weight="bold", pad=20)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_visible(False)
ax.tick_params(left=False)
ax.set_yticks([0, 25, 50, 75, 100])
ax.set_yticklabels(["0%", "25%", "50%", "75%", "100%"])
ax.grid(axis="y", linestyle=":", color="#c8c4ba", alpha=0.4)
ax.legend(loc="center left", bbox_to_anchor=(1.01, 0.5), frameon=False,
          fontsize=9, labelcolor=INK)

fig.text(0.06, 0.015,
         "Source: OpenAlex (queried 2026-05-11)  -  Each paper assigned to ONE habitat via priority chain (most specific first)  -  Themes (biogeochem, microbial coupling, etc.) shown separately",
         fontsize=8, color=INK_SOFT, style="italic", ha="left")
plt.tight_layout(rect=[0, 0.04, 0.82, 0.95])

base_dir = Path(r"C:\Users\erika\Organise\aslo2026\presentation\figures")
plt.savefig(base_dir / "fticr_habitat_by_year.png", dpi=200, facecolor=BG, bbox_inches="tight", pad_inches=0.25)
print("Saved chart: {}".format(base_dir / "fticr_habitat_by_year.png"))
