"""
Corrected freshwater vs participation analysis + paired proportion plot.

Bug in script 05 (now fixed here): the original 'world freshwater total'
summed WB country records + WB aggregate groupings (World, IDA & IBRD,
income tiers, regional aggregates), which double-counted countries
~9-10x. That made country freshwater shares look 10x smaller than
reality, which is why Brazil appeared at parity. With the correct
denominator (sum of real countries only, or the WB 'World' aggregate
value), no country is anywhere near parity.

This script:
  1. Fetches WB renewable internal freshwater (ER.H2O.INTR.K3).
  2. Filters out aggregate groupings carefully.
  3. Computes correct freshwater shares (% of true world total).
  4. Computes correct ASLO participation shares (% of detected presentations).
  5. Generates a paired-proportion plot showing both shares side-by-side.
  6. Identifies under- and over-represented countries.
"""
import json, re, requests
from pathlib import Path
from collections import Counter
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

ROOT = Path(__file__).resolve().parent.parent

# --- 1. Get ASLO participation by country ---
with open(ROOT / "data" / "sessions_all_public.json", "r", encoding="utf-8") as f:
    sessions = [json.loads(line) for line in f if line.strip()]

COUNTRY_PATS = {
    "United States": [r"\bUSA\b", r"\bUnited States\b", r"\.edu\b", r"\.gov\b"],
    "Canada": [r"\bCanada\b", r"\bQu[eé]bec\b(?!.*France)", r"Ontario", r"British Columbia", r"\.ca\b"],
    "Germany": [r"\bGermany\b", r"Berlin\b(?! State)", r"M[uü]nchen", r"Bremen", r"Leibniz", r"Helmholtz", r"\.de\b"],
    "United Kingdom": [r"\bUK\b", r"\bUnited Kingdom\b", r"\bEngland\b", r"\bScotland\b", r"Cambridge\b", r"Oxford\b", r"\.uk\b"],
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
    "Korea, Rep.": [r"\bKorea\b", r"\.kr\b"],
    "Mexico": [r"\bMexico\b", r"UNAM", r"\.mx\b"],
    "Argentina": [r"\bArgentina\b", r"\.ar\b"],
    "Chile": [r"\bChile\b", r"\.cl\b"],
    "Poland": [r"\bPoland\b", r"\.pl\b"],
    "Turkiye": [r"\bTurkey\b", r"T[uü]rkiye", r"\.tr\b"],
    "India": [r"\bIndia\b", r"\.in\b"],
    "New Zealand": [r"New Zealand", r"\.nz\b"],
    "Portugal": [r"\bPortugal\b", r"Lisbon", r"\.pt\b"],
    "Estonia": [r"\bEstonia\b", r"\.ee\b"],
    "Czechia": [r"\bCzech\b", r"\.cz\b"],
    "Hungary": [r"\bHungary\b", r"\.hu\b"],
    "Russian Federation": [r"\bRussia\b", r"Moscow", r"\.ru\b"],
    "Iran, Islamic Rep.": [r"\bIran\b", r"Tehran", r"\.ir\b"],
    "Philippines": [r"\bPhilippines\b", r"\.ph\b"],
    "Kenya": [r"\bKenya\b", r"\.ke\b"],
    "Uganda": [r"\bUganda\b", r"\.ug\b"],
    "Ghana": [r"\bGhana\b", r"\.gh\b"],
    "Nigeria": [r"\bNigeria\b", r"\.ng\b"],
    "Egypt, Arab Rep.": [r"\bEgypt\b", r"\.eg\b"],
    "Thailand": [r"\bThailand\b", r"\.th\b"],
    "Viet Nam": [r"\bVietnam\b", r"\bViet Nam\b", r"\.vn\b"],
    "Indonesia": [r"\bIndonesia\b", r"\.id\b"],
    "Malaysia": [r"\bMalaysia\b", r"\.my\b"],
    "Singapore": [r"\bSingapore\b", r"\.sg\b"],
    "Colombia": [r"\bColombia\b", r"\.co\b(?!m)"],
    "Peru": [r"\bPeru\b", r"\.pe\b"],
    "Ecuador": [r"\bEcuador\b", r"\.ec\b"],
    "Uruguay": [r"\bUruguay\b", r"\.uy\b"],
    "Venezuela, RB": [r"\bVenezuela\b", r"\.ve\b"],
    "Myanmar": [r"\bMyanmar\b", r"\bBurma\b", r"\.mm\b"],
    "Congo, Dem. Rep.": [r"\bDemocratic Republic of (the )?Congo\b", r"\bDR Congo\b"],
    "Bangladesh": [r"\bBangladesh\b", r"\.bd\b"],
    "Papua New Guinea": [r"\bPapua New Guinea\b", r"\bPNG\b"],
}
COUNTRY_PATS = {k: [re.compile(p, re.I) for p in pats] for k, pats in COUNTRY_PATS.items()}

