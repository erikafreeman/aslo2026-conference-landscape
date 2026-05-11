"""
Where water resources are under pressure — countries ordered by water-stress
(freshwater withdrawal as % of renewable resources), paired with ASLO-SIL 2026
participation. Complements scripts/09 (which orders by absolute volume).

Indicator: World Bank ER.H2O.FWST.ZS — 'Level of water stress: freshwater
withdrawal as a proportion of available freshwater resources.' Values >25%
typically indicate water stress; >70% indicates extreme stress; >100% means
withdrawals exceed renewable supply (the system is mining stored water or
relying on inflows from neighbours).
"""
import json, re, requests
from pathlib import Path
from collections import Counter
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

ROOT = Path(__file__).resolve().parent.parent

# --- 1. ASLO participation by country (re-use country detection from script 09) ---
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
    "Russian Federation": [r"\bRussia\b", r"Moscow", r"\.ru\b"],
    "Iran, Islamic Rep.": [r"\bIran\b", r"Tehran", r"\.ir\b"],
    "Philippines": [r"\bPhilippines\b", r"\.ph\b"],
    "Kenya": [r"\bKenya\b", r"\.ke\b"],
    "Egypt, Arab Rep.": [r"\bEgypt\b", r"\.eg\b"],
    "Indonesia": [r"\bIndonesia\b", r"\.id\b"],
    "Malaysia": [r"\bMalaysia\b", r"\.my\b"],
    "Singapore": [r"\bSingapore\b", r"\.sg\b"],
    "Colombia": [r"\bColombia\b", r"\.co\b(?!m)"],
    "Peru": [r"\bPeru\b", r"\.pe\b"],
    "Saudi Arabia": [r"\bSaudi Arabia\b"],
    "United Arab Emirates": [r"\bUAE\b", r"United Arab Emirates"],
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

total_aslo = sum(aslo_counts.values())
print("Total country-detected presentations: {}".format(total_aslo))

# --- 2. Get water-stress indicator from WB ---
print("\nFetching WB ER.H2O.FWST.ZS (Level of water stress) ...")
r = requests.get(
    "https://api.worldbank.org/v2/country/all/indicator/ER.H2O.FWST.ZS?format=json&per_page=20000&date=1990:2025",
    timeout=60,
)
wb = r.json()
records = wb[1] if isinstance(wb, list) else []
print("WB records: {}".format(len(records)))

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

stress = {}
for rec in records:
    name = (rec.get("country") or {}).get("value", "")
    val = rec.get("value")
    if not name or val is None: continue
    if name in AGGREGATE_NAMES: continue
    date = rec.get("date", "0")
    if name not in stress or date > stress[name][1]:
        stress[name] = (val, date)

stress_vals = {n: v[0] for n, v in stress.items()}
print("Countries with water-stress data: {}".format(len(stress_vals)))

# --- 3. Build the comparison table ---
all_countries = set(aslo_counts.keys()) | set(stress_vals.keys())
table = []
for c in all_countries:
    talks = aslo_counts.get(c, 0)
    s_val = stress_vals.get(c)
    aslo_pct = 100 * talks / total_aslo if total_aslo else 0
    table.append({
        "country": c, "talks": talks,
        "stress_pct": s_val,
        "aslo_pct": aslo_pct,
    })

# --- 4. Choose countries: union of top 10 by stress + top 10 by talks ---
have_both = [r for r in table if r["stress_pct"] is not None and r["talks"] > 0]
no_aslo_high_stress = [r for r in table if r["stress_pct"] is not None and r["talks"] == 0 and r["stress_pct"] > 30]
top_stress = sorted([r for r in table if r["stress_pct"] is not None], key=lambda r: -r["stress_pct"])[:12]
top_aslo = sorted([r for r in table if r["talks"] > 0], key=lambda r: -r["talks"])[:12]

seen = set()
chosen = []
for r in top_stress + top_aslo:
    if r["country"] not in seen:
        chosen.append(r); seen.add(r["country"])
chosen = [r for r in chosen if r["stress_pct"] is not None]  # need stress to plot
chosen.sort(key=lambda r: -r["stress_pct"])  # highest stress at top

print("\n=== CHOSEN COUNTRIES (sorted by water stress, highest first) ===")
print("{:<25s} {:>6s} {:>8s} {:>10s}".format("Country", "Talks", "ASLO%", "Stress %"))
for r in chosen:
    print("{:<25s} {:>6d} {:>7.2f}% {:>9.1f}%".format(
        r["country"], r["talks"], r["aslo_pct"], r["stress_pct"]))

# --- 5. The chart ---
plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 11,
    "axes.edgecolor": "#4a5568", "axes.labelcolor": "#1a2332",
    "xtick.color": "#4a5568", "ytick.color": "#4a5568",
})
BG = "#f7f5f0"; INK = "#1a2332"; INK_SOFT = "#4a5568"
STRESS_COLOR = "#c44e3a"
ASLO_COLOR = "#2d5f5d"

countries = [r["country"] for r in chosen]
stress_pct = [r["stress_pct"] for r in chosen]
aslo_pct = [r["aslo_pct"] for r in chosen]

