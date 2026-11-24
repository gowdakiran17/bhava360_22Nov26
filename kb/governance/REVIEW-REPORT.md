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

## KB-35 evidence, lordship and internal grade (draft)

The migration covers 1,824 source rules, including aliases. Zero new readings. Added three derived facts, two doctrine profiles and the mercury-strict variant. Re-run governance/review/assign-evidence.py to refresh the metadata. The direction-review YAML alongside it enumerates each conditional or disputed placement by canonical ID. Technical evidence stays in the staff export. Functional polarity replaces the generic lordship contribution at rung 3; the maraka flag cannot contribute. Staff may inspect uncertainty; dependent readings wait for chart evidence.

The 108 first-match cells reproduce the six classical Yogakarakas. Virgo Saturn remains Benefic, Leo Jupiter Neutral, Gemini Saturn Neutral, Aquarius Mercury Neutral, and Sagittarius Mars Benefic. Each records its MT-house alternative. Nodes inherit from the D1 sign owner, with association recorded as a variant. Venus transits in 8 and 12 from Moon use support while the Rao source's mixed reading and independent Vedha lookup are preserved.

Scenario P1 adds Saturn’s exaltation (+3), angle (+1), cancelling received aspects (0) and D9 debility (−1): 3.0, Strong. P2 totals −0.5, Weak; P3 totals 1.0, Moderate. The public vocabulary remains well supported, steady and modest. Cancellation uses distinct branches of the canonical Neecha Bhanga candidate, including exchange with the same planet’s dispositor. The grading arithmetic is Bhava360 practitioner convention.

Sources for the synthesis are BPHS (lordship and strength), Laghu Parashari (lordship and MT practice), Saravali and Phaladeepika (strength and cancellation), the existing KB dignity and natural-nature profiles, and the cited Rao transit tables. Newly listed classical passages await edition/locator verification. The existing all-quarter planetary Drik formula is labelled MODERN; BPHS's full Mercury/Jupiter treatment is a separate reading. The published Raman worksheet remains pending. Bhava Dig retains the Raman/PyJHora water classification for Cancer and records BPHS's grouping with Scorpio.

## KB-48 birth-time confidence (draft)

The MODERN/POPULAR product policy follows the supplied expert review (item 7, 23 Nov), PRD §8.4.2 and the KB-32 interval contract. The consultation-method C-VER-01..03 locator is supplied; independent verification remains pending. The owner confirmed ±5 minutes uses Tier B; Tier A except D60 is a documented alternative. Tier B may give stable Antar months and omits peak months and days. Tier C may retain a stable planet-only KP star or sub lord independently; cusp-based KP stays hidden.

The final cap follows KB-36 synthesis. Omitted factors supply no vote. The raw KB-35 worksheet and the internal Bhava Bala tie-break remain separate. The geometric civil twilight convention is MODERN and the classical time award can change when the interval crosses sunrise or sunset. All MVP confidence records carry rectified false. Future rectification acceptance belongs to KB-47.

### Worked output decisions

Dev uses the synthetic Chennai date with time unknown. The Lahiri Moon stays in Aquarius and crosses a nakshatra boundary during that date. The selected KP body is the Moon; the selected strength target is the Sun. Query conditions and the post-ladder input are synthetic probes. B1 is an invented component worksheet with ±15 minutes, a D10 crossing, and both possible Antar bounds in their respective common months. Each row below shows the resolver action for this bound example.