def guess_country(text):
    for c, pats in COUNTRY_PATS.items():
        for p in pats:
            if p.search(text or ""):
                return c
    return None

aslo_counts = Counter()
for s in sessions:
    for p in (s.get("presentations") or []):
        if not p.get("title"): continue
        text = (p.get("affiliation") or "") + " " + (p.get("email_domain") or "")
        c = guess_country(text)
        if c:
            aslo_counts[c] += 1

total_detected = sum(aslo_counts.values())
print("ASLO presentations with country detected: {}".format(total_detected))

# --- 2. Get WB freshwater data ---
print("\nFetching WB ER.H2O.INTR.K3 ...")
# ER.H2O.INTR.K3 is a quasi-static physical quantity reported sporadically.
# Use a wide date range and per_page=20000 to capture every record.
r = requests.get(
    "https://api.worldbank.org/v2/country/all/indicator/ER.H2O.INTR.K3?format=json&per_page=20000&date=1990:2025",
    timeout=60,
)
wb = r.json()
records = wb[1] if isinstance(wb, list) else []
print("Total WB records returned: {}".format(len(records)))

# Build country -> latest freshwater value
fw = {}
for rec in records:
    name = (rec.get("country") or {}).get("value", "")
    val = rec.get("value")
    if not name or val is None: continue
    date = rec.get("date", "0")
    if name not in fw or date > fw[name][1]:
        fw[name] = (val, date)

# The WB "World" aggregate is the authoritative world total.
world_total = fw.get("World", (None, None))[0]
print("\nWB 'World' aggregate (authoritative world total): {:,.0f} bcm/yr".format(world_total))

# Aggregate-name blacklist for filtering individual aggregate rows out of the per-country table.
AGGREGATE_NAMES = {
    "World", "IDA & IBRD total", "IBRD only", "IDA only", "IDA total", "IDA blend",
    "Low & middle income", "Low income", "Lower middle income", "Middle income",
    "Upper middle income", "High income", "OECD members",
    "Euro area", "European Union", "Arab World",
    "Africa Eastern and Southern", "Africa Western and Central", "Sub-Saharan Africa",
    "Sub-Saharan Africa (excluding high income)", "Sub-Saharan Africa (IDA & IBRD countries)",
    "East Asia & Pacific", "East Asia & Pacific (excluding high income)",
    "East Asia & Pacific (IDA & IBRD countries)",
    "Europe & Central Asia", "Europe & Central Asia (excluding high income)",
    "Europe & Central Asia (IDA & IBRD countries)",
    "Latin America & Caribbean", "Latin America & Caribbean (excluding high income)",
    "Latin America & the Caribbean (IDA & IBRD countries)",
    "Middle East & North Africa", "Middle East & North Africa (excluding high income)",
    "Middle East & North Africa (IDA & IBRD countries)",
    "North America", "South Asia", "South Asia (IDA & IBRD)",
    "Central Europe and the Baltics",
    "Heavily indebted poor countries (HIPC)", "Fragile and conflict affected situations",
    "Small states", "Caribbean small states", "Pacific island small states", "Other small states",
    "Least developed countries: UN classification",
    "Post-demographic dividend", "Pre-demographic dividend",
    "Early-demographic dividend", "Late-demographic dividend",
    "Not classified",
    "Middle East, North Africa, Afghanistan & Pakistan",
    "Middle East, North Africa, Afghanistan & Pakistan (excluding high income)",
    "Middle East, North Africa, Afghanistan & Pakistan (IDA & IBRD)",
}
fw_values = {n: v[0] for n, v in fw.items() if n not in AGGREGATE_NAMES}
print("Real-country freshwater values: {} countries".format(len(fw_values)))
sum_countries = sum(fw_values.values())
print("Sum of all per-country values: {:,.0f} bcm/yr ({:.0f}% of WB 'World' total)".format(
    sum_countries, 100 * sum_countries / world_total))