# Two side-by-side panels with shared Y-axis. Stress on the left (log scale,
# because Gulf-state values reach 3,800% and would otherwise crush everything
# below). ASLO share on the right (linear, 0-40%).
fig, (ax1, ax2) = plt.subplots(
    1, 2, figsize=(13, max(7, 0.45 * len(countries) + 2)),
    facecolor=BG, sharey=True, gridspec_kw={"width_ratios": [3, 2], "wspace": 0.05}
)
ax1.set_facecolor(BG); ax2.set_facecolor(BG)
y_pos = list(range(len(countries)))[::-1]

# Left panel: water stress (log scale)
ax1.barh(y_pos, stress_pct, height=0.65, color=STRESS_COLOR, edgecolor="none")
for y, v in zip(y_pos, stress_pct):
    if v >= 1000:
        label = "{:,.0f}%".format(v)
    elif v >= 100:
        label = "{:.0f}%".format(v)
    else:
        label = "{:.0f}%".format(v) if v >= 10 else "{:.1f}%".format(v)
    ax1.text(v * 1.12, y, label, va="center", color=INK_SOFT, fontsize=9.5)

ax1.set_xscale("log")
ax1.set_xlim(0.5, max(stress_pct) * 2.5)
ax1.set_xlabel("Water stress: withdrawal as % of renewable freshwater (log scale)",
               fontsize=10, color=INK_SOFT)
# Reference threshold lines
for x, label in [(25, "25% stressed"), (70, "70% high stress"), (100, "100% exceeds renewal")]:
    ax1.axvline(x, color="#8a9a8e", linestyle="--", linewidth=1, alpha=0.6)
    ax1.text(x, len(countries) - 0.4, " " + label, fontsize=8, color="#8a9a8e",
             rotation=90, va="top", ha="left")
ax1.set_yticks(y_pos)
ax1.set_yticklabels(countries, fontsize=11, color=INK)
ax1.spines["top"].set_visible(False); ax1.spines["right"].set_visible(False); ax1.spines["left"].set_visible(False)
ax1.tick_params(left=False)
ax1.grid(axis="x", which="major", linestyle=":", color="#c8c4ba", alpha=0.5)

# Right panel: ASLO share (linear)
ax2.barh(y_pos, aslo_pct, height=0.65, color=ASLO_COLOR, edgecolor="none")
for y, v in zip(y_pos, aslo_pct):
    if v > 0:
        ax2.text(v + max(aslo_pct) * 0.02, y, "{:.1f}%".format(v) if v >= 0.05 else "<0.1%",
                 va="center", color=INK_SOFT, fontsize=9.5)
    else:
        ax2.text(max(aslo_pct) * 0.02, y, "no presentations", va="center",
                 color="#aaa", fontsize=9, style="italic")
ax2.set_xlim(0, max(aslo_pct) * 1.25)
ax2.set_xlabel("Country's share of ASLO-SIL 2026 country-detected presentations",
               fontsize=10, color=INK_SOFT)
ax2.spines["top"].set_visible(False); ax2.spines["right"].set_visible(False); ax2.spines["left"].set_visible(False)
ax2.tick_params(left=False)
ax2.grid(axis="x", linestyle=":", color="#c8c4ba", alpha=0.5)

fig.suptitle("Water stress vs. ASLO-SIL 2026 participation — countries sorted by water stress",
             x=0.06, y=0.97, ha="left", fontsize=13, weight="bold", color=INK)
fig.text(0.06, 0.94,
         "Left panel (red, log scale): freshwater withdrawal as % of available renewable supply (WB ER.H2O.FWST.ZS). "
         "Right panel (green, linear): country's share of the meeting. Countries with the most stretched water resources contribute few or no presentations.",
         fontsize=9.5, color=INK_SOFT, style="italic")

fig.text(0.06, 0.012,
         "Sources: WB ER.H2O.FWST.ZS (level of water stress, latest 1990-2022)  ·  ASLO-SIL 2026 public schedule, country detection on affiliations (78% coverage).\n"
         "Total presentations with detected country: {:,}.".format(total_aslo),
         fontsize=8, color=INK_SOFT, style="italic")

plt.tight_layout(rect=[0, 0.04, 1, 0.92])
out_path = ROOT / "output" / "charts" / "water_stress_vs_participation.png"
plt.savefig(out_path, dpi=200, facecolor=BG, bbox_inches="tight", pad_inches=0.25)
print("\nSaved: {}".format(out_path))

import json as J
out_table = ROOT / "output" / "tables" / "water_stress_vs_participation.json"
with open(out_table, "w", encoding="utf-8") as f:
    J.dump({
        "source": "WB indicator ER.H2O.FWST.ZS (Level of water stress: freshwater withdrawal as a proportion of available freshwater resources)",
        "queried": "2026-05-11",
        "thresholds": {
            "stressed": "stress_pct > 25",
            "highly_stressed": "stress_pct > 70",
            "withdrawals_exceed_renewal": "stress_pct > 100",
        },
        "rows": chosen,
    }, f, indent=2, ensure_ascii=False)
print("Saved data: {}".format(out_table))
