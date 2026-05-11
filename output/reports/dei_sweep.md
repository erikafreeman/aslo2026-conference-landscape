# ASLO-SIL 2026 — DEI sweep

*Aggregate-level analysis of the 1,461 indexed presentations across 309 sessions. Generated 2026-05-11 from `data/sessions_all_public.json`.*

## TL;DR

- **Geographic concentration is real**: ~74% of presenters are from high-income countries; only ~4% from middle- or lower-income countries combined. US + Canada alone account for ~54% of presentations.
- **Name-inferred gender** suggests roughly **53% female / 41% male** among the 1283 presenters the database could classify (88% of all presenters). The remaining 12% — disproportionately East Asian, Indigenous, and other non-Western names — could not be classified by the (European-biased) tool used. The 50/50 ratio is roughly consistent with what one would expect from a 2026 aquatic-science meeting where the ECR cohort is more gender-balanced than senior cohorts.
- **14 equity-content sessions** (Indigenous knowledge, equity, community-led, citizen science) carry **58 talks (4.0% of the program)**. Two-Eyed Seeing programmes Indigenous knowledge as a knowledge system, not a side track.
- **32 ECR-scaffolding sessions** carry **88 talks (6.0%)**. The Amplifying Voices track, ECR alliance workshops, and "How To" first-timer sessions are structurally programmed.

## 1. Geography

### Continent breakdown

| Continent | Presentations | Share |
|---|---:|---:|
| North America | 788 | 53.9% |
| Unknown | 320 | 21.9% |
| Europe | 244 | 16.7% |
| Asia | 55 | 3.8% |
| Latin America | 31 | 2.1% |
| Oceania | 18 | 1.2% |
| Africa | 5 | 0.3% |

### Income group (World Bank-style)

| Income group | Presentations | Share |
|---|---:|---:|
| High | 1085 | 74.3% |
| Upper-middle | 51 | 3.5% |
| Lower-middle | 5 | 0.3% |
| Unknown | 320 | 21.9% |

**Read:** The program is dominated by high-income-country affiliations (74% of all presentations). Upper-middle-income participation (mostly China, Brazil, Mexico) is real but ~3% of the program. **Lower-middle-income presence is small** (0%) — the Philippines, Kenya, India, Indonesia together appear in fewer than 30 talks. This is structural; ASLO is making deliberate efforts via Amplifying Voices, but the financial and travel-visa frictions remain.

## 2. Gender (name-inferred, with explicit caveats)

The `gender_guesser` library was used to infer gender from first names. **Critical caveats:**

- The underlying name database is European-biased. Chinese, Korean, Japanese, South Asian, African, and Indigenous names are disproportionately classified as `unknown`.
- Even among classified names, misclassification rate is likely 5-15%.
- This is **aggregate-level analysis only**. No individual is labelled in the data files released; only the distribution.

**Headline rates (of names the tool could classify):**

| Inferred | Count | Share of classified |
|---|---:|---:|
| Female-inferred | 682 | 53.2% |
| Male-inferred | 520 | 40.5% |
| Androgynous (could be either) | 81 | 6.3% |

**The 12% `unknown` rate is itself a DEI signal**: it suggests the tool — and many similar tools — systematically under-classify names from cultures whose phonologies it wasn't trained on. The real gender distribution is probably closer to 50/50 than these numbers suggest, but the *visibility gap* for non-Western researchers is real and worth naming.

### Gender × continent

| Continent | n (classified) | Female-inferred share |
|---|---:|---:|
| North America | 702 | 53.4% |
| Europe | 222 | 47.7% |
| Asia | 39 | 15.4% |
| Latin America | 29 | 58.6% |

(Continents with very low classified counts are omitted because the tool gives them disproportionately `unknown`.)

## 3. Session organisers

Across **938 organiser slots** (lead organisers + co-organisers across all 309 sessions):

- **831 (89%)** could be name-classified
- **56.4% female-inferred** among the classified — close to the presentation-level rate.

