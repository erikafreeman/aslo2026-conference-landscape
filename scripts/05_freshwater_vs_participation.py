"""
Country-by-country comparison: share of global renewable freshwater resources
vs. share of ASLO-SIL 2026 presentations.

Data sources:
  - Freshwater: World Bank API indicator ER.H2O.INTR.K3 (Renewable internal
    freshwater resources, total, billion cubic meters). Pulled at run time.
  - ASLO participation: sessions_all_public.json (this repo).

For each country we compute:
  - Renewable freshwater (bcm/yr)
  - Number of ASLO-SIL 2026 presentations (country-detected from affiliation)
  - Share of global freshwater
  - Share of ASLO participation
  - Representation index = (ASLO share) / (freshwater share)
    * 1.0 = proportional
    * >1 = participation exceeds freshwater share (high research investment)
    * <1 = freshwater share exceeds participation (room for the meeting to grow)

This is descriptive, not normative. Countries with low representation indices
have made fewer trips to Quebec; that reflects travel/visa/funding realities
more than scientific capacity. The ratio is one lens among many.
"""
import json, re, time
from pathlib import Path
from collections import Counter
import requests
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "sessions_all_public.json"
OUT_CHARTS = ROOT / "output" / "charts"
OUT_TABLES = ROOT / "output" / "tables"
OUT_REPORTS = ROOT / "output" / "reports"
for d in [OUT_CHARTS, OUT_TABLES, OUT_REPORTS]:
    d.mkdir(parents=True, exist_ok=True)

# ============ 1. Pull ASLO country counts ============
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
}
COUNTRY_PATS = {k: [re.compile(p, re.I) for p in pats] for k, pats in COUNTRY_PATS.items()}

def guess_country(text):
    for c, pats in COUNTRY_PATS.items():
        for p in pats:
            if p.search(text or ""):
                return c
    return None

