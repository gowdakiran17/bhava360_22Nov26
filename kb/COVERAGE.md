# Bhava360 knowledge base edition 1

This is a reviewable authoring edition. It contains 1,812 individually addressable YAML rules across ten systems, plus 661 glossary entries, calculation tables and product recipes. All 1,812 rules have English, Kannada and Hindi user text and retain draft status.

## Where to start

| Reading or tool | Records to inspect |
|---|---|
| Natal chart, placements and strengths | [D1 guide](vedic/D1.md), [108 graha/house readings](vedic/planets-in-houses/), [16 divisional sign mappings](vedic/vargas/methods.yaml), [six-component strength record](vedic/strength/shadbala/components.yaml), [Ashtakavarga contributions](vedic/strength/ashtakavarga/bindu.yaml) |
| Chapters, dates and matching | [Vimshottari](vedic/dashas/vimshottari/periods.yaml), [Yogini](vedic/dashas/yogini/periods.yaml), [32 yoga entries](vedic/yogas/), [transits](vedic/transits/evidence.yaml), [Panchang](vedic/panchang/limbs.yaml), [matching profile](vedic/matching/north-profile.yaml), [muhurta](vedic/muhurta/selection.yaml) |
| Jaimini and KP | [Jaimini](jaimini/), [Chara variant](jaimini/chara-dasha/kn-rao-candidate.yaml), [KP significators](kp/significators/bhava360.yaml), [249 exact KP intervals](kp/number-horary/249-divisions.yaml) |
| Western and numerology | [Tropical natal readings](western/natal/), [aspects and orbs](western/aspects/orbs.yaml), [Western timing and relationship methods](western/), [three numerology schools](numerology/), [compound numbers 10–52](numerology/chaldean/compounds.yaml) |
| Reflective and later systems | [78 tarot cards in both orientations](tarot/), [palmistry](palmistry/), [Vastu](vastu/), [Lal Kitab](lal-kitab/), [face reflection](face-reading/) |
| App composition | [All eleven life areas](life-areas/catalog.yaml), [all six checkers](checkers/), [Ask, reports, timelines and family views](modules/), [public and admin explanation fields](shared/explain/payload.yaml) |
| Evidence and editorial review | [Source and edition register](shared/source-editions/catalog.yaml), [typed facts](shared/fact-dictionary/catalog.yaml), [convention profiles](shared/conventions/profiles.yaml), [release flags](governance/release-flags/phases.yaml), [validation](governance/validation/check.py) |

## How a result is assembled

For a vehicle purchase, the admin trace records the registration’s digit total and comparison with the birth date. The public reading can reflect on the registration and delivery window. Each explanation links to its own predicate and source. The recipe deduplicates evidence. If a user with unknown birth time supplies a registration, the calculation can still provide its digit details. The missing fourth-house fact limits the personalized reading. A missing fact never supplies a reason for a verdict. [Vehicle recipe](checkers/vehicle-number/recipe.yaml)

For a career question, the present slot binds the active period lord and natal house. The upcoming slot needs the next dated period and its lord. The concerns slot requires a qualifying transit with its origin and dates. The action is a practical prompt in the user's language. Real dates, profile identity and place are bound by the consuming app. [Career recipe](life-areas/career/reading.yaml)

## Checks and remaining release work

The included Python checker requires PyYAML. Run `python kb/governance/validation/check.py` from the repository root. It checks rule shapes, ID uniqueness, location, source references, languages, predicates, unknown-fact behavior, area and checker references, tarot orientation coverage, numerical tables and representative yoga cases.

The raw Ashtakavarga distribution was checked against the published worked values transcribed in the pinned PyJHora test suite. A second calculation using the alternate Rashi multipliers reproduced all seven Rashi and Graha Pindas for the recorded chart. The Shadbala check covers the Sun’s 198-virupa Sthana subtotal. [Raw BAV/SAV example](vedic/strength/ashtakavarga/worked-reference.yaml) · [Reduction comparison](vedic/strength/ashtakavarga/pinda-comparison.yaml) · [Shadbala reference](vedic/strength/shadbala/worked-reference.yaml)

A verified citation supports the claim named in its `supports` field. The 1950 Sastri edition of *Phaladeepika*, for example, supports the Sakata formation and its angular-Moon cancellation. The practical prompts are original editorial adaptations. Many historical passages and regional variants still need edition-level review. The curated personal-name lexicon starts with five meanings and returns an unavailable meaning for unlisted names.

Production release requires native Kannada/Hindi review, approval of rule interpretations and doctrine variants, and integration tests against the actual chart and timing engines. The KB does not contain the Swiss Ephemeris engine, the app UI, licensed card artwork or a production support directory. The selected conventions for D60, the node and dasha-year defaults, and regional activity rules remain subject to product review. Nakshatra Nadi and gift purchase retain their PRD hold.

## KB-32 calculation conventions

The 1,812 rules and 401 fact keys are unchanged. Seven referenced profiles and one named Ashtakavarga variant now have registry entries. Two parameter tables cover civil time and rise/set. One synthetic convention record identifies the effective ephemeris. Vimshottari has six reference timelines across three year lengths and four levels (24 nested intervals).

## KB-33 strength coverage

Three new draft house component entries bring coverage to 1,815 rules and 402 fact keys. Scenario S1 covers all 42 planetary components and twelve house totals. The published Raman matrix awaits a source worksheet.
## KB-34 Western, numerology and strength

Added nine draft rules and four fact keys. The KB now holds 1,824 reading rules across ten systems and 406 fact keys. Four Western house systems, six technique orb tables and all 81 directed Ank root comparisons have reference coverage. Lo Shu arrows and planes remain deferred.

## KB-51 public copy

1,824 rules, 406 fact keys, and 661 staff glossary entries. The public glossary exposes 660 entries. Eleven Vimshottari and twelve rising-sign readings use life-area wording. Four dosha entries have localized display names; all ten standalone remedy records and their options use the shared practice label. Public copy is checked in eight locale bundles, including English fallback.

## KB-35 synthesis inputs (draft)

All 1,824 reading rules across ten systems carry internal evidence metadata. The Lagna table covers 108 cells and six strict Yogakarakas. The grade worksheet covers all nine grahas, with P1, P2 and P3 checking both inclusive band edges. The fact dictionary now contains 409 keys. The 660-entry public glossary and eight KB-51 locale bundles retain their existing copy.

## KB-48 birth-time confidence (draft)

Five declared precisions map to three tiers and 46 output rows. Four explanations cover exact, approximate, Moon-chart approximate, and time-unknown readings. The three internal confidence fields bring the fact dictionary to 412 keys. The 1,824 reading rules and 661 staff glossary entries retain their KB-35 counts.

## KB-36 and KB-37 synthesis and personal timing

Ten summary recipes use the five-stage pipeline. Eight ordered conflict rules, nine graha practice rows, and a single practice-selection policy accompany 25 synthesis cases. The personal calendar covers 14 day cases, seven-day composition and duration-weighted months. The localized catalogue adds 63 messages across three required languages. The dictionary now has 458 facts and the reading-rule inventory remains 1,824 across ten systems. Two glossary terms moved to staff-only access. [Synthesis](life-areas/pipeline.yaml) · [Daily policy](modules/home/day.yaml) · [Worked examples and source review](governance/REVIEW-REPORT.md)
