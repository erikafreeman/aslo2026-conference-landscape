# ASLO-SIL 2026 conference landscape analysis

A reproducible bibliometric and disciplinary read of the [ASLO-SIL 2026 Joint Meeting](https://www.aslo.org/aslo-sil-2026/), 12-16 May 2026, Palais des congrès de Montréal, Quebec, Canada. 1,455 scheduled presentations across 308 session items, audited against the live conference site on 11 May 2026.

## What's in here

| Path | What |
|---|---|
| `data/` | Sanitised conference inventory (sessions, presentations, audit + pruned-withdrawal records). Presenter emails stripped to domain only for privacy; full data available on request. |
| `scripts/` | Numbered analysis scripts: audit -> inventory completion -> landscape analysis -> FT-ICR-MS sub-analysis (in `scripts/fticr/`). |
| `output/charts/` | Generated PNG figures. |
| `output/tables/` | JSON and CSV outputs from each analysis stage. |
| `output/reports/` | Narrative summaries (the conference-landscape Markdown). |
| `manuscripts/` | The Meeting Highlights piece (~500 w), the long-form essay (~1,500 w), Bluesky thread, LinkedIn post. |

## Headline findings (2026)

- 1,461 indexed presentations across 309 sessions. 1,400 unique presenters, 741 institutions.
- The verbs of the schedule have shifted from *describe* to *integrate*: "multiple stressors" 9x, "bridging the gap" 8x, "towards convergence" 6x as session-name bigrams.
- Three simultaneous legacy sessions (Pace, Cotner, Elser) paired structurally with early-career scaffolding (Amplifying Voices x4, ECR alliance workshops, "How To" first-timer session).
- Freshwater science dominates: lakes + limnology = 28% of all talks, rivers + wetlands = +11%, marine = 9%.
- Indigenous knowledge ("Two-Eyed Seeing") programmed as a science session, not as a side workshop. 11 sessions and 28 talks carry equity / community-led framings.
- AI/ML adoption modest but pointed (2.4%). eDNA / -omics undertold (3.2%). Long-term monitoring holding at 9%.
- FT-ICR-MS sub-analysis: 1,746 papers since 2000, 343 in 2025. Saltwater 46% of cumulative corpus; inland waters 17%; wastewater 8%.

### DEI sweep (full report: `output/reports/dei_sweep.md`)

- **Geography:** North America 54% of presentations, Europe 17%, Asia 4%, Latin America 2%, Africa 0.3%. High-income countries 74%; lower-middle income 0.3% (5 talks from Philippines/Kenya/India/Indonesia combined).
- **Gender (name-inferred, with explicit caveats):** of the 88% of presenter names the tool could classify, ~53% female-inferred, ~41% male-inferred. Among session organisers, 56% female-inferred — slightly above the presenter rate.
- **Equity-content sessions:** 14 sessions (58 talks, 4% of program) explicitly programme Indigenous knowledge, equity, community-led, or citizen science. EP013 Two-Eyed Seeing sits as a peer to the Pace/Cotner/Elser legacy sessions.
- **ECR scaffolding:** 32 sessions (88 talks, 6%) — Amplifying Voices x4, ECR alliance workshops, "How To" first-timer guides, mentorship cafes.
- **Institutional type:** 72% university, 8% research institute, <1% government/industry/NGO.

See `output/reports/dei_sweep.md` for full methodology, gender-by-continent breakdown, and limitations (name-inference biases, country-detection coverage, what this analysis is *not*).

See `output/reports/conference_landscape.md` for the full landscape read.

## Reproducing the analysis

### Requirements

Python 3.10+. Install dependencies:

```bash
pip install -r requirements.txt
```

### Run pipeline

```bash
# 1. Audit captured inventory against the live conference site
python scripts/01_audit_capture.py

# 2. Fill in any missing abstracts and prune withdrawn entries
python scripts/02_complete_inventory_and_prune.py

# 3. Run the main landscape analysis (methods, frames, countries, institutions)
python scripts/03_landscape_analysis.py

# 4. FT-ICR-MS sub-analyses (independent — uses OpenAlex)
python scripts/fticr/01_venue_breakdown.py
python scripts/fticr/02_comprehensive_subdiscipline.py
python scripts/fticr/habitat_coarse.py

# 5. UHR-MS adjacent communities (added 2026-05-14)
python scripts/fticr/03_communities_strict_fticr.py    # strict FT-ICR variants only
python scripts/fticr/04_communities_uhrms_expanded.py  # adds Orbitrap + ultrahigh-res
python scripts/fticr/05_environmental_nts.py           # non-target screening / suspect screening
python scripts/fticr/06_consolidated_comparison.py     # builds the headline comparison charts
python scripts/fticr/07_habitat_mismatch_vs_aslo.py    # ASLO program vs FT-ICR literature habitat share
```

All scripts read from `data/` and write to `output/`. They are idempotent (running twice gives the same result).

> **Note on paths.** Scripts 03-07 hard-code Windows output paths near the top of each file (`OUT_LISTS`, `OUT_RAW`, etc.) and use a personal email in the OpenAlex `mailto` polite-pool. Edit those two-to-three constants to local paths and your own email before running. Scripts 01-02 follow the same pattern with a single `base_dir`.

### Data sources

- **Conference inventory**: scraped from the ASLO-SIL 2026 session gallery (public) at https://aslo.secure-platform.com/2026/solicitations/18/sessiongallery. See `data/sessions_all_public.json` for the full dataset.
- **FT-ICR-MS bibliometrics**: queried via OpenAlex (free, open scholarly metadata) on 11-14 May 2026. See `output/tables/fticr_comprehensive_subdiscipline.json` for the DOM corpus and `output/tables/fticr_communities_v3_consolidated.csv` for the cross-community comparison.

## UHR-MS adjacent communities (2026-05-14)

Pulls FT-ICR-MS and Orbitrap publication counts for the seven application communities that use the same instruments, plus the environmental non-target screening (NTS) literature, and compares each against the DOM corpus.

| Community | Total 2000-2025 | 2025 papers |
|---|---|---|
| Environmental non-target screening (NTS) | 1,830 | 360 |
| **DOM science (this repo)** | **1,746** | **343** |
| Petroleomics (NHMFL / Marshall lineage) | 731 | 37 |
| Proteomics (top-down, intact, PTMs) | 636 | 34 |
| Lipidomics | 427 | 52 |
| MALDI imaging of tissue | 405 | 37 |
| Microbiome / exposome | 220 | 55 |
| Pharma (drug metabolism, ADME, impurity profiling) | 207 | 17 |
| Clinical metabolomics | 94 | 4 |

**Headline.** Environmental NTS and DOM science are functionally identical in scale and growth trajectory (within 5% on both cumulative count and 2025 output). Same instruments, same molecular-formula assignment workflow, different molecules (anthropogenic contaminants vs. natural organic matter), different anchor labs (Schymanski / Hollender / Reemtsma vs. Dittmar / Kujawinski / Spencer), almost no citation overlap. See `output/charts/uhrms_dom_vs_nts_growth_v1.png`.

Per-community CSVs in `output/tables/fticr_<community>_v2.csv`. Consolidated summary in `output/tables/fticr_communities_v3_consolidated.csv`.

## Replication guide

See `docs/openalex_replication_guide.md` for a step-by-step explainer of OpenAlex, the query construction, and how to regenerate the FT-ICR-MS growth figure from scratch.

## Methodology notes & caveats

- **Multi-label vs single-label classification.** Theme tags (biogeochem, microbial, methods, disturbance) are multi-label — a paper can carry several — so theme percentages do not sum to 100%. Habitat classification (saltwater / inland / terrestrial / applied) is single-label — each paper is in exactly one category, summing to 100%.
- **Country detection** is keyword-based on affiliation strings and email-domain TLDs. Coverage is ~75%; small countries are likely undercounted.
- **Methods are systematically undertold in titles** because most presentation titles describe findings, not instruments. The true methodological intensity of the meeting is higher than the per-presentation method counts suggest.
- **Captured-vs-live audit (May 11, 2026)** showed 8 entries in our scrape that have since been withdrawn from the live program. These are pruned in the analysis; the record is preserved in `data/pruned_withdrawals.json`.

## Citation

If you use these data or scripts, please cite:

> Freeman, E.C. (2026). *ASLO-SIL 2026 conference landscape analysis*. GitHub repository.

Or use the entry in `CITATION.cff`.

## License

- **Code** (everything in `scripts/`): MIT.
- **Data and figures**: CC-BY-4.0.

See `LICENSE` for details.

## Author

Erika C. Freeman, Group Leader, ABC Lab, Leibniz Institute of Freshwater Ecology and Inland Fisheries (IGB) Berlin.
[ORCID 0000-0001-7161-6038](https://orcid.org/0000-0001-7161-6038)
