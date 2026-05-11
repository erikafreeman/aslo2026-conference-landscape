# Version notes — long-form member narrative

*Audit trail for `01_member_narrative_1500w_v1.md` through `_v8.md`. Kept here so the public article body in the published version stays clean of audit mechanics; the trail remains traceable for any reviewer or reader.*

---

## v10 — wired-together analysis added (current)

One new section vs v9: **"How the questions are wired together,"** slotted between *Methods in the program* and *Indigenous knowledge, equity, and community-led science.* About 280 words. Reports the co-attention network (top co-occurrences, bridge topics by betweenness centrality, hubs by eigenvector centrality) and the methods × problems matrix (long-term monitoring as connective-tissue method; eDNA concentrated in microbial / biodiversity; UHR-MS concentrated in DOM; AI/ML horizontal-but-low everywhere). Network and matrix visualisations referenced as living in the repository, not embedded as additional figures in the manuscript body (keeps the figure count flexible for whichever submission category the editor selects).

Closing portrait updated to reflect the new section — adds "long-term monitoring as the connective-tissue method" and "rivers, estuaries, fisheries, food webs, DOM, and equity content as the bridge topics."

Data-and-methods endnote updated with a one-line note on the network construction (networkx; weight ≥10 edge threshold; betweenness and eigenvector centrality).

Word count: ~2,050. Still within L&O Bulletin Article range (3,000–5,000) or the upper end of Meeting Highlights (500–1,500); if Laura selects Meeting Highlights with the 1,500-word ceiling, the wired-together section is the natural first cut (and the v9 piece is the ready-to-trim parent).

---

## v9 — gender-parity finding added

New short section *"Gender parity, quietly reached"* between the Indigenous-knowledge/equity section and the geography section. Names the finding (about 53% female-inferred presenters, about 56% organisers among classifiable names) and the European-biased classifier caveat. Frames as "a real and unevenly acknowledged victory."

Closing summary updated to add "Gender parity reached at both presenter and organiser levels" to the portrait list.

Data-and-methods endnote updated with the gender-inference caveat.

---

## v8 — editorial polish for publication

Three editorial polishes vs v7:
- **Title set in title case**: "Reading Ourselves Through the Program: ASLO-SIL 2026 in Numbers, Verbs, and Invitations."
- **Subtitle replaced** with a less repetitive line: "What 1,455 scheduled presentations reveal about aquatic science in 2026."
- **Opener softened** from "So I read the program." (slightly bloggy) to "I read the program as a record of collective attention."
- **Version note removed from the article body.** It now lives in this file. The article itself ends on its closing thought, not on audit mechanics.
- **Data and methods endnote slimmed** to a single short paragraph: data source, audit date, classifier caveat, country-detection caveat, freshwater data source, GitHub link. Removed the per-line breakdown that read like a methods appendix.

The piece's load-bearing sentence is preserved: *"Read generously, this is not only a gap. It is a map for future collaboration."*

---

## v7 — opportunity-language reframe (per editor feedback)

Two substantive changes vs v6:
1. **Reframed throughout from deficit language to opportunity language.** Paragraph openers rewritten — "Freshwater science is a major center of gravity in this joint meeting" replaced "The SIL half is doing real work"; "A map for future invitations" replaced "The geographic gap remains." Closing reframed from synthesis-moment-it-has-earned to "building the collaborations, methods, and institutional habits needed to respond." Dense-day paragraph closes with abundance framing.
2. **Corrected the freshwater denominator bug carried over from v6.** The v6 world-freshwater total had summed WB indicator records that included both real countries and aggregate groupings (World, IDA & IBRD, income tiers, regional aggregates), inflating the total by roughly 10× and making every country's freshwater share look 10× smaller than reality. With the corrected denominator (WB "World" aggregate ≈ 42,809 bcm/yr, matching the sum of real-country values), Brazil's freshwater share is about 13% (not 1.3%) and Brazil is significantly under-represented at the meeting, not at parity. Japan is the closest-to-parity country. The "Brazil only proportional" claim from v6 has been replaced with the corrected facts.

Title updated to add "invitations" alongside "numbers and verbs."

---

## v6 — Dittmar/Freeman lineage explicit (carry-over from deck v6)

Not an L&O Bulletin manuscript change, but covered the audit pass that fed into v7.

---

## v5 — portal-verified corrections

Cross-checked against the live ASLO-SIL 2026 public portal:
- Venue is Montreal (Palais des congrès), not Quebec City.
- 1,455 scheduled presentations (was 1,461).
- 308 session items (was 309).
- About 1,400 primary presenters, about 740 institutions (stated as approximations).
- Friday density updated to 260 oral + 230 posters (was 257 + 232).
- AV001 is a single session, not a four-part series (v4 said "AV001A–D").
- SS070 title corrected to "Exploring the Confluence of Data, Models, and Forecasts."
- Topic-bucket percentages prefixed "about" and explicitly cited as repository-classifier output.

---

## v6 (manuscript-track v6, distinct from deck v6) — audited, every assertion verified

Major changes vs v5:

**REMOVED — unverifiable historical / vibe claims:**
- "Twenty years ago, ASLO session names were dominated by measure, describe, characterise." Historical bigram check on 2003/2007/2010 ASM program books did not support the contrast.
- "Decades learning how to separate" — unverified historical.
- "The field's methodological soul" (about long-term monitoring).
- "The chemodiversity conversation is a coherent young community."
- "The subsurface is one of the spaces aquatic science is best positioned to grow into."
- "By 2031 this will be a much larger share" — speculative forecast.
- "Until recently outside our reach."
- Several other "the community is X" / "the field is Y" character assertions.

**CORRECTED:**
- "80% of the program lives in eight topical homes" (mathematically meaningless sum of multi-label percentages) → "about 93%" (the actual union).
- SS048 mischaracterised as "HAB toxin tracking" → "Some like It Hot: Cyanobacteria Adaptations and Expansion Across Different Environments" (real title).
- "Mike Pace's tribute... because the people who built the meeting think they belong" (speculates intent) → "the program structurally pairs the two" (description, not speculation).

**VERIFIED:**
- All 23 session codes referenced cross-checked against the public schedule.
- AV001 speaker affiliations confirmed against the scraped inventory.
- All classifier percentages traceable to repository tables.

---

## v5 — corrected framework citation + paper QRs added (deck-track)

(Belongs to the deck version history, included here for completeness.)

---

## v4 — "Pie in the sky" → "Moonshot"

Single-section label change on slide 4 of the deck.

---

## v3 — paper QR codes added + framework citation corrected

Corrected the Ecology of Molecules attribution: published in TREE 40(3):219–223 (2025), not "in revision at Am Nat" as v2 stated.

---

## v2 — 8-section restructure per outline

Original deck v1 (representation-taxonomy thesis) restructured to the 8-section outline (Ecology of Molecules framework → individual molecules → the mixture → interactions → matrices → ask).

---

## v1 — original

The reveal.js deck as it stood before the ASLO submission and the L&O Bulletin work began.

---

*Maintained: 2026-05-11. If you spot a claim in v8 that you can't trace to a corresponding entry in `output/tables/` or that survives this audit list, please flag it.*