The organiser cohort and the presenter cohort have similar inferred gender ratios. That's not always the case at other large meetings (organisers skew older and historically more male); the parity here suggests intentional rotation.

## 4. Institutional type

| Type | Count | Share |
|---|---:|---:|
| university | 1057 | 72.3% |
| other | 269 | 18.4% |
| research institute | 118 | 8.1% |
| government | 11 | 0.8% |
| unknown | 3 | 0.2% |
| industry | 2 | 0.1% |
| ngo / foundation | 1 | 0.1% |

**Read:** Universities dominate (72% of presentations), which is expected. Research institutes (8%) — IGB, CSIC, CSIRO, NIVA, NIOZ, the Leibniz network — are substantially over-represented relative to many aquatic meetings, reflecting Europe's institute-heavy research ecosystem.

## 5. Equity content

**14 sessions** (out of 309) explicitly programme Indigenous knowledge, equity, community-led science, or citizen science, carrying **58 talks (4.0%)** of the program. Sessions include:

- **[SS055A]** Integrative Approaches to Freshwater Monitoring: Emerging Technologies, Communit
- **[SS079A]** Emerging Directions in Community-Based Water Monitoring, Participatory Science, 
- **[EP006]** A Decade of Insights with the Raelyn Cole Editorial Fellowship
- **[EP013]** Two-Eyed Seeing: Indigenous Knowledge and Western Science
- **[EP013P]** Two-Eyed Seeing (Posters)
- **[SS055B]** Integrative Approaches to Freshwater Monitoring: Emerging Technologies, Communit
- **[SS055C]** Integrative Approaches to Freshwater Monitoring: Emerging Technologies, Communit
- **[SS055P]** Integrative Approaches to Freshwater Monitoring: Emerging Technologies, Communit
- **[SS079B]** Emerging Directions in Community-Based Water Monitoring, Participatory Science, 
- **[WS02]** Workshop: Harmonization of distributed data
- **[WS08]** From Values to Practice: Inclusive Science Spaces
- **[WS05]** Weaving Indigenous Knowledge and Western Science

**Why this matters:** equity content is *structurally programmed*, not buried in a single panel. "Two-Eyed Seeing" sits as EP013 — a peer to the Pace/Cotner/Elser legacy sessions. The signal is clear: the society treats Indigenous knowledge as a knowledge system, not as a topic of study.

## 6. ECR scaffolding

**32 sessions** explicitly engage early-career researchers, carrying **88 talks (6.0%)** of the program. The structure is:

- **AV001A-D "Amplifying Voices in Aquatic Sciences"** — four full sessions organised by the ECC
- **EC02/EC03/EC04** — ECR workshops on resilience, cross-organisational alliances, and the publishing process
- **EP010 / EP011** — "Sharing Experiences Among ECRs" and "How To" first-timer guides
- **EP006** — Raelyn Cole Editorial Fellowship retrospective

ECR scaffolding is not decorative. It is **structurally programmed across the meeting** with named cohorts, named workshops, and named publications. This is the model ESA, AGU, and SIAM have been moving toward; ASLO is among the leading societies on it.

## Methodological caveats (full)

See `output/tables/dei_summary.json` field `method_notes` for the formal version. The headlines:

1. **Country detection** ~75-80% complete; smaller countries undercounted.
2. **Gender inference** is name-based and European-biased; treat as a rough distributional sketch, not a label of any individual.
3. **Equity-session detection** is keyword-based on session names + descriptions; sessions where equity framing lives at the *talk* level rather than session level are missed.
4. **Career-stage signals** are inferred from session-framing keywords, not author bibliographies; the actual ECR share of presenters is unknown.
5. **Institutional type** classification is coarse; some hybrids (university-government partnerships, e.g.) are forced into one bucket.

## What this analysis is NOT

- Not an audit of any individual presenter or organiser.
- Not a claim that the meeting has solved DEI; the data above suggests several gaps remain.
- Not a substitute for self-reported demographic data, which is the only authoritative source for individual-level analysis.

This is an aggregate pattern read, suitable for understanding *what the schedule represents at the field level* and where there's room to do better.