| Output | Dev | Scenario B1 |
|---|---|---|
| lagna | hide | show |
| houses-from-lagna | hide | show |
| lagna-transits | hide | show |
| moon-transits | show | show |
| daily-panchang | show | show |
| d9 | hide | show |
| d10 | hide | hide |
| d2 | hide | show |
| d4 | hide | show |
| d7 | hide | show |
| d12 | hide | show |
| d24 | hide | hide |
| d60 | hide | hide |
| d3 | hide | show |
| d16 | hide | show |
| d20 | hide | show |
| d27 | hide | show |
| d30 | hide | show |
| d40 | hide | show |
| d45 | hide | show |
| kp-cuspal-sub-lords | hide | hide |
| kp-house-significators | hide | hide |
| kp-cuspal-prashna | hide | hide |
| kp-planet-star-lord | hide | show |
| kp-planet-sub-lord | hide | show |
| maha-name | hide | show |
| maha-dates | hide | month-resolution |
| antar-name | hide | show |
| antar-dates | hide | month-resolution |
| pratyantar-windows | hide | hide |
| sookshma-windows | hide | hide |
| event-window | hide | month-resolution |
| peak-month | hide | hide |
| peak-day | hide | hide |
| lagna-lord-yogas | hide | show |
| promise-house | hide | show |
| promise-house-lord | hide | show |
| promise-occupants | hide | show |
| promise-house-aspects | hide | show |
| promise-functional-lordship | hide | show |
| promise-varga-lagna | hide | hide |
| promise-significator | show | show |
| promise-moon-relative | show | show |
| strength-house-term | show | show |
| final-card-grade | cap-moderate | cap-moderate |
| bhava-bala-tiebreak | hide | show |

Both final sample cards clamp Strong to Moderate. The B1 window exposes only November 2026 through February 2027. Dev’s strength house term uses the Moon reference.

| Draft public explanation | English | Kannada | Hindi |
|---|---|---|---|
| Dev | Without a birth time, you can explore the parts of a Moon-sign reading that stay consistent through the day. | ಜನನ ಸಮಯ ತಿಳಿದಿಲ್ಲದಿದ್ದರೆ, ದಿನವಿಡೀ ಸ್ಥಿರವಾಗಿರುವ ಚಂದ್ರರಾಶಿ ಆಧಾರಿತ ಅಂಶಗಳನ್ನು ನೋಡಬಹುದು. | जन्म समय मालूम न होने पर आप चंद्र राशि पर आधारित वे बातें देख सकते हैं जो पूरे दिन एक जैसी रहती हैं। |
| Scenario B1 | Your birth time is approximate. You can explore the parts of the reading that stay the same across that time. | ನಿಮ್ಮ ಜನನ ಸಮಯ ಅಂದಾಜಿನದು. ಆ ಅವಧಿಯಲ್ಲಿ ಒಂದೇ ರೀತಿ ಉಳಿಯುವ ಅಂಶಗಳನ್ನು ನೋಡಬಹುದು. | आपका जन्म समय अनुमानित है। आप पाठ के उन हिस्सों को देख सकते हैं जो उस अवधि में एक जैसे रहते हैं। |

Kannada and Hindi native review is pending. Planned locales inherit the English copy. No new classical claim or reading rule is introduced.

## KB-36 and KB-37 review

The ten life-area summaries use one five-step pipeline and eight conflict rungs. The worksheets cover 25 synthetic synthesis cases and 14 personal day cases, plus week and month boundaries. The fact dictionary adds 46 keys, including 32 yoga-activation reservations for KB-41. Their values remain unknown until a producer supplies them. All 1,824 reading entries retain draft status. The new copy catalogue has 63 EN/KN/HI messages, with five English-fallback locales and Kannada/Hindi review pending.

**Career worksheet C3.** Saturn owns the career sign and is Strong. The Lagna lord-strength, occupants, aspect balance, karakas and topic-varga factors support the promise. The Moon-repeat factor does not. Saturn Antar activates the area. Jupiter and Saturn reach the Lagna-based targets together, while the Moon-reference targets lack simultaneous confirmation. The earliest intersection starts March 10 and ends before April 22, 2032. Saturn-sign SAV of 26 marks the pace slower. The card stays Supportive. Its chips are “Work and responsibilities”, “Current chapter” and “Timing patterns”. The pace line is “This may unfold more gradually.” No practice attaches to this card.

