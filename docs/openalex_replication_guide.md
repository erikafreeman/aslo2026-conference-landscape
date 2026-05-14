# Reproducing the FT-ICR-MS growth figure with OpenAlex

A step-by-step guide to regenerating the cumulative-plus-per-year publication chart that opens the ASLO-SIL 2026 talk. Includes a short primer on OpenAlex, the exact API parameters, and the differences between the deck figure and the publicly archived analysis script.

## 1. What this guide reproduces

The chart on slide 1 of `index_v8.html` ("Twenty years of UHR DOM measurements") shows the annual and cumulative publication volume of FT-ICR-MS / ultrahigh-resolution mass spectrometry papers applied to dissolved organic matter, 2000-2025. The figure files in the talk and repo are:

- `_DECK/figures/fticr_growth.png` (the slide-1 image)
- `_BibliometricAnalysis/charts/fticr_growth.png` (working copy)
- `_GitHubRepo/aslo2026-conference-landscape/output/charts/fticr_growth.png` (repo copy)

The deck image was rendered from `fticr_growth_data.json` (version `v2_strict`, 1,038 deduplicated works) queried on 11 May 2026.

## 2. Where the public code lives

Repository: https://github.com/erikafreeman/aslo2026-conference-landscape

Branch: `main`

The FT-ICR-MS subanalysis scripts are in `scripts/fticr/`:

- `01_venue_breakdown.py` reuses the same three strict queries that produced the deck figure, classifies hits by journal venue, and writes `fticr_growth_by_venue.png` plus the ecology-only paper list.
- `02_comprehensive_subdiscipline.py` unions eleven strict queries (broader recall), tags each paper by subdiscipline, and writes `fticr_growth_comprehensive.png` plus the per-subdiscipline JSON and CSV.

Direct links:
- https://github.com/erikafreeman/aslo2026-conference-landscape/blob/main/scripts/fticr/01_venue_breakdown.py
- https://github.com/erikafreeman/aslo2026-conference-landscape/blob/main/scripts/fticr/02_comprehensive_subdiscipline.py

The exact plotting script that produced the slide-1 PNG (the strict 3-query version with no venue stacking) is not in the public repo. The data behind it (`fticr_growth_data.json`) and the regenerated comprehensive chart from script 02 are both archived. A reader can reproduce the same figure shape from either path.

## 3. What OpenAlex is

OpenAlex is a free, open, programmatic index of scholarly works run by OurResearch, launched in January 2022 as the successor to Microsoft Academic Graph. It indexes roughly 250 million works (papers, books, datasets, preprints), 90 million authors, and 100,000 sources (journals, repositories). It pulls metadata from Crossref, PubMed, ORCID, DOAJ, ROR, the Unpaywall API, and direct publisher feeds.

Why use it instead of Web of Science or Scopus:

| Property | OpenAlex | Web of Science / Scopus |
|---|---|---|
| Cost | Free | Institutional subscription required |
| API | Open, no auth needed | Restricted, license-bound |
| Coverage | Includes preprints, datasets, books | Mostly journal-indexed |
| Reproducibility | Anyone can rerun the query | Reader must have a subscription |
| Rate limits | 10 requests/sec; ~100,000/day (polite pool) | Tighter and license-dependent |

The trade-off: OpenAlex coverage is broader but slightly noisier. Citation counts and author disambiguation are less curated than WoS. For a bibliometric trend like FT-ICR-MS adoption that is dominated by recent indexed work, the noise floor is acceptable.

Endpoint base: `https://api.openalex.org/works`

Documentation: https://docs.openalex.org/

To enter the "polite pool" (higher rate limits, no extra cost), pass an email via the `mailto` query parameter on every call. The queries below do this.

## 4. The exact query that produced the deck figure

Three independent searches, deduplicated by OpenAlex work-ID:

```
title_and_abstract.search:"FT-ICR" AND "dissolved organic matter"
title_and_abstract.search:"FTICR" AND "DOM"
title_and_abstract.search:"ultrahigh resolution mass" AND "dissolved organic matter"
```

For each query, results are restricted to `publication_year:2000-2025` and paginated with cursor `*` (200 per page). Hits are merged into a single dictionary keyed on `id` so duplicates across the three queries collapse to one work. The 11 May 2026 pull returned 1,038 unique works.

The plotting code stacks two axes:
- left axis: per-year publication count as bars
- right axis: cumulative count as a line with markers

Title and footer carry the source attribution.

## 5. Step-by-step replication

### Prerequisites

- Python 3.10 or newer
- Internet access (the OpenAlex API is unauthenticated but rate-limited)
- Disk: ~10 MB for outputs

### Clone the repo

```
git clone https://github.com/erikafreeman/aslo2026-conference-landscape.git
cd aslo2026-conference-landscape
```

### Install dependencies

```
pip install -r requirements.txt
```

The relevant packages are `requests` (HTTP) and `matplotlib` (plotting). No matplotlib backend tweaks are needed; the scripts write PNGs directly.

### Edit one path before running

