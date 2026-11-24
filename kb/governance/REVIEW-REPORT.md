# KB-30 consistency review

Baseline: KB-29 commit `0f5a39a7658fbe770577c74f3991bcbaec6e4ab5`. Scope: all KB files. The totals below count top-level reading rules. Templates, synthetic examples, glossary definitions, tables, spreads, remedies and checker recipes have separate roles. No reading or glossary content was added.

## Totals

**1,812 addressable rules, 1,699 distinct evidence IDs after declared aliases, 661 glossary entries, 10 systems.** The 156 Tarot orientations are included. All rules are drafts. Each carries English, Kannada and Hindi user text and at least one registered source.

| System | Rule IDs | Evidence aliases | Low | Disputed | Missing tradition notes among flagged | EN status unrecorded | KN pending | HI pending |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| face-reading | 1 | 0 | 0 | 0 | 0 | 1 | 1 | 1 |
| jaimini | 32 | 0 | 0 | 0 | 0 | 32 | 32 | 32 |
| kp | 19 | 0 | 0 | 0 | 0 | 19 | 19 | 19 |
| lal-kitab | 14 | 0 | 0 | 0 | 0 | 14 | 14 | 14 |
| numerology | 101 | 0 | 0 | 0 | 0 | 101 | 101 | 101 |
| palmistry | 83 | 0 | 0 | 0 | 0 | 83 | 83 | 83 |
| tarot | 156 | 0 | 0 | 0 | 0 | 156 | 156 | 156 |
| vastu | 99 | 0 | 0 | 0 | 0 | 99 | 99 | 99 |
| vedic | 997 | 113 | 0 | 90 | 0 | 997 | 997 | 997 |
| western | 310 | 0 | 0 | 0 | 0 | 310 | 310 | 310 |

English is the authoring language. The rule schema tracks native review for Kannada and Hindi. No rule records approval for those two languages. The 661 glossary definitions also await language review. Planned locales retain English fallback.

## Top ten fixes

1. Registered 108 legacy Vedic graha-in-house IDs as evidence aliases of their expanded whole-sign placement entries. Historical lookups retain the old text. New readings have one evidence identity per placement.
2. Aliased four redundant active-house-lord IDs for the fourth and seventh houses. Their life-area routes remain available and the same ownership fact contributes once.
3. Linked the dosha and transit versions of Ashtama Shani to one evidence identity for the same person and transit interval. The source records retain their explanations.
4. Registered 26 shared-copy aliases for numerology records with identical rule sentences and trilingual text. Retained separate calculation predicates and school-specific comparisons.
5. Corrected 271 public text fields in 228 files. Edits cover legacy “might/could” phrasing, bare instructions, checker assertions and the health referral. Each corrected file and locale appears below.
6. Filled the missing Kannada and Hindi labels for all eleven life-area navigation keys. The English, Kannada and Hindi label maps now contain the same keys.
7. Pinned numeric sidereal modes in the shared machine-readable profiles and removed the obsolete open KP-variant statement from the coverage guide. Vedic uses Lahiri mode 1 with whole-sign houses. KP uses Krishnamurti mode 5 with Placidus cusps.
8. Reconciled Western house options across the shared, natal and aspect configurations. Tropical Placidus is the default. Whole-sign is selectable and is the documented polar fallback. Koch and equal-house remain glossary reference terms.
9. Corrected the two retired sample identifiers in Asha’s fixture to the current Jupiter-in-house-ten and Gaja Kesari IDs. The fixture remains hypothetical and its validator now checks both target IDs.
10. Separated the muhurta tone-selection instruction from the output tone field. Stored tone values and the three shared display labels use Supportive, Steady and Take care.

Also updated the edition guide’s stale counts (574 rules and 26 yogas), canonical placement directory and checker description, linked the glossary from the KB overview, and extended the low-confidence tradition-note requirement to match the disputed-rule requirement.

## Cross-system references and duplicate review

The [alias registry](review/rule-aliases.yaml) has separate evidence and wording mappings. The [explanation payload](../shared/explain/payload.yaml) specifies their use. Validation rejects missing targets, chained aliases, divergent wording within a shared-copy alias and changed formation predicates within an evidence alias. The Ashtama equivalence test explicitly compares its singleton list with the scalar transit condition. Engine integration still needs to consume these identities within each dated, person-specific context.