sessions = []
with open(DATA, "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if line:
            sessions.append(json.loads(line))

aslo_counts = Counter()
total_presentations = 0
for s in sessions:
    for p in (s.get("presentations") or []):
        if p.get("title"):
            total_presentations += 1
            text = (p.get("affiliation") or "") + " " + (p.get("email_domain") or "")
            c = guess_country(text)
            if c:
                aslo_counts[c] += 1

print("Country-detected presentations: {} / {}".format(sum(aslo_counts.values()), total_presentations))


# ============ 2. Pull World Bank freshwater data ============
print("\nPulling World Bank renewable freshwater resources (ER.H2O.INTR.K3) ...")
freshwater_bcm = {}
url = "https://api.worldbank.org/v2/country/all/indicator/ER.H2O.INTR.K3"
page = 1
while True:
    r = requests.get(url, params={"format": "json", "per_page": 300, "page": page, "date": "2015:2022"})
    if not r.ok:
        print("  API error: {}".format(r.status_code))
        break
    data = r.json()
    if not isinstance(data, list) or len(data) < 2:
        break
    page_meta, records = data[0], data[1]
    for rec in records:
        country = rec.get("country", {}).get("value")
        val = rec.get("value")
        if country and val is not None:
            # Keep the most recent non-null value per country
            if country not in freshwater_bcm or rec.get("date", "0") > freshwater_bcm[country].get("date", "0"):
                freshwater_bcm[country] = {"value_bcm": val, "date": rec.get("date")}
    if page >= page_meta.get("pages", 1):
        break
    page += 1
    time.sleep(0.1)

# Flatten: just the numeric value
fresh = {c: v["value_bcm"] for c, v in freshwater_bcm.items()}
print("  Got freshwater data for {} countries".format(len(fresh)))

# World total (sum) — used to compute share
world_total_fresh = sum(fresh.values())
print("  World total renewable internal freshwater: {:.0f} bcm/yr".format(world_total_fresh))


# ============ 3. Match and compute ============
total_aslo = sum(aslo_counts.values())

records = []
for country, talks in aslo_counts.items():
    fw = fresh.get(country)
    if fw is None or fw == 0:
        records.append({
            "country": country, "aslo_talks": talks,
            "freshwater_bcm": None, "aslo_share_pct": 100*talks/total_aslo,
            "freshwater_share_pct": None, "rep_index": None,
        })
        continue
    rec = {
        "country": country,
        "aslo_talks": talks,
        "freshwater_bcm": fw,
        "aslo_share_pct": 100 * talks / total_aslo,
        "freshwater_share_pct": 100 * fw / world_total_fresh,
        "rep_index": (talks / total_aslo) / (fw / world_total_fresh),
    }
    records.append(rec)

# Also: countries with significant freshwater BUT no ASLO talks
# Filter out World Bank aggregate groupings (regions, income groups, etc.)
AGGREGATE_PATTERNS = [
    "World", "income", "IDA", "IBRD", "OECD", "Euro area", "European Union",
    "Africa Eastern", "Africa Western", "Sub-Saharan", "Latin America",
    "East Asia & Pacific", "Europe & Central Asia", "Middle East & North Africa",
    "South Asia", "North America", "Central Europe", "Heavily indebted",
    "demographic dividend", "Fragile", "Small states", "Arab World",
    "Caribbean small states", "Pacific island", "Other small states",
    "Least developed", "Post-demographic", "Pre-demographic", "Early-demographic",
    "Late-demographic", "Lower middle", "Upper middle", "Middle income",
    "Low income", "High income",
]
def is_aggregate(name):
    return any(p in name for p in AGGREGATE_PATTERNS)

big_fresh_no_aslo = []
for country, fw in sorted(fresh.items(), key=lambda x: -x[1]):
    if country in aslo_counts: continue
    if is_aggregate(country): continue
    if fw < 100: continue
    big_fresh_no_aslo.append({"country": country, "freshwater_bcm": fw,
                               "freshwater_share_pct": 100*fw/world_total_fresh})
    if len(big_fresh_no_aslo) >= 25:
        break

# Also recompute world total excluding aggregates (more honest)
world_total_real = sum(v for k, v in fresh.items() if not is_aggregate(k))
print("  World total (excluding aggregate groupings): {:.0f} bcm/yr".format(world_total_real))

# Sort by absolute ASLO presence
records_sorted = sorted([r for r in records if r["freshwater_bcm"]],
                         key=lambda x: -x["aslo_talks"])

print("\n{:<22s} {:>8s} {:>10s} {:>8s} {:>8s} {:>10s}".format(
    "Country", "Talks", "Talk%", "FW bcm", "FW%", "Rep idx"))
print("-" * 75)
for r in records_sorted[:30]:
    print("{:<22s} {:>8d} {:>9.1f}% {:>8.0f} {:>7.2f}% {:>10.2f}".format(
        r["country"][:22], r["aslo_talks"], r["aslo_share_pct"],
        r["freshwater_bcm"], r["freshwater_share_pct"], r["rep_index"]))

print("\nCountries with substantial renewable freshwater but no detected ASLO talks:")
for r in big_fresh_no_aslo[:20]:
    print("  {:<22s} {:>6.0f} bcm/yr ({:.2f}% of global)".format(
        r["country"][:22], r["freshwater_bcm"], r["freshwater_share_pct"]))

# Save table
out_json = OUT_TABLES / "freshwater_vs_aslo.json"
with open(out_json, "w", encoding="utf-8") as f:
    json.dump({
        "method": "World Bank ER.H2O.INTR.K3 (Renewable internal freshwater resources, billion m³/yr) matched against ASLO-SIL 2026 presentation counts (country detected from affiliation strings + email TLDs).",
        "queried": "2026-05-11",
        "world_total_freshwater_bcm": world_total_fresh,
        "aslo_total_country_detected": total_aslo,
        "aslo_total_all_presentations": total_presentations,
        "records": sorted(records, key=lambda x: -x["aslo_talks"]),
        "big_freshwater_no_aslo": big_fresh_no_aslo,
        "interpretation_note": "Rep index >1 = country's ASLO share exceeds its freshwater share (strong research investment, possibly proximity advantage). <1 = freshwater share exceeds presentation share. Index is descriptive only; reflects travel/funding/visa realities at least as much as scientific capacity.",
    }, f, indent=2, ensure_ascii=False)
print("\nSaved: {}".format(out_json))


# ============ 4. Charts ============
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11,
                     "axes.edgecolor": "#4a5568", "axes.labelcolor": "#1a2332",
                     "xtick.color": "#4a5568", "ytick.color": "#4a5568"})
