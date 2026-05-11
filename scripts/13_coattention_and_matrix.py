"""
Two analyses of "how the field is wiring its questions together":

  (1) CO-ATTENTION NETWORK — which tags travel together across talks.
      Each tag is a node, each edge weighted by the number of talks where
      two tags co-occur. Identify bridge topics by betweenness centrality.

  (2) METHODS × PROBLEMS MATRIX — cross-tab of method tags against frame
      tags. Shows what work each method is being asked to do.

Both built from the existing keyword classifier applied to session and
presentation titles + descriptions in sessions_all_public.json.
"""
import json, re
from pathlib import Path
from collections import Counter, defaultdict
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import networkx as nx
import numpy as np

ROOT = Path(__file__).resolve().parent.parent

# ============ Load corpus ============
with open(ROOT / "data" / "sessions_all_public.json", "r", encoding="utf-8") as f:
    sessions = [json.loads(line) for line in f if line.strip()]

presentations = []
for s in sessions:
    for p in (s.get("presentations") or []):
        if p.get("title"):
            text = " ".join([
                p.get("title") or "",
                p.get("abstract") or "",
                s.get("name") or "",
                s.get("description") or "",
            ])
            presentations.append({"text": text, "session_code": s.get("session_code")})
print("Presentations: {}".format(len(presentations)))

# ============ Tag patterns (consolidated from scripts 03 and 04) ============
# Frame / problem tags
FRAMES = {
    "Biogeochem / C cycle": [r"\bbiogeochem", r"\bcarbon cycle\b", r"\bcarbon flux\b", r"\bgreenhouse gas", r"\bCO2\b", r"\bmethane\b", r"\bN2O\b", r"\bnutrient cycl"],
    "Microbial ecology": [r"\bmicrobial\b", r"\bmicrobiome\b", r"\bbacteri", r"\barchaea\b", r"\bvirome\b", r"\bphytoplankton\b", r"\bzooplankton\b", r"\bplankton\b"],
    "Community ecology": [r"\bcommunity ecology\b", r"\bmetacommunity\b", r"\bcommunity assembly\b", r"\bcommunity structure\b", r"\bbeta diversity\b", r"\balpha diversity\b"],
    "Food web / trophic": [r"\bfood web\b", r"\btrophic\b", r"\bpredator[\s\-]prey", r"\bfish.*diet", r"\bfeeding ecology"],
    "Functional ecology / traits": [r"\bfunctional ecology\b", r"\btrait[\s\-]based\b", r"\bfunctional diversity\b", r"\bfunctional trait"],
    "Biodiversity / biogeography": [r"\bbiodiversity\b", r"\bbiogeograph", r"\bspecies richness\b", r"\bendemism\b", r"\binvasive species\b"],
    "Climate change": [r"\bclimate change\b", r"\bglobal change\b", r"\bwarming\b", r"\bdrought\b", r"\bheatwave\b", r"\bextreme event"],
    "Eutrophication": [r"\beutrophicat", r"\bnitrogen loading\b", r"\bphosphorus loading\b", r"\balgal bloom\b", r"\bharmful algal"],
    "Pollution / contaminants": [r"\bpollution\b", r"\bcontaminant\b", r"\bmicroplastic\b", r"\bpharmaceutical\b", r"\bPFAS\b", r"\bpesticide\b"],
    "DOM / NOM chemistry": [r"\bdissolved organic\b", r"\bDOM\b", r"\bnatural organic\b", r"\bNOM\b", r"\bhumic\b", r"\bfulvic\b"],
    "Carbon export": [r"\bblue carbon\b", r"\bcarbon export\b", r"\bcarbon sequestrat", r"\bsoil carbon\b", r"\bcarbon stor"],
    "Ecosystem function": [r"\becosystem function\b", r"\becosystem service\b", r"\bsecondary production\b", r"\bdecomposition\b", r"\brespiration\b"],
    "Conservation / restoration": [r"\bconservation\b", r"\brestoration\b", r"\brewilding\b", r"\bprotected area\b"],
    "Fisheries": [r"\bfisher", r"\baquacultur", r"\bstock assess"],
    "Cryosphere / ice": [r"\bice\b(?! cream)", r"\bglacial\b", r"\bpermafrost\b", r"\bsnowpack\b"],
    "Estuarine / coastal": [r"\bestuar", r"\bcoastal\b", r"\bmangrove\b", r"\bsalt marsh"],
    "Marine / ocean": [r"\bmarine\b", r"\bocean\b", r"\bpelagic\b", r"\bseawater\b"],
    "Lakes / limnology": [r"\blake\b", r"\blimnolog", r"\bpond\b", r"\breservoir\b"],
    "Rivers / streams": [r"\briver\b", r"\bstream\b", r"\bfluvial\b", r"\bheadwater\b"],
    "Wetlands / peatlands": [r"\bwetland\b", r"\bpeatland\b", r"\bbog\b", r"\bmarsh"],
    "Groundwater": [r"\bgroundwater\b", r"\baquifer\b", r"\bhyporheic\b"],
    "Indigenous / equity": [r"\bindigenous\b", r"\bequity\b", r"\bjustice\b", r"\bdecoloniz", r"\binclusion\b", r"\bcommunity-led", r"\btraditional knowledge"],
    "Disturbance / fire / land-use": [r"\bwildfire\b", r"\bdeforestation\b", r"\blogging\b", r"\bland[\s\-]use\b", r"\burbanization\b"],
}
FRAMES = {k: [re.compile(p, re.I) for p in pats] for k, pats in FRAMES.items()}