Every reading ID has at least one incoming link from a different KB document, excluding the review report and validator code. 1,202 rules have incoming literal references only from the glossary. These rules are discoverable by the rule loader, which scans rule files and tests their fact predicates. That is a static reachability check. An app-level navigation test for each entry still belongs in integration. Glossary entries are reached by their inventory and locale keys. The spread definitions have stable short IDs and glossary references.

The audit checked literal dotted rule and glossary IDs across KB text, typed reference fields, fact keys, source works and editions, and relative YAML and Markdown paths. Symbolic ID builders (for example a house-lord pair) use bounded module inventories and are checked by their module validators. No unresolved concrete KB ID or orphan reading record remained.

Duplicate review grouped predicates, rule sentences, trilingual public text and repeated system/filename pairs. A predicate shared by all eight northern matching factors or all ten southern factors selects a comparison profile; each factor reads its own table. Direction rulership and room-use records share a sector but answer different questions. The dated Saturn phase and instant house reading have different time scopes. Different cards and named Sun-flank formations can share wording while testing distinct facts. Preserve their IDs. Semantic equivalence in unstructured prose still needs editorial judgment.

## Public copy, locale and source checks

Checked 7,194 localized strings under `user_text`, including nested remedies, summaries, examples and spread positions. The template contains authoring placeholders. All live copy fields have en/kn/hi. All English entries contain “may” or “can”, with corresponding possibility language in Kannada and Hindi. The sweep covered fear terms, scores, percentages, luck, products, paid remedies and compatibility verdicts. A house number, a date or the phrase “starting point” is meaningful information and does not constitute a score. The health guidance still directs the reader to a doctor for worries. **Remaining files failing the wording check: none.**

Every rule has a source. Citation records by status: chapter-only 304, pending 1,190, verified 2,760. These counts refer to citations rather than unique books. A citation marked verified supports only the claim described in its record.

**Manual length screen:** 0 public strings exceed 40 whitespace-delimited words in any locale. This threshold is a triage measure. Full editions and rights-cleared comparison texts are not part of this repository, so absence of copied passages cannot be certified by the length screen. Compare suspect close paraphrases and pending locators with the specified editions before publication.

## Low and disputed register

No production rule has low confidence. The following 90 disputed rules each have a populated school-difference note. The separate Gaja Kesari snapshot in the Asha example also carries a dispute note.

### vedic