**Tuesday worksheet D1.** The requested inputs independently exercise the mixed row. The Moon house contributes caution, Sampat Tara contributes support and the transit-sign SAV of 30 contributes support. Mars Antar focuses the day on learning. The result is Steady. Quiet work is the Good for item. A new task and a journey are the Go easy on items. After exclusions, the best local interval is 11:40–12:20. Its chips are “Moon movement”, “Daily star pattern” and “Current chapter”. D1 is a policy-input test. An eighth-house Moon and Sampat Tara do not arise together from one consistent pair of sidereal positions. The separate personalization cases use the synthetic Asha and Ravi birth instants and the same invented transit Moon in Anuradha. Their natal Moon sign/star indices are 1/4 and 10/23 (zero-based, Lahiri/Moshier). The resulting day tones are Supportive and Steady, respectively.

**Defaults reviewed.** The classical individual Lagna lists supersede the generic ownership order in eleven cells. Node occupied-house and association testimony take precedence over the dispositor. The low-bindu grade deduction is inactive. Janma Tara is neutral for daily composition. The editorial Moon phase term is half a point in either direction, neutral at exact conjunction or opposition. Month testimony uses elapsed duration with an exact tie neutral. Bhava Bala ordering, KP and Jaimini remain disabled by default. Western and numerology have separate cards.

**Sources and pending review.** The policies reference BPHS, Laghu Parashari, Phaladeepika, Jataka Parijata, Muhurta Chintamani, Prasna Marga, Uttara Kalamrita, B.V. Raman’s Moon BAV table and K.N. Rao’s double-transit method. Newly supplied classical locators remain pending edition-level verification. The arithmetic, rankings and copy are editorial decisions. Kiran retains approval of draft content. Production recipes and yoga activation belong to KB-38 and KB-41.

## KB-38 and KB-41 — area timing and yoga activation

Added 68 draft reading rules (18 fine-period readings and 50 yogas), 227 fact keys, 11 area recipes and 11 timing scenarios. The 50 new yogas comprise 32 Nabhasa shapes, four Kartari reference/direction combinations, Dharma-Karmadhipati, twelve other named combinations and one private Pravrajya/Sanyasa record. The 32 earlier activation reservations now have a producer. Both gate and activation are checked for all 82 formations. A single-participant formation cannot have a mixed grade; a separate softening exception can still select gentle wording. Kannada and Hindi remain pending native review.

**Scenario T2.** In the invented Aries chart Venus owns the partnership sign and occupies Libra. Its grade, the Venus karaka and stable favourable D9 support the promise. Strong Venus sets the Maha theme. Jupiter in Pisces is relevant to the Antar through its Mercury star; natal Mercury aspects the partnership sign. Jupiter occupies Libra in transit and Saturn reaches Libra from Leo. The intersection runs from March 10 up to April 12, 2032 (exclusive end). The window is Supportive with supported pace. Jupiter is sixth from Venus. That relationship qualifies how the experience may feel without creating or deleting the window. The accompanying sentence is “You may feel some pull between what you want and what circumstances allow.”

**Scenario Y4.** Sun at 120° and direct Mercury at 126° share a sign. Their 6° separation falls within the 14° direct combustion orb. Strong Sun and Moderate Mercury give the internal Full gate. With Saturn Maha and Mercury Antar the result is active and softened: “A gentle support may show in small ways.” With Saturn in both period roles it is background: “This quality may show more in its own periods.” A background observation supplies no event or tone.

**Defaults and owner review.** Venus is the marriage karaka for everyone; the classical gender-specific variant requires owner review. Rahu is a lower-priority editorial significator. Career D10 and stable D9 are available in MVP; other topic divisions stay deferred. Business, family-home and spirituality are editorial recipes awaiting Vedic review. The selected Nabhasa profile requires the specified houses to be occupied, excludes nodes and gives specific shapes precedence over counts. The alternative aspect formations, stricter Viparita association rule, optional narrow Mercury orb and the dispositor-exchange cancellation extension are labelled. Mahabhagya needs an explicit choice of classical branch. Pravrajya is confined to staff evidence.