# Method tags
METHODS = {
    "Long-term monitoring": [r"\blong[\s\-]term\b", r"\btime[\s\-]series\b", r"\bdecadal\b", r"\bmonitoring\b", r"\bLTER\b"],
    "Hydrology / hydrodynamic": [r"\bhydrolog", r"\bhydrodynam", r"\bdischarge\b", r"\bflow regime\b", r"\bcatchment\b", r"\bwatershed\b"],
    "eDNA / -omics": [r"\beDNA\b", r"\bmetagenomic", r"\b16S\b", r"\btranscriptomic", r"\bproteomic", r"\bmetabolomic", r"\bsequencing\b", r"\bamplicon"],
    "Modelling / simulation": [r"\bmodel[\s\-]ing\b", r"\bmodel\b", r"\bsimulation\b", r"\bnumerical\b", r"\bBayesian\b", r"\bmechanistic", r"\bprocess[\s\-]based\b"],
    "Remote sensing": [r"\bremote sensing\b", r"\bsatellite\b", r"\bLandsat\b", r"\bSentinel[\s\-]\d", r"\bMODIS\b", r"\bhyperspectral\b"],
    "Experimental / mesocosm": [r"\bmesocosm\b", r"\bexperimental\b", r"\bmanipul", r"\bincubation\b", r"\bbioassay\b", r"\bchamber\b"],
    "ML / AI": [r"\bmachine learning\b", r"\bdeep learning\b", r"\bneural network\b", r"\bAI\b", r"\brandom forest\b", r"\bartificial intelligence", r"\bdata[\s\-]driven\b", r"\bclassifier\b"],
    "Network / co-occurrence": [r"\bnetwork\b", r"\bco[\s\-]occurrence\b", r"\bbipartite\b", r"\bcommunity assembly\b"],
    "Citizen science": [r"\bcitizen science\b", r"\bcommunity[\s\-]based\b", r"\bparticipatory\b"],
    "Mass spectrometry / UHR-MS": [r"\bFT[\s\-]?ICR\b", r"\bFTICR\b", r"\bOrbitrap\b", r"\bmass spectrom", r"\bultra.?high[\s\-]?resolution"],
    "Stable isotopes": [r"\bisotop\b", r"\bisotopic", r"\bd13C\b", r"\bd15N\b", r"\b18O\b", r"\bradiocarbon"],
    "Optical / fluorescence": [r"\bfluorescen", r"\bPARAFAC\b", r"\bCDOM\b", r"\bFDOM\b", r"\babsorbance\b"],
    "Paleo / cores": [r"\bpaleo\b", r"\bsediment core\b", r"\bdiatom record\b", r"\bvarve\b"],
    "Mass-balance / tracer": [r"\bmass balance\b", r"\bbudget\b", r"\bflux measurement", r"\bdye tracer", r"\beddy covariance\b"],
}
METHODS = {k: [re.compile(p, re.I) for p in pats] for k, pats in METHODS.items()}

