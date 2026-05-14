"""
Build the v3 consolidated UHR-MS community comparison:
  - Horizontal bar chart of all communities + DOM, sorted by size
  - DOM <-> NTS pair highlighted as parallel-literatures
  - Growth-over-time comparison (DOM vs NTS year-by-year)
  - Consolidated CSV + JSON summary
"""
import json, csv
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.patches as patches

RAW = Path(r"G:\My Drive\3-WorkAndPurpose\0-ABC_Lab\06-Teaching_Outreach\1-ConferenceTalks\ASLO2026\_BibliometricAnalysis\raw_data")
CHARTS = Path(r"G:\My Drive\3-WorkAndPurpose\0-ABC_Lab\06-Teaching_Outreach\1-ConferenceTalks\ASLO2026\_BibliometricAnalysis\charts")
DECK_FIG = Path(r"G:\My Drive\3-WorkAndPurpose\0-ABC_Lab\06-Teaching_Outreach\1-ConferenceTalks\ASLO2026\_DECK\figures")
BIB = Path(r"G:\My Drive\3-WorkAndPurpose\0-ABC_Lab\06-Teaching_Outreach\1-ConferenceTalks\ASLO2026\_BibliometricAnalysis")

with open(RAW / "fticr_communities_summary_v2.json") as f:
    v2 = json.load(f)
with open(RAW / "fticr_environmental_nts_v1.json") as f:
    nts = json.load(f)
with open(RAW / "fticr_comprehensive_subdiscipline.json") as f:
    dom = json.load(f)

# Compose comparison
def get_year(yt, y):
    return int(yt.get(str(y), yt.get(y, 0)))

def yt_int(yt):
    return {int(k): int(v) for k, v in yt.items()}

rows = []
rows.append(("DOM science", dom["total_unique_works"], get_year(dom["year_totals"], 2025), yt_int(dom["year_totals"])))
rows.append(("Environmental non-target screening (NTS)", nts["total_unique_works"], nts["year_2025"], yt_int(nts["year_totals"])))
for slug, d in v2["communities"].items():
    rows.append((d["label"], d["total_unique_works"], d["year_2025"], yt_int(d["year_totals"])))

rows.sort(key=lambda r: -r[1])

# ---- Consolidated CSV ----
with open(BIB / "fticr_communities_v3_consolidated.csv", "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f)
    w.writerow(["community", "total_papers_2000_2025", "papers_2025"])
    for label, total, y25, _ in rows:
        w.writerow([label, total, y25])

# ===== Chart 1: horizontal bars, all communities, DOM <-> NTS highlighted =====
BG = "#f7f5f0"
INK = "#1a2332"
INK_SOFT = "#4a5568"
DOM_COLOR = "#2d5f5d"
NTS_COLOR = "#c44e3a"
OTHER = "#8a9a8e"
MUTED = "#c8c4ba"

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 11,
    "axes.edgecolor": INK_SOFT, "axes.labelcolor": INK,
    "xtick.color": INK_SOFT, "ytick.color": INK_SOFT,
})

fig, ax = plt.subplots(figsize=(13, 7.5), facecolor=BG)
ax.set_facecolor(BG)

labels = [r[0] for r in rows]
totals = [r[1] for r in rows]
y25 = [r[2] for r in rows]
y_positions = list(range(len(labels)))[::-1]

def color_for(label):
    if "DOM science" in label:
        return DOM_COLOR
    if "non-target" in label.lower():
        return NTS_COLOR
    return MUTED

colors = [color_for(L) for L in labels]

ax.barh(y_positions, totals, color=colors, edgecolor="none", height=0.7)

for y, total, y25_n, lbl in zip(y_positions, totals, y25, labels):
    is_hl = "DOM science" in lbl or "non-target" in lbl.lower()
    txt_color = "white" if is_hl else INK
    weight = "bold" if is_hl else "normal"
    if total > 700:
        ax.text(total / 2, y, f"{total:,} papers   ({y25_n} in 2025)",
                ha="center", va="center", color=txt_color, fontsize=11, fontweight=weight)
    else:
        ax.text(total + max(totals) * 0.012, y, f"{total:,}   ({y25_n} in 2025)",
                ha="left", va="center", color=INK_SOFT, fontsize=10)

ax.set_yticks(y_positions)
ax.set_yticklabels(labels, fontsize=11, color=INK)
ax.set_xlim(0, max(totals) * 1.18)
ax.set_xlabel("Publications, 2000-2025 (OpenAlex)", fontsize=11, color=INK_SOFT)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_visible(False)
ax.tick_params(left=False)
ax.grid(axis="x", linestyle=":", color=INK_SOFT, alpha=0.25)

# Annotate the pair
ax.annotate("",
            xy=(rows[0][1] + 80, 0 if "DOM science" in labels[-1] else len(labels) - 1 - labels.index("DOM science")),
            xytext=(rows[0][1] + 80, 0 if "non-target" in labels[-1].lower() else len(labels) - 1 - [i for i, L in enumerate(labels) if "non-target" in L.lower()][0]),
            arrowprops=dict(arrowstyle="<->", color=INK_SOFT, lw=1.5))

ax.text(rows[0][1] * 1.04, (len(labels) - 1 - labels.index("DOM science") + len(labels) - 1 - [i for i, L in enumerate(labels) if "non-target" in L.lower()][0]) / 2,
        "Parallel literatures.\nSame instrument, same goal.\nDifferent molecules,\ndifferent community.",
        ha="left", va="center", color=INK_SOFT, fontsize=10, style="italic", linespacing=1.4)

