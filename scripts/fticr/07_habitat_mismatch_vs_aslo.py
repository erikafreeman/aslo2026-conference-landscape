"""
Paired horizontal stacked bar: ASLO-SIL 2026 program habitat share vs.
FT-ICR-MS DOM corpus habitat share. The mismatch is the slide.

Sources:
  - ASLO habitat shares: aslo2026-conference-landscape README (session keywords).
    Inland (lakes + limnology + rivers + wetlands) = 39%; Marine = 9%; Other = 52%.
  - FT-ICR-MS corpus habitat shares: fticr_habitat_coarse.json (single-label).
    Inland = 16.6%; Saltwater (marine + estuary) = 46.2%; Other = 37.2%.
"""
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.patches as patches

OUT_DECK = Path(r"G:\My Drive\3-WorkAndPurpose\0-ABC_Lab\06-Teaching_Outreach\1-ConferenceTalks\ASLO2026\_DECK\figures\fticr_vs_aslo_habitat_v1.png")
OUT_BIB = Path(r"G:\My Drive\3-WorkAndPurpose\0-ABC_Lab\06-Teaching_Outreach\1-ConferenceTalks\ASLO2026\_BibliometricAnalysis\charts\fticr_vs_aslo_habitat_v1.png")

# Palette matched to the existing deck
BG = "#f7f5f0"
INK = "#1a2332"
INK_SOFT = "#4a5568"
INLAND = "#2d5f5d"      # the highlight (audience habitat)
SALTWATER = "#4a7a98"   # blue
OTHER = "#c8c4ba"       # muted ecru

# Data
aslo = {"Inland waters": 39.0, "Marine": 9.0, "Other / unspecified": 52.0}
fticr = {"Inland waters": 17.0, "Saltwater (marine + estuary)": 46.0, "Other": 37.0}

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 11,
    "axes.edgecolor": INK_SOFT,
    "axes.labelcolor": INK,
    "xtick.color": INK_SOFT,
    "ytick.color": INK_SOFT,
})

fig, ax = plt.subplots(figsize=(12, 6.8), facecolor=BG)
ax.set_facecolor(BG)
fig.subplots_adjust(top=0.78, bottom=0.14, left=0.18, right=0.97)

bar_h = 0.55
y_aslo, y_fticr = 1.0, 0.0

# ASLO bar (top)
x = 0
for label, color in [("Inland waters", INLAND), ("Marine", SALTWATER), ("Other / unspecified", OTHER)]:
    v = aslo[label]
    ax.barh(y_aslo, v, height=bar_h, left=x, color=color, edgecolor="none")
    if v >= 5:
        text_color = "white" if color != OTHER else INK
        ax.text(x + v / 2, y_aslo, f"{label}\n{v:.0f}%", ha="center", va="center",
                color=text_color, fontsize=11, fontweight="bold", linespacing=1.3)
    x += v

# FT-ICR bar (bottom)
x = 0
for label, color in [("Inland waters", INLAND), ("Saltwater (marine + estuary)", SALTWATER), ("Other", OTHER)]:
    v = fticr[label]
    ax.barh(y_fticr, v, height=bar_h, left=x, color=color, edgecolor="none")
    if v >= 5:
        text_color = "white" if color != OTHER else INK
        ax.text(x + v / 2, y_fticr, f"{label}\n{v:.0f}%", ha="center", va="center",
                color=text_color, fontsize=11, fontweight="bold", linespacing=1.3)
    x += v

# Y-axis labels (left side)
ax.set_yticks([y_aslo, y_fticr])
ax.set_yticklabels([
    "This room\nASLO-SIL 2026 program\n(n=1,461 talks)",
    "FT-ICR-MS literature\nOpenAlex corpus\n(n=1,746 papers, 2000-2025)"
], fontsize=11, color=INK)

ax.set_xlim(0, 100)
ax.set_ylim(-0.6, 1.6)
ax.set_xlabel("Share of talks / papers (%)", fontsize=11, color=INK_SOFT)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_visible(False)
ax.tick_params(left=False)
ax.set_xticks([0, 25, 50, 75, 100])
ax.grid(axis="x", linestyle=":", color=INK_SOFT, alpha=0.2)

# Connector arrows / mismatch annotation
ax.annotate("",
            xy=(17, y_fticr + bar_h / 2 + 0.02),
            xytext=(17, y_aslo - bar_h / 2 - 0.02),
            arrowprops=dict(arrowstyle="-|>", color=INK_SOFT, lw=1.2,
                            connectionstyle="arc3,rad=0"))
ax.text(20, 0.5, "39 -> 17%\ninland-waters share\nhalves in the literature",
        ha="left", va="center", color=INK_SOFT, fontsize=10, style="italic")

ax.annotate("",
            xy=(50, y_fticr + bar_h / 2 + 0.02),
            xytext=(50, y_aslo - bar_h / 2 - 0.02),
            arrowprops=dict(arrowstyle="-|>", color=INK_SOFT, lw=1.2,
                            connectionstyle="arc3,rad=0"))
ax.text(53, 0.5, "9 -> 46%\nsaltwater share\nfive times higher",
        ha="left", va="center", color=INK_SOFT, fontsize=10, style="italic")

# Title and footer
fig.text(0.04, 0.92, "What this room studies. What FT-ICR-MS has measured.",
         fontsize=17, color=INK, ha="left", weight="bold")
fig.text(0.04, 0.86,
         "Habitat share of ASLO-SIL 2026 talks vs. the global FT-ICR-MS DOM literature.",
         fontsize=12, color=INK_SOFT, ha="left", style="italic")

fig.text(0.04, 0.04,
         "ASLO shares from session-keyword classification of 1,461 talks (lakes + limnology = 28%, rivers + wetlands = 11%, marine = 9%).\n"
         "FT-ICR shares from single-label habitat classification of 1,746 OpenAlex matches (queried 2026-05-11). Categories simplified for comparison.",
         fontsize=8, color=INK_SOFT, style="italic", ha="left", linespacing=1.5)

OUT_DECK.parent.mkdir(parents=True, exist_ok=True)
OUT_BIB.parent.mkdir(parents=True, exist_ok=True)
plt.savefig(OUT_DECK, dpi=200, facecolor=BG, bbox_inches="tight", pad_inches=0.25)
plt.savefig(OUT_BIB, dpi=200, facecolor=BG, bbox_inches="tight", pad_inches=0.25)
print(f"Wrote {OUT_DECK}")
print(f"Wrote {OUT_BIB}")
