"""Pull 2023/2024/2025 FT-ICR-MS DOM papers, classify by venue, save lists + chart."""
import requests, time, json, csv, re
from pathlib import Path
from collections import Counter, defaultdict
import matplotlib.pyplot as plt

base = "https://api.openalex.org/works"
mail = "erika.freeman@igb-berlin.de"

filters = [
    'title_and_abstract.search:"FT-ICR" AND "dissolved organic matter"',
    'title_and_abstract.search:"FTICR" AND "DOM"',
    'title_and_abstract.search:"ultrahigh resolution mass" AND "dissolved organic matter"',
]

def fetch_year(year):
    works = {}
    for f in filters:
        cursor = "*"
        while cursor:
            params = {
                "filter": f + ",publication_year:{}".format(year),
                "per-page": 200,
                "select": "id,doi,title,publication_year,authorships,primary_location",
                "cursor": cursor, "mailto": mail,
            }
            r = requests.get(base, params=params, timeout=45)
            if not r.ok:
                break
            data = r.json()
            for w in data.get("results", []):
                works[w["id"]] = w
            cursor = data.get("meta", {}).get("next_cursor")
            if not cursor or not data.get("results"):
                break
            time.sleep(0.1)
    return works

PREPRINT_VENUES = {
    "figshare", "ssrn electronic journal", "ssrn", "research square",
    "authorea preprints", "biorxiv", "chemrxiv", "earth arxiv", "eartharxiv",
    "essoar", "ecoevorxiv", "preprints.org", "preprints", "arxiv",
    "zenodo", "dryad", "dataverse", "osf", "open science framework",
}
ENGINEERING_PATTERNS = [
    r"water process", r"chemical engineering", r"environmental chemical engineering",
    r"separation and purification", r"desalination",
    r"water science.*technology", r"process safety",
    r"membrane", r"nanofiltration", r"coagulation",
    r"water treatment", r"oxidation processes",
    r"bioresource technology", r"cleaner production",
]
ENGINEERING_PAT = [re.compile(p, re.I) for p in ENGINEERING_PATTERNS]

def classify(journal):
    j = (journal or "").strip().lower()
    if not j:
        return "unknown"
    if j in PREPRINT_VENUES:
        return "preprint_data"
    for pat in ENGINEERING_PAT:
        if pat.search(j):
            return "engineering"
    return "ecology_chem"

results = {}
for y in [2023, 2024, 2025]:
    print("Fetching {}...".format(y))
    results[y] = fetch_year(y)
    print("  -> {} papers".format(len(results[y])))

breakdown = {}
classified = {y: defaultdict(list) for y in results}
for y, works in results.items():
    for wid, w in works.items():
        journal = ((w.get("primary_location") or {}).get("source") or {}).get("display_name", "") or ""
        cat = classify(journal)
        classified[y][cat].append(w)
    breakdown[y] = {cat: len(papers) for cat, papers in classified[y].items()}

print("\n=== YEAR-OVER-YEAR BREAKDOWN ===")
print("{:<6} {:<14} {:<13} {:<15} {:<10} {:<6}".format("Year", "Ecology/Chem", "Engineering", "Preprint/Data", "Unknown", "Total"))
for y in [2023, 2024, 2025]:
    b = breakdown[y]
    total = sum(b.values())
    print("{:<6} {:<14} {:<13} {:<15} {:<10} {:<6}".format(
        y, b.get("ecology_chem", 0), b.get("engineering", 0),
        b.get("preprint_data", 0), b.get("unknown", 0), total))

# ---- Save ecology-only 2025 list ----
ecology_2025 = []
for w in classified[2025]["ecology_chem"]:
    authors = [a.get("author", {}).get("display_name") for a in w.get("authorships", []) if a.get("author")]
    authors = [n for n in authors if n]
    if len(authors) <= 5:
        auth_str = ", ".join(authors)
    else:
        auth_str = ", ".join(authors[:3]) + ", ... , {} (n={})".format(authors[-1], len(authors))
    journal = ((w.get("primary_location") or {}).get("source") or {}).get("display_name", "") or "-"
    ecology_2025.append({
        "title": (w.get("title") or "").strip(),
        "authors": auth_str,
        "all_authors": "; ".join(authors),
        "journal": journal,
        "doi": w.get("doi", "") or "",
    })
ecology_2025.sort(key=lambda r: (r["journal"].lower(), r["authors"].lower()))

base_dir = Path(r"C:\Users\erika\Organise\aslo2026\presentation\figures")

out_md = base_dir / "fticr_2025_papers_ecology_only.md"
with open(out_md, "w", encoding="utf-8") as f:
    f.write("# FT-ICR-MS in DOM science - 2025 papers (ecology / env-chem subset)\n\n")
    f.write("Total: {} papers. Excludes preprint/data deposits and water-treatment engineering venues.\n\n".format(len(ecology_2025)))
    f.write("Source: OpenAlex (queried 2026-05-11). Strict title-or-abstract filter. Sorted by journal then first author.\n\n")
    cur_j = None
    for r in ecology_2025:
        if r["journal"] != cur_j:
            cur_j = r["journal"]
            f.write("\n## {}\n\n".format(cur_j))
        f.write("- **{}**  \n  _{}_  \n  {}\n\n".format(r["title"], r["authors"], r["doi"]))