Both fticr scripts hard-code a Windows path for their output directory:

```
base_dir = Path(r"C:\Users\erika\Organise\aslo2026\presentation\figures")
```

Change this to a path that exists on your machine, for example `Path("output/charts")` relative to the repo root, before running.

### Run

```
# Same 3 strict queries as the deck figure, plus venue classification
python scripts/fticr/01_venue_breakdown.py

# Broader 11-query union with per-subdiscipline tagging
python scripts/fticr/02_comprehensive_subdiscipline.py
```

Expected runtime: 30 to 90 seconds per script depending on network. Each script prints a per-query "new works" count as it goes, then a deduplicated total, then writes its outputs.

### What you get

Script 01 outputs:
- `fticr_growth_by_venue.png` (stacked bar chart by venue type, 2023-2025)
- `fticr_2025_papers_ecology_only.md` and `.csv` (paper lists)
- `fticr_breakdown_2023_2025.json` (the underlying counts)

Script 02 outputs:
- `fticr_growth_comprehensive.png` (the equivalent of the slide-1 figure, with 11 queries instead of 3)
- `fticr_subdisciplines.png` (horizontal bar of subdiscipline totals)
- `fticr_comprehensive_subdiscipline.json` (per-year, per-subdiscipline counts and the query list)
- `fticr_comprehensive_all_papers_tagged.csv` (one row per paper with subdiscipline tags)

## 6. Reading the OpenAlex API call

The core API call inside both scripts is structured like this:

```python
params = {
    "filter": 'title_and_abstract.search:"FT-ICR" AND "dissolved organic matter",publication_year:2000-2025',
    "per-page": 200,
    "select": "id,doi,title,publication_year,authorships,primary_location,abstract_inverted_index,topics,keywords",
    "cursor": "*",
    "mailto": "erika.freeman@igb-berlin.de",
}
r = requests.get("https://api.openalex.org/works", params=params, timeout=60)
```

Key things to know:

- `filter` is comma-separated. Multiple filters AND together. `title_and_abstract.search` is a free-text search across the title and the reconstructed abstract.
- `select` keeps the payload small. Without it you get every available field per work.
- Cursor pagination: the response contains `meta.next_cursor`; pass it back as the next request's `cursor`. When it is missing, you have reached the end.
- `mailto` puts you in the polite pool. It is not authentication; it is courtesy. Anonymous calls are throttled harder.

OpenAlex stores abstracts as an inverted index (word -> list of positions). To get human-readable text, walk the index and place each word at its earliest position. The function `reconstruct_abstract` in script 02 does exactly this.

## 7. Caveats and limitations

- **Recall is bounded by the query.** "FT-ICR" plus "dissolved organic matter" misses a paper that says "ultrahigh resolution mass spectrometry of DOM" without the canonical phrase. The 11-query version in script 02 widens the net (Orbitrap, van Krevelen, molecular formula assignment, natural organic matter as a synonym for DOM) and pulls 1,746 papers instead of 1,038. Both are defensible; the strict 3-query figure is more conservative.
- **OpenAlex coverage decays before 2010.** Early-2000s FT-ICR-MS DOM papers existed but indexing is patchier. Counts in 2000-2007 are likely slight undercounts. Post-2010 counts are reliable.
- **Preprints and data deposits inflate raw totals.** Script 01 separates these out (figshare, ChemRxiv, ESSOAr, etc.) so the ecology and engineering bars represent peer-reviewed venues only.
- **Topic and keyword fields are derived.** OpenAlex assigns topics with a machine-learning classifier (the `Topics` system). They are useful for triage but not gold-standard. Subdiscipline tagging in script 02 uses keyword regex on title + abstract + topics + keywords as a four-way fallback.
- **Query date matters.** The deck figures are stamped "queried 2026-05-11." A rerun on a later date will show slightly higher counts in 2025 because of late indexing.

## 8. Citing OpenAlex

OpenAlex asks users to cite the platform paper:

> Priem, J., Piwowar, H., & Orr, R. (2022). *OpenAlex: A fully-open index of scholarly works, authors, venues, institutions, and concepts*. arXiv:2205.01833. https://arxiv.org/abs/2205.01833

When reusing the conference-landscape repo, cite:

> Freeman, E.C. (2026). *ASLO-SIL 2026 conference landscape analysis*. GitHub repository. https://github.com/erikafreeman/aslo2026-conference-landscape

## 9. Quick checklist for a clean rerun

1. Clone the repo.
2. `pip install -r requirements.txt`.
3. Replace the hard-coded `base_dir` Windows path in both fticr scripts with a path that exists locally.
4. Run `python scripts/fticr/01_venue_breakdown.py` (~1 min, three queries, venue breakdown).
5. Run `python scripts/fticr/02_comprehensive_subdiscipline.py` (~1 min, eleven queries, growth + subdiscipline chart).
6. Inspect `output/charts/fticr_growth_comprehensive.png` and the JSON outputs.
7. If the numbers shifted, check `meta.queried` date in the JSON; OpenAlex back-fills indexes for several months after the publication year closes.
