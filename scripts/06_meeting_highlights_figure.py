"""
Make the single figure for the L&O Bulletin Meeting Highlights submission.

A horizontal-bar disciplinary portrait of the ASLO-SIL 2026 program, with
editorial callouts that mirror the narrative (synthesis verbs, freshwater
dominance, methodological bets). Exports PNG (for email + screen) and
TIFF/CMYK 300 dpi (for the ScholarOne submission).
"""
import json
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "output" / "tables" / "landscape_data.json"
OUT_CHARTS = ROOT / "output" / "charts"
OUT_SUBMISSION = Path(r"G:\My Drive\3-WorkAndPurpose\0-ABC_Lab\06-Teaching_Outreach\1-ConferenceTalks\ASLO2026\_ConferenceLandscape\submission_package")

with open(DATA, "r", encoding="utf-8") as f:
    d = json.load(f)

frames = d["frames_distribution"]["presentation_level"]
# Use the portal-audited count (1,455) for display, not the raw classifier total (1,462).
# Percentages are computed against the raw count internally; we display the audited count.
total_pres_display = 1455
total_pres_classifier = d["community_structure"]["total_presentations_with_titles"]

# Curate the order — group bread-and-butter, then methodological emphases, then frontiers
# Use the actual counts; just order for readability.
ORDER = [
    "Lakes / limnology",
    "Microbial ecology",
    "Biogeochemistry / C cycle",
    "Climate change / global change",
    "Marine / oceanography",
    "Rivers / streams",
    "Biodiversity / biogeography",
    "Estuarine / coastal",
    "Food web / trophic",
    "Eutrophication / nutrient pollution",
    "Cryosphere / ice",
    "Pollution / contaminants",
    "Conservation / restoration",
    "DOM / NOM chemistry",
    "Community / metacommunity ecology",
    "Disturbance / fire / land use",
    "Indigenous / equity / social",
    "Wetlands / peatlands",
]

labels = [f for f in ORDER if f in frames]
values = [frames[f] for f in labels]
percentages = [100.0 * v / total_pres_classifier for v in values]

# Categorise by visual role: the dominant trio, the freshwater/marine layer, the smaller emphases
DOMINANT = {"Lakes / limnology", "Microbial ecology", "Biogeochemistry / C cycle"}
FRESHWATER_MARINE = {"Rivers / streams", "Marine / oceanography", "Estuarine / coastal", "Wetlands / peatlands"}
ACCENT = {"DOM / NOM chemistry", "Indigenous / equity / social"}

# Colour mapping (deck palette)
BG = "#f7f5f0"; INK = "#1a2332"; INK_SOFT = "#4a5568"
ACCENT_GREEN = "#2d5f5d"; DEEP_GREEN = "#1f4747"
NEUTRAL = "#8a9a8e"; HIGHLIGHT = "#c44e3a"

def bar_color(label):
    if label in DOMINANT:
        return DEEP_GREEN
    if label in FRESHWATER_MARINE:
        return ACCENT_GREEN
    if label in ACCENT:
        return HIGHLIGHT
    return NEUTRAL

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 11,
    "axes.edgecolor": "#4a5568",
    "axes.labelcolor": "#1a2332",
    "xtick.color": "#4a5568",
    "ytick.color": "#4a5568",
})

fig, ax = plt.subplots(figsize=(11, 9), facecolor=BG)
ax.set_facecolor(BG)

y_pos = list(range(len(labels)))[::-1]
colors = [bar_color(l) for l in labels]
bars = ax.barh(y_pos, values, color=colors, height=0.68, edgecolor="none")

for yp, label, v, pct in zip(y_pos, labels, values, percentages):
    ax.text(v + 6, yp, "{:.0f} ({:.0f}%)".format(v, pct),
            va="center", color=INK_SOFT, fontsize=10)

ax.set_yticks(y_pos)
ax.set_yticklabels(labels, fontsize=11.5, color=INK)
ax.set_xlim(0, max(values) * 1.32)
ax.set_xlabel("Presentations  (of ~{:,} scheduled — multi-label tagging, columns overlap)".format(total_pres_display),
              fontsize=10.5, color=INK_SOFT)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_visible(False)
ax.tick_params(left=False)
ax.grid(axis="x", linestyle=":", color="#c8c4ba", alpha=0.5)