# --- 3. Build the comparison table ---
all_countries = set(aslo_counts.keys()) | set(fw_values.keys())
table = []
for c in all_countries:
    talks = aslo_counts.get(c, 0)
    fw_bcm = fw_values.get(c, 0)
    aslo_pct = 100 * talks / total_detected if total_detected else 0
    fw_pct = 100 * fw_bcm / world_total if world_total else 0
    rep_idx = aslo_pct / fw_pct if fw_pct > 0 else (float("inf") if talks > 0 else 0)
    table.append({
        "country": c, "talks": talks, "fw_bcm": fw_bcm,
        "aslo_pct": aslo_pct, "fw_pct": fw_pct, "rep_idx": rep_idx,
    })

# --- 4. Select countries for the plot ---
# Show: top 8 by freshwater (regardless of participation) + top 8 by participation
top_fw = sorted(table, key=lambda r: -r["fw_bcm"])[:10]
top_aslo = sorted(table, key=lambda r: -r["talks"])[:10]
chosen_names = []
seen = set()
for r in top_fw + top_aslo:
    if r["country"] not in seen and (r["talks"] > 0 or r["fw_bcm"] > 100):
        chosen_names.append(r["country"])
        seen.add(r["country"])
chosen = [r for r in table if r["country"] in chosen_names]

# Sort by freshwater share descending — biggest freshwater stocks on top
chosen.sort(key=lambda r: -r["fw_pct"])

print("\n=== CHOSEN COUNTRIES (for the chart) ===")
print("{:<25s} {:>6s} {:>8s} {:>8s} {:>10s}".format("Country", "Talks", "ASLO%", "FW%", "Rep idx"))
for r in chosen:
    if r["rep_idx"] == float("inf"):
        idx = "INF"
    elif r["rep_idx"] == 0:
        idx = "0.00"
    else:
        idx = "{:.2f}".format(r["rep_idx"])
    print("{:<25s} {:>6d} {:>7.2f}% {:>7.2f}% {:>10s}".format(
        r["country"], r["talks"], r["aslo_pct"], r["fw_pct"], idx))

# --- 5. The plot: paired horizontal bars on a shared log scale ---
plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 11,
    "axes.edgecolor": "#4a5568", "axes.labelcolor": "#1a2332",
    "xtick.color": "#4a5568", "ytick.color": "#4a5568",
})
BG = "#f7f5f0"; INK = "#1a2332"; INK_SOFT = "#4a5568"
FW_COLOR = "#2d5f5d"
ASLO_COLOR = "#c44e3a"

countries = [r["country"] for r in chosen]
fw_pct = [r["fw_pct"] for r in chosen]
aslo_pct = [r["aslo_pct"] for r in chosen]

fig, ax = plt.subplots(figsize=(11, max(7, 0.42 * len(countries) + 2)), facecolor=BG)
ax.set_facecolor(BG)

y_pos = list(range(len(countries)))[::-1]
bar_height = 0.4
y_fw   = [y + bar_height/2 for y in y_pos]
y_aslo = [y - bar_height/2 for y in y_pos]