print("\nSaved ecology-only MD: {}".format(out_md))

out_csv = base_dir / "fticr_2025_papers_ecology_only.csv"
with open(out_csv, "w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["title", "authors", "journal", "doi", "all_authors"])
    w.writeheader()
    for r in ecology_2025:
        w.writerow(r)
print("Saved ecology-only CSV: {}".format(out_csv))

out_json = base_dir / "fticr_breakdown_2023_2025.json"
with open(out_json, "w", encoding="utf-8") as f:
    json.dump({
        "method": "OpenAlex strict title-or-abstract filter, classified by journal name",
        "queried": "2026-05-11",
        "breakdown": breakdown,
        "totals_by_year": {y: sum(breakdown[y].values()) for y in breakdown},
    }, f, indent=2)
print("Saved breakdown JSON: {}".format(out_json))

# ---- Stacked-bar chart ----
years_plot = [2023, 2024, 2025]
ecology_vals = [breakdown[y].get("ecology_chem", 0) for y in years_plot]
engineering_vals = [breakdown[y].get("engineering", 0) for y in years_plot]
preprint_vals = [breakdown[y].get("preprint_data", 0) for y in years_plot]
unknown_vals = [breakdown[y].get("unknown", 0) for y in years_plot]

plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11,
                     "axes.edgecolor": "#4a5568", "axes.labelcolor": "#1a2332",
                     "xtick.color": "#4a5568", "ytick.color": "#4a5568"})
BG = "#f7f5f0"; INK = "#1a2332"; INK_SOFT = "#4a5568"
ECOL = "#2d5f5d"; ENG = "#8a9a8e"; PRE = "#c8c4ba"; UNK = "#e5e2db"

fig, ax = plt.subplots(figsize=(8, 5.5), facecolor=BG)
ax.set_facecolor(BG)

ax.bar(years_plot, ecology_vals, color=ECOL, label="Ecology / env-chem", width=0.6, edgecolor="none")
ax.bar(years_plot, engineering_vals, bottom=ecology_vals, color=ENG, label="Water-treatment engineering", width=0.6, edgecolor="none")
bottom2 = [a + b for a, b in zip(ecology_vals, engineering_vals)]
ax.bar(years_plot, preprint_vals, bottom=bottom2, color=PRE, label="Preprints / data deposits", width=0.6, edgecolor="none")
bottom3 = [a + b for a, b in zip(bottom2, preprint_vals)]
ax.bar(years_plot, unknown_vals, bottom=bottom3, color=UNK, label="Unknown venue", width=0.6, edgecolor="none")

for i, y in enumerate(years_plot):
    if ecology_vals[i] > 0:
        ax.text(y, ecology_vals[i] / 2, str(ecology_vals[i]), ha="center", va="center", color="white", fontsize=11, fontweight="bold")
    if engineering_vals[i] > 4:
        ax.text(y, ecology_vals[i] + engineering_vals[i] / 2, str(engineering_vals[i]), ha="center", va="center", color="white", fontsize=10, fontweight="bold")
    if preprint_vals[i] > 4:
        ax.text(y, bottom2[i] + preprint_vals[i] / 2, str(preprint_vals[i]), ha="center", va="center", color=INK, fontsize=10, fontweight="bold")
    total = ecology_vals[i] + engineering_vals[i] + preprint_vals[i] + unknown_vals[i]
    ax.text(y, total + 5, "{}".format(total), ha="center", va="bottom", color=INK, fontsize=11, fontweight="bold")

ax.set_xticks(years_plot)
ax.set_xlabel("Year", fontsize=12, color=INK_SOFT)
ax.set_ylabel("Publications per year", fontsize=12, color=INK_SOFT)
ax.set_title("FT-ICR-MS in DOM science - growth by venue type, 2023-2025",
             fontsize=13, color=INK, loc="left", weight="bold", pad=15)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.grid(axis="y", linestyle=":", color="#c8c4ba", alpha=0.6)
ax.legend(loc="upper left", frameon=False, fontsize=10, labelcolor=INK)

fig.text(0.06, 0.015,
         "Source: OpenAlex (queried 2026-05-11)  -  Strict title-or-abstract filter  -  Journal-name classification (see fticr_breakdown_2023_2025.json)",
         fontsize=8, color=INK_SOFT, style="italic", ha="left")

plt.tight_layout(rect=[0, 0.04, 1, 0.96])
out_chart = base_dir / "fticr_growth_by_venue.png"
plt.savefig(out_chart, dpi=200, facecolor=BG, bbox_inches="tight", pad_inches=0.25)
print("Saved venue-split chart: {}".format(out_chart))