# Title — magazine-style, two-line
fig.suptitle("ASLO-SIL 2026 — what 1,455 presentations tell us about the field",
             x=0.06, y=0.98, ha="left", fontsize=14, weight="bold", color=INK)
fig.text(0.06, 0.935,
         "The disciplinary distribution of the joint meeting. Lakes, microbes, and biogeochemistry are the connective tissue; freshwater outweighs marine; DOM is small but coherent; equity content is structurally programmed.",
         fontsize=9.5, color=INK_SOFT, style="italic")

# --- Editorial callouts ---
# Helper to draw an annotation arrow + text block
def callout(bar_label, text, x_text_offset, y_text_offset, ha="left"):
    if bar_label not in labels:
        return
    idx = labels.index(bar_label)
    yp = y_pos[idx]
    x_bar_end = values[idx]
    # Annotation
    ax.annotate(
        text,
        xy=(x_bar_end + 6, yp),
        xytext=(x_bar_end + x_text_offset, yp + y_text_offset),
        fontsize=9.5, color=INK, ha=ha,
        bbox=dict(boxstyle="round,pad=0.4", facecolor="white",
                  edgecolor="#c8c4ba", linewidth=0.8),
        arrowprops=dict(arrowstyle="-", color="#8a9a8e", lw=0.9,
                        connectionstyle="arc3,rad=0.15"),
    )

callout("Lakes / limnology",
        "The standing wave of the field —\nthe SIL half doing real work.",
        110, 2.5, ha="left")
callout("DOM / NOM chemistry",
        "Small but coherent — concentrated\nin the three-part SS050 symposium.",
        140, 1.8, ha="left")
callout("Indigenous / equity / social",
        "Structurally programmed: EP013 Two-Eyed\nSeeing, AV001 Amplifying Voices, WS05, WS08.",
        140, 1.8, ha="left")

# --- Legend (colour key) — bottom left ---
legend_handles = [
    mpatches.Patch(color=DEEP_GREEN, label="Connective tissue (lakes, microbes, biogeochem)"),
    mpatches.Patch(color=ACCENT_GREEN, label="Other aquatic systems (rivers, marine, estuarine, wetlands)"),
    mpatches.Patch(color=HIGHLIGHT, label="The DOM and equity sub-conversations"),
    mpatches.Patch(color=NEUTRAL, label="Other frames"),
]
ax.legend(handles=legend_handles, loc="lower right",
          bbox_to_anchor=(0.99, -0.18),
          frameon=False, fontsize=9, labelcolor=INK,
          handleheight=0.9, handlelength=1.2, ncol=2)

# Footnote
fig.text(0.06, 0.005,
         "Data: ASLO-SIL 2026 public schedule, audited 11 May 2026 (1,455 scheduled presentations, 308 session items). "
         "Disciplinary tags assigned by keyword classifier on session names and descriptions; multi-label.\n"
         "Full inventory, classifier code, and reproducible analysis at github.com/erika-freeman/aslo2026-conference-landscape.",
         fontsize=8, color=INK_SOFT, style="italic")

plt.tight_layout(rect=[0, 0.07, 1, 0.93])

# Save PNG (for email + screen + web)
png_path = OUT_CHARTS / "meeting_highlights_figure1.png"
plt.savefig(png_path, dpi=200, facecolor=BG, bbox_inches="tight", pad_inches=0.25)
print("Saved PNG: {}".format(png_path))

# Also save TIFF/CMYK 300 dpi for the formal ScholarOne submission
tif_intermediate = OUT_CHARTS / "_meeting_highlights_figure1_rgb.png"
plt.savefig(tif_intermediate, dpi=300, facecolor=BG, bbox_inches="tight", pad_inches=0.25)
plt.close()
img = Image.open(tif_intermediate).convert("RGB").convert("CMYK")
tif_path = OUT_SUBMISSION / "Freeman_MeetingHighlights_Figure1.tif"
OUT_SUBMISSION.mkdir(parents=True, exist_ok=True)
img.save(tif_path, format="TIFF", compression="tiff_lzw", dpi=(300, 300))
tif_intermediate.unlink()
print("Saved TIFF (CMYK, 300 dpi, LZW): {}".format(tif_path))

# Copy a second PNG to the submission package
import shutil
shutil.copy(png_path, OUT_SUBMISSION / "Freeman_MeetingHighlights_Figure1.png")
print("Copied PNG to submission package")
print("\nFigure ready for: email attachment (PNG), ScholarOne upload (TIFF/CMYK).")