- `vedic.doshas.bhakoot`
- `vedic.doshas.grahan`
- `vedic.doshas.guru-chandal`
- `vedic.doshas.mars-partnership`
- `vedic.doshas.nadi`
- `vedic.doshas.nodal-axis`
- `vedic.doshas.pitru`
- `vedic.doshas.shrapit`
- `vedic.matching.bhakoot`
- `vedic.matching.nadi`
- `vedic.planets.ketu`
- `vedic.planets.rahu`
- `vedic.planets-in-houses.ketu-house-1`
- `vedic.planets-in-houses.ketu-house-10`
- `vedic.planets-in-houses.ketu-house-11`
- `vedic.planets-in-houses.ketu-house-12`
- `vedic.planets-in-houses.ketu-house-2`
- `vedic.planets-in-houses.ketu-house-3`
- `vedic.planets-in-houses.ketu-house-4`
- `vedic.planets-in-houses.ketu-house-5`
- `vedic.planets-in-houses.ketu-house-6`
- `vedic.planets-in-houses.ketu-house-7`
- `vedic.planets-in-houses.ketu-house-8`
- `vedic.planets-in-houses.ketu-house-9`
- `vedic.planets-in-houses.rahu-house-1`
- `vedic.planets-in-houses.rahu-house-10`
- `vedic.planets-in-houses.rahu-house-11`
- `vedic.planets-in-houses.rahu-house-12`
- `vedic.planets-in-houses.rahu-house-2`
- `vedic.planets-in-houses.rahu-house-3`
- `vedic.planets-in-houses.rahu-house-4`
- `vedic.planets-in-houses.rahu-house-5`
- `vedic.planets-in-houses.rahu-house-6`
- `vedic.planets-in-houses.rahu-house-7`
- `vedic.planets-in-houses.rahu-house-8`
- `vedic.planets-in-houses.rahu-house-9`
- `vedic.planets-in-signs.ketu-aquarius`
- `vedic.planets-in-signs.ketu-aries`
- `vedic.planets-in-signs.ketu-cancer`
- `vedic.planets-in-signs.ketu-capricorn`
- `vedic.planets-in-signs.ketu-gemini`
- `vedic.planets-in-signs.ketu-leo`
- `vedic.planets-in-signs.ketu-libra`
- `vedic.planets-in-signs.ketu-pisces`
- `vedic.planets-in-signs.ketu-sagittarius`
- `vedic.planets-in-signs.ketu-scorpio`
- `vedic.planets-in-signs.ketu-taurus`
- `vedic.planets-in-signs.ketu-virgo`
- `vedic.planets-in-signs.rahu-aquarius`
- `vedic.planets-in-signs.rahu-aries`
- `vedic.planets-in-signs.rahu-cancer`
- `vedic.planets-in-signs.rahu-capricorn`
- `vedic.planets-in-signs.rahu-gemini`
- `vedic.planets-in-signs.rahu-leo`
- `vedic.planets-in-signs.rahu-libra`
- `vedic.planets-in-signs.rahu-pisces`
- `vedic.planets-in-signs.rahu-sagittarius`
- `vedic.planets-in-signs.rahu-scorpio`
- `vedic.planets-in-signs.rahu-taurus`
- `vedic.planets-in-signs.rahu-virgo`
- `vedic.states.graha-drishti`
- `vedic.states.graha-yuddha`
- `vedic.transits.ketu-moon-house-1`
- `vedic.transits.ketu-moon-house-10`
- `vedic.transits.ketu-moon-house-11`
- `vedic.transits.ketu-moon-house-12`
- `vedic.transits.ketu-moon-house-2`
- `vedic.transits.ketu-moon-house-3`
- `vedic.transits.ketu-moon-house-4`
- `vedic.transits.ketu-moon-house-5`
- `vedic.transits.ketu-moon-house-6`
- `vedic.transits.ketu-moon-house-7`
- `vedic.transits.ketu-moon-house-8`
- `vedic.transits.ketu-moon-house-9`
- `vedic.transits.nodal-axis`
- `vedic.transits.rahu-moon-house-1`
- `vedic.transits.rahu-moon-house-10`
- `vedic.transits.rahu-moon-house-11`
- `vedic.transits.rahu-moon-house-12`
- `vedic.transits.rahu-moon-house-2`
- `vedic.transits.rahu-moon-house-3`
- `vedic.transits.rahu-moon-house-4`
- `vedic.transits.rahu-moon-house-5`
- `vedic.transits.rahu-moon-house-6`
- `vedic.transits.rahu-moon-house-7`
- `vedic.transits.rahu-moon-house-8`
- `vedic.transits.rahu-moon-house-9`
- `vedic.transits.venus-moon-house-12`
- `vedic.transits.venus-moon-house-8`
- `vedic.vargas.d60-placement`

## Files that failed the initial wording sweep

File names are relative to `kb/`. Each line identifies the affected field or fields before correction.

