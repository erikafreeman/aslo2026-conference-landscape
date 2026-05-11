"""
Coarse 4-category single-label habitat classification.
Each paper goes into exactly one of:
  - Saltwater (marine + estuary/coastal)
  - Inland waters (lakes + rivers + wetlands + groundwater)
  - Terrestrial / atmospheric (soil + atmosphere + cryosphere + sediment + petroleum)
  - Applied / treatment (wastewater + drinking water, with NO natural-habitat tag)
  - Unclassified (no habitat tags at all)
Plus an aggregate 2025 vs all-years comparison and a 100% stacked-bar chart by year.
"""
import csv, json
from pathlib import Path
from collections import Counter, defaultdict
import matplotlib.pyplot as plt

base_dir = Path(r"C:\Users\erika\Organise\aslo2026\presentation\figures")
papers = []
with open(base_dir / "fticr_comprehensive_all_papers_tagged.csv", "r", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        try:
            row["year"] = int(row["year"]) if row["year"] else None
        except ValueError:
            row["year"] = None
        row["tags"] = set(t.strip() for t in (row.get("subdisciplines") or "").split(";") if t.strip())
        papers.append(row)

SALTWATER = {"marine", "estuary_coastal"}
INLAND = {"freshwater_lake", "freshwater_river", "wetland_peatland", "groundwater"}
TERRESTRIAL_ATMOS = {"soil_terrestrial", "atmosphere_aerosol", "cryosphere", "sediment_porewater", "petroleum_fossil", "biochar_black_carbon"}
APPLIED = {"wastewater_drinking"}

def assign_coarse(tags):
    # Assign to the group with the MOST tag matches (keyword density).
    # Ties broken by: saltwater > inland > terrestrial > applied (so a single-tag overlap
    # between groups goes to the historically dominant category).
    counts = {
        "saltwater": len(tags & SALTWATER),
        "inland_waters": len(tags & INLAND),
        "terrestrial_atmospheric": len(tags & TERRESTRIAL_ATMOS),
        "applied_treatment": len(tags & APPLIED),
    }
    if all(v == 0 for v in counts.values()):
        return "unclassified"
    tiebreak_order = ["saltwater", "inland_waters", "terrestrial_atmospheric", "applied_treatment"]
    # max count, then tiebreak order
    return max(tiebreak_order, key=lambda k: (counts[k], -tiebreak_order.index(k)))

LABELS = {
    "saltwater": "Saltwater (marine + estuary/coastal)",
    "inland_waters": "Inland waters (lake / river / wetland / groundwater)",
    "terrestrial_atmospheric": "Terrestrial + atmospheric (soil / aerosol / cryosphere / sediment / petroleum)",
    "applied_treatment": "Applied (wastewater / drinking water treatment)",
    "unclassified": "Unclassified",
}
ORDER = ["saltwater", "inland_waters", "terrestrial_atmospheric", "applied_treatment", "unclassified"]

for p in papers:
    p["coarse"] = assign_coarse(p["tags"])

# 2025 breakdown
papers_2025 = [p for p in papers if p["year"] == 2025]
n_2025 = len(papers_2025)
counts_2025 = Counter(p["coarse"] for p in papers_2025)

print("=== COARSE 4-CATEGORY HABITAT BREAKDOWN - 2025 papers (n = {}) ===\n".format(n_2025))
print("{:<58s} {:>6s} {:>7s}".format("Category", "Count", "Share"))
total_pct = 0.0
rows_2025 = []
for cat in ORDER:
    c = counts_2025.get(cat, 0)
    if c == 0:
        continue
    pct = 100.0 * c / n_2025
    print("{:<58s} {:>6d} {:>6.1f}%".format(LABELS[cat], c, pct))
    rows_2025.append({"category": LABELS[cat], "count": c, "pct": round(pct, 2)})
    total_pct += pct
print("{:<58s} {:>6d} {:>6.1f}%".format("TOTAL", n_2025, total_pct))

# All-years breakdown
n_all = len(papers)
counts_all = Counter(p["coarse"] for p in papers)
print("\n=== ALL YEARS (2000-2025, n = {}) ===\n".format(n_all))
print("{:<58s} {:>6s} {:>7s}".format("Category", "Count", "Share"))
rows_all = []
for cat in ORDER:
    c = counts_all.get(cat, 0)
    if c == 0:
        continue
    pct = 100.0 * c / n_all
    print("{:<58s} {:>6d} {:>6.1f}%".format(LABELS[cat], c, pct))
    rows_all.append({"category": LABELS[cat], "count": c, "pct": round(pct, 2)})

# Themes (multi-label) on 2025 corpus
THEME_TAGS = {
    "biogeochem_carbon": "Biogeochemistry / C cycling",
    "microbial_coupling": "Microbial coupling",
    "disturbance_anthropogenic": "Disturbance / anthropogenic forcing",
    "methods_instrumentation": "Methods / instrumentation",
}
theme_rows = []
for tag, label in THEME_TAGS.items():
    c = sum(1 for p in papers_2025 if tag in p["tags"])
    theme_rows.append({"theme": label, "count": c, "pct_of_2025": round(100.0 * c / n_2025, 1)})
theme_rows.sort(key=lambda r: -r["count"])

print("\n=== THEMES (multi-label overlay, 2025) ===")
print("{:<40s} {:>6s} {:>10s}".format("Theme", "Count", "% of 2025"))
for r in theme_rows:
    print("{:<40s} {:>6d} {:>9.1f}%".format(r["theme"], r["count"], r["pct_of_2025"]))

# Per-year 2021-2025 stacked-bar
years = [2021, 2022, 2023, 2024, 2025]
per_year = {y: Counter(p["coarse"] for p in papers if p["year"] == y) for y in years}
totals = {y: sum(per_year[y].values()) for y in years}

# Save JSON
out_json = base_dir / "fticr_habitat_coarse.json"
with open(out_json, "w", encoding="utf-8") as f:
    json.dump({
        "method": "Coarse 4-category single-label habitat classification. Priority: inland > saltwater > terrestrial/atmospheric > applied/treatment > unclassified.",
        "categories": LABELS,
        "n_2025": n_2025,
        "habitat_2025": rows_2025,
        "n_all_years": n_all,
        "habitat_all_years": rows_all,
        "themes_2025_multilabel": theme_rows,
        "per_year_2021_2025": {str(y): {LABELS[c]: per_year[y].get(c, 0) for c in ORDER} for y in years},
    }, f, indent=2)
print("\nSaved: {}".format(out_json))

# ---- 100% stacked-bar chart ----
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11,
                     "axes.edgecolor": "#4a5568", "axes.labelcolor": "#1a2332",
                     "xtick.color": "#4a5568", "ytick.color": "#4a5568"})