BG = "#f7f5f0"; INK = "#1a2332"; INK_SOFT = "#4a5568"
ACCENT = "#2d5f5d"; HI = "#c44e3a"; NEUTRAL = "#8a9a8e"

# Chart A: scatter log-log freshwater vs presentations
plot_recs = [r for r in records if r["freshwater_bcm"] and r["aslo_talks"] >= 1]
fig, ax = plt.subplots(figsize=(11, 8), facecolor=BG)
ax.set_facecolor(BG)

xs = [r["freshwater_bcm"] for r in plot_recs]
ys = [r["aslo_talks"] for r in plot_recs]

# Colour-code by representation index
def col(r):
    if r["rep_index"] is None: return NEUTRAL
    if r["rep_index"] >= 1.0: return ACCENT
    return HI

cols = [col(r) for r in plot_recs]

ax.scatter(xs, ys, s=80, c=cols, alpha=0.85, edgecolor=BG, linewidth=1.5)

# Label each point
for r in plot_recs:
    ha = "left"
    offset = 1.1
    ax.annotate(r["country"], (r["freshwater_bcm"], r["aslo_talks"]),
                 xytext=(r["freshwater_bcm"] * offset, r["aslo_talks"]),
                 fontsize=8, color=INK, va="center", ha=ha)

# 1:1 reference line (proportional representation)
# In a world where ASLO share == freshwater share, log(talks) = log(fw) + const
# Constant: log(total_aslo) - log(world_total_fresh)
import numpy as np
x_ref = np.logspace(np.log10(min(xs)*0.5), np.log10(max(xs)*2), 100)
y_ref = x_ref * (total_aslo / world_total_fresh)
ax.plot(x_ref, y_ref, "--", color=INK_SOFT, alpha=0.6, lw=1.5, label="Proportional (rep. index = 1)")

ax.set_xscale("log")
ax.set_yscale("log")
ax.set_xlabel("Renewable internal freshwater resources (bcm/yr, log scale)", fontsize=12, color=INK_SOFT)
ax.set_ylabel("ASLO-SIL 2026 presentations (log scale)", fontsize=12, color=INK_SOFT)
ax.set_title("Country participation vs. freshwater endowment\n(green: participation exceeds freshwater share · red: freshwater exceeds participation)",
             fontsize=13, color=INK, loc="left", weight="bold", pad=15)
ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
ax.grid(True, which="both", linestyle=":", color="#c8c4ba", alpha=0.5)
ax.legend(loc="upper left", frameon=False, fontsize=10, labelcolor=INK)

fig.text(0.06, 0.015,
         "Data: World Bank ER.H2O.INTR.K3 (renewable internal freshwater) · ASLO-SIL 2026 program (1,461 presentations, country detected from affiliations)",
         fontsize=8, color=INK_SOFT, style="italic", ha="left")
plt.tight_layout(rect=[0, 0.04, 1, 0.95])
plt.savefig(OUT_CHARTS / "freshwater_vs_participation_scatter.png", dpi=200, facecolor=BG, bbox_inches="tight")
plt.close()
print("Saved scatter: {}".format(OUT_CHARTS / "freshwater_vs_participation_scatter.png"))