- `lal-kitab/placements/house-1.yaml` — `user_text.en`
- `lal-kitab/placements/house-10.yaml` — `user_text.en`
- `lal-kitab/placements/house-11.yaml` — `user_text.en`
- `lal-kitab/placements/house-12.yaml` — `user_text.en`
- `lal-kitab/placements/house-2.yaml` — `user_text.en`
- `lal-kitab/placements/house-3.yaml` — `user_text.en`
- `lal-kitab/placements/house-4.yaml` — `user_text.en`
- `lal-kitab/placements/house-5.yaml` — `user_text.en`
- `lal-kitab/placements/house-6.yaml` — `user_text.en`
- `lal-kitab/placements/house-7.yaml` — `user_text.en`
- `lal-kitab/placements/house-8.yaml` — `user_text.en`
- `lal-kitab/placements/house-9.yaml` — `user_text.en`
- `life-areas/health/summary.yaml` — `always_append.user_text.en`, `always_append.user_text.kn`, `always_append.user_text.hi`
- `numerology/ank-jyotish/check-house-relocation-dwelling-root.yaml` — `user_text.en`, `user_text.kn`, `user_text.hi`
- `numerology/ank-jyotish/check-mobile-number-birth-root.yaml` — `user_text.en`, `user_text.kn`, `user_text.hi`
- `numerology/ank-jyotish/check-mobile-number-distinct-destiny-match.yaml` — `user_text.en`, `user_text.kn`, `user_text.hi`
- `numerology/ank-jyotish/check-mobile-number-missing-digits.yaml` — `user_text.en`
- `numerology/ank-jyotish/check-vehicle-number-root.yaml` — `user_text.en`, `user_text.kn`, `user_text.hi`
- `numerology/chaldean/check-business-name-brand-root.yaml` — `user_text.en`, `user_text.kn`, `user_text.hi`
- `numerology/chaldean/compound-10.yaml` — `user_text.en`
- `numerology/chaldean/compound-11.yaml` — `user_text.en`
- `numerology/chaldean/compound-12.yaml` — `user_text.en`
- `numerology/chaldean/compound-13.yaml` — `user_text.en`
- `numerology/chaldean/compound-14.yaml` — `user_text.en`
- `numerology/chaldean/compound-15.yaml` — `user_text.en`
- `numerology/chaldean/compound-16.yaml` — `user_text.en`
- `numerology/chaldean/compound-17.yaml` — `user_text.en`
- `numerology/chaldean/compound-18.yaml` — `user_text.en`
- `numerology/chaldean/compound-19.yaml` — `user_text.en`
- `numerology/chaldean/compound-20.yaml` — `user_text.en`
- `numerology/chaldean/compound-21.yaml` — `user_text.en`
- `numerology/chaldean/compound-22.yaml` — `user_text.en`
- `numerology/chaldean/compound-23.yaml` — `user_text.en`
- `numerology/chaldean/compound-24.yaml` — `user_text.en`
- `numerology/chaldean/compound-25.yaml` — `user_text.en`
- `numerology/chaldean/compound-26.yaml` — `user_text.en`
- `numerology/chaldean/compound-27.yaml` — `user_text.en`
- `numerology/chaldean/compound-28.yaml` — `user_text.en`
- `numerology/chaldean/compound-29.yaml` — `user_text.en`
- `numerology/chaldean/compound-30.yaml` — `user_text.en`
- `numerology/chaldean/compound-31.yaml` — `user_text.en`
- `numerology/chaldean/compound-32.yaml` — `user_text.en`
- `numerology/chaldean/compound-33.yaml` — `user_text.en`
- `numerology/chaldean/compound-34.yaml` — `user_text.en`
- `numerology/chaldean/compound-35.yaml` — `user_text.en`
- `numerology/chaldean/compound-36.yaml` — `user_text.en`
- `numerology/chaldean/compound-37.yaml` — `user_text.en`
- `numerology/chaldean/compound-38.yaml` — `user_text.en`
- `numerology/chaldean/compound-39.yaml` — `user_text.en`
- `numerology/chaldean/compound-40.yaml` — `user_text.en`
- `numerology/chaldean/compound-41.yaml` — `user_text.en`
- `numerology/chaldean/compound-42.yaml` — `user_text.en`
- `numerology/chaldean/compound-43.yaml` — `user_text.en`
- `numerology/chaldean/compound-44.yaml` — `user_text.en`
- `numerology/chaldean/compound-45.yaml` — `user_text.en`
- `numerology/chaldean/compound-46.yaml` — `user_text.en`
- `numerology/chaldean/compound-47.yaml` — `user_text.en`
- `numerology/chaldean/compound-48.yaml` — `user_text.en`
- `numerology/chaldean/compound-49.yaml` — `user_text.en`
- `numerology/chaldean/compound-50.yaml` — `user_text.en`
- `numerology/chaldean/compound-51.yaml` — `user_text.en`
- `numerology/chaldean/compound-52.yaml` — `user_text.en`
- `numerology/pythagorean/check-personal-baby-name-name-root.yaml` — `user_text.en`, `user_text.kn`, `user_text.hi`
- `vedic/dashas/vimshottari/check-business-name-trade-period.yaml` — `user_text.en`, `user_text.kn`, `user_text.hi`
- `vedic/dashas/vimshottari/check-vehicle-number-vehicle-period.yaml` — `user_text.en`, `user_text.kn`, `user_text.hi`
- `vedic/dashas/vimshottari/learning-upcoming.yaml` — `user_text.en`
- `vedic/doshas/bhakoot.yaml` — `remedy.user_text.en`, `remedy.user_text.hi`
- `vedic/doshas/mars-partnership.yaml` — `remedy.user_text.en`, `remedy.user_text.hi`
- `vedic/doshas/nadi.yaml` — `remedy.user_text.en`, `remedy.user_text.hi`
- `vedic/doshas/nodal-axis.yaml` — `remedy.user_text.en`
- `vedic/house-lords/lord-1-in-house-8.yaml` — `remedy.user_text.en`, `remedy.user_text.hi`
- `vedic/house-lords/lord-10-in-house-8.yaml` — `remedy.user_text.en`, `remedy.user_text.hi`
- `vedic/house-lords/lord-11-in-house-8.yaml` — `remedy.user_text.en`, `remedy.user_text.hi`
- `vedic/house-lords/lord-12-in-house-8.yaml` — `remedy.user_text.en`, `remedy.user_text.hi`
- `vedic/house-lords/lord-2-in-house-8.yaml` — `remedy.user_text.en`, `remedy.user_text.hi`
- `vedic/house-lords/lord-3-in-house-8.yaml` — `remedy.user_text.en`, `remedy.user_text.hi`
- `vedic/house-lords/lord-4-in-house-8.yaml` — `remedy.user_text.en`, `remedy.user_text.hi`
- `vedic/house-lords/lord-5-in-house-8.yaml` — `remedy.user_text.en`, `remedy.user_text.hi`
- `vedic/house-lords/lord-6-in-house-8.yaml` — `remedy.user_text.en`, `remedy.user_text.hi`
- `vedic/house-lords/lord-7-in-house-8.yaml` — `remedy.user_text.en`, `remedy.user_text.hi`
- `vedic/house-lords/lord-8-in-house-8.yaml` — `remedy.user_text.en`, `remedy.user_text.hi`
- `vedic/house-lords/lord-9-in-house-8.yaml` — `remedy.user_text.en`, `remedy.user_text.hi`
- `vedic/houses/house-8.yaml` — `remedy.user_text.en`, `remedy.user_text.hi`
- `vedic/houses/jupiter-house-1.yaml` — `user_text.en`
- `vedic/houses/jupiter-house-10.yaml` — `user_text.en`
- `vedic/houses/jupiter-house-11.yaml` — `user_text.en`
- `vedic/houses/jupiter-house-12.yaml` — `user_text.en`
- `vedic/houses/jupiter-house-2.yaml` — `user_text.en`
- `vedic/houses/jupiter-house-3.yaml` — `user_text.en`
- `vedic/houses/jupiter-house-4.yaml` — `user_text.en`
- `vedic/houses/jupiter-house-5.yaml` — `user_text.en`
- `vedic/houses/jupiter-house-6.yaml` — `user_text.en`
- `vedic/houses/jupiter-house-7.yaml` — `user_text.en`
- `vedic/houses/jupiter-house-8.yaml` — `user_text.en`
- `vedic/houses/jupiter-house-9.yaml` — `user_text.en`
- `vedic/houses/ketu-house-1.yaml` — `user_text.en`
- `vedic/houses/ketu-house-10.yaml` — `user_text.en`
- `vedic/houses/ketu-house-11.yaml` — `user_text.en`
- `vedic/houses/ketu-house-12.yaml` — `user_text.en`
- `vedic/houses/ketu-house-2.yaml` — `user_text.en`
- `vedic/houses/ketu-house-3.yaml` — `user_text.en`
- `vedic/houses/ketu-house-4.yaml` — `user_text.en`
- `vedic/houses/ketu-house-5.yaml` — `user_text.en`
- `vedic/houses/ketu-house-6.yaml` — `user_text.en`
- `vedic/houses/ketu-house-7.yaml` — `user_text.en`
- `vedic/houses/ketu-house-8.yaml` — `user_text.en`
- `vedic/houses/ketu-house-9.yaml` — `user_text.en`
- `vedic/houses/mars-house-1.yaml` — `user_text.en`
- `vedic/houses/mars-house-10.yaml` — `user_text.en`
- `vedic/houses/mars-house-11.yaml` — `user_text.en`
- `vedic/houses/mars-house-12.yaml` — `user_text.en`
- `vedic/houses/mars-house-2.yaml` — `user_text.en`
- `vedic/houses/mars-house-3.yaml` — `user_text.en`
- `vedic/houses/mars-house-4.yaml` — `user_text.en`
- `vedic/houses/mars-house-5.yaml` — `user_text.en`
- `vedic/houses/mars-house-6.yaml` — `user_text.en`
- `vedic/houses/mars-house-7.yaml` — `user_text.en`
- `vedic/houses/mars-house-8.yaml` — `user_text.en`
- `vedic/houses/mars-house-9.yaml` — `user_text.en`
- `vedic/houses/mercury-house-1.yaml` — `user_text.en`
- `vedic/houses/mercury-house-10.yaml` — `user_text.en`
- `vedic/houses/mercury-house-11.yaml` — `user_text.en`
- `vedic/houses/mercury-house-12.yaml` — `user_text.en`
- `vedic/houses/mercury-house-2.yaml` — `user_text.en`
- `vedic/houses/mercury-house-3.yaml` — `user_text.en`
- `vedic/houses/mercury-house-4.yaml` — `user_text.en`
- `vedic/houses/mercury-house-5.yaml` — `user_text.en`
- `vedic/houses/mercury-house-6.yaml` — `user_text.en`
- `vedic/houses/mercury-house-7.yaml` — `user_text.en`
- `vedic/houses/mercury-house-8.yaml` — `user_text.en`
- `vedic/houses/mercury-house-9.yaml` — `user_text.en`
- `vedic/houses/moon-house-1.yaml` — `user_text.en`
- `vedic/houses/moon-house-10.yaml` — `user_text.en`
- `vedic/houses/moon-house-11.yaml` — `user_text.en`
- `vedic/houses/moon-house-12.yaml` — `user_text.en`
- `vedic/houses/moon-house-2.yaml` — `user_text.en`
- `vedic/houses/moon-house-3.yaml` — `user_text.en`
- `vedic/houses/moon-house-4.yaml` — `user_text.en`
- `vedic/houses/moon-house-5.yaml` — `user_text.en`
- `vedic/houses/moon-house-6.yaml` — `user_text.en`
- `vedic/houses/moon-house-7.yaml` — `user_text.en`
- `vedic/houses/moon-house-8.yaml` — `user_text.en`
- `vedic/houses/moon-house-9.yaml` — `user_text.en`
- `vedic/houses/rahu-house-1.yaml` — `user_text.en`
- `vedic/houses/rahu-house-10.yaml` — `user_text.en`
- `vedic/houses/rahu-house-11.yaml` — `user_text.en`
- `vedic/houses/rahu-house-12.yaml` — `user_text.en`
- `vedic/houses/rahu-house-2.yaml` — `user_text.en`
- `vedic/houses/rahu-house-3.yaml` — `user_text.en`
- `vedic/houses/rahu-house-4.yaml` — `user_text.en`
- `vedic/houses/rahu-house-5.yaml` — `user_text.en`
- `vedic/houses/rahu-house-6.yaml` — `user_text.en`
- `vedic/houses/rahu-house-7.yaml` — `user_text.en`
- `vedic/houses/rahu-house-8.yaml` — `user_text.en`
- `vedic/houses/rahu-house-9.yaml` — `user_text.en`
- `vedic/houses/saturn-house-1.yaml` — `user_text.en`
- `vedic/houses/saturn-house-10.yaml` — `user_text.en`
- `vedic/houses/saturn-house-11.yaml` — `user_text.en`
- `vedic/houses/saturn-house-12.yaml` — `user_text.en`
- `vedic/houses/saturn-house-2.yaml` — `user_text.en`
- `vedic/houses/saturn-house-3.yaml` — `user_text.en`
- `vedic/houses/saturn-house-4.yaml` — `user_text.en`
- `vedic/houses/saturn-house-5.yaml` — `user_text.en`
- `vedic/houses/saturn-house-6.yaml` — `user_text.en`
- `vedic/houses/saturn-house-7.yaml` — `user_text.en`
- `vedic/houses/saturn-house-8.yaml` — `user_text.en`
- `vedic/houses/saturn-house-9.yaml` — `user_text.en`
- `vedic/houses/sun-house-1.yaml` — `user_text.en`
- `vedic/houses/sun-house-10.yaml` — `user_text.en`
- `vedic/houses/sun-house-11.yaml` — `user_text.en`
- `vedic/houses/sun-house-12.yaml` — `user_text.en`
- `vedic/houses/sun-house-2.yaml` — `user_text.en`
- `vedic/houses/sun-house-3.yaml` — `user_text.en`
- `vedic/houses/sun-house-4.yaml` — `user_text.en`
- `vedic/houses/sun-house-5.yaml` — `user_text.en`
- `vedic/houses/sun-house-6.yaml` — `user_text.en`
- `vedic/houses/sun-house-7.yaml` — `user_text.en`
- `vedic/houses/sun-house-8.yaml` — `user_text.en`
- `vedic/houses/sun-house-9.yaml` — `user_text.en`
- `vedic/houses/venus-house-1.yaml` — `user_text.en`
- `vedic/houses/venus-house-10.yaml` — `user_text.en`
- `vedic/houses/venus-house-11.yaml` — `user_text.en`
- `vedic/houses/venus-house-12.yaml` — `user_text.en`
- `vedic/houses/venus-house-2.yaml` — `user_text.en`
- `vedic/houses/venus-house-3.yaml` — `user_text.en`
- `vedic/houses/venus-house-4.yaml` — `user_text.en`
- `vedic/houses/venus-house-5.yaml` — `user_text.en`
- `vedic/houses/venus-house-6.yaml` — `user_text.en`
- `vedic/houses/venus-house-7.yaml` — `user_text.en`
- `vedic/houses/venus-house-8.yaml` — `user_text.en`
- `vedic/houses/venus-house-9.yaml` — `user_text.en`
- `vedic/muhurta/check-big-decision-muhurta-activity-limb.yaml` — `user_text.en`, `user_text.kn`, `user_text.hi`
- `vedic/muhurta/check-big-decision-muhurta-moon-support.yaml` — `user_text.en`, `user_text.kn`, `user_text.hi`
- `vedic/muhurta/check-big-decision-muhurta-tara-support.yaml` — `user_text.en`, `user_text.kn`, `user_text.hi`
- `vedic/nakshatras/purva-phalguni.yaml` — `user_text.en`
- `vedic/nakshatras/rohini.yaml` — `user_text.en`
- `vedic/planets/mercury.yaml` — `user_text.en`
- `vedic/relocation/check-house-relocation-destination-work.yaml` — `user_text.en`, `user_text.kn`, `user_text.hi`
- `vedic/signs/virgo.yaml` — `user_text.en`
- `vedic/states/baladi.yaml` — `remedy.user_text.en`
- `vedic/states/combustion.yaml` — `remedy.user_text.en`
- `vedic/states/graha-drishti.yaml` — `remedy.user_text.en`
- `vedic/states/graha-yuddha.yaml` — `remedy.user_text.en`
- `vedic/states/vakri.yaml` — `remedy.user_text.en`
- `vedic/states/vargottama.yaml` — `remedy.user_text.en`
- `vedic/states/yuti.yaml` — `remedy.user_text.en`
- `vedic/transits/career-watch.yaml` — `user_text.en`
- `vedic/transits/health-watch.yaml` — `user_text.en`
- `vedic/vargas/d1-placement.yaml` — `remedy.user_text.en`
- `vedic/vargas/d10-placement.yaml` — `remedy.user_text.en`
- `vedic/vargas/d12-placement.yaml` — `remedy.user_text.en`
- `vedic/vargas/d16-placement.yaml` — `remedy.user_text.en`
- `vedic/vargas/d2-placement.yaml` — `remedy.user_text.en`
- `vedic/vargas/d20-placement.yaml` — `remedy.user_text.en`
- `vedic/vargas/d24-placement.yaml` — `remedy.user_text.en`
- `vedic/vargas/d27-placement.yaml` — `remedy.user_text.en`
- `vedic/vargas/d3-placement.yaml` — `remedy.user_text.en`
- `vedic/vargas/d30-placement.yaml` — `remedy.user_text.en`
- `vedic/vargas/d4-placement.yaml` — `remedy.user_text.en`
- `vedic/vargas/d40-placement.yaml` — `remedy.user_text.en`
- `vedic/vargas/d45-placement.yaml` — `remedy.user_text.en`
- `vedic/vargas/d60-placement.yaml` — `remedy.user_text.en`
- `vedic/vargas/d7-placement.yaml` — `remedy.user_text.en`
- `vedic/vargas/d9-placement.yaml` — `remedy.user_text.en`, `remedy.user_text.hi`
- `vedic/yogas/kemadruma.yaml` — `remedy.user_text.en`
- `western/planets/neptune.yaml` — `remedy.user_text.en`
- `western/planets/pluto.yaml` — `remedy.user_text.en`
- `western/planets/uranus.yaml` — `remedy.user_text.en`