def tag(text, pattern_dict):
    found = set()
    for k, pats in pattern_dict.items():
        if any(p.search(text) for p in pats):
            found.add(k)
    return found

# ============ Tag every presentation ============
for p in presentations:
    p["frames"] = tag(p["text"], FRAMES)
    p["methods"] = tag(p["text"], METHODS)
    p["all_tags"] = p["frames"] | p["methods"]

n_with_any = sum(1 for p in presentations if p["all_tags"])
print("Presentations with at least one tag: {} ({:.0f}%)".format(n_with_any, 100*n_with_any/len(presentations)))

# ============ ANALYSIS 1: CO-ATTENTION NETWORK ============
# Edge weight = number of talks where both tags appear
cooccur = Counter()
tag_count = Counter()
for p in presentations:
    tags = list(p["all_tags"])
    for t in tags:
        tag_count[t] += 1
    for i, t1 in enumerate(tags):
        for t2 in tags[i+1:]:
            edge = tuple(sorted([t1, t2]))
            cooccur[edge] += 1

print("\nTotal unique tags: {}".format(len(tag_count)))
print("Total unique co-occurring pairs: {}".format(len(cooccur)))

# Build graph
G = nx.Graph()
for t, n in tag_count.items():
    G.add_node(t, weight=n)
# Edge threshold: only show edges with at least 10 co-occurrences (legibility)
MIN_EDGE = 10
edges_in = 0
for (t1, t2), w in cooccur.items():
    if w >= MIN_EDGE:
        G.add_edge(t1, t2, weight=w)
        edges_in += 1
print("Edges retained (weight >= {}): {}".format(MIN_EDGE, edges_in))

# Centrality measures
between = nx.betweenness_centrality(G, weight="weight")
eigen = nx.eigenvector_centrality_numpy(G, weight="weight") if G.number_of_edges() > 0 else {}

print("\n=== TOP 10 BRIDGE TOPICS (by betweenness centrality) ===")
print("These are tags that connect otherwise-distinct sub-conversations.")
for t, b in sorted(between.items(), key=lambda x: -x[1])[:10]:
    print("  {:<32s} betweenness={:.3f}  (appears in {} talks)".format(t, b, tag_count[t]))

print("\n=== TOP 10 HUB TOPICS (by eigenvector centrality) ===")
print("These are tags most connected to other heavily-connected tags.")
for t, e in sorted(eigen.items(), key=lambda x: -x[1])[:10]:
    print("  {:<32s} eigenvector={:.3f}  (appears in {} talks)".format(t, e, tag_count[t]))

# Strongest edges
print("\n=== TOP 15 STRONGEST CO-OCCURRENCES ===")
print("Topics that travel together most often.")
for (t1, t2), w in sorted(cooccur.items(), key=lambda x: -x[1])[:15]:
    print("  {:<25s} <-> {:<25s} {} talks".format(t1, t2, w))

# ============ Plot the network ============
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10,
                     "axes.edgecolor": "#4a5568"})
BG = "#f7f5f0"; INK = "#1a2332"; INK_SOFT = "#4a5568"
FRAME_COLOR = "#2d5f5d"; METHOD_COLOR = "#c44e3a"; EQUITY_COLOR = "#8a9a8e"

fig, ax = plt.subplots(figsize=(14, 11), facecolor=BG)
ax.set_facecolor(BG)
ax.set_axis_off()

# Layout — use spring with weight; seed for reproducibility
pos = nx.spring_layout(G, k=1.4, iterations=200, seed=42, weight="weight")