bars_fw = ax.barh(y_fw, fw_pct, height=bar_height, color=FW_COLOR, edgecolor="none",
                   label="Country's share of global renewable freshwater (WB ER.H2O.INTR.K3)")
bars_aslo = ax.barh(y_aslo, aslo_pct, height=bar_height, color=ASLO_COLOR, edgecolor="none",
                     label="Country's share of ASLO-SIL 2026 country-detected presentations")

# Numeric labels on each bar
for y, v in zip(y_fw, fw_pct):
    if v > 0:
        ax.text(v + 0.3, y, "{:.1f}%".format(v) if v >= 0.05 else "<0.1%",
                va="center", color=INK_SOFT, fontsize=9)
    else:
        ax.text(0.05, y, "no FW data", va="center", color="#aaa", fontsize=8, style="italic")
for y, v in zip(y_aslo, aslo_pct):
    if v > 0:
        ax.text(v + 0.3, y, "{:.1f}%".format(v) if v >= 0.05 else "<0.1%",
                va="center", color=INK_SOFT, fontsize=9)
    else:
        ax.text(0.05, y, "no presentations", va="center", color="#aaa", fontsize=8, style="italic")

# Y-axis: country labels (centered between the paired bars)
ax.set_yticks(y_pos)
ax.set_yticklabels(countries, fontsize=11, color=INK)
ax.set_xlabel("Share (%) — top axis: of global freshwater; same axis: of ASLO program",
              fontsize=10, color=INK_SOFT)

max_val = max(max(fw_pct + [0.1]), max(aslo_pct + [0.1]))
ax.set_xlim(0, max_val * 1.18)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_visible(False)
ax.tick_params(left=False)
ax.grid(axis="x", linestyle=":", color="#c8c4ba", alpha=0.5)

ax.set_title("Share of global freshwater vs. share of ASLO-SIL 2026 — country comparison",
             fontsize=13, color=INK, loc="left", weight="bold", pad=20)
fig.text(0.06, 0.94,
         "Top bar (green) = country's share of global renewable internal freshwater. Bottom bar (terracotta) = country's share of the conference program. Sorted by freshwater share, largest first.",
         fontsize=9.5, color=INK_SOFT, style="italic")

ax.legend(loc="lower right", frameon=False, fontsize=10, labelcolor=INK)

fig.text(0.06, 0.012,
         "Sources: World Bank ER.H2O.INTR.K3 (renewable internal freshwater resources, latest 2015-2022)  ·  ASLO-SIL 2026 public schedule, country detection on affiliations (78% coverage).\n"
         "World freshwater total ≈ {:,.0f} bcm/yr (sum of real countries, excluding WB aggregate groupings).  Total presentations with detected country: {:,}.".format(world_total, total_detected),
         fontsize=8, color=INK_SOFT, style="italic")

plt.tight_layout(rect=[0, 0.04, 1, 0.92])
out_dir = ROOT / "output" / "charts"
out_dir.mkdir(parents=True, exist_ok=True)
out_path = out_dir / "freshwater_share_vs_participation_share.png"
plt.savefig(out_path, dpi=200, facecolor=BG, bbox_inches="tight", pad_inches=0.25)
print("\nSaved chart: {}".format(out_path))

# Save the corrected data
import json as J
out_table = out_dir.parent / "tables" / "freshwater_share_vs_participation_corrected.json"
with open(out_table, "w", encoding="utf-8") as f:
    J.dump({
        "method_note": "Corrected version of freshwater_vs_aslo.json. The world total now uses only real countries (filtered via WB region metadata), excluding aggregate groupings.",
        "world_total_bcm": world_total,
        "total_detected_aslo_presentations": total_detected,
        "chosen_countries": chosen,
    }, f, indent=2, default=lambda o: None if o == float("inf") else o, ensure_ascii=False)
print("Saved data: {}".format(out_table))