BG = "#f7f5f0"; INK = "#1a2332"; INK_SOFT = "#4a5568"

cat_colors = {
    "saltwater": "#1f4747",
    "inland_waters": "#2d5f5d",
    "terrestrial_atmospheric": "#8a9a8e",
    "applied_treatment": "#c44e3a",
    "unclassified": "#c8c4ba",
}

fig, ax = plt.subplots(figsize=(11, 6.5), facecolor=BG)
ax.set_facecolor(BG)

bottoms = [0.0] * len(years)
for cat in ORDER:
    pcts = [100.0 * per_year[y].get(cat, 0) / max(totals[y], 1) for y in years]
    ax.bar(years, pcts, bottom=bottoms, color=cat_colors[cat],
           width=0.65, edgecolor=BG, linewidth=0.8, label=LABELS[cat])
    for i, (y, p, b) in enumerate(zip(years, pcts, bottoms)):
        if p >= 5:
            ax.text(y, b + p/2, "{}%".format(round(p)), ha="center", va="center",
                    color="white" if p > 8 else INK, fontsize=10,
                    fontweight="bold" if p > 10 else "normal")
    bottoms = [b + p for b, p in zip(bottoms, pcts)]

for y in years:
    ax.text(y, 102, "n = {}".format(totals[y]), ha="center", va="bottom",
            color=INK, fontsize=10, fontweight="bold")

ax.set_xticks(years)
ax.set_ylim(0, 110)
ax.set_xlabel("Year", fontsize=12, color=INK_SOFT)
ax.set_ylabel("Share of papers (%)", fontsize=12, color=INK_SOFT)
ax.set_title("FT-ICR-MS in DOM science - habitat distribution, 2021-2025",
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
         "Source: OpenAlex (queried 2026-05-11)  -  Single-label coarse classification (each paper in exactly one category)  -  Themes (biogeochem, microbial coupling) are multi-label and not shown here",
         fontsize=8, color=INK_SOFT, style="italic", ha="left")
plt.tight_layout(rect=[0, 0.04, 0.75, 0.95])

out_chart = base_dir / "fticr_habitat_coarse_by_year.png"
plt.savefig(out_chart, dpi=200, facecolor=BG, bbox_inches="tight", pad_inches=0.25)
print("Saved chart: {}".format(out_chart))