# Chart B: ranked representation index bar chart
ranked = sorted([r for r in records if r["rep_index"] is not None and r["aslo_talks"] >= 3],
                 key=lambda x: -x["rep_index"])
labels = [r["country"] for r in ranked]
indices = [r["rep_index"] for r in ranked]
cols2 = [ACCENT if i >= 1 else HI for i in indices]

fig, ax = plt.subplots(figsize=(11, 10), facecolor=BG)
ax.set_facecolor(BG)
y_pos = list(range(len(labels)))[::-1]
ax.barh(y_pos, indices, color=cols2, height=0.7, edgecolor="none")
ax.axvline(1.0, color=INK_SOFT, ls="--", lw=1.2)
for yp, r, idx in zip(y_pos, ranked, indices):
    if idx < 50:  # don't label extreme outliers
        ax.text(idx + 0.5, yp, "{:.1f} ({} talks)".format(idx, r["aslo_talks"]),
                va="center", color=INK_SOFT, fontsize=9)
ax.set_yticks(y_pos); ax.set_yticklabels(labels, fontsize=10, color=INK)
ax.set_xlabel("Representation index — ASLO share ÷ freshwater share (log-spaced markers)", fontsize=10, color=INK_SOFT)
ax.set_title("Representation index by country\n(values > 1: ASLO presence exceeds proportional share of global freshwater · values < 1: room for the meeting to grow into these countries' freshwater stake)",
             fontsize=12, color=INK, loc="left", weight="bold", pad=15)
ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
ax.grid(axis="x", linestyle=":", color="#c8c4ba", alpha=0.5)
plt.tight_layout()
plt.savefig(OUT_CHARTS / "freshwater_rep_index.png", dpi=200, facecolor=BG, bbox_inches="tight")
plt.close()
print("Saved ranked bar: {}".format(OUT_CHARTS / "freshwater_rep_index.png"))

# ============ 5. Markdown report ============
sorted_by_idx = sorted([r for r in records if r["rep_index"] is not None],
                       key=lambda x: -x["rep_index"])
top_over = sorted_by_idx[:10]
top_under = sorted([r for r in records if r["rep_index"] is not None and r["aslo_talks"] >= 3],
                    key=lambda x: x["rep_index"])[:10]