## Release work for people and integration

- Native reviewers should evaluate Kannada and Hindi phrasing, including the eleven navigation labels and the updated optional advice. Sanskrit glossary spellings and descriptive translations also need a language editor.
- Source reviewers should examine disputed rules, pending citations, chapter-only locators and any apparent close paraphrases. Editorial and native approvals are separate.
- Compare live Swiss Ephemeris output with dated fixtures using the recorded time scale, location and mode. Cover Lahiri positions, KP mode 5 cusps and sub-boundaries, Placidus polar failure, Western fallback and exact transit ingress and exit. Current synthetic checks use supplied positions or published reference tables.
- Exercise alias handling, privacy, locale fallback and one public tone through the eventual app. The repository contains the KB and validation tools; end-to-end rendering and live calculations remain integration work.

Run the full validator from the repository root with `python kb/governance/validation/check.py`.

## KB-32 convention review

Zero reading rules, meanings or fact keys added. Seven profile declarations, one named variant, two parameter tables and one synthetic convention record added. Five draft Vimshottari rule notes now describe the Julian default. Two Julian reference paths supplement the four preserved paths. The four recommendations awaiting Kiran are in shared/conventions/DECISIONS.md.

Convention sources are the supplied PRD v1.2 §8.4 and §8.4.5 requirements, STEP-04, Swiss Ephemeris API constants and rise/set calling conventions, IANA tzdb history for Asia/Kolkata, and the existing KB period and candidate-method tables. The source of the mean-node confirmation is the PRD. No book locator received a new verification status.