# Node sizes proportional to occurrence
sizes = [tag_count[n] * 6 for n in G.nodes()]
# Colours: frames = green, methods = terracotta, equity = grey-green
def node_color(t):
    if t in METHODS: return METHOD_COLOR
    if t == "Indigenous / equity": return EQUITY_COLOR
    return FRAME_COLOR
colors = [node_color(n) for n in G.nodes()]

# Draw edges with width scaled by co-occurrence count
edges_data = [(u, v, d["weight"]) for u, v, d in G.edges(data=True)]
max_w = max(w for _, _, w in edges_data)
for u, v, w in edges_data:
    width = 0.5 + 4 * (w / max_w) ** 0.7
    alpha = 0.15 + 0.55 * (w / max_w) ** 0.7
    ax.plot([pos[u][0], pos[v][0]], [pos[u][1], pos[v][1]],
            color="#4a5568", linewidth=width, alpha=alpha, zorder=1)

# Nodes
for n, c, s in zip(G.nodes(), colors, sizes):
    ax.scatter(*pos[n], s=s, c=c, edgecolors="white", linewidths=1.5, zorder=2)

# Labels — place outside the node
for n in G.nodes():
    x, y = pos[n]
    ax.text(x, y + 0.025, n, fontsize=9.5, ha="center", va="bottom",
            color=INK, weight="bold" if between.get(n, 0) > 0.05 else "normal",
            zorder=3, bbox=dict(boxstyle="round,pad=0.2", facecolor=BG,
                                edgecolor="none", alpha=0.7))

ax.set_title("Co-attention network — which topics travel together across the program",
             fontsize=14, color=INK, loc="left", weight="bold", pad=18)
fig.text(0.06, 0.94,
         "Each node is a frame or method tag; each edge connects tags that co-occur in at least 10 talks (line width = co-occurrence count). "
         "Node size reflects total tag occurrences. Forest green = frames; terracotta = methods; soft grey-green = equity/Indigenous-knowledge. "
         "Topics with higher betweenness centrality (bold labels) act as bridges between otherwise-distinct sub-conversations.",
         fontsize=9, color=INK_SOFT, style="italic", wrap=True)

# Legend
legend_handles = [
    mpatches.Patch(color=FRAME_COLOR, label="Frame / problem tag"),
    mpatches.Patch(color=METHOD_COLOR, label="Method tag"),
    mpatches.Patch(color=EQUITY_COLOR, label="Indigenous knowledge / equity"),
]
ax.legend(handles=legend_handles, loc="lower right", frameon=False, fontsize=10, labelcolor=INK)

fig.text(0.06, 0.012,
         "Source: ASLO-SIL 2026 public schedule, scraped + audited 11 May 2026. Tags by keyword classifier on titles + descriptions; edges drawn at weight >= 10 co-occurrences for legibility.",
         fontsize=8, color=INK_SOFT, style="italic")

plt.tight_layout(rect=[0, 0.04, 1, 0.92])
out_net = ROOT / "output" / "charts" / "co_attention_network.png"
plt.savefig(out_net, dpi=200, facecolor=BG, bbox_inches="tight", pad_inches=0.25)
print("\nSaved network: {}".format(out_net))


# ============ ANALYSIS 2: METHODS × PROBLEMS MATRIX ============
method_names = list(METHODS.keys())
frame_names = list(FRAMES.keys())

# Build the cross-tab
matrix = np.zeros((len(method_names), len(frame_names)), dtype=int)
for p in presentations:
    for i, m in enumerate(method_names):
        if m in p["methods"]:
            for j, f in enumerate(frame_names):
                if f in p["frames"]:
                    matrix[i, j] += 1

# Sort frame_names by total column sum (descending), method_names by row sum
col_totals = matrix.sum(axis=0)
row_totals = matrix.sum(axis=1)
col_order = np.argsort(-col_totals)
row_order = np.argsort(-row_totals)
matrix_sorted = matrix[np.ix_(row_order, col_order)]
methods_sorted = [method_names[i] for i in row_order]
frames_sorted = [frame_names[i] for i in col_order]

