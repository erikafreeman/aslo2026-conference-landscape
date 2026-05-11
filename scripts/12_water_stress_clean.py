"""
Cleaner single-panel water-stress chart.

One horizontal bar per country = water stress (log scale, red).
A small green dot to the left of the country name = number of ASLO talks
(no dot = no presentations).
Country name itself includes the talk count for redundancy.

Fewer countries (top 15 most-stressed + a few comparators at the bottom)
and much more vertical breathing room than the two-panel version.
"""
import json, re, requests
from pathlib import Path
from collections import Counter
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent.parent

# --- ASLO participation (re-use country detection) ---
with open(ROOT / "data" / "sessions_all_public.json", "r", encoding="utf-8") as f:
    sessions = [json.loads(line) for line in f if line.strip()]

COUNTRY_PATS = {
    "United States": [r"\bUSA\b", r"\bUnited States\b", r"\.edu\b", r"\.gov\b"],
    "Canada": [r"\bCanada\b", r"\bQu[eé]bec\b(?!.*France)", r"Ontario", r"British Columbia", r"\.ca\b"],
    "Germany": [r"\bGermany\b", r"Berlin\b(?! State)", r"M[uü]nchen", r"Leibniz", r"Helmholtz", r"\.de\b"],
    "United Kingdom": [r"\bUK\b", r"\bUnited Kingdom\b", r"\bEngland\b", r"\bScotland\b", r"Cambridge\b", r"Oxford\b", r"\.uk\b"],
    "France": [r"\bFrance\b", r"\bParis\b", r"CNRS", r"IFREMER", r"\.fr\b"],
    "China": [r"\bChina\b", r"Beijing", r"Shanghai", r"Nanjing", r"\.cn\b"],
    "Netherlands": [r"\bNetherlands\b", r"Wageningen", r"\bNIOZ\b", r"\.nl\b"],
    "Spain": [r"\bSpain\b", r"\bMadrid\b", r"Barcelona\b", r"CSIC", r"\.es\b"],
    "Italy": [r"\bItaly\b", r"\bRoma\b", r"Milano", r"\.it\b"],
    "Australia": [r"\bAustralia\b", r"CSIRO", r"\.au\b"],
    "Brazil": [r"\bBrazil\b", r"S[aã]o Paulo", r"Rio de Janeiro", r"\.br\b"],
    "Japan": [r"\bJapan\b", r"Tokyo", r"\.jp\b"],
    "Sweden": [r"\bSweden\b", r"Uppsala", r"Stockholm", r"\.se\b"],
    "Austria": [r"\bAustria\b", r"Vienna", r"WasserCluster", r"\.at\b"],
    "Israel": [r"\bIsrael\b", r"\.il\b"],
    "Saudi Arabia": [r"\bSaudi Arabia\b"],
    "United Arab Emirates": [r"\bUAE\b", r"United Arab Emirates"],
    "Egypt, Arab Rep.": [r"\bEgypt\b", r"\.eg\b"],
    "India": [r"\bIndia\b", r"\.in\b"],
    "Russian Federation": [r"\bRussia\b", r"Moscow", r"\.ru\b"],
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

# --- WB water-stress data ---
r = requests.get(
    "https://api.worldbank.org/v2/country/all/indicator/ER.H2O.FWST.ZS?format=json&per_page=20000&date=1990:2025",
    timeout=60,
)
records = r.json()[1] if isinstance(r.json(), list) else []

AGGREGATE_NAMES = {
    "World", "IDA & IBRD total", "IBRD only", "IDA only", "IDA total", "IDA blend",
    "Low & middle income", "Low income", "Lower middle income", "Middle income",
    "Upper middle income", "High income", "OECD members", "Euro area", "European Union",
    "Arab World", "North America", "South Asia", "Central Europe and the Baltics",
    "Heavily indebted poor countries (HIPC)", "Fragile and conflict affected situations",
    "Small states", "Caribbean small states", "Pacific island small states", "Other small states",
    "Least developed countries: UN classification", "Not classified",
}
def is_agg(n):
    if n in AGGREGATE_NAMES: return True
    return any(p in n for p in [
        "Sub-Saharan", "East Asia & Pacific", "Europe & Central Asia",
        "Latin America & Caribbean", "Latin America & the Caribbean",
        "Middle East & North Africa", "Middle East, North Africa",
        "Post-demographic", "Pre-demographic", "Early-demographic", "Late-demographic",
        "Africa Eastern", "Africa Western",
    ])

stress = {}
for rec in records:
    name = (rec.get("country") or {}).get("value", "")
    val = rec.get("value")
    if not name or val is None or is_agg(name): continue
    date = rec.get("date", "0")
    if name not in stress or date > stress[name][1]:
        stress[name] = (val, date)

# --- Curate: top 12 most-stressed + 4 low-stress comparators ---
all_with_stress = [(n, v[0], aslo_counts.get(n, 0)) for n, v in stress.items()]
top_stress = sorted(all_with_stress, key=lambda r: -r[1])[:12]

# Low-stress comparators: pick a few with high ASLO share or large freshwater
comparators_priority = ["United States", "Germany", "Canada", "Brazil"]
comparators = []
for name in comparators_priority:
    if name in stress:
        comparators.append((name, stress[name][0], aslo_counts.get(name, 0)))
    elif name == "Brazil":
        # Brazil may not have a recent stress value
        # try alternate names
        for alt in ["Brazil", "Brazilian"]:
            for n2 in stress:
                if alt.lower() in n2.lower():
                    comparators.append((n2, stress[n2][0], aslo_counts.get(name, 0)))
                    break

# Combine + dedupe
seen = set()
chosen = []
for entry in top_stress + comparators:
    if entry[0] not in seen:
        chosen.append(entry); seen.add(entry[0])

# Sort by stress descending so the most-stretched are at top
chosen.sort(key=lambda r: -r[1])

print("=== CHOSEN COUNTRIES ===")
print("{:<25s} {:>10s} {:>10s}".format("Country", "Stress %", "ASLO talks"))
for c, s, t in chosen:
    print("{:<25s} {:>9.1f}% {:>10d}".format(c, s, t))

# --- Plot ---
plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 11.5,
    "axes.edgecolor": "#4a5568", "axes.labelcolor": "#1a2332",
    "xtick.color": "#4a5568", "ytick.color": "#4a5568",
})
BG = "#f7f5f0"; INK = "#1a2332"; INK_SOFT = "#4a5568"
STRESS = "#c44e3a"; PRESENT = "#2d5f5d"; ABSENT = "#c8c4ba"