**Sources.** BPHS (bhava, dasha and yoga chapters), Phaladeepika, Laghu Parashari, Saravali and Jataka Parijata supply the traditional references. K.N. Rao’s double-transit method is inherited from KB-36. Named functions in the PyJHora 5.0.6 wheel were checked as implementation comparisons. Pending classical locators, particularly the named-yoga variants, require edition-level review before approval. No new classical verse is marked verified on the basis of the software comparison.

## Batch 3 · KB-39, KB-40 and KB-42

The inventory contains 2,175 reading rules across ten systems and 897 registered facts. This batch adds 108 Lagna transit topics, 108 full aspects to houses, 12 targeted aspects, 36 same-sign pairs and 19 area-varga readings. Nine divisional readings are eligible for MVP synthesis. Ten are reserved for later releases. Eleven transit-area predicate maps and eight election activity profiles use the shared confidence and regional gates. The confidence matrix has 66 rows.

Classical locators awaiting edition checks retain pending status. Election offset and weekday tables were checked in the PyJHora 5.0.6 distribution. Murti nirnaya, Latta and node Vedha as independent transit readings, and Samvatsara, Ritu and Ayana names, are deferred. Election-star obstruction is a required input to marriage screening. New copy is draft and awaits Kannada and Hindi native review. [Synthetic worksheets](../examples/transits-vargas-elections.yaml)

## Batch 4 · KP judgement, Western contacts and matching

The corpus now contains 2,540 draft reading rules across ten systems and 916 registered facts. The 365 new readings comprise five KP judgements, 198 Western natal pair readings, 105 transit pair readings, 42 synastry readings, twelve MC signs, two return readings and one Papasamya comparison. The confidence matrix covers 71 outputs. Six checker worksheets cover complete, limited and private input paths. The lookup tables contain 319 name spellings and 52 Indian-market brands.

The Western point adjustments, the matching summary bands and the Papasamya unit weights are editorial conventions. KP retains true node, Krishnamurti mode 5 and Placidus without fallback. Koota totals and sensitive evidence remain internal. Native Kannada/Hindi review and first-party brand spelling checks remain pending; Sanskrit dictionary senses are distinguished from name usage.

## Batch 5 · Golden readings

Five named Swiss-file charts and five consultation worksheets cover thirty area traces. The inventory remains 2,540 draft readings across ten systems and grows to 922 fact keys. Fifteen legacy example files have scenario lookup aliases. Worked references include the Venus endpoints, Moon contributor cells, Sripati sandhi totals, a master Life Path, three Maha–Antar relationships and an explicitly pending second-cycle Chara case.

Asha and Ravi receive different daily and monthly tones for the same date. Dev receives a Moon-based reading and independently stable planet-only outputs. The sources include Swiss Ephemeris, the registered BPHS, Brihat Jataka, Phaladeepika and Saravali entries, Laghu Parashari and Raman’s Bhava Bala method. The deep-combust threshold and lunar phase grading scale are product conventions. Kannada and Hindi rewrites await native review. [Reference charts](../examples/fixtures/README.md)

## Batch 6 · Tajika, nakshatras and Prashna

Added 78 draft readings and 30 typed facts. The inventory is 2,618 rules and 952 facts. The annual and Prashna methods now share the inclusive mean deeptamsha. Scenario V1 binds a sidereal return and elects the year lord at the residence. Scenario Q1 tests a contact that the smaller orb would discard. Scenario N1 binds both stars, their quarters and lords, and derives a qualitative strength band. The private D60 reference contains 60 deity slots. Seven Muhurta groups cover 27 stars. KP regressions cover all twelve event groups.

The annual section uses its own clocks, with birthplace retained as a location variant. Post-MVP entries include advanced natal points and optional Sripati; Tri-pataki is deferred. Kannada and Hindi native review and edition-level classical locator checks are pending. Source leads include Tajika Neelakanthi, BPHS, Prasna Tantra, Prasna Marga, Muhurta Chintamani and KP Readers. Swiss Ephemeris provides the independent return calculation. Selected numerical tables were compared with the PyJHora 5.0.6 distribution.