# Plot heatmap
fig, ax = plt.subplots(figsize=(15, 8), facecolor=BG)
ax.set_facecolor(BG)
im = ax.imshow(matrix_sorted, cmap="YlOrRd", aspect="auto",
               vmin=0, vmax=np.percentile(matrix_sorted[matrix_sorted > 0], 90) if matrix_sorted.max() > 0 else 1)

# Annotate cells with counts
for i in range(matrix_sorted.shape[0]):
    for j in range(matrix_sorted.shape[1]):
        v = matrix_sorted[i, j]
        if v == 0:
            ax.text(j, i, ".", ha="center", va="center", color="#cccccc", fontsize=10)
        else:
            color = "white" if v > matrix_sorted.max() * 0.6 else INK
            ax.text(j, i, str(v), ha="center", va="center", color=color, fontsize=9)

ax.set_xticks(range(len(frames_sorted)))
ax.set_xticklabels(frames_sorted, rotation=45, ha="right", fontsize=10, color=INK)
ax.set_yticks(range(len(methods_sorted)))
ax.set_yticklabels(methods_sorted, fontsize=10.5, color=INK)
ax.set_xlabel("Frame / problem tags  (sorted by total method-talk co-occurrence)", fontsize=10, color=INK_SOFT)
ax.set_ylabel("Method tags  (sorted by total problem-talk co-occurrence)", fontsize=10, color=INK_SOFT)

cbar = plt.colorbar(im, ax=ax, shrink=0.6, pad=0.02)
cbar.set_label("Number of talks (capped at 90th percentile for contrast)", fontsize=9, color=INK_SOFT)

ax.set_title("Methods × Problems — what work each method is being asked to do",
             fontsize=14, color=INK, loc="left", weight="bold", pad=14)
fig.text(0.06, 0.94,
         "Each cell = the number of talks tagged with both a method (row) and a frame/problem (column). "
         "Empty cells (·) mean no detected co-tag.",
         fontsize=9.5, color=INK_SOFT, style="italic")

fig.text(0.06, 0.012,
         "Source: ASLO-SIL 2026 public schedule, scraped + audited 11 May 2026. Multi-label keyword classifier.",
         fontsize=8, color=INK_SOFT, style="italic")

plt.tight_layout(rect=[0, 0.04, 1, 0.92])
out_mat = ROOT / "output" / "charts" / "methods_x_problems_matrix.png"
plt.savefig(out_mat, dpi=200, facecolor=BG, bbox_inches="tight", pad_inches=0.25)
print("Saved matrix:  {}".format(out_mat))

# Save underlying data
out_data = ROOT / "output" / "tables" / "coattention_and_matrix.json"
with open(out_data, "w", encoding="utf-8") as f:
    json.dump({
        "method_note": "Both analyses use the same multi-label keyword classifier on session and presentation titles + descriptions.",
        "presentations_with_any_tag": n_with_any,
        "total_presentations": len(presentations),
        "tag_counts": dict(tag_count),
        "top_15_cooccurrences": [
            {"tag1": t1, "tag2": t2, "count": w}
            for (t1, t2), w in sorted(cooccur.items(), key=lambda x: -x[1])[:15]
        ],
        "betweenness_centrality": {t: round(b, 4) for t, b in sorted(between.items(), key=lambda x: -x[1])},
        "eigenvector_centrality": {t: round(e, 4) for t, e in sorted(eigen.items(), key=lambda x: -x[1])},
        "methods_x_problems": {
            "rows_methods": methods_sorted,
            "cols_frames": frames_sorted,
            "matrix": matrix_sorted.tolist(),
        },
    }, f, indent=2, ensure_ascii=False)
print("Saved data:    {}".format(out_data))

# ============ Print interesting cells of the matrix ============
print("\n=== STRONGEST METHOD x PROBLEM CO-TAGS ===")
flat = []
for i, m in enumerate(methods_sorted):
    for j, f in enumerate(frames_sorted):
        if matrix_sorted[i, j] > 0:
            flat.append((m, f, matrix_sorted[i, j]))
flat.sort(key=lambda x: -x[2])
for m, f, c in flat[:25]:
    print("  {:<30s} x {:<30s} {} talks".format(m, f, c))
