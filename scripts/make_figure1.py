"""
make_figure1.py
===============
Regenerates Figure 1: disciplinary distribution of the ASLO-SIL 2026 programme.

WHY THIS EXISTS
---------------
Figure 1 was originally produced by an ad-hoc inline script that was never committed.
When the manuscript's denominator was corrected from 1,461 scheduled slots to 1,458
real presentations (three slots are empty/withdrawn placeholders), every other artefact
was updated but Figure 1 could not be regenerated, because there was no script to run.
The delivered PNG therefore kept asserting "1,461 presentations" in its title and axis
while its own caption said 1,458. A figure outside the reproducible pipeline is a figure
that silently goes stale; committing this file closes that hole.

The bar COUNTS are unaffected by the correction: the three placeholder rows carry no
frame tags (verified), so lakes 346, microbial 269, biogeochemistry 246, limnology 65
and DOM 47 are identical under either denominator. Only the reported percentages'
denominator changes, and no bar changes its rounded value.

Scope note: tags are assigned over (presentation title + session description), which is
the same scope the manuscript and verify_manuscript_claims.py use for Figure 1 frames.

Run:  python make_figure1.py
"""
import json, re, sys
from collections import Counter
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from _data_access import data_path, email_of

SRC = Path(__file__).parent
OUT = str(SRC.parent / "output" / "charts" / "Figure1_disciplines_REVISED.png")
PLACEHOLDER = "[EMPTY/WITHDRAWN SLOT]"

sessions = []
with open(data_path(), encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if line:
            try: sessions.append(json.loads(line))
            except json.JSONDecodeError: pass

# Real presentations only: exclude the three empty/withdrawn placeholder slots.
# This is the manuscript's denominator (1,458), not the 1,461 scheduled slots.
rows = []
for s in sessions:
    desc = s.get("description") or ""
    for p in (s.get("presentations") or []):
        t = p.get("title") or ""
        if not t or t.strip().upper() == PLACEHOLDER:
            continue
        rows.append(t + " " + desc)
N = len(rows)
assert N == 1458, "expected 1,458 real presentations, got %d" % N

src = (SRC / "_conference_landscape.py").read_text(encoding="utf-8")
FRAMES = eval("{" + re.search(r"FRAMES = \{\n(.*?)\n\}\nFRAMES = \{k", src, re.S).group(1) + "\n}")

# Reviewer 2 asked that lakes not be merged with limnology: limnology denotes inland
# waters broadly, not lakes alone. Split the pipeline's single "Lakes / limnology" frame.
del FRAMES["Lakes / limnology"]
FRAMES["Lakes, ponds & reservoirs"] = [r"\blake\b", r"\bpond\b", r"\breservoir\b"]
FRAMES["Limnology / inland waters"] = [r"\blimnolog"]
FRAMES = {k: [re.compile(p, re.I) for p in v] for k, v in FRAMES.items()}

fc = Counter()
for text in rows:
    for frame, pats in FRAMES.items():
        if any(p.search(text) for p in pats):
            fc[frame] += 1

MIN_N = 15  # ~1% of 1,458; frames below this are omitted and named in the footnote
items = [(k, v) for k, v in fc.most_common() if v >= MIN_N]
dropped = [(k, v) for k, v in fc.most_common() if v < MIN_N]
labels = [k for k, _ in items]
values = [v for _, v in items]

BG, INK, INK_SOFT = "#f7f5f0", "#1a2332", "#4a5568"
FRAME_C, SPLIT_C = "#3d7a76", "#c98a3a"
SPLIT_BARS = ("Lakes, ponds & reservoirs", "Limnology / inland waters")

plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11,
                     "axes.edgecolor": "#4a5568", "axes.labelcolor": "#1a2332",
                     "xtick.color": "#4a5568", "ytick.color": "#4a5568"})
fig, ax = plt.subplots(figsize=(11, 8.5), facecolor=BG)
ax.set_facecolor(BG)
y = list(range(len(labels)))[::-1]
colors = [SPLIT_C if l in SPLIT_BARS else FRAME_C for l in labels]
ax.barh(y, values, color=colors, height=0.72, edgecolor="none")
for yp, v in zip(y, values):
    ax.text(v + 2, yp, "{} ({:.0f}%)".format(v, 100.0 * v / N), va="center",
            color=INK_SOFT, fontsize=10)
ax.set_yticks(y); ax.set_yticklabels(labels, fontsize=11, color=INK)
ax.set_xlabel("Presentations (of {:,}); multi-label, so bars overlap".format(N),
              fontsize=11, color=INK_SOFT)
ax.set_title("ASLO-SIL 2026: disciplinary distribution of {:,} presentations".format(N),
             fontsize=13, color=INK, loc="left", weight="bold", pad=14)
ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
ax.set_xlim(0, max(values) * 1.16)
ax.grid(axis="x", linestyle=":", color="#c8c4ba", alpha=0.6)

note = ("Lakes and limnology shown separately (gold): limnology denotes inland waters broadly, not lakes alone.")
if dropped:
    note += "  Frames tagged in <1% of talks omitted: " + ", ".join(k for k, _ in dropped) + "."
fig.text(0.01, -0.02, note, fontsize=8.2, color=INK_SOFT, ha="left", wrap=True)
plt.tight_layout()
plt.savefig(OUT, dpi=220, facecolor=BG, bbox_inches="tight")
plt.close()

print("Saved:", OUT)
print("Denominator: %d real presentations (placeholders excluded)\n" % N)
for k, v in items:
    print("  {:<34s}{:4d}  {:.1f}%".format(k, v, 100.0 * v / N))
print("\nOmitted (<%d): %s" % (MIN_N, dropped))