## Batch 7 — final polish and gated systems

The corpus now has 2,732 draft rules across ten systems, 955 facts and 661 glossary entries. This batch adds 114 rules. The tarot expansion has 312 career/relationship lines, the Lo Shu table has eight planes, and all eight newly specified conditional clocks have true, false and unknown gate checks. J2 covers the second Chara cycle from year 64. Native review remains pending.

The synthetic D8 and L1 scenarios cover clock eligibility and flag isolation. Lal Kitab annual permutations need an identifiable edition before lookup can return placements. Nadi stays held. The software checks do not verify the original Rao or Rath texts. The source-review-batch-07.md inventory distinguishes original editorial wording from claims awaiting an edition. Tajika annual work and Prashna use the Batch 6 rules.

## Batch 8 — Jyoti’s Batch 6 review

Thirteen review items cover existing rules and tables. Counts remain 2,732 draft rules across ten systems and 955 facts. The four state families have 30 distinct localized prompts. The 30 Prashna cases include four pre-chart sensitive redirects and a same-sign applying conjunction. The revised V1 uses its actual Mercury–Jupiter square. Its year lord remains Venus. The KP synthetic case distinguishes Ketu’s direct and represented houses.

The profile uses a three-degree inclusive KP node conjunction orb. The year-lord strength tie uses the sign-aspect strength class, followed by Muntha preference. Simultaneous Moon applications or a residual election tie withhold the result. Draft native-language review remains pending. The supplied classical locators are recorded as review references where the edition has not been checked.

## Batch 9 — Jyoti’s Batch 7 review

The eleven review items revise existing material. Rule and fact counts remain 2,732 and 955. Each known-time fixture now has distinct area bands. Dev’s six Lagna-based promises remain withheld. The health worksheet records resistance separately from the primary constitution reading. Wealth requires both resources and gains to confirm its highest band. The one-step limit and tie handling are editorial.

All 82 yoga entries have revised Kannada and Hindi text, pending native review. Eight conditional dasha messages are distinct in each required locale. All 120 Lal Kitab placement readings are marked pending_source. The public gate requires a single verified edition for both placements and all 120 annual rows. Joshi 1952 remains a candidate. The source register tracks 1,185 pending blocks and 304 chapter-only blocks; suggested books are leads for review. Chara Antar order and Sthira karakas still await edition checks.

## Batch 10 source review

Across 5,386 authored citation blocks, 241 have a high-confidence chapter locator, 485 have an edition-dependent locator, and 62 await verification. The latter include nine nested japa citations and the primary Mula edition candidate. There are 451 newly classified editorial blocks, 959 earlier editorial attributions, 305 chapter-only citations, two supplied in the brief and 2,881 previously verified blocks. Run the source audit to reproduce the breakdown. Every pending block has an explicit verification task.

The review used Jyoti’s supplied map. Chapter-location confidence does not establish that an edition or verse was independently inspected. Lal Kitab remains gated on the single Joshi 1952 edition. Nadi remains held.

## Batch 11 final review

The historical 1,185 pending reading-rule citations plus 44 top-level citations in other authored files and one excluded template account for the locator map’s 1,230 top-level blocks. Including the nine nested remedy citations gives 1,238 authored blocks in that historical cohort. The current all-depth audit covers 5,388 source blocks. Two new candidate health locators bring the pending count to 64. The remaining counts are 2,881 verified, 241 verified_locator, 485 locator_medium, 305 chapter-only, 451 editorial, 959 editorial-no-classical-claim and two supplied-in-brief.

The health witness changes Asha’s health promise to Moderate and her card to Steady. Kabir has a new witness with the same band. The other three fixtures keep their recorded results. A Tajika conjunction can establish application while leaving the question’s direction unresolved. All 120 gated Lal Kitab placement texts await native review. The two yoga copy revisions also await native review.