fig.text(0.04, 0.95, "Who uses ultrahigh-resolution MS?",
         fontsize=17, color=INK, ha="left", weight="bold")
fig.text(0.04, 0.91,
         "FT-ICR-MS and Orbitrap publication counts by application community, 2000-2025.",
         fontsize=11, color=INK_SOFT, ha="left", style="italic")

fig.text(0.04, 0.025,
         "OpenAlex strict title_and_abstract.search, deduplicated by work-id (queried 2026-05-14).\n"
         "Each community: instrument variants (FT-ICR / FTICR / Orbitrap / ultrahigh resolution mass) AND community-specific topic phrases. "
         "NTS also includes 'high resolution mass spectrometry' as an instrument variant since that is how the NTS community self-describes; "
         "this is a slightly broader net (455 with strict UHR-MS terms, 1,830 with the broader net used here).",
         fontsize=7.5, color=INK_SOFT, style="italic", ha="left", linespacing=1.5)

plt.subplots_adjust(left=0.32, right=0.97, top=0.86, bottom=0.13)

out1 = CHARTS / "uhrms_communities_comparison_v1.png"
out1_deck = DECK_FIG / "uhrms_communities_comparison_v1.png"
CHARTS.mkdir(parents=True, exist_ok=True)
plt.savefig(out1, dpi=200, facecolor=BG, bbox_inches="tight", pad_inches=0.25)
plt.savefig(out1_deck, dpi=200, facecolor=BG, bbox_inches="tight", pad_inches=0.25)
print(f"Wrote {out1}")
print(f"Wrote {out1_deck}")
plt.close()

# ===== Chart 2: DOM vs NTS growth over time =====
fig, ax = plt.subplots(figsize=(12, 6.5), facecolor=BG)
ax.set_facecolor(BG)

years = list(range(2000, 2026))
dom_yt = yt_int(dom["year_totals"])
nts_yt = yt_int(nts["year_totals"])
dom_y = [dom_yt.get(y, 0) for y in years]
nts_y = [nts_yt.get(y, 0) for y in years]

ax.bar([y - 0.2 for y in years], dom_y, width=0.4, color=DOM_COLOR, label="DOM science", edgecolor="none")
ax.bar([y + 0.2 for y in years], nts_y, width=0.4, color=NTS_COLOR, label="Environmental NTS", edgecolor="none")

ax.set_xlim(1999.5, 2025.5)
ax.set_xlabel("Year", fontsize=11, color=INK_SOFT)
ax.set_ylabel("Publications per year", fontsize=11, color=INK_SOFT)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.grid(axis="y", linestyle=":", color=INK_SOFT, alpha=0.25)
ax.legend(loc="upper left", frameon=False, fontsize=11, labelcolor=INK)

# Annotate 2025 totals
ax.annotate(f"DOM 2025: {dom_y[-1]}", xy=(2025 - 0.2, dom_y[-1]), xytext=(2024, dom_y[-1] + 30),
            color=DOM_COLOR, fontsize=10, fontweight="bold",
            arrowprops=dict(arrowstyle="-", color=DOM_COLOR, lw=0.8))
ax.annotate(f"NTS 2025: {nts_y[-1]}", xy=(2025 + 0.2, nts_y[-1]), xytext=(2024, nts_y[-1] + 30),
            color=NTS_COLOR, fontsize=10, fontweight="bold",
            arrowprops=dict(arrowstyle="-", color=NTS_COLOR, lw=0.8))

fig.text(0.06, 0.95, "Two parallel literatures, same instrument.",
         fontsize=17, color=INK, ha="left", weight="bold")
fig.text(0.06, 0.91,
         "Molecular-formula assignment by UHR-MS: DOM science vs. environmental non-target screening (NTS).",
         fontsize=11, color=INK_SOFT, ha="left", style="italic")

fig.text(0.06, 0.025,
         "OpenAlex (queried 2026-05-14). Both use FT-ICR or Orbitrap to assign molecular formulas. "
         "DOM science studies natural organic matter compositional fingerprints; NTS studies anthropogenic contaminants of emerging concern. "
         "Different anchor labs (Dittmar/Kujawinski/Spencer vs. Schymanski/Hollender/Reemtsma), almost no citation overlap.",
         fontsize=7.5, color=INK_SOFT, style="italic", ha="left", linespacing=1.5)

plt.subplots_adjust(left=0.08, right=0.97, top=0.86, bottom=0.13)

out2 = CHARTS / "uhrms_dom_vs_nts_growth_v1.png"
out2_deck = DECK_FIG / "uhrms_dom_vs_nts_growth_v1.png"
plt.savefig(out2, dpi=200, facecolor=BG, bbox_inches="tight", pad_inches=0.25)
plt.savefig(out2_deck, dpi=200, facecolor=BG, bbox_inches="tight", pad_inches=0.25)
print(f"Wrote {out2}")
print(f"Wrote {out2_deck}")
plt.close()

# ===== Print clean summary =====
print("\n=== v3 CONSOLIDATED COMPARISON (UHR-MS communities, 2000-2025) ===")
print(f"{'Community':<55s} {'Total':>8s} {'2025':>6s}")
print("-" * 72)
for label, total, y25_n, _ in rows:
    print(f"{label:<55s} {total:>8,d} {y25_n:>6d}")