report = """# Country participation vs. freshwater endowment — ASLO-SIL 2026

*Generated 2026-05-11. Data: World Bank ER.H2O.INTR.K3 (renewable internal freshwater resources, billion cubic metres per year) cross-referenced against the ASLO-SIL 2026 program (1,461 presentations, country detected from affiliation strings).*

## What this is

For each country with both a freshwater-resource value and detectable presentations, we compute:

- **Renewable freshwater** (bcm/yr) — World Bank latest available 2015-2022
- **ASLO presentations** in the 2026 program
- **Freshwater share** of the global total
- **ASLO share** of country-detected presentations
- **Representation index** = ASLO share ÷ freshwater share
  - Index = 1.0 → proportional
  - Index > 1 → participation exceeds the country's freshwater stake (strong research investment, often a proximity / wealth signal)
  - Index < 1 → the country's freshwater stake exceeds its participation; an obvious place for the meeting to grow into

The index is **descriptive, not normative.** Low-index countries are not "doing less science." They reflect travel costs, visa friction, currency strength, and historical institutional networks at least as much as scientific capacity. The number simply asks where the freshwater is, and where the people in the room come from.

## Headline numbers

- Total country-detected presentations: **{n_detect}** of {n_total}
- World renewable internal freshwater (sum of WB country values): **{world:.0f} bcm/yr**
- Countries represented with both metrics: **{n_match}**

## Top countries by ASLO presentations (with freshwater context)

| Country | Talks | % of ASLO | Freshwater (bcm/yr) | % of global FW | Rep index |
|---|---:|---:|---:|---:|---:|
{top_table}

## Countries where the meeting punches well above its freshwater stake

These are countries with strong research investment and historical participation. Their participation exceeds their proportional freshwater share — usually a mix of wealth, proximity, and institutional density.

| Country | Talks | Freshwater (bcm) | Rep index |
|---|---:|---:|---:|
{over_table}

## Countries with significant freshwater and growing participation

These are countries whose freshwater resources are large relative to their meeting participation. Each one is a place where the field's community could grow — and where local researchers may have the deepest direct knowledge of systems that matter at the global scale.

| Country | Talks | Freshwater (bcm) | % of global FW | Rep index |
|---|---:|---:|---:|---:|
{under_table}

## Countries with large freshwater resources and no detected ASLO talks

These are the freshwater systems most absent from the room. Each represents a partnership opportunity for the next meeting.

| Country | Freshwater (bcm/yr) | % of global FW |
|---|---:|---:|
{no_aslo_table}

## The structural picture

The world's top freshwater countries by absolute volume are, roughly: Brazil, Russia, Canada, USA, Indonesia, China, Colombia, Peru, DRC, India, Venezuela, Bangladesh, Myanmar, Argentina, Chile.

Of these:
- **Canada and USA** are over-represented relative to their freshwater stake — the proximity and historical-institution effects.
- **Brazil, Indonesia, Colombia, Peru, India, Venezuela, Bangladesh, Myanmar, DRC** are under-represented or absent — and each holds a meaningful slice of the global hydrological cycle.
- **Sweden, Finland, Norway, Switzerland, Netherlands** are over-represented relative to freshwater — small-country effect, but also a deep European institute network.

This is exactly the picture the meeting's **Amplifying Voices** track is built to address. The structural scaffold is in place. The next chapter is bringing more of those high-freshwater, low-participation countries into the rest of the program.

## Caveats

- **Country detection from affiliation strings ≈ 78% complete.** Smaller countries are likely undercounted.
- **Renewable internal freshwater** excludes water flowing in from upstream countries. The "total renewable" metric (which includes inflows) would shift Bangladesh, Egypt, the Netherlands upward — but ASLO/SIL is more typically interested in within-country aquatic systems, so internal renewable is the better fit.
- **The metric does not distinguish lake-rich, river-rich, and rain-rich countries.** A more SIL-specific lens would weight by inland water area (countries like Finland, Sweden, Canada become even more visible) or by lake count.
- **The representation index says nothing about quality of contributions** — it is a volume comparison, not a value judgment.
""".format(
    n_detect=total_aslo, n_total=total_presentations, world=world_total_fresh,
    n_match=len([r for r in records if r["freshwater_bcm"]]),
    top_table="\n".join(
        "| {} | {} | {:.1f}% | {:.0f} | {:.2f}% | {:.2f} |".format(
            r["country"], r["aslo_talks"], r["aslo_share_pct"],
            r["freshwater_bcm"], r["freshwater_share_pct"], r["rep_index"])
        for r in records_sorted[:20]),
    over_table="\n".join(
        "| {} | {} | {:.0f} | {:.1f} |".format(
            r["country"], r["aslo_talks"], r["freshwater_bcm"], r["rep_index"])
        for r in top_over),
    under_table="\n".join(
        "| {} | {} | {:.0f} | {:.2f}% | {:.2f} |".format(
            r["country"], r["aslo_talks"], r["freshwater_bcm"],
            r["freshwater_share_pct"], r["rep_index"])
        for r in top_under),
    no_aslo_table="\n".join(
        "| {} | {:.0f} | {:.2f}% |".format(
            r["country"], r["freshwater_bcm"], r["freshwater_share_pct"])
        for r in big_fresh_no_aslo[:15]),
)

out_md = OUT_REPORTS / "freshwater_vs_participation.md"
with open(out_md, "w", encoding="utf-8") as f:
    f.write(report)
print("Saved report: {}".format(out_md))
