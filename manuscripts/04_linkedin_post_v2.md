# LinkedIn post — ASLO-SIL 2026 reading *(v2, audited)*

**Format:** ~1,200-char main post + a first comment with links + methodology + caveats.

**Timing:** Friday evening or Saturday after the meeting wraps.

---

## MAIN POST (~1,180 chars)

A conference is two things at once: the meeting in the rooms, and the portrait the programme paints of the community putting it on.

For ASLO-SIL 2026 in Montreal this week, the second portrait is striking. I read all 1,455 scheduled presentations across 308 session items before flying. Six things the schedule itself says:

→ The most-repeated session-title phrases are about working across. "Multiple stressors" ×9. "Bridging the gap" ×8. "Towards a Convergence of Current Knowledge and Application" ×6.

→ Three career-tribute sessions (Mike Pace, Jim Cotner, Jim Elser) appear in the same programme as six dedicated early-career sessions (Amplifying Voices, ECR alliance, "How To" first-timer, Raelyn Cole Fellowship retrospective).

→ Lakes 28%, microbial ecology 18%, biogeochemistry 17%, climate-as-forcing 10%. About 93% of talks carry at least one of the dominant tags. Freshwater systems (39%) outweigh saltwater (15%).

→ Indigenous knowledge, equity, and community-led science are programmed across 14 session items (58 talks). EP013 "Two-Eyed Seeing" is a science session.

→ Method tags: AI/ML 2.4%, eDNA/-omics 3.2%, mass spectrometry 2%, long-term monitoring 9% (the most-tagged single method).

→ US 29% + Canada 25% = 54% of presenters. Brazil is the only top-20 country whose share of the programme roughly matches its share of global renewable freshwater.

(Full data, reproducible analysis, long-form essay: see comments.)

#ASLO2026 #AquaticSciences #Limnology #DOM

---

## FIRST COMMENT (links + methods + caveats, ~860 chars)

Methodology: scraped the full session gallery from the ASLO-SIL public site (1,455 scheduled presentations across 308 session items, audited 11 May 2026). Tagged presentations by methodology and disciplinary frame using keyword classifiers (multi-label; classifier is approximate). Country detection is keyword-based on affiliation strings and email-domain TLDs — about 78% coverage; small countries undercounted.

→ GitHub repo (data + code, fully reproducible): [LINK]
→ Long-form essay (~1,700 words, v6 with every assertion audited): [LINK]
→ Meeting Highlights piece submitted to L&O Bulletin

Caveats are baked into the repo README. Topical and method percentages are tag rates, not exclusive shares — they describe what the classifier finds, not what the field "is."

If you presented or attended ASLO-SIL 2026, what did the programme get right, and what did it leave out? Find me at SS050B "Ecological Significance of DOM" on Friday afternoon.

---

## SECOND COMMENT *(optional — networking, ~390 chars)*

A few people from the programme working at the integration/synthesis edge:

— Nandita Basu (Waterloo) — POSEIDON watershed nutrient platform (SS070)
— Andrew Tanentzap (Trent) — DOM chemodiversity, co-organising SS050
— Blake Matthews (Eawag) — eco-evolutionary cascades (SS030)
— Sara Soria-Píriz & Masumi Stadler (UQAM) — microbial-DOM coupling, co-organising SS058

Worth catching if you're at the meeting.

---

**Notes on tone:** declarative, specific numbers, no overclaim, ends with a question. Disclosure of own talk is in the cited GitHub repo and the long-form essay, not crowded into the main post.

**Hashtags:** lean. Skip #ScienceTwitter / #SciComm — too broad for the target audience.

**Before posting:** swap `[LINK]` placeholders for the live GitHub repo URL and the long-form essay URL.

---

**Version note (v2):** five claims from v1 were removed because they didn't survive verification:
1. *"The verbs have changed. 2006 session names said measure, describe, characterise"* — historical bigram check on 2003/2007/2010 ASM programmes did not support the contrast.
2. *"The Montreal venue + joint meeting put freshwater back at the front"* — softened to a description of the data (freshwater 39% vs saltwater 15%) without the implied historical comparison.
3. *"The field's methodological soul"* (about long-term monitoring) — replaced with the literal numeric ranking ("the most-tagged single method").
4. *"The bets being placed in Montreal this week will look obvious in 2031"* — speculative forecast removed.
5. *"The community is handing off in public"* and *"the field is naming its synthesis moment out loud"* — replaced with structural descriptions of what's in the programme (the session pairing; the bigram counts) without claiming community intent.

Also: the methodology comment was updated to use the corrected count (1,455 scheduled presentations, not 1,461) and to flag the multi-label-tagging caveat explicitly.