fig, ax = plt.subplots(figsize=(12, max(9, 0.6 * len(chosen) + 3)), facecolor=BG)
ax.set_facecolor(BG)

y_pos = list(range(len(chosen)))[::-1]
stress_vals = [s for _, s, _ in chosen]
talks = [t for _, _, t in chosen]
countries = [c for c, _, _ in chosen]

ax.barh(y_pos, stress_vals, height=0.6, color=STRESS, edgecolor="none")

# Value labels at end of each bar
for y, v in zip(y_pos, stress_vals):
    if v >= 1000:
        label = "{:,.0f}%".format(v)
    elif v >= 100:
        label = "{:.0f}%".format(v)
    else:
        label = "{:.0f}%".format(v) if v >= 10 else "{:.1f}%".format(v)
    ax.text(v * 1.15, y, label, va="center", color=INK_SOFT, fontsize=11)

# Y-tick labels: country + talk-count annotation (with a coloured dot prefix)
y_labels = []
for c, s, t in chosen:
    if t > 0:
        # Present at meeting
        y_labels.append("●  {}  ({} ASLO talk{})".format(c, t, "" if t == 1 else "s"))
    else:
        y_labels.append("○  {}  (no presentations)".format(c))

ax.set_yticks(y_pos)
ax.set_yticklabels(y_labels, fontsize=11.5, color=INK)

# Colour-code the y-tick labels: green dot if present, grey if absent
for i, (_, _, t) in enumerate(chosen):
    yt = ax.get_yticklabels()[len(chosen) - 1 - i]
    # We can't easily multi-colour ticklabels; rely on the text symbol (● vs ○)

ax.set_xscale("log")
ax.set_xlim(0.5, max(stress_vals) * 2.5)
ax.set_xlabel("Water stress — freshwater withdrawal as % of renewable supply  (log scale)",
              fontsize=11, color=INK_SOFT)
ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False); ax.spines["left"].set_visible(False)
ax.tick_params(left=False)
ax.grid(axis="x", which="major", linestyle=":", color="#c8c4ba", alpha=0.4)

# Threshold reference lines — no in-chart text, info goes in caption
for x in [25, 100]:
    ax.axvline(x, color="#8a9a8e", linestyle="--", linewidth=1, alpha=0.6)

# Title and subtitle in the top margin (well above the chart area)
ax.set_title("Water stress, by country — and who is in the room",
             fontsize=15, color=INK, loc="left", weight="bold", pad=32)
fig.text(0.07, 0.945,
         "Top 12 most-water-stressed countries plus four lower-stress comparators. "
         "Filled dot (●) before the country name = present at ASLO-SIL 2026; open dot (○) = not detected. "
         "Dashed reference lines at 25% (stress threshold) and 100% (withdrawals exceed renewable supply).",
         fontsize=10, color=INK_SOFT, style="italic")

fig.text(0.07, 0.015,
         "Source: World Bank ER.H2O.FWST.ZS (level of water stress, latest 1990–2022); ASLO-SIL 2026 public schedule, country detection on affiliations (~78% coverage).",
         fontsize=8.5, color=INK_SOFT, style="italic")

plt.tight_layout(rect=[0.02, 0.05, 1, 0.89])

out_path = ROOT / "output" / "charts" / "water_stress_clean.png"
plt.savefig(out_path, dpi=200, facecolor=BG, bbox_inches="tight", pad_inches=0.3)
print("\nSaved: {}".format(out_path))
