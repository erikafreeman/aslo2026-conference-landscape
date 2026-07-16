"""
make_figure2.py
===============
Regenerates Figure 2: share of global renewable freshwater (World Bank
ER.H2O.INTR.K3, 2022) vs share of ASLO-SIL 2026 presentations, for the top-20
countries by freshwater stock.

Program shares use country_resolver_v2.resolve: institution gazetteer first, then
email country code (institutional domains only), with generic .edu/.gov last. The
original rule assigned every .edu.au / .edu.cn address to the USA, and could not
see institutions named in Portuguese or Spanish whose authors used consumer mail,
which undercounted Brazil roughly threefold. Denominator is 1,458 real
presentations (the 3 empty/withdrawn placeholder slots are excluded).

Committed so the figure is reproducible, per the manuscript's claim that the
full analysis is available.

Run:  python make_figure2.py
"""
import json, sys
from collections import Counter
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from country_resolver_v2 import resolve
from _data_access import data_path, email_of

SRC = Path(__file__).parent
OUT = str(SRC.parent / "output" / "charts" / "Figure2_freshwater_parity_REVISED.png")

# World Bank ER.H2O.INTR.K3 (renewable internal freshwater resources, bn m3, 2022).
# World total (WLD aggregate) = 42,807.04 bn m3.
WORLD_TOTAL = 42807.04
STOCK = [
    ("Brazil", 5661.0), ("Russia", 4312.0), ("Canada", 2850.0), ("USA", 2818.0),
    ("China", 2812.9), ("Colombia", 2145.0), ("Indonesia", 2018.7), ("Peru", 1641.0),
    ("India", 1446.0), ("Myanmar", 1002.8), ("DR Congo", 900.0), ("Chile", 885.0),
    ("Venezuela", 805.0), ("Papua New Guinea", 801.0), ("Malaysia", 580.0),
    ("Australia", 492.0), ("Philippines", 479.0), ("Ecuador", 442.4),
    ("Japan", 430.0), ("Mexico", 409.0),
]

sessions = []
with open(data_path(), encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if line:
            try: sessions.append(json.loads(line))
            except json.JSONDecodeError: pass
PH = "[EMPTY/WITHDRAWN SLOT]"
slots = [p for s in sessions for p in (s.get("presentations") or [])
         if p.get("title") and p["title"].strip().upper() != PH]
N = len(slots)   # 1,458 real presentations

counts = Counter(c for c in (resolve(p.get("affiliation"), email_of(p))[0] for p in slots) if c)

rows = []
for name, stock in STOCK:
    fw = 100.0 * stock / WORLD_TOTAL
    n = counts.get(name, 0)
    rows.append((name, fw, 100.0 * n / N, n))
rows.sort(key=lambda r: -r[1])

BG, INK, INK_SOFT = "#f7f5f0", "#1a2332", "#4a5568"
TEAL, GOLD = "#3d7a76", "#c98a3a"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11,
                     "axes.edgecolor": "#4a5568", "axes.labelcolor": "#1a2332",
                     "xtick.color": "#4a5568", "ytick.color": "#4a5568"})
fig, ax = plt.subplots(figsize=(11, 10), facecolor=BG)
ax.set_facecolor(BG)
h = 0.38
ys = list(range(len(rows)))[::-1]
for y, (name, fw, pg, n) in zip(ys, rows):
    ax.barh(y + h/2, fw, height=h, color=TEAL, edgecolor="none")
    ax.barh(y - h/2, pg, height=h, color=GOLD, edgecolor="none")
    ax.text(fw + 0.25, y + h/2, f"{fw:.1f}%", va="center", fontsize=9, color=TEAL)
    ax.text(pg + 0.25, y - h/2, f"{pg:.1f}%" if pg > 0 else "0%",
            va="center", fontsize=9, color=GOLD if pg > 0 else INK_SOFT)
ax.set_yticks(ys); ax.set_yticklabels([r[0] for r in rows], fontsize=11, color=INK)
ax.set_xlabel("Percent of world total (freshwater) or of all 1,458 talks (presentations)",
              fontsize=11, color=INK_SOFT)
ax.set_title("ASLO-SIL 2026: freshwater stock versus conference presence",
             fontsize=13, color=INK, loc="left", weight="bold", pad=14)
ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
ax.set_xlim(0, max(max(r[1] for r in rows), max(r[2] for r in rows)) * 1.14)
ax.grid(axis="x", linestyle=":", color="#c8c4ba", alpha=0.6)
from matplotlib.patches import Patch
ax.legend(handles=[Patch(facecolor=TEAL, label="Share of global renewable freshwater"),
                   Patch(facecolor=GOLD, label="Share of presentations")],
          loc="lower right", frameon=False, fontsize=11)

def annotate(country, text, dy):
    for i, (nm, fw, pg, n) in enumerate(rows):
        if nm == country:
            y = ys[i]
            ax.annotate(text, xy=(max(fw, pg), y), xytext=(max(fw, pg) + 4.5, y + dy),
                        fontsize=9.5, color=INK_SOFT,
                        arrowprops=dict(arrowstyle="->", color=INK_SOFT,
                                        connectionstyle="arc3,rad=-0.25", lw=0.9))
annotate("Brazil", "Largest gap: 13% of the world's\nfreshwater, about 3.6% of the talks", -1.0)
annotate("Japan", "Japan and Mexico came closest to\nmatching their freshwater share", -2.6)

fig.text(0.01, -0.06,
         "Freshwater: World Bank indicator ER.H2O.INTR.K3 (renewable internal freshwater resources, total; 2022), each country as a percent of the world total.\n"
         "Presentations: share of 1,458 ASLO-SIL 2026 talks; country resolved from the presenting author's institution, then email domain, for 99% of talks.\n"
         "Freshwater share is a reference point, not an expected quota. A zero means no talk was resolved to that country, not proof of absence.",
         fontsize=8, color=INK_SOFT, ha="left")
plt.tight_layout()
plt.savefig(OUT, dpi=220, facecolor=BG, bbox_inches="tight")
plt.close()
print("Saved:", OUT)
print(f"\n{'country':<18s}{'freshwater%':>12s}{'program%':>10s}{'n':>5s}")
for name, fw, pg, n in rows:
    print(f"  {name:<16s}{fw:11.2f}%{pg:9.2f}%{n:5d}")
