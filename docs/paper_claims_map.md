# Paper → source map

Every quantitative claim in the manuscript
(`manuscripts/00_SUBMISSION_reading_the_room_1100w.md`) traced to the data,
script, and output that produces it. Run order and environment are in the
top-level `README.md`. All counts derive from the audited public inventory
`data/sessions_all_public.json` (1,461 presentations across 309 session items,
audited 11 May 2026).

| Claim in the paper | Value | Produced by | Output |
|---|---|---|---|
| Presentations / session items | 1,461 / 309 | `data/sessions_all_public.json` (audited inventory) | — |
| Presenters / institutions | ~1,400 / ~720 | `scripts/03_landscape_analysis.py` (community structure) | stdout + `output/tables/` |
| Long-term monitoring share | ~9% of talks | `scripts/03_landscape_analysis.py` (method tags) | `output/charts/methods.png` |
| Machine learning / AI share | 2.4% | `scripts/03_landscape_analysis.py` (method tags) | `output/charts/methods.png` |
| eDNA / -omics share | 3.2% | `scripts/03_landscape_analysis.py` (method tags) | `output/charts/methods.png` |
| Lakes / microbial / biogeochem shares | ~28% / ~18% / ~17% | `scripts/03_landscape_analysis.py` (frames) | `output/charts/frames.png`, Figure 1 (`meeting_highlights_figure1.png`) |
| Title-phrase bigrams | "multiple stressor(s)" 9, "bridging the gap" 8, "convergence" 6 | `scripts/03_landscape_analysis.py` (session-name bigrams) | stdout |
| Equity / Indigenous / community / citizen-science | 14 session items, 58 talks, ~4% | `scripts/04_dei_analysis.py` | `output/reports/dei_sweep.md` |
| Early-career framing | >30 session items, ~6% of talks | `scripts/04_dei_analysis.py` | `output/reports/dei_sweep.md` |
| Gender (presenters / organisers / unclassified) | 53% / 56% / 12% | `scripts/04_dei_analysis.py` (name inference, aggregate only) | `output/charts/dei_gender.png`, `output/reports/dei_sweep.md` |
| Day density (Thu/Fri heaviest, ~490 each; Fri 258 oral + 230 posters) | — | `scripts/03_landscape_analysis.py` (date/room counts) | stdout |
| Country detected | ~78% of presentations (1,138 / 1,461) | `scripts/05_freshwater_vs_participation.py` | `output/reports/freshwater_vs_participation.md` |
| US / Canada share of programme | ~29% / ~25% (together ~54%) | `scripts/04_dei_analysis.py` (geography) + `scripts/05` | `output/reports/dei_sweep.md` |
| Country freshwater shares (Japan 1.1% vs 1.0%; Brazil ~13%; Russia 10%; etc.) | — | `scripts/05_freshwater_vs_participation.py` (World Bank ER.H2O.INTR.K3) | `output/reports/freshwater_vs_participation.md`, `output/tables/freshwater_vs_aslo.json` |
| Seven high-freshwater absentees hold ~42% of global renewable freshwater | Brazil+Russia+Colombia+Indonesia+Peru+India+Myanmar | `scripts/05_freshwater_vs_participation.py` | `output/reports/freshwater_vs_participation.md` |
| Figure 2 (share of programme vs share of global freshwater) | — | `scripts/09_freshwater_proportion_plot.py` | `output/charts/freshwater_share_vs_participation_share.png` |

## Notes on the freshwater denominator

The world freshwater total is the **sum of real-country** World Bank values
(`scripts/05`, corrected 2026-06-11). The World Bank `country/all` endpoint
returns aggregate groupings (regions, income groups, the World total) alongside
individual countries; an earlier version summed all of them, inflating the world
total ~10x. The pipeline now filters to real countries via WB region metadata,
giving ~42,810 bcm/yr (Brazil ~13% of global renewable freshwater). `scripts/09`
independently uses the World Bank "World" aggregate as the denominator and agrees
to within rounding.

## Reproducibility status

- **Runs from the bundled public data** (`data/sessions_all_public.json`), no
  private inputs: `scripts/04_dei_analysis.py`, `scripts/05_freshwater_vs_participation.py`,
  `scripts/09_freshwater_proportion_plot.py`, the water-stress scripts, and the
  FT-ICR-MS sub-analyses (these query OpenAlex live).
- **Need the raw, pre-sanitisation inventory** (held privately for presenter
  privacy; available on request): `scripts/01_audit_capture.py`,
  `scripts/02_complete_inventory_and_prune.py`. The public file in `data/` is the
  sanitised output of that step (presenter emails reduced to domain only).
- Network is required for the freshwater (World Bank API) and FT-ICR-MS
  (OpenAlex) scripts; everything else runs offline from `data/`.