## KB-33 strength review

Added three draft rules, one component selector fact and one natural-benefic profile. Totals are 1,815 draft rules across ten systems, 402 fact keys and 661 glossary entries. Numerical evidence stays in the admin export. The published Raman worksheet awaits source verification.
## KB-34 review

Seven new numerology reflections and two house-strength components bring the totals to 1,824 draft rules, 406 fact keys and 661 glossary entries. S1 uses the corrected house weights, occupant terms and rising-type award. The published Raman matrix remains pending. The Moon table uses Raman/Santhanam by owner selection and retains the PVR variant for its original comparisons. New edition locators supplied in review are recorded pending primary inspection.
The strict and predominance Mercury rules agreed on all five known-time synthetic charts. The equal-companions probe distinguishes the methods. New speculative school mappings, including node-to-number compatibility, are labelled editorial.

## KB-51 editorial review (draft)

The owner’s public-copy policy and Jyoti’s 23 Nov review govern these edits. No new rules, fact keys, doctrine profiles or classical claims. Staff retain 661 glossary entries; users can access 660. EN, KN and HI are authored; TE, TA, ML, ES and FR inherit the English rewrites. Kannada and Hindi review remains pending.

| Example | Locale | Previous public copy | Draft public copy |
|---|---|---|---|
| maraka | en | Maraka | Removed, including its definition. |
| maraka | hi | मारक | Removed, including its definition. |
| neecha-bhanga-raja-yoga | en | A qualified form of relief for a weakly placed planet with further conditions for interpreting responsibility. | A planet may be less at ease in its sign. Other chart factors can shape how its connection to responsibility is read. |
| neecha-bhanga-raja-yoga | hi | कम बल की स्थिति में राहत के साथ जिम्मेदारी की व्याख्या के लिए अतिरिक्त शर्तों वाला मेल। | किसी राशि में ग्रह कम सहज माना जा सकता है। ज़िम्मेदारी से उसके संबंध को समझने में कुंडली के दूसरे संकेत भी मदद कर सकते हैं। |
| spirituality-house-lord | en | The current period lord rules house 9. You can explore this connection in the area reading. | This period may bring learning and long journeys into focus. |
| spirituality-house-lord | hi | वर्तमान दशा के स्वामी भाव 9 के भी स्वामी हैं। इस संबंध को क्षेत्र के विवरण में देख सकते हैं। | इस अवधि में इन विषयों पर ध्यान जा सकता है: सीख और लंबी यात्राएँ। |
| shrapit | en | Shrapit | Saturn with Rahu |
| shrapit | hi | श्रापित | राहु के साथ शनि |

The planted message `weakly placed` fails the public scanner in each locale. The single English card title “Transformation (Death card)” is scoped to its own glossary label and English fallback; free-standing use fails. All remedies expose the localized “Traditional practice” label. Matching uses qualitative wording. Bindu counts and edition-specific scores stay in staff evidence.

Scenario N1 uses the test alphabet ABCDEF. For S1 the optional Sripati method uses Mercury for the home-area midpoint and Jupiter for the work-area midpoint. The default whole-sign worksheet and its “modest” label remain the baseline.

Setup follow-up outside the KB: `scripts/codex-setup.sh` should also install `kb/requirements-dev.txt`.
